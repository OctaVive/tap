#!/usr/bin/env python3
"""Run two disposable VMs over an inherited socketpair, with no host NIC/route.
Roots must already contain reviewed binaries/config and real M07 handoff records.
This development lifecycle diagnostic is not the full M09 acceptance driver.
"""
import argparse
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import threading
import time
from artifact_fault import corrupt_archives, restore_archives, workload_manifests
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from deadline import arm_deadline
from clock_evidence import clock_bounds
from network_evidence import validate_network_proof

REVOCATION_SCENARIOS = ('approval-revoke', 'admission-revoke', 'scan-policy-change', 'lease-expiry', 'certificate-revoke-rotate')
DENIAL_SCENARIOS = ('deny-signature', 'deny-worker', 'deny-expiry', 'deny-matrix')
DENIAL_FIELDS = ('version', 'operation', 'id', 'worker', 'incarnation', 'app', 'deployment', 'generation', 'nonce', 'key-id', 'expiry', 'policy-hash', 'spec-hash', 'target', 'spec', 'log-limit')

def network_proof(serial, dual=False):
    prefix = 'M09-OPERATOR-NETWORK '
    records = [json.loads(line.removeprefix(prefix)) for line in complete_lines(serial) if line.startswith(prefix)]
    if len(records) != 1:
        raise RuntimeError('missing or duplicated network proof')
    try:
        return validate_network_proof(records[0], dual=dual)
    except ValueError as error:
        raise RuntimeError(str(error)) from error


class SerialEvidence:
    """Bounded root-only protocol, separate from console/kernel diagnostics."""
    def __init__(self, connection, path, limit=1 << 20):
        self.connection, self.path, self.limit = connection, path, limit
        self.lock = threading.Lock()
        self.data = b''
        self.error = None
        self.closing = False
        self.thread = threading.Thread(target=self.collect, daemon=True)
        self.thread.start()

    def collect(self):
        try:
            with self.path.open('xb', buffering=0) as stream:
                while not self.closing:
                    try:
                        chunk = self.connection.recv(4096)
                    except socket.timeout:
                        continue
                    if not chunk:
                        if not self.closing:
                            raise RuntimeError('private evidence channel closed')
                        break
                    with self.lock:
                        if len(self.data)+len(chunk) > self.limit:
                            raise RuntimeError('private evidence exceeds bound')
                        self.data += chunk
                        stream.write(chunk)
        except Exception as error:
            if not self.closing:
                with self.lock:
                    self.error = str(error)

    def snapshot(self):
        with self.lock:
            if self.error is not None:
                raise RuntimeError(self.error)
            return self.data.decode('ascii', errors='strict')

    def close(self):
        self.closing = True
        try:
            self.connection.shutdown(socket.SHUT_RD)
        except OSError:
            pass
        self.thread.join(timeout=3)


def initialize_guest_clock(control, process, role, record, evidence=None):
    """One startup exchange with a role-pinned disposable guest, never retried."""
    control.settimeout(.1)
    def frame(prefix, timeout):
        deadline = time.monotonic()+timeout
        raw = b''
        while time.monotonic() < deadline:
            if evidence is not None:
                frames = [line for line in complete_lines(evidence.snapshot()) if line.startswith(prefix)]
                if len(frames) > 1:
                    raise RuntimeError('duplicated clock initialization frame')
                if frames:
                    return frames[0]
                time.sleep(.005)
            else:
                try:
                    value = control.recv(1)
                except socket.timeout:
                    value = None
                if value == b'':
                    raise RuntimeError('clock initialization channel closed')
                if value:
                    raw += value
                    if len(raw) > 512:
                        raise RuntimeError('clock initialization frame exceeds bound')
                    if value == b'\n':
                        result = raw[:-1].decode('ascii')
                        if not result.startswith(prefix):
                            raise RuntimeError('unexpected clock initialization frame')
                        return result
            if process.poll() is not None:
                raise RuntimeError('guest exited before clock initialization')
        raise RuntimeError('clock initialization timeout')

    if frame('M09-CLOCK-INIT-READY ', 100) != 'M09-CLOCK-INIT-READY '+role:
        raise RuntimeError('incorrect clock initialization role')
    send = time.time_ns()
    record.update(role=role, send_ns=send)
    control.sendall(('initialize-clock '+str(send)+'\n').encode('ascii'))
    response = frame('M09-CLOCK-INITIALIZED ', 5)
    received = time.time_ns()
    record['receive_ns'] = received
    value = json.loads(response.removeprefix('M09-CLOCK-INITIALIZED '))
    record['guest'] = value
    if (not isinstance(value, dict) or set(value) != {'role','before_ns','applied_ns','after_ns'}
            or value['role'] != role
            or any(type(value[key]) is not int for key in ('before_ns','applied_ns','after_ns'))
            or value['applied_ns'] != send
            or abs(value['before_ns']-send) > 120_000_000_000
            or not send <= value['after_ns'] <= received
            or not 0 <= received-send <= 250_000_000):
        raise RuntimeError('invalid or delayed clock initialization')
    record['valid'] = True
    control.sendall(b'clock-initialized\n')


