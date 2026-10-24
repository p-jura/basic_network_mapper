"""Project-scoped deterministic identities, deliberately conservative."""
import json
from uuid import UUID, uuid5


def identity(project_id, *parts):
    return str(uuid5(UUID(project_id), json.dumps(parts, separators=(',', ':'), ensure_ascii=False)))


def context(run):
    if run['target_id'] is None:
        return 'local:' + run['scope_id']
    if run['context_status'] == 'known':
        return 'known:' + run['context_id']
    # A default SNMP context does not prove a shared VRF between switches.
    return 'target:' + run['target_id'] + ':' + run['context_status'] + ':' + run['context_id']
