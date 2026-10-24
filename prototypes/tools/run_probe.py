import argparse
import getpass
import ipaddress
import os
import subprocess
import sys
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("mode", choices=["snmp2", "snmp3", "ssh"])
args = parser.parse_args()
env = os.environ.copy()
env["MAPPER_TARGET_IP"] = str(
    ipaddress.IPv4Address(input("IPv4 urządzenia laboratoryjnego: ").strip())
)
if args.mode == "snmp2":
    env["MAPPER_SNMP2_COMMUNITY"] = getpass.getpass("Community RO: ")
elif args.mode == "snmp3":
    env["MAPPER_SNMP3_USER"] = input("Użytkownik SNMPv3: ").strip()
    env["MAPPER_SNMP3_AUTH_KEY"] = getpass.getpass("Hasło uwierzytelniania: ")
    env["MAPPER_SNMP3_PRIV_KEY"] = getpass.getpass("Hasło szyfrowania: ")
else:
    env["MAPPER_SSH_USER"] = input("Użytkownik SSH RO: ").strip()
    env["MAPPER_SSH_PASSWORD"] = getpass.getpass("Hasło SSH (puste = klucz/agent): ")
    env["MAPPER_KNOWN_HOSTS"] = str(
        Path(input("Ścieżka do zweryfikowanego known_hosts: ").strip()).expanduser()
    )
script = "probe_ssh.py" if args.mode == "ssh" else "probe_snmp.py"
command = [sys.executable, str(Path(__file__).with_name(script))]
if args.mode != "ssh":
    command.append(args.mode)
raise SystemExit(subprocess.run(command, env=env, check=False).returncode)