def observe_pair_clocks(runtime_control, controller_control, evidence, controller_process):
    controller_control.settimeout(.1)
    def line(deadline):
        raw = b''
        while time.monotonic() < deadline:
            try:
                value = controller_control.recv(1)
            except socket.timeout:
                if controller_process.poll() is not None:
                    raise RuntimeError('controller exited before clock observation')
                continue
            if not value:
                raise RuntimeError('controller private clock channel closed')
            raw += value
            if len(raw) > 64:
                raise RuntimeError('private clock frame exceeds bound')
            if value == b'\n':
                return raw[:-1].decode('ascii')
        raise RuntimeError('private clock observation timeout')
    if line(time.monotonic()+100) != 'M09-CLOCK-READY':
        raise RuntimeError('controller clock observer unavailable')
    send = time.time_ns()
    controller_control.sendall(b'sample-clock\n')
    frame = line(time.monotonic()+5)
    received = time.time_ns()
    match = re.fullmatch(r'M09-CLOCK ([0-9]{19})', frame)
    if match is None:
        raise RuntimeError('invalid controller clock frame')
    controller = dict(send_ns=send,receive_ns=received,guest_ns=int(match[1]))
    send = time.time_ns()
    runtime_control.sendall(b'sample-clock\n')
    deadline = time.monotonic()+5
    while time.monotonic() < deadline:
        frames = [value for value in complete_lines(evidence.snapshot()) if value.startswith('M09-CLOCK ')]
        if frames:
            received=time.time_ns()
            if len(frames)!=1 or not re.fullmatch(r'M09-CLOCK [0-9]{19}',frames[0]):
                raise RuntimeError('invalid runtime clock frame')
            runtime=dict(send_ns=send,receive_ns=received,guest_ns=int(frames[0].split()[1]))
            return clock_bounds(runtime,controller)
        time.sleep(.01)
    raise RuntimeError('runtime clock observation timeout')


def source_snapshot():
    repo = Path(__file__).resolve().parents[3]
    files = set()
    for pattern in ('internal/**/*.go', 'cmd/**/*.go', 'infra/runtime/**/*.go', 'infra/runtime/**/*.py', 'infra/runtime/**/*.sh', 'infra/runtime/services/*', 'infra/runtime/tools.lock.json', 'infra/runtime/tap-runtime.apparmor', 'docs/project/specifications/runtime-execution.md', 'docs/project/specifications/deployment-agent.md', 'docs/project/specifications/configuration-policy.md', 'docs/project/PH1/P1M09/testing/constituents.json', 'go.mod', 'go.sum', 'api/runtime-v3.schema.json', 'docs/architecture/docker-security.md'):
        files.update(path for path in repo.glob(pattern) if path.is_file())
    return {str(path.relative_to(repo)): hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(files)}


