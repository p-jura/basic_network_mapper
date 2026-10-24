import asyncio
from dataclasses import asdict
import ipaddress
import sqlite3

from .config import Limits, target_id
from .errors import MapperError
from .models import TableResult
from .discovery.basic import collect_basic, preview as basic_preview
from .collectors.snmp import collect_snmp
from .collectors.ssh import collect_ssh
from .storage.repository import cycle_lock


def in_ranges(ip, ranges):
    return any(ipaddress.IPv4Address(ip) in ipaddress.IPv4Network(n) for n in ranges)


async def preview(config, adapter=None):
    limits = Limits(**config.get("limits", {}))
    seeds = config.get("seeds", [])
    ranges = config.get("allowed_ranges", [])
    if len(seeds) > limits.recursion_devices:
        raise MapperError("DEVICE_BUDGET_EXCEEDED")
    if ranges and any(not in_ranges(seed["ip"], ranges) for seed in seeds):
        raise MapperError("SEED_OUTSIDE_SCOPE")
    result = {"project_id": config["project_id"], "basic": None, "targets": [{"ip": s["ip"], "port": s["port"], "profile_id": s["profile_id"], "context": s.get("context", "")} for s in seeds], "limits": asdict(limits), "recursive": config.get("recursive", False), "allowed_ranges": ranges, "sends_probes": False}
    if config.get("basic"):
        result["basic"] = await basic_preview(config["basic"], limits, adapter)
    if not seeds and not config.get("basic"):
        raise MapperError("NO_SOURCES_CONFIGURED")
    return result


async def run_cycle(repo, config, cancel=None, *, adapter=None, snmp_collector=collect_snmp, ssh_collector=collect_ssh):
    limits = Limits(**config.get("limits", {}))
    cancel = cancel or asyncio.Event()
    with cycle_lock(repo.directory.parent):
        plan = await preview(config, adapter)
        repo.recover_interrupted()
        repo.prune()
        cycle_id = repo.begin_cycle(plan)
        queue = asyncio.Queue(maxsize=2)
        tasks = set()
        managed = asyncio.Semaphore(limits.parallel)
        ssh_gate = asyncio.Semaphore(limits.ssh_parallel)
        seen = set()
        depths = {}
        incomplete = False
        execution = "finished"
        reason = None

        def spawn(coro):
            task = asyncio.create_task(coro)
            tasks.add(task)
            task.add_done_callback(tasks.discard)

        async def produce(iterator, source):
            try:
                async for result in iterator:
                    await queue.put(result)
            except asyncio.CancelledError:
                raise
            except Exception:
                await queue.put(TableResult(source, "collector", status="transport_error", reason="COLLECTOR_FAILED"))
            finally:
                # put_nowait prevents cleanup deadlock after the consumer stops.
                try:
                    queue.put_nowait(None)
                except asyncio.QueueFull:
                    pass

        async def managed_producer(seed, profile):
            async with managed:
                if cancel.is_set():
                    await queue.put(TableResult("ssh" if profile["type"] == "ssh" else "snmp", "session", status="cancelled", reason="CANCELLED", target_id=seed["target_id"]))
                    return
                if profile["type"] == "ssh":
                    async with ssh_gate:
                        await produce(ssh_collector(seed, profile, limits, cancel), "ssh")
                else:
                    await produce(snmp_collector(seed, profile, limits, cancel), "snmp")

        def schedule(seed, depth, origin):
            ident = target_id(config["project_id"], seed)
            if ident in seen:
                return False
            seen.add(ident)
            depths[ident] = depth
            repo.register_target(ident, seed, origin)
            seed = {**seed, "target_id": ident}
            spawn(managed_producer(seed, config["profiles"][seed["profile_id"]]))
            return True

        try:
            if config.get("basic"):
                spawn(produce(collect_basic(config["basic"], limits, cancel, adapter), "os_interfaces"))
            for seed in config.get("seeds", []):
                schedule(seed, 0, "seed")
            async with asyncio.timeout(limits.cycle_timeout):
                while tasks or not queue.empty():
                    # A short event wait also observes producers finishing while
                    # the bounded queue is full and their sentinel is omitted.
                    try:
                        result = await asyncio.wait_for(queue.get(), 0.1)
                    except TimeoutError:
                        continue
                    if result is None:
                        continue
                    repo.write_result(cycle_id, result)
                    if config.get("recursive") and result.target_id and not cancel.is_set():
                        for obs in result.observations:
                            ip = obs.payload.get("management_ip") if obs.kind == "lldp_neighbor" else None
                            if not ip or not in_ranges(ip, config.get("allowed_ranges", [])):
                                continue
                            profile_id = config["recursive_profile_id"]
                            profile = config["profiles"][profile_id]
                            seed = {"ip": ip, "port": 22 if profile["type"] == "ssh" else 161, "profile_id": profile_id}
                            if target_id(config["project_id"], seed) in seen:
                                continue
                            depth = depths.get(result.target_id, 0) + 1
                            if depth > limits.recursion_depth or len(seen) >= limits.recursion_devices:
                                incomplete = True
                                reason = "RECURSION_BUDGET"
                                continue
                            schedule(seed, depth, "lldp")
        except TimeoutError:
            cancel.set(); execution = "cancelled"; reason = "CYCLE_DEADLINE"; incomplete = True
        except asyncio.CancelledError:
            cancel.set(); execution = "cancelled"; reason = "CANCELLED"; incomplete = True
        except BaseException:
            cancel.set()
            with repo.db:
                repo.db.execute("UPDATE cycles SET execution_status='failed',coverage_status='partial',reason='WRITE_OR_CONTROL_FAILED' WHERE cycle_id=?", (cycle_id,))
            raise
        finally:
            remaining = list(tasks)
            for task in remaining:
                task.cancel()
            await asyncio.gather(*remaining, return_exceptions=True)
        if cancel.is_set():
            execution = "cancelled"; reason = reason or "CANCELLED"; incomplete = True
        sid = repo.publish(cycle_id, execution, reason, force_partial=incomplete)
        return {"cycle_id": cycle_id, "snapshot_id": sid, "execution_status": execution, "coverage_status": repo.snapshots()[0]["coverage_status"]}