def complete_lines(serial):
    # QEMU appends serial output asynchronously; a trailing fragment is not a
    # complete enrollment/acknowledgment and must be retried, never decoded.
    return [line.rstrip('\r') for line in serial.split('\n')[:-1]]


def connect_control(path, process):
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        connection = socket.socket(socket.AF_UNIX)
        connection.settimeout(2)
        try:
            connection.connect(str(path))
            return connection
        except OSError:
            connection.close()
            if process.poll() is not None:
                break
            time.sleep(.1)
    raise RuntimeError('private serial connection unavailable')


def operator_proof(serial, phase, app_ids):
    records = [json.loads(line.removeprefix('M09-OPERATOR-STATE '))
               for line in complete_lines(serial) if line.startswith('M09-OPERATOR-STATE ')]
    selected = [record for record in records if record.get('phase') == phase]
    if len(selected) != len(app_ids) or {record.get('app_id') for record in selected} != app_ids:
        raise RuntimeError('missing or duplicated operator state: ' + phase)
    for record in selected:
        if (any(type(record.get(key)) is not int or record[key] < 0 for key in ('containers', 'networks', 'running'))
                or record['running'] > record['containers']):
            raise RuntimeError('invalid operator counts')
    return {record['app_id']: (record['containers'], record['networks'], record['running']) for record in selected}


def denial_step_proof(serial, label, expected_manifests):
    prefix = 'M09-OPERATOR-DENIAL-'+label+' '
    records = [json.loads(line.removeprefix(prefix)) for line in complete_lines(serial) if line.startswith(prefix)]
    if len(records) != 1:
        raise RuntimeError('missing or duplicated denial proof')
    proof = records[0]
    if (sorted(proof.get('images_absent', [])) != expected_manifests
            or any(proof.get(key) != value for key, value in {'containers': 0, 'networks': 3, 'running': 0, 'candidate_reservations': 0, 'recorded_resources': 0, 'command_count': 1}.items())):
        raise RuntimeError('denial mutated execution state')
    return proof


def restart_proof(serial, app_ids):
    acknowledgments = re.findall(r'^M09-OPERATOR-ACK restart-agent old=(\d+) new=(\d+)\r?$', serial, re.M)
    if len(acknowledgments) != 1:
        raise RuntimeError('missing or duplicated restart acknowledgment')
    old, new = map(int, acknowledgments[0])
    if min(old, new) <= 1 or old == new:
        raise RuntimeError('agent PID did not change')
    before = operator_proof(serial, 'before-restart', app_ids)
    after = operator_proof(serial, 'after-restart', app_ids)
    if (before != after or sum(value[0] for value in before.values()) < 1
            or any(value[0] != value[2] for value in before.values())):
        raise RuntimeError('restart changed resource counts or had no live candidate')
    return {'old_pid': old, 'new_pid': new, 'before': before, 'after': after}


def crash_proof(serial):
    acknowledgments = re.findall(r'^M09-OPERATOR-ACK crash-probe old=(\d+) new=(\d+)\r?$', serial, re.M)
    records = [json.loads(line.removeprefix('M09-OPERATOR-FAULT '))
               for line in complete_lines(serial) if line.startswith('M09-OPERATOR-FAULT ')]
    if len(acknowledgments) != 1 or len(records) != 1:
        raise RuntimeError('missing or duplicated probe crash proof')
    old, new = map(int, acknowledgments[0])
    record = records[0]
    ids = record.get('resource_ids', [])
    if (old <= 1 or new <= 1 or old == new or record.get('old_pid') != old
            or not re.fullmatch(r'[0-9a-f-]{36}', record.get('command_id', ''))
            or len(ids) != 2 or len(set(ids)) != 2
            or any(not re.fullmatch(r'[0-9a-f]{64}', value) for value in ids)):
        raise RuntimeError('invalid probe crash boundary')
    return dict(record, new_pid=new)


def stop_disposable_vm(path):
    # This is a fresh snapshot VM. Product stop/remove and a final signed clean
    # probe precede teardown; no guest disk is reused or adopted after quit.
    with socket.socket(socket.AF_UNIX) as monitor:
        monitor.settimeout(3)
        monitor.connect(str(path))
        response = b''
        while b'(qemu)' not in response:
            chunk=monitor.recv(4096)
            if not chunk or len(response)>8192:
                raise RuntimeError('monitor greeting missing')
            response+=chunk
        monitor.sendall(b'quit\n')
        # QEMU exits instead of returning a prompt. wait() verifies termination.


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-root', required=True)
    parser.add_argument('--controller-root', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--kernel', required=True)
    parser.add_argument('--initrd', required=True)
    parser.add_argument('--scenario', choices=('lifecycle', 'agent-restart', 'probe-crash', 'corrupt-archive', 'network-ipv4', 'network-dual-stack')+REVOCATION_SCENARIOS+DENIAL_SCENARIOS, default='lifecycle')
    args = parser.parse_args()
    os.umask(0o077)
    if os.geteuid() != 0 or shutil.disk_usage('/').free < 24 << 30:
        raise RuntimeError('root and at least 24GiB free required')
    out = Path(args.output)
    out.mkdir(mode=0o700)
    source = source_snapshot()
    (out/'source-manifest.json').write_text(json.dumps(source, indent=2)+'\n')
    roots = [Path(args.runtime_root), Path(args.controller_root)]
    for root in roots:
        if not (root/'etc/m09-disposable-guest').is_file():
            raise RuntimeError('disposable guest root required')
    sockets = socket.socketpair()
    processes = []
    controls = []
    evidence = None
    errors = []
    lifecycle_complete=False
    restart = None
    fault = None
    relay_checks = []
    quarantine = None
    artifact_backups = []
    image_absence = None
    expected_manifests = None
    denial_proofs = {}
    network = None
    clocks = None
    clock_initialization = {}
    final_inventory = None
    app_ids = set()
    # Leave sixty seconds of the catalog's 300-second outer budget for exact
    # owned VM teardown, evidence finalization and process-group reaping.
    cancel_deadline = arm_deadline(240)
    try:
        agent_config_path = roots[0]/'var/lib/tap-runtime/agent/config.json'
        agent_configuration = json.loads(agent_config_path.read_text())
        agent_configuration['origin'] = 'https://[fd00:9::11]:9443' if args.scenario == 'network-dual-stack' else 'https://192.0.2.11:9443'
        agent_config_path.write_text(json.dumps(agent_configuration))
        if args.scenario == 'corrupt-archive':
            expected_manifests = corrupt_archives(roots[0], roots[1], out, artifact_backups)
        elif args.scenario in DENIAL_SCENARIOS:
            expected_manifests = workload_manifests(roots[0], roots[1])
        for index, (role, root) in enumerate(zip(('runtime', 'controller'), roots)):
            if index == 1:
                deadline = time.monotonic()+100
                while time.monotonic() < deadline:
                    serial = evidence.snapshot()
                    lines = [line for line in complete_lines(serial) if line.startswith('M09-PROCESS-ENROLLMENTS ')]
                    if lines:
                        raw = lines[-1].removeprefix('M09-PROCESS-ENROLLMENTS ')
                        if len(raw) > 65536:
                            raise RuntimeError('oversized root enrollment')
                        records = json.loads(raw)
                        if not isinstance(records, list) or not 1 <= len(records) <= 16:
                            raise RuntimeError('invalid root enrollment')
                        target = root/'var/lib/m09-process/enrollments.json'
                        target.write_text(json.dumps({"enrollments": records}))
                        target.chmod(0o600)
                        os.chown(target,1002,1002)
                        app_ids = {record['backend']['AppID'] for record in records}
                        fixture_path = root/'var/lib/m09-process/fixture.json'
                        fixture = json.loads(fixture_path.read_text())
                        fixture['scenario'] = args.scenario
                        fixture_path.write_text(json.dumps(fixture))
                        config_path = root/'var/lib/m09-process/config.json'
                        configuration = json.loads(config_path.read_text())
                        configuration['listen'] = '[::]:9443' if args.scenario == 'network-dual-stack' else '192.0.2.11:9443'
                        config_path.write_text(json.dumps(configuration))

                        break
                    if processes[0].poll() is not None:
                        raise RuntimeError('runtime exited before enrollment')
                    time.sleep(.2)
                else:
                    raise RuntimeError('runtime enrollment timeout')
            image = out/(role+'.raw')
            with image.open('xb') as stream:
                stream.truncate(4 << 30)
            subprocess.run(['mkfs.ext4','-q','-F','-d',str(root),str(image)],check=True,timeout=90)
            serial = out/(role+'.log')
            serial.touch(mode=0o600)
            command = ['qemu-system-x86_64','-enable-kvm','-machine','q35','-cpu','host','-smp','2','-m','2560' if index == 0 else '1024',
                       '-fw_cfg','name=opt/tap/m09-role,string='+role,
                       '-kernel',args.kernel,'-initrd',args.initrd,'-append','root=/dev/vda rw noresume console=ttyS0 apparmor=1 security=apparmor',
                       '-drive',f'file={image},format=raw,if=virtio,snapshot=on','-netdev',f'socket,id=lab,fd={sockets[index].fileno()}',
                       '-device',f'virtio-net-pci,netdev=lab,mac=52:54:00:09:00:{10+index:02x}','-display','none','-serial',f'file:{serial}','-monitor','unix:'+str(out/(role+'.monitor'))+',server=on,wait=off','-no-reboot']
            if role == 'runtime':
                command += ['-serial', 'null']
            command += ['-serial', 'unix:'+str(out/(role+'.control'))+',server=on,wait=off']
            stderr = (out/(role+'.stderr')).open('wb')
            process = subprocess.Popen(command,pass_fds=(sockets[index].fileno(),),stdout=stderr,stderr=stderr)
            stderr.close()
            processes.append(process)
            sockets[index].close()
            controls.append(connect_control(out/(role+'.control'), process))
            if index == 0:
                evidence = SerialEvidence(controls[0], out/'operator.log')
            clock_initialization[role] = {}
            initialize_guest_clock(controls[index],process,role,clock_initialization[role],evidence if index == 0 else None)
            if index == 1:
                clocks=observe_pair_clocks(controls[0],controls[1],evidence,process)
                if clocks['valid'] is not True:
                    raise RuntimeError('VM clock bounds exceed authorization headroom')
                if args.scenario == 'probe-crash':
                    controls[0].sendall(b'arm-probe-crash\n')
                controls[1].sendall(b'clock-observed\n')
        deadline = time.monotonic()+260
        while processes[1].poll() is None and time.monotonic() < deadline:
            if shutil.disk_usage('/').free < 8 << 30:
                raise RuntimeError('management storage reserve reached; aborting owned lab')
            report = (out/'controller.log').read_text(errors='replace')
            if args.scenario == 'deny-matrix':
                for index, field in enumerate(DENIAL_FIELDS):
                    label = str(index)
                    if 'M09-PROCESS-REQUEST verify-denial-'+label not in complete_lines(report) or label in denial_proofs:
                        continue
                    controls[0].sendall(('probe-denial-step-'+label+'\n').encode('ascii'))
                    started = time.monotonic()
                    while time.monotonic()-started < 10:
                        serial = evidence.snapshot()
                        if 'M09-OPERATOR-ACK denial-'+label in complete_lines(serial):
                            proof = denial_step_proof(serial, label, expected_manifests)
                            if proof != denial_proofs.get('baseline'):
                                raise RuntimeError('field denial changed baseline')
                            denial_proofs[label] = proof
                            controls[1].sendall(('denial-'+label+'-confirmed\n').encode('ascii'))
                            break
                        time.sleep(.1)
                    else:
                        raise RuntimeError('field denial observation timeout: '+field)
            for phase, request, command, acknowledgment, reply in (
                    ('network-dual-stack', 'verify-network-dual-stack', b'probe-network-dual-stack\n', 'M09-OPERATOR-ACK network-dual-stack', b'network-dual-stack-confirmed\n'),
                    ('network-ipv4', 'verify-network-ipv4', b'probe-network-ipv4\n', 'M09-OPERATOR-ACK network-ipv4', b'network-ipv4-confirmed\n'),
                    ('live', 'verify-relay-live', b'probe-relay-live\n', 'M09-OPERATOR-ACK relay-live status=200', b'relay-live-confirmed\n'),
                    ('removed', 'verify-relay-removed', b'probe-relay-removed\n', 'M09-OPERATOR-ACK relay-removed', b'relay-removed-confirmed\n'),
                    ('owned-stopped', 'verify-owned-stopped', b'probe-owned-stopped\n', 'M09-OPERATOR-ACK owned-stopped', b'owned-stopped-confirmed\n'),
                    ('no-image-effects', 'verify-no-image-effects', b'probe-no-image-effects\n', 'M09-OPERATOR-ACK no-image-effects', b'no-image-effects-confirmed\n'),
                    ('denial-baseline', 'verify-denial-baseline', b'probe-denial-baseline\n', 'M09-OPERATOR-ACK denial-baseline', b'denial-baseline-confirmed\n'),
                    ('denial-after', 'verify-denial-after', b'probe-denial-after\n', 'M09-OPERATOR-ACK denial-after', b'denial-after-confirmed\n'),
                    ('certificate-provisioned', 'rotate-agent-certificate', b'rotate-agent-certificate\n', 'M09-OPERATOR-ACK certificate-provisioned', b'certificate-provisioned\n')):
                if ('M09-PROCESS-REQUEST '+request in complete_lines(report)
                        and phase not in [check['phase'] for check in relay_checks]):
                    if (args.scenario not in REVOCATION_SCENARIOS
                            and not (args.scenario == 'corrupt-archive' and phase == 'no-image-effects')
                            and not (args.scenario in ('network-ipv4', 'network-dual-stack') and phase in ('live', 'removed', args.scenario))
                            and not (args.scenario in DENIAL_SCENARIOS and phase in ('denial-baseline', 'denial-after'))):
                        raise RuntimeError('unexpected relay check request')
                    if phase == 'owned-stopped' and args.scenario not in ('lease-expiry', 'certificate-revoke-rotate'):
                        raise RuntimeError('unexpected quarantine check')
                    if phase == 'certificate-provisioned' and (args.scenario != 'certificate-revoke-rotate' or quarantine is None):
                        raise RuntimeError('certificate rotation before independent quarantine')
                    if phase == 'removed' and not relay_checks:
                        raise RuntimeError('relay denial has no positive control')
                    started = time.monotonic()
                    controls[0].sendall(command)
                    phase_budget = 45 if phase == 'network-dual-stack' else 25 if phase == 'network-ipv4' else 15
                    while time.monotonic() - started < phase_budget:
                        serial = evidence.snapshot()
                        if complete_lines(serial).count(acknowledgment) == 1:
                            if phase in ('network-ipv4', 'network-dual-stack'):
                                network = network_proof(serial, dual=phase == 'network-dual-stack')
                            if phase in ('denial-baseline', 'denial-after'):
                                label = phase.removeprefix('denial-')
                                prefix = 'M09-OPERATOR-DENIAL-'+label+' '
                                records = [json.loads(line.removeprefix(prefix)) for line in complete_lines(serial) if line.startswith(prefix)]
                                if len(records) != 1:
                                    raise RuntimeError('missing or duplicated denial proof')
                                proof = records[0]
                                if (sorted(proof.get('images_absent', [])) != expected_manifests
                                        or any(proof.get(key) != value for key, value in {'containers': 0, 'networks': 3, 'running': 0, 'candidate_reservations': 0, 'recorded_resources': 0, 'command_count': 1}.items())):
                                    raise RuntimeError('denial mutated execution state')
                                denial_proofs[label] = proof
                            if phase == 'no-image-effects':
                                records = [json.loads(line.removeprefix('M09-OPERATOR-NO-IMAGE-EFFECTS ')) for line in complete_lines(serial) if line.startswith('M09-OPERATOR-NO-IMAGE-EFFECTS ')]
                                if len(records) != 1:
                                    raise RuntimeError('missing or duplicated image absence proof')
                                image_absence = records[0]
                                if (sorted(image_absence.get('images_absent', [])) != expected_manifests
                                        or any(image_absence.get(key) != value for key, value in {'app_id': '22222222-2222-4222-8222-222222222222', 'owner_id': '66666666-6666-4666-8666-000000000002', 'containers': 0, 'networks': 3, 'running': 0, 'candidate_reservations': 0, 'recorded_resources': 0}.items())):
                                    raise RuntimeError('invalid image absence proof')
                            if phase == 'owned-stopped':
                                records = [json.loads(line.removeprefix('M09-OPERATOR-OWNED-STOPPED ')) for line in complete_lines(serial) if line.startswith('M09-OPERATOR-OWNED-STOPPED ')]
                                if len(records) != 1:
                                    raise RuntimeError('missing or duplicated quarantine observation')
                                quarantine = records[0]
                                ids = quarantine.get('container_ids', [])
                                if (quarantine.get('app_id') != '22222222-2222-4222-8222-222222222222'
                                        or quarantine.get('owner_id') != '66666666-6666-4666-8666-000000000002'
                                        or quarantine.get('stop_fence') is not True or quarantine.get('kernel_empty') is not True
                                        or type(quarantine.get('reserved_memory')) is not int or quarantine['reserved_memory'] <= 0
                                        or len(ids) != 2 or len(set(ids)) != 2
                                        or any(not re.fullmatch(r'[0-9a-f]{64}', value) for value in ids)):
                                    raise RuntimeError('invalid quarantine proof')
                            relay_checks.append({'phase': phase, 'elapsed_seconds': time.monotonic()-started})
                            controls[1].sendall(reply)
                            break
                        if processes[0].poll() is not None:
                            raise RuntimeError('runtime exited during relay check')
                        time.sleep(.1)
                    else:
                        raise RuntimeError('independent relay check timeout: '+phase)
            if 'M09-PROCESS-REQUEST restart-agent' in report and restart is None:
                if args.scenario != 'agent-restart':
                    raise RuntimeError('unexpected restart request')
                controls[0].sendall(b'restart-agent\n')
                restart_deadline = time.monotonic()+15
                while time.monotonic() < restart_deadline:
                    serial = evidence.snapshot()
                    if 'M09-OPERATOR-ACK restart-agent ' in serial:
                        restart = restart_proof(serial, app_ids)
                        controls[1].sendall(b'restart-complete\n')
                        break
                    if processes[0].poll() is not None:
                        raise RuntimeError('runtime exited during restart')
                    time.sleep(.1)
                else:
                    raise RuntimeError('agent restart timeout')
            time.sleep(.5)
        if processes[1].poll() is None:
            raise RuntimeError('controller lifecycle timeout')
        report = (out/'controller.log').read_text(errors='replace')
        if 'M09-PROCESS-COMPLETE scope=real-M07-stateless-lifecycle-only' not in report or 'M09-PROCESS-CONTROLLER-END rc=0' not in report:
            raise RuntimeError('controller lifecycle incomplete')
        if args.scenario == 'agent-restart' and restart is None:
            raise RuntimeError('required restart not executed')
        if args.scenario == 'probe-crash':
            fault = crash_proof(evidence.snapshot())
            results = [line for line in complete_lines(report) if line.startswith('M09-PROCESS-RESULT ')]
            if not results or results[0] != 'M09-PROCESS-RESULT operation=probe code=uncertain':
                raise RuntimeError('probe uncertainty not delivered durably')
        if args.scenario in REVOCATION_SCENARIOS:
            if ('M09-PROCESS-REVOKED '+args.scenario not in complete_lines(report)
                    or [check['phase'] for check in relay_checks if check['phase'] in ('live', 'removed')] != ['live', 'removed']):
                raise RuntimeError('required revocation not executed')
        if args.scenario in ('network-ipv4', 'network-dual-stack'):
            if network is None or [check['phase'] for check in relay_checks] != ['live', args.scenario, 'removed']:
                raise RuntimeError('network proof or relay removal missing')
        if args.scenario in ('lease-expiry', 'certificate-revoke-rotate') and quarantine is None:
            raise RuntimeError('required independent quarantine proof missing')
        if args.scenario == 'certificate-revoke-rotate' and ('M09-PROCESS-CERTIFICATE-ROTATED' not in complete_lines(report) or 'certificate-provisioned' not in [check['phase'] for check in relay_checks]):
            raise RuntimeError('required certificate rotation missing')
        if args.scenario == 'corrupt-archive' and (image_absence is None or 'M09-PROCESS-RESULT operation=create code=uncertain' not in complete_lines(report)):
            raise RuntimeError('required corrupt archive rejection missing')
        if args.scenario in DENIAL_SCENARIOS:
            expected = {'baseline', 'after'} if args.scenario != 'deny-matrix' else {'baseline'} | {str(index) for index in range(len(DENIAL_FIELDS))}
            if (set(denial_proofs) != expected or any(proof != denial_proofs.get('baseline') for proof in denial_proofs.values())
                    or 'M09-DENIAL-INJECTED '+args.scenario not in complete_lines(report)
                    or 'runtime_preflight_command_denied' not in (out/'runtime.log').read_text(errors='replace')):
                raise RuntimeError('missing actual agent rejection or zero-mutation proof')
            if args.scenario == 'deny-matrix' and any('M09-DENIAL-FIELD-PASS index='+str(index)+' field='+field not in complete_lines(report) for index,field in enumerate(DENIAL_FIELDS)):
                raise RuntimeError('missing named denial field')
        lifecycle_complete=True
        controls[0].sendall(b'snapshot\n')
        snapshot_deadline = time.monotonic()+10
        while time.monotonic() < snapshot_deadline:
            serial = evidence.snapshot()
            if 'M09-OPERATOR-ACK snapshot' in serial:
                final_inventory = operator_proof(serial, 'final', app_ids)
                if any(counts != (0, 3, 0) for counts in final_inventory.values()):
                    raise RuntimeError('final inventory not clean')
                break
            time.sleep(.1)
        else:
            raise RuntimeError('final inventory timeout')
        stop_disposable_vm(out/'runtime.monitor')
        processes[0].wait(timeout=15)
        if any(process.returncode != 0 for process in processes):
            raise RuntimeError('QEMU did not exit successfully')
        if source != source_snapshot():
            raise RuntimeError('source changed during development scenario')
        print('M09-PROCESS-PAIR-COMPLETE scope=development-lifecycle-not-full-acceptance')
    except Exception as error:
        errors.append(str(error))
        raise
    finally:
        cancel_deadline()
        for process in reversed(processes):
            if process.poll() is None:
                role='runtime' if process is processes[0] else 'controller'
                try:
                    stop_disposable_vm(out/(role+'.monitor'))
                    process.wait(timeout=12)
                except (OSError,subprocess.TimeoutExpired):
                    pass
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
        for connection in sockets:
            connection.close()
        if evidence is not None:
            evidence.close()
        for connection in controls:
            connection.close()
        try:
            restore_archives(artifact_backups)
        except Exception as error:
            errors.append('archive restoration: '+str(error))
            raise
        finally:
            (out/'result.json').write_text(json.dumps({'scope':'development lifecycle only','source_unchanged':source==source_snapshot(),'scenario':args.scenario,'teardown':'exact owned snapshot QEMU quit','final_signed_clean_probe_verified':lifecycle_complete,'restart':restart,'fault':fault,'relay_checks':relay_checks,'quarantine':quarantine,'image_absence':image_absence,'denial_proofs':denial_proofs,'network':network,'clocks':clocks,'clock_initialization':clock_initialization,'final_inventory':final_inventory,'errors':errors,'qemu_exit_codes':[p.returncode for p in processes]},indent=2)+'\n')


if __name__ == '__main__':
    main()
