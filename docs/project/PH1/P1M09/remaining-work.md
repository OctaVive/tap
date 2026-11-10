# PH1M09 remaining work and resume handoff

Updated: 2026-11-09. Workspace: `/root/tap`.

**M09 remains INCOMPLETE / NOT PASSED.** This is a working handoff, not an
acceptance certificate. Preserve all existing tracked and untracked changes;
do not reset or discard them. No commit or production deployment was made.

## Current checkpoint — 2026-11-09 23:13 UTC

**cd13 passed all four IPv6 constituents**, using the complete eight-target dual-stack
matrix, both families' positive connection controls and final signed cleanup.
Bounded evidence: `testing/development-20261109/network-dual-stack.json`.
34 distinct constituents have passing DEVELOPMENT evidence across versions;
there has still been no passing combined batch of all34 on one frozen source.

**cd14 failed the combined34 batch after18 passes**, before abandoned-probe
execution. Its independent clock gate measured1.074309392s against900ms allowed.
No authorization/probe was attempted in that failed fixture, QEMU[0,0], source
unchanged; logs retained and raw images retired. The clock guard correctly stopped
execution. Do not report this as a failure of abandoned-probe recovery itself.

The nested host has kvm-clock/acpi_pm, no TSC clocksource or available KVM PTP
path. A disposable-guest-only initial clock exchange was added before agent and
controller startup. It requires root, the disposable filesystem marker AND the
exact role in read-only QEMU fw_cfg; the filesystem marker alone cannot enable it.
Only one bounded timestamp and startup acknowledgment are accepted. Each exchange
must finish within250ms and is recorded. No later operator clock-setting command
exists, host time is untouched, and the independent900ms relative clock guard and
4s issuance/5s maximum authorization bounds remain unchanged.

Processlab component tests and14 Python harness tests passed. Only the lab binary
and guest scripts were rebuilt/replaced in trusted never-booted roots; the current
16-check canary and production binaries remain. **cd15 selected
R03.abandoned-probe PASSED**: source unchanged, relative clock bound9.559429ms,
both startup exchanges valid, actual agent PID991→1060 at the durable probe
boundary, final signed cleanup/probe and inventories complete, QEMU[0,0]. Raw
images retired. Bounded copy: testing/development-20261109/clock-bootstrap-probe-recovery.json.

**cd16 is running combined34**, output `m09-tools/cd16`, log
`/var/tmp/tap-m09/constituent-driver-16.log`. Keep source/catalog/roots unchanged
until this run exits. Driver overall exit1 still means INCOMPLETE even if all
implemented fixtures succeed. No combined34 pass is claimed yet.

Catalog193, mapped34 across15 VM scenarios, unsupported159. Formal constituent
ledger remains all NOT_RUN; top gates R01 FAIL/R02–R10 NOT_RUN. Accepted host/VM
profile and full acceptance remain required. Older checkpoints below are history.
Storage43GiB idle; quota69% at23:11UTC. Existing watcher PIDs64340/64341 were checked
alive; user's4% stop threshold remains. No agents/commit/deploy.

## Latest operational checkpoint — 2026-11-09 22:48 UTC

**cd9 did NOT pass the combined batch.** It completed26 development constituents,
then its IPv4 network fixture failed during create with durable uncertain result.
Runtime logged `runtime_authority_grant_denied` / preflight approval denial. It
never reached network probing. Source unchanged; QEMU[0,0], failed evidence kept,
raw disks retired. Do not describe cd9 as30 passing or erase the failure.

Added closed value-free grant failure diagnostics in actual
`internal/runtimerpc/authority.go`: encoding/expired/future/binding. Strict Matches
and the5s ceiling are unchanged. RPC tests pass. First diagnostic cd10 failed
because I accidentally wrote tools hashes without sha256: prefix; the host
correctly refused the invalid profile. Fixed all prefixes. **cd11 then passed all
four IPv4 cases**, but did not reproduce the transient grant rejection. Root
cause is unconfirmed. Checked original controller disassembly: runtimeGrant does
contain4-second issuance constants (MOVL -0x1194d800), not stale5-second code.
Saved old controller executable privately as `/var/tmp/tap-m09/pre-v6-controller.bin`.

Added READ-ONLY private clock observations for network fixtures. Controller
initial root helper on ttyS1 responds to sample-clock before unprivileged services
start; runtime operator has a fixed sample-clock enum. No input sets a clock or
selects PID/path/URL/command. Host samples bound each offset using request/response
intervals; worst-case inter-VM difference must be <=900ms before any authorization
starts. Interval uncertainty cannot hide bad offsets. Clock tests pass.
**cd12 passed all four IPv4 cases with76.6ms observed relative bound**, source
unchanged, full cleanup and signed final probe. This guards a fixture prerequisite;
it does not prove the earlier transient cause or deliver production time sync.

### IPv6 now integrated and first real run active

The17 staged IPv6 changes were copied into actual `/root/tap` only after original
file hashes matched the saved baseline. Record: `/var/tmp/tap-m09/ipv6-integrated-files.json`.
Stage remains `/var/tmp/tap-m09/ipv6-work` but is no longer the authoritative code.
Root authority diagnostics and clock observations are also present.

- Internal candidate and canary networks now request EnableIPv6=true; measured
  enforcement requires that observed flag plus existing internal/owner checks.
  Cleanup guards remain unchanged. New component readiness tests pass for valid
  dual stack, missing/disabled IPv6, external/foreign/wrong-driver and bad backend.
- Platform canary now requires16 checks, adding actual private ULA presence and
  an actual IPv6 TCP round trip to its own ULA. Unsupported IPv6 cannot pass.
  Trusted canary was rebuilt/repackaged, descriptor and every tools hash refreshed
  with correct sha256: prefixes. Runtime agent/measurement, controller and lab
  binaries rebuilt using CGO0, trimpath and buildvcs=false; executables0755.
- Network dual fixture uses an actual admitted BusyBox workload, explicit DNS A/
  AAAA controls, >=8 observed positive intra-app SYNs EACH family, zero forbidden
  SYNs in all8 cases, live root probes and exact inert-listener ordinals. Root
  kernel/ownership/netns proof and final relay removal/probe/inventory remain
  mandatory. Fresh low-risk veth instrumentation tests passed both families.
- Private scripts assign fd00:9::10/::11 to disconnected peers, plus inert
  fd00:ec2::254 and2001:db8:100::10 aliases/routes on the peer. Agent origin is the
  pinned IPv6 HTTPS endpoint for dual only; controller listens[::]:9443 for dual
  and restores IPv4 for other scenarios. No host NIC/route or real metadata/
  Internet destination exists. DB binds[::]:8081 to prove real family support.
- Root full Go tests/vet and all13 Python harness tests passed on integrated
  source. Logs: full-tests-20261109-dual.log / vet-20261109-dual.log.
  Earlier staged Go command without umask077 hit fixture privacy failures; its
  corrected full run passed. Keep old failure logs; never relax private paths.
- Catalog still193 required cases,34 mapped (new four IPv6 definitions sharpened);
  formal results all NOT_RUN, top gates R01 FAIL and R02–R10 NOT_RUN. Thirty distinct
  constituents have prior passing development evidence across recorded versions;
  no full final34 batch has passed. No IPv6 case has passed yet.

**cd13 is active**: selected four IPv6 cases, output `m09-tools/cd13`, launcher
session93815, log `/var/tmp/tap-m09/constituent-driver-13.log`. Likely actual run dir
c112 (host-ipv6). Keep runtime/source/catalog/templates unchanged until completion.
The launch command omitted TMPDIR export; inspect only TMPDIR for owned QEMU if
needed, do not dump process environment. Actual overlays should be modest but use
explicit TMPDIR=/var/tmp/tap-m09 for every future launcher, as already required.

Fresh private material (from preparation record `/var/tmp/tap-m09/dual-preparation.json`):
`process-trust-20261109T224522Z/` and `canary-dual-20261109T224522Z/` in m09-tools.
Leaves expire aboutNov10 02:45UTC; CA04:45UTC. Agent/rotation/controller key ownership
1000/root/1002 is restored, all key files0600, rotation dir0700. No keys were logged.

Owned watchers restarted at22:23UTC: quota PID64340 (about4h), storage PID64341
(about2h); record `/var/tmp/tap-m09/watchers-20261109-latest.json`. Old PIDs safely
signaled via pidfd after exact script identity verification. Latest quota about74%
remaining; stop at user's4%. Drive42GiB idle, about40GiB while paired. No agents
spawned, no production deploy/commit. Full M06–M08 regression baselines passed
before later runtime changes and need final freeze repetition.

## Current live checkpoint — 2026-11-09 22:07 UTC

**cd8 passed all four IPv4 cases** (host/actual controller/inert metadata/inert
external), source unchanged, no errors, QEMU[0,0], final signed probe and inventories
0/3/0. Capture265 packets/139 outgoing/eight intra-app SYNs and zero forbidden
SYNs. Metadata/external ordinals1 then2, host accepts2; attempt times8/12/9/9ms.
Bounded result: `testing/development-20261109/network-ipv4-four-targets.json`.
All completed raw disks were retired; failed cd4/5/6 evidence remains private.

**cd9 is running all30 mapped constituents together on the current frozen source**
(session86695, log `/var/tmp/tap-m09/constituent-driver-9.log`, output
`m09-tools/cd9/results.json`). Latest observed:24 DEVELOPMENT_PASS, zero FAIL,
169 NOT_RUN including pending cases. Full Go/vet and11 Python tests passed before
startup (`full-tests-20261109-network.log`, `vet-20261109-network.log`). Keep actual
repo runtime code/catalog/roots unchanged until cd9 finishes. There are193 total
constituents,30 mapped and163 unsupported; formal ledger remains entirely NOT_RUN.
Top gates R01 FAIL, R02–R10 NOT_RUN. No production acceptance/deployment.

### Isolated IPv6 work waiting for cd9 completion

Staging copy: `/var/tmp/tap-m09/ipv6-work`, with `baseline-sha256.json` from original
source before edits. Nothing below has been integrated into `/root/tap` or its
trusted guest roots. Do not overwrite live root files from staging until cd9
finishes; verify baseline hashes for every changed existing file before copying.
Old unused network-work staging copy was safely retired after FD checks.

- Production changes in stage: Engine.Create and canary request EnableIPv6=true
  on their internal bridges; MeasuredEnforcement.Network requires observed
  EnableIPv6=true. Existing exact ownership/cleanup checks are unchanged.
- New `internal/runtimeengine/network_linux_test.go` verifies valid dual-stack
  internal readiness, disabled/missing IPv6, external/foreign/wrong-driver and
  failed independent backend observation. It passes. Runtimeengine tests pass.
- Stage lab network fixture adds `network-dual-stack`, eight fixed probes, explicit
  BusyBox nslookup A/AAAA positive controls, and IPv6 packet counters. Actual db
  command becomes httpd on [::]:8081 for dual only. Worker lease is refreshed
  immediately before the potentially longer proof. IPv4 fixture keeps explicit
  A lookup so DNS family preference cannot make its capture ambiguous.
- Fixed global lab ULA addresses fd00:9::10/64 and ::11/64, inert peer aliases
  fd00:ec2::254 and2001:db8:100::10 with explicit private peer routes. Still no host
  NIC or external route. Process-pair sets controller listen[::]:9443 only for
  dual, restoring192.0.2.11:9443 for other scenarios. Actual mTLS IPv4 polling must
  still work; IPv6 root controls must reach that same listener. Existing DNS SAN
  keeps agent TLS valid; no key material changed.
- Child capture has fixed `capture-fixture6`/entered modes on inherited verified
  netns FD3. Dual-family veth compatibility passed:57 packets,35 outgoing,
  IPv4 SYN4 and IPv6 SYN4, all forbidden counters0. This is instrumentation proof,
  not M09 IPv6 workload acceptance. BusyBox DNS A/AAAA output was checked against
  a private namespace stub; real embedded DNS/workload still needs VM validation.
- Stage Python validation requires eight actual positive intra-app SYNs in EACH
  family, live controls bracketing all eight attempts, typed closed counters,
  exact root inert-listener ordinals, and both host listener counts2. Missing
  IPv6/unsupported sockets cannot pass. All12 stage Python tests pass.
- Stage Go vet passed. First full stage Go test command omitted required umask077
  and hit private-directory fixture failures; retained `ipv6-full-tests.log`.
  Corrected full Go/vet command with umask077 is session80879, logs
  `ipv6-full-tests-private.log` and `ipv6-vet-private.log`; check completion before
  claiming PASS. Do not relax any storage/private path check to fix this.
- Stage acceptance maps four IPv6 IDs to dual-stack, but their catalog definitions
  still need sharpening before execution. After integration, update just those
  definitions and formal catalog hash (all formal cases must remain NOT_RUN).
  Mapping34 cases is not34 passes. Build current agent and relevant measurement/
  lab binaries, chmod0755, refresh every tools digest in trusted host.json, copy
  both reviewed guest scripts, then run a fresh selected dual-stack development
  case in new cd10 output. Refresh private transport if near23:27UTC expiry.

Primary Docker docs checked: https://docs.docker.com/engine/daemon/ipv6/ explains
custom-network EnableIPv6 and automatic ULA allocation; release27 notes confirm
that allocation behavior predates pinned Docker29.5.0. This supports a proposed
implementation, not actual observed runtime support.

Monitor storage (about42GiB idle/40GiB during a pair) and weekly quota (about80%
remaining). Refresh watchers before their22:35/22:36UTC expiry if continuing; root
quota PID6022, storage PID36135, verify identities before signals. The user's4%
remaining stop instruction still applies. No subagents authorized.

## Live checkpoint — 2026-11-09 21:42 UTC

Full M06–M08 regressions passed as recorded below. New IPv4 host/management
fixture **cd7 passed both named cases**: exact workload/kernel verification,
root live probes before/after, actual workload tool positive controls, 123 captured
packets/65 outgoing/**four** outgoing intra-app SYNs, zero forbidden
host/management SYNs, inert host connection count exactly2. Each attempt took8ms.
Relay removal, final signed clean probe, inventories0/3/0 and QEMU exits[0,0]
passed on unchanged source. Bounded result:
`testing/development-20261109/network-ipv4-host-management.json`.
Failed cd4/5/6 runs remain privately recorded; their exact completed raw disks
were retired. The first issue compared a full registry reference to Docker's
local digest; fixed to exact admitted digest. ETH_P_IP capture missed outgoing
veth SYNs; changed to ETH_P_ALL plus PACKET_OUTGOING filtering, independently
verified across a fresh veth pair (26 packets,17 outgoing,four positive SYNs).
These are corrected fixture issues; no negative criterion was relaxed.

The driver now enforces the300s outer bound using a new private process group.
It observes its child with waitid(WNOWAIT), keeping the leader PID allocated
until killing any remaining group members; it cannot target a recycled PID.
The child has a240s soft alarm allowing bounded owned-VM teardown first. Tests
prove soft cleanup/alarm restoration and hard killing of the owned descendant,
plus normal success/nonzero exit handling. All11 Python tests pass; current Go
fixture compilation passes. No formal acceptance promotion.

**cd8 is now running**, output `m09-tools/cd8`, launcher session97133, log
`/var/tmp/tap-m09/constituent-driver-8.log`. This extends the same actual workload
probe to inert169.254.169.254:80 and203.0.113.10:80 listeners inside the isolated
controller VM. Runtime guest routes those two destinations only to its private
peer; there is still no host NIC/route or actual Internet/metadata access.
Metadata/external listener ordinals must be1 before and2 after each probe; capture
must show>=8 outgoing intra-app SYNs across all four probes and zero forbidden
SYNs. Fixed proof budgets: root process observation5s +capture/probes18s;
parent observation25s; controller acknowledgment30s. Other controls keep20s.
Both source scripts and lab binaries were refreshed in trusted roots before
startup. Keep source/catalog/templates unchanged until cd8 finishes. The catalog
has193 cases,30 mapped drivers; only28 distinct constituents currently have
passing development runs across their recorded source versions. Do not claim
30 passes until the new cases and source guard/cleanup actually pass.

Watchers remain active, quota about80% remaining, drive about42GiB idle/40GiB
with a VM pair. Transport leaves expire about23:27UTC. No subagents authorized.

## Current checkpoint — 2026-11-09 21:23 UTC

**Full M07/M08 and M06 regressions passed** on the source frozen for each run.
M07/M08: all 13 scenarios, exit0, no skips, unchanged source, zero forbidden
arrivals and complete cleanup. M06: 51 corpus cases plus lifecycle, broker
ownership/recovery/cancellation races and durable adapter; both exits0, no missing
cases/roots/skips, unchanged source, no forbidden arrivals and complete cleanup.
Bounded summaries are `testing/development-20261109/full-m07-m08-regression.json`
and `full-m06-regression.json`. Private evidence directories are the ones below.
These are regression baselines; later source changes still require final freeze
verification. They do not pass the remaining M09 constituents.

The next network fixture was built/tested in isolated
`/var/tmp/tap-m09/network-work` while M06 source remained unchanged. After M06
finished, its five changed/new files were integrated with original-source hash
checks. `network_linux.go` adds a fixed BusyBox HTTP probe command, exact recorded
web owner/PID/backend/kernel verification, pinned netns FD and a bounded private
AF_PACKET IPv4/TCP header counter helper. No engine exec or generic selector.
Root live controls bracket workload denial attempts against 192.0.2.10:18080
(inert listener) and the actual controller 192.0.2.11:9443. The same workload nc
tool fetches db health before/after each attempt. Missing/ambiguous controls,
capture or kernel proof fails. IPv6 and all other network variants stay NOT_RUN.
The helper's inherited-FD/setns/exec/capture compatibility passed in an isolated
mount/network namespace (25 packets, four positive SYNs); this is not workload
isolation acceptance. All nine Python harness tests and Go fixture compilation
pass. Source helpers were rebuilt into both trusted never-booted roots, 0755.

**cd4 is now running** the two named R06 IPv4 development cases with the maintained
driver, output `m09-tools/cd4`, launcher session99917, log
`/var/tmp/tap-m09/constituent-driver-4.log`. No network case has passed yet. Keep
source/catalog/templates unchanged until it finishes. Current catalog still has
193 cases; only the two IPv4 definitions were sharpened and formal result catalog
binding refreshed (all formal cases remain NOT_RUN). The earlier cd3 batch of
26 DEVELOPMENT_PASS/zero FAIL/167 NOT_RUN is retained against its original
catalog/source binding. The driver now has 28 mapped cases, not 28 passing cases.

Do not run VM labs concurrently. Retire only exact completed unreferenced raw
images; preserve logs/results/hashes. Weekly quota and storage watchers remain
active; stop at the user's 4% remaining threshold. Transport leaves generated at
19:27 UTC expire around23:27 UTC, so regenerate private material before later
runs if needed. A remaining harness task is to enforce the declared per-case
300s outer execution/cleanup budget, beyond existing individual bounded waits;
do this before final acceptance and test the timeout cleanup path.

## Completed batch and regression checkpoint — 2026-11-09 21:03 UTC

Frozen development batch `m09-tools/cd3` completed: **26 DEVELOPMENT_PASS,
zero FAIL, 167 NOT_RUN** across **13 distinct actual VM scenarios**. Every result
has unchanged source, no errors, QEMU exits [0,0], final signed clean probe and
per-app [0 containers, 3 builtin networks, 0 running]. All completed batch raw
images were retired by the maintained FD/loop-checking driver. Detailed private
results/source manifests/retirement hashes remain. Bounded nonsecret copies and
the full development coverage list are in `testing/development-20261109/frozen-batch/`.
The parent exit code 1 denotes overall INCOMPLETE, not a failed constituent.

Full Go tests/vet, eight Python tests, targeted four-package races and bounded
command fuzzing passed. Fuzzing ran 1,350 executions; logs are under
`/var/tmp/tap-m09/`. Formal ledgers remain R01 FAIL, R02–R10 NOT_RUN; development
success is not acceptance. Network/exhaustion/remaining fault/identity/accepted
host-profile constituents remain required.

**A full M07/M08 regression is now running** (no `--cases`, no debug, no handoff
export) via `infra/config/lab.py`. Evidence directory:
`/var/lib/orchestrator-builder/m05-lab.4cac6wpp/m08.1794258098310216748`.
Launcher session 9781; summary log `/var/tmp/tap-m09/full-m07-m08-20261109.log`.
Keep Go/Python/shell source unchanged until it completes, because its final
source guard must match. Watch storage and cleanup; about 42 GiB was free before
its first 10 GiB guest, 32 GiB while the first guest was active. Require both root
suites, all 13 subcases, no skip, source stability and cleanup before recording
success. Then the full M06 regression remains outstanding. Do not run heavy VM
labs concurrently. Monitor the user's 4% weekly remaining stop instruction.

## Live test checkpoint — 2026-11-09 20:53 UTC

The active frozen development batch is
`/var/lib/orchestrator-builder/m09-tools/cd3/`; read its `results.json` before
resuming. At this checkpoint, 19 constituents have DEVELOPMENT_PASS, zero FAIL,
and 174 NOT_RUN including pending cases. Six distinct scenarios completed:
signed-field matrix, signed wrong worker, signed expired command, bad signature,
actual live-ledger restart and abandoned probe. Real lease expiry is running;
five further implemented scenarios follow. Thirteen distinct scenarios cover 26
named constituents. Never promote the remaining unmapped cases or the formal
ledger from development results. Source, catalog and trusted template roots must
remain unchanged until the batch finishes. Owned parent acceptance process was
PID37946, started about 20:45 UTC; verify its identity before any signal.

Current full Go tests and vet passed; eight Python harness tests passed.
Targeted four-package races and bounded command fuzzing are being repeated on
this frozen source, with logs `race-20261109-frozen.log` and
`fuzz-20261109-frozen.log` under `/var/tmp/tap-m09/`.
The drive has about 40 GiB free during a VM pair. The maintained driver retires
only exact completed unreferenced raw images, retaining results/logs/hashes.
Watchers remain active; latest quota is 84% remaining. The user's 4% weekly
remaining stop instruction still applies.

The private restart controls, exact probe recovery and strengthened running-state
proof have now been implemented and actually VM-tested. Earlier statements below
about incomplete wiring, old handoffs or pending pair16–29 runs are historical.
Fresh admitted handoff is `m08.1794250511322523515`; all three selected scenarios
and cleanup passed, but it is a subset rather than a full regression. Actual
idle approval/admission/scan/lease/certificate variants, corrupt archives and
command denial passed individually and are being repeated in cd3. Remaining
network/exhaustion/crash/identity/accepted-profile work and full M06–M08 regression
still block M09. Formal required statuses remain R01 FAIL, R02–R10 NOT_RUN.

## Continuation checkpoint — 2026-11-09

The user authorized the six-step execution sequence in `execution-plan.md`.
The workspace was clean at the start; the statements about uncommitted work
below refer to the earlier save. Preserve all current changes.

- Reconciled the resume prompt, README and historical acceptance report.
- Added an initial 193-constituent coverage catalog and extended the reporter to
  require complete constituent results plus a hashed catalog. Trigger-specific
  drivers still need implementation; the initial enumeration is not a coverage
  ceiling or an acceptance certificate.
- Wired private runtime ttyS2/controller ttyS1 and fixed-enum restart handshake,
  PID/count proof and independent final inventory into the development pair lab.
  Component tests pass; actual same-ledger restart remains unproven.
- Pair13 failed on a partial serial enrollment read (fixed to wait for newline).
  Pair14 reached controller setup but correctly rejected the old scan policy:
  M07/M08 records are ten days old and the database maximum age is two days.
  Retained both logs/results. Completed unused raw images pair10–14 were hashed
  and retired through the existing FD-checking helper; all evidence remains.
- Refreshed Trivy database from the official configured repository and updated
  `infra/build/tools.lock.json`; new tools are in `m09-tools/tools-20261109/`.
  Fresh scanner template/database build is in progress, logs in
  `/var/tmp/tap-m09/ingest-{template,database}-refresh.log`. Next create a private
  scanner config with their exact digests, execute a fresh actual M07/M08 handoff
  and copy its immutable metadata/artifacts into trusted controller sources.
- Added kernel mountinfo verification for the three engine-managed etc files;
  component test passes. Rebuild measurement binaries and profile hashes before
  another runtime VM. New short-lived transport material: process-trust-20261109-1.
- Full Go tests had one clonejob 100ms fixture deadline failure under concurrent
  VM/build load. Vet and targeted runtimeagent/runtimeengine tests passed. Retain
  the failure and rerun idle. Reporter and restart proof tests pass.
- Quota watcher now reads the current November 9 session (latest: 98% remaining).
  Restart watchers after daemon/process loss; old October telemetry is historical.
  Storage is monitored; check current free space before further images/labs.

No runtime acceptance constituent has been promoted. R01 FAIL and R02–R10 NOT_RUN
and the old manifest remain historical. Follow this checkpoint and execution plan
before the older operational details below.

### Later continuation update (2026-11-09)

The user requested urgent disk cleanup and then explicitly asked to continue M09.
The aborted full pipeline had consumed the filesystem after failed cleanup. It
was stopped; exact unused disks and superseded image-build templates/initramfs
copies were retired after FD/loop/mount checks. Logs and metadata were retained.
Free space recovered to 44 GiB (currently about 33 GiB while one 10 GiB lab guest
is reserved). Private retirement manifest: `m09-tools/cleanup-20261109.json`.
The initial removed fenced disk was
`m08.1794249867800958755/builder/779e98f6-de0a-4f12-85db-96850ccfb238.raw`
(10 GiB); its metadata remains in that run. The completed historical
`backend-observer-3.raw` was also retired; its serial log remains.

The build lab now requires 32 GiB free and trusted `/run/netns` before starting,
checks 32 GiB before each scenario, stops after failed scenarios and uses Go's
failfast flag. The process-pair lab requires 24 GiB initially and aborts below an
8 GiB management reserve. `/run/netns` was absent after host reboot; it is now
restored as root-owned mode 0755. Fixture addresses and trust have been restored.

A database-image digest was computed before the image build finished; the next
run rejected it. Correct completed digest:
`sha256:05cde6bfc8054f29a7aa07b729a5b8f852e1fbd03970087750235e94a2f04c28`.
Run `m08.1794250301809869473` failed and confirmed complete cleanup. The current
selected three-case handoff is `m08.1794250511322523515`, exporting into
`m09-tools/m07-handoff-20261109-3/`. Single handoff already exported; Compose and
policy-denial cases are still running. `--cases` makes this development evidence,
not complete M07/M08 acceptance. Check its final results before using any export.

Latest full Go tests and vet pass. The clonejob success fixture's deadline was
raised from 100ms to 5s to allow durable fsync on this shared lab disk; timeout
negative-case criteria are unchanged. Targeted runtimeagent/runtimeengine/
runtimeisolation races pass. Additional component fault cases validate exact
abandoned-canary records and kernel readonly bind mount flags.

Implemented exact abandoned-probe reconciliation, including reserved owners with
no saved resource IDs. Unknown engine objects continue to block release; create
intents stay uncertain/fenced. The fixed disposable operator now also supports
`probe-crash`, killing only its own agent after a probe's two resource IDs are
persisted in the real ledger. Its host proof and controller uncertain-result
expectation are implemented but not yet VM-executed. First run `agent-restart`,
then `probe-crash` after copying fresh merged M07/M08 records and opaque artifacts
into the controller root. Current binaries/profile hashes are being refreshed;
confirm build completion and 0755 modes. Pair13/14 are still the latest attempted
runtime pairs; pair12 is the latest completed development lifecycle.

### Real restart result — 2026-11-09

All three selected fresh M08 handoff cases passed; the handoff run's cleanup
confirmed trust restoration, unchanged firewall and no guest disks. Metadata was
merged without changing admission/job/event identities into
`m09-tools/combined-metadata-20261109.db`; fresh Compose handoff and opaque
artifacts are now in the trusted controller root. The selected run still does not
claim full M06/M07/M08 regression acceptance.

**process-pair-16 PASSED the development same-ledger restart scenario**:
agent PID 989→1791, app222 retains 2 containers/4 networks before and after restart,
app333 remains 0/3; inspect/log/stop/remove and final signed probe pass. Final
inventory is 0 containers/3 builtin networks per app; both QEMU exits zero, no
errors. Pair15 had passed probe/create but failed because controller ttyS1 was not
accessible to UID1002. The disposable controller script now assigns only that
fixed serial device to its controller account, mode 0600. Failed logs retained;
pair15/16 raw disks are retired after completion through the FD-checking helper.

The current actual probe-crash scenario is **process-pair-17**, pending. It records
source hashes and requires unchanged source, a changed agent PID, exact persisted
probe IDs, the durable uncertain result and final clean inventory. Do not edit
tracked runtime source until this run finishes, or its source guard will fail.
Current free storage is about 40 GiB. No required gate/constituent has been promoted.

### Probe crash and first revocation results — 2026-11-09

**process-pair-17 passed real probe-crash recovery** on unchanged source. The
operator froze/killed PID993 with a pending probe and two persisted exact resource
IDs, restarted PID1147 on the same VM/ledger, and the controller received the
uncertain result durably. The subsequent actual two-service create/inspect/log/
stop/remove/final probe passed. Final inventory: zero containers and three builtin
networks per app; QEMU exits [0,0], no errors. The operator's readonly barrier
freezes its owned process while reading to avoid a race with command completion.

**process-pair-18 passed the development idle approval-revocation stop case**:
trusted approval revoked after successful create, inspection observes stopped
before explicit stop is queued, subsequent logs/stop/remove/final probe pass.
Source unchanged, clean final inventory and both QEMU exits zero. This first
variant did not independently fetch the relay before/after revocation.

A stronger fixed private relay positive/negative control is now implemented:
controller waits for the guest operator to fetch the fixed app222/create2 relay
health endpoint with HTTP200 before revoking, then waits for root-observed socket
removal plus ENOENT on an independent new connection. The fixture accepts no
app/path/URL selectors. The current stronger approval test is process-pair-19,
pending. Admission-revoke and stricter scan-policy-change scenarios are also
implemented but unexecuted. Do not edit runtime source while pair19 runs.

Full Go/vet, targeted races, bounded command fuzz and four reporter/proof tests
have passed at their recorded checkpoints; final-source regression still remains.
`fstrim -v /` returned 6.2 GiB to the virtual backing disk after cleanup. Raw pair17
and pair18 images are being retired after completion; logs/results remain. Watch
storage before every run; the root filesystem has about 40 GiB free.

### Idle authority variants — 2026-11-09

The stronger variants **pair19 (approval), pair20 (admission), pair21 (stricter
scan policy)** all passed on unchanged source. Each independently fetched HTTP200
through the fixed private relay before revocation, confirmed socket removal and
new-connection ENOENT after revocation, inspected stopped workloads before any
explicit stop command, and completed logs/stop/remove/final signed probe. Final
inventories were 0 containers/3 builtin networks per app; QEMU exits [0,0], no
errors. Their unused raw images have been retired, with logs and hashes retained.
Bounded nonsecret results are in `testing/development-20261109/`.

**pair22 lease-expiry is now pending.** It deliberately stops renewing the worker
lease, waits for the recorded 55s lease deadline, then independently checks relay
removal, actual stopped exact containers, empty matching kernel cgroups, durable
stop fence and retained candidate memory before renewing only to authorize cleanup.
The new fixed readonly helper is `processlab/lifecycle_linux.go`. A subsequent
certificate-revoke-rotate scenario uses the same quarantine proof, explicitly
registers a preprovisioned replacement certificate, installs only fixed certificate/
key files and signals the same agent to reload transport. It never unrevokes an
identity or resets restart/stop/generation state. This rotation case is implemented
but not yet executed.

Fresh transport material (including replacement client identity) is in
`process-trust-20261109-2/`, prepared at about 19:27 UTC. Trusted runtime root has
root-only `/opt/m09/agent-rotation/`; private keys are never copied to the controller.
The main fixture fields and current roots are already updated. Keep runtime source
unchanged until pair22 finishes. Free space is about 40 GiB; quota about 91% remains.
The top-level ledger reasons now describe current gaps; statuses and historical
failure evidence are unchanged. No constituent/gate is promoted from development.

### Current checkpoint — 2026-11-09 19:52 UTC

**pair22 lease-expiry and pair23 certificate-revoke-rotate passed** on unchanged
source with independent kernel/container stop proof, durable fence and retained
512 MiB candidate charge before authorized cleanup. Pair23 explicitly enrolled a
preprovisioned replacement certificate and reloaded the same agent after old-cert
quarantine, then completed stopped inspect/log/stop/remove/final signed probe.
Both ended with clean inventories and QEMU exits [0,0]. Raw images retired.

Pair24 failed solely because shell tracing interleaved into a ttyS0 JSON snapshot.
Structured enrollment/proofs now use a bounded bidirectional root-only ttyS2
protocol recorded in `operator.log`, mirrored to ttyS0 only for human diagnostics.
Both guest scripts disable shell tracing. A 1 MiB private-evidence bound and
partial-frame tests pass. Controller lifecycle requests remain fixed enum.

**pair25 passed private-channel restart with explicit running/stopped inspect
assertions. Pair26 additionally passed with both containers counted running
before/after restart**, different agent PIDs and final 0 containers/3 builtin
networks/0 running per app. Object counts now reject duplicate IDs, malformed IDs,
unknown state and oversized inventories; component cases pass. This removes the
ambiguity where an aggregate running state could hide a partially stopped app.
The next work is real corrupt-artifact rejection and the constituent driver.

Latest runtime source is compiled into trusted roots, tool digests refreshed.
Current free storage ~40 GiB; quota ~90% remains. After further client changes,
rebuild both agent and measurement binaries plus processlab, chmod only rebuilt
executables 0755, refresh profile tool hashes, and run on fresh images. Source
remains mutable development; all required gates/constituents remain incomplete.

### Current checkpoint — 2026-11-09 20:32 UTC

**pair27 passed actual corrupt-archive rejection**: private copies of the two
actual admitted M07 archives had one opaque byte flipped, without changing any
immutable record. Create returned uncertain/refused, root independently observed
neither application image present, no application resources/candidate charges,
then authorized remove and final signed clean probe passed. Original copies were
restored and rehashed. `artifact_fault.py` never parses an archive format.

The maintained `infra/runtime/acceptance.py` driver enumerates every required
case, records unselected/unimplemented cases NOT_RUN, and only emits
DEVELOPMENT_PASS for real development fixtures. It never promotes required
ledgers or permits production acceptance. `retire.py` automatically checks inactive
owned VM image inodes, open FDs and loop attachments, retains SHA256 and deletes
only the exact run's generated raw disks. The first actual driver run, `m09-tools/cd1`,
passed R04.corrupt-archive, explicitly recorded 192 NOT_RUN and returned INCOMPLETE.
Definitions (`constituents.json`, schema2) are now immutable and separate from
`constituent-results.json`; result promotion cannot alter frozen definitions.
Reporter requires exact IDs, definition hash, real-acceptance scope and verified
hashes for both files. The formal result ledger remains entirely NOT_RUN.

**pair28 passed actual bad-signature zero-mutation denial**, using a separate
fixed private fixture controller wrapping the actual production authority handler.
The actual production agent remains unchanged/outbound-only. It logged command
rejection; independent before/after observations showed only the original probe
intent, no create intent, no application images/resources/candidate charges. The
exact original valid command was then delivered and completed full lifecycle,
proving liveness. No public injection endpoint or generic execution was added.
The new `denial_linux.go` contains the bounded fixture controller. All role TLS,
metadata, approval and artifact paths remain real. Wrong-worker and expired-command
fixtures are also implemented and currently running through catalog driver `cd2`.
Do not edit runtime source until cd2 finishes its two cases.

Eight Python reporter/driver/proof/fault-fixture tests pass. Last full Go/vet/races
precede the newest readonly client/lab additions and must be rerun. One review
finding still pending: Agent.Serve immediately polls again after preflight command
rejection; add bounded pacing and a meaningful invalid-command flood test after
cd2 finishes. Draft test is `/tmp/tap-pacing-test.go` (copy to repo, verify the
mutated nonce truly differs, then implement delay). This is required R10 work.

Free space ~40 GiB, quota ~87% remains. Storage watcher started ~18:36 UTC lasts
two hours: restart it before ~20:36 UTC. Quota watcher lasts until ~22:36 UTC.
Private source transport `process-trust-20261109-2` leaf certificates expire about
23:27 UTC; regenerate if needed. No required milestone gate has been promoted.

### Current checkpoint — 2026-11-09 20:45 UTC

Driver cd2 passed both correctly signed wrong-worker and expired-command cases,
with actual agent rejection, unchanged independent before/after observations and
subsequent valid-command lifecycle. Raw images automatically retired.

The invalid-command pacing test reproduced **1097 rejected polls in 270ms**.
`Agent.Serve` now waits 100ms after execution/preflight rejection, bounding repeated
invalid delivery rather than hot-looping. New `pacing_test.go` passes and verifies
no durable intent was admitted. Before/after logs are retained in `/var/tmp/tap-m09`.
Full Go tests/vet and targeted four-package races pass after the production fix.

**pair29 passed all 16 signed-field tamper variants in one real VM**, including
version/operation/ID/worker/incarnation/app/deployment/generation/nonce/key/expiry/
policy/spec hashes/target/spec/log limit. The fixture preserves the original
signature, waits for a subsequent poll to prove the previous response was handled,
and obtains an independent unchanged ledger/engine/image observation after each
field. The valid original command then completed full lifecycle and final probe.
There are 17 matching observations (baseline plus 16), unchanged source, no errors,
clean final inventory, QEMU exits [0,0]. Raw images retired; logs/results retained.

Catalog driver now has **26 mapped constituents**. A complete named matrix run is
shared only for the exact fields actually tested; all other constituents remain
NOT_RUN. Definitions schema2 and separate formal results are unchanged/all NOT_RUN.
Eight Python tests pass. The maintained driver/retirer has already passed a real
single-case run (cd1, corrupt artifact) and two-case run (cd2, semantic denials).

**cd3 is currently running every implemented handler on one frozen source**:
`m09-tools/cd3/results.json`, live top log `/var/tmp/tap-m09/constituent-driver-3.log`.
It enumerates all 193 cases; unsupported cases are explicit NOT_RUN, and only real
development results become DEVELOPMENT_PASS. Source/catalog must stay unchanged
through this batch. It runs one VM pair at a time and retires raw images before
continuing. Expect about 30 minutes for the full implemented subset. No milestone
PASS or final-source acceptance is claimed. Do not edit runtime code or definitions
until cd3 finishes; docs outside the architecture/specifications may be updated.

Storage watcher was restarted at ~20:35 UTC (now lasts until ~22:35); quota watcher
still lasts until ~22:36. Free space ~43 GiB between cases, ~40 during a pair.
Transport source `process-trust-20261109-2` leaves expire about 23:27 UTC. Check or
regenerate before longer runs. Latest weekly quota ~85% remains.

Next implementation priorities after this frozen batch: actual network attacks
with live IPv4/IPv6 positive controls; resource exhaustion and host responsiveness;
remaining deterministic crash/lost-response boundaries and foreign-object retention;
actual API/UI/credential separation; reproducible accepted VM/host profile/M04
integration. These are still blocking, not optional. Full M06/M07/M08 regression
and final source/evidence freeze/report remain required after implementation.

## User instructions that remain active

- Execute `prompts/PH1M09-next-window.md`, create a completion plan and implement it.
- Every required real acceptance constituent must pass before marking M09 passed.
- Keep monitoring storage. Retain evidence; never remove an active VM disk or
  unrelated project artifact. Do not mount guest-modified disks on management.
- Monitor weekly Codex usage. **At 4% remaining, save/update this handoff and its
  `.md5` checksum, terminate only owned lab runs safely, and stop task work.**
  Do not wait for the quota to reach zero. The user explicitly requested this stop.
- No subagents unless the user explicitly authorizes delegation.

## Current quota and storage monitoring

Latest observed weekly telemetry when this handoff was prepared: 75% used,
25% remaining (latest telemetry timestamp 2026-10-30T21:39:25.555Z). Read `/var/tmp/tap-m09/quota-latest.json` for the current sample.
This is the seven-day window (`window_minutes: 10080`), not a token budget.

Background watchers started during this task:

- `/var/tmp/tap-m09/quota-watch.py`: samples session quota every five seconds;
  writes `quota-latest.json`, `quota-watch.jsonl`, and `quota-stop.requested`
  when remaining quota reaches 4%. At that point it also refreshes this checksum.
  Its initial process runs for up to four hours. Check it is alive after resuming.
- `/var/tmp/tap-m09/storage-watch.py`: samples disk usage every 15 seconds;
  writes `storage-watch.jsonl`. Initial watcher lasts two hours from approximately
  19:55 UTC, so restart it if work continues after approximately 21:55 UTC.
  Stop marker: `/var/tmp/tap-m09/storage-watch.stop`.

Recent storage: about 15 GiB free on `/` and 1.8 GiB free on `/tmp`.
The Go cache was moved to `/var/tmp/tap-go-cache`; `/tmp/tap-go-cache` is a symlink
there. Continue using a private umask and short scratch paths:

```sh
umask 077
export TMPDIR=/var/tmp/tap-m09 GOCACHE=/tmp/tap-go-cache
/usr/local/go/bin/go test ./...
```

Do not launch another large build/scan lab with insufficient headroom. Actual M07
labs temporarily consume many GiB and enforce a separate management free-space
floor. Prefer at least 20 GiB free before those runs. The runtime process-pair
harness refuses startup below 8 GiB; continue monitoring peak usage afterward.

Only completed disposable development images were retired. Their hashes and
retention reasons are in
`/var/lib/orchestrator-builder/m09-tools/retired-development-images.json`.
Serial logs, stderr, result files, trusted source roots and evidence were retained.
The local helper `/var/tmp/tap-m09/retire-images.py` checks open process FDs and
requires the matching serial log before deleting an explicitly named lab image.

## Implementation now present

Read the C01–C08 completion sequence in `implementation-plan.md`, plus
`implementation-evidence.md`, `test-plan.md`, the runtime execution/deployment
agent specifications and `docs/architecture/docker-security.md`.

- `internal/runtimehost`, `cmd/runtime-host`: fixed root oneshot inside the runtime
  VM; finite operator app slots, durable reserve-before-provisioning, physical
  hard-sized per-app ext4 storage, parent memory/CPU/PID cgroups, separate rootless
  Docker daemons, root-owned enrollment and agent-ledger anchor. No generic RPC.
- `internal/runtimeisolation`, `runtimeprofile`, `cmd/runtime-runc`: independently
  measured boot/process/userns/map identity; inherited app namespace support
  only after trusted enrollment; nonroot IDs, zero capabilities, NNP, enforced
  AppArmor/seccomp, private namespaces, cgroups, readonly root and bounded tmpfs.
  Engine-managed etc bind files are made readonly.
- `internal/runtimemeasure`, `runtimenet`, `runtimeobservation`, and their commands:
  bounded root measurement Unix service; exact app/container ownership; fixed
  privilege-dropping health/relay helper; private network namespace and Unix
  relay, separate relay UID, tracked child/socket ownership and finite lifetime.
- `internal/runtimeengine`: app-scoped guarded factory, concrete measured
  enforcement, unknown-object refusal, immutable platform canary, candidate
  capacity accounting, private ingress, inspected typed lifecycle, supervisor.
- `internal/storage/runtime.go`, `migrations/004_runtime.sql`, `runtimeauthority`:
  durable explicit trusted approval/admission/current scan policy, worker leases,
  certificates/revocation, command queue, result acknowledgment and runtime
  artifact authorization. No HTTP approval/queue mutation endpoints.
- `runtimeagent`: ledger schema 3, migration from old schemas, immutable ledger
  identity, outbox, stored command specs, candidate budgets, finite restart
  allowances and stop/generation fences. Background current-authorization checks
  cancel long requests. Incidents block new execution but permit authorized
  exact stop/remove so recovery can proceed.
- `cmd/runtime-agent`, `cmd/runtime-controller`, `runtimeprocess`, `runtimerpc`:
  actual separate processes, outbound mTLS polling/artifact transfer, independent
  inventory signing, provisioned transport reload and revocation checks.
- Service templates are in `infra/runtime/services/`. They still require real
  acceptance and an accepted reproducible runtime VM/host profile.
- Volumes/secrets remain denied pending M10. Production routing belongs to M11;
  the M09 relay is a private connectivity fixture. Assignment/scheduling is M12.

## Important fixes discovered through actual VM execution

1. RootlessKit needs `--net=none`, port driver `none` and
   `DOCKERD_ROOTLESS_ROOTLESSKIT_DETACH_NETNS=false` for the pinned version.
2. The rootless hardener must verify inherited kernel namespaces/maps, rather
   than invent nested mappings or accept missing maps without enrollment.
3. Root cannot reliably statfs through an unprivileged FUSE root. Kernel mountinfo
   superblock options now supply actual tmpfs bounds.
4. Pinned runtime executables require explicit chmod 0755 after builds under
   umask 077. Docker also changes its data-root mode; provisioner restores 0700.
5. Classic Docker rejects the plain OCI archives emitted by M07. The runtime now
   uses Docker 29.5.0's containerd image store with native snapshotter. Inspect and
   create resolve the exact admitted OCI manifest digest. No tag/registry fallback
   or management OCI parsing was introduced. Repository-digest lists may be empty.
6. Runtime enrollment reads completed immutable M07 records after the old build
   lease expires, while preserving current scan/admission checks. It grants no
   new build authority. M07's live build fence was not weakened.
7. Concurrent authorization refreshes no longer expose a transient empty image
   resolver. Failed refreshes still invalidate its view. Controller grants use
   four seconds below the receiver's strict five-second ceiling to leave small
   independent VM clock offsets headroom.
8. `internal/cloner/context.go` incorrectly materialized Git content using private
   staging permissions (0600/0700), so Docker COPY produced executables unusable
   by nonroot workloads. Git content modes are now normalized to 0644/0755 while
   the context root stays private. This needs complete M06/M08 regression too.
9. `/run` tmpfs now belongs to the validated service UID/GID. The platform canary
   has 14 checks, including successful bounded writes to both `/tmp` and `/run`.
10. Relay tracking now includes exact container ID, so draining a non-ingress
    sibling does not fail or affect the deployment's actual ingress relay.
11. Cleanup now permits independently confirmed absent recorded objects, and
    DELETE acknowledgment alone is insufficient: exact GET 404 must precede
    forgetting a resource. Capacity release additionally checks for unknown
    engine objects. Add direct fault tests and execute real lost-response/crash
    variants for this most recent recovery change.

## Actual evidence achieved (development scope only)

Private lab root: `/var/lib/orchestrator-builder/m09-tools`.
Trusted never-booted runtime source root: `rootfs/`.
Trusted controller source root: `controller-rootfs/`.
Linux: 6.12.113+deb13-amd64; Docker/rootless extras: 29.5.0;
systemd: 257.13; QEMU: 10.0.13; API contract: 1.47.

- `profile-7.log`: narrow kernel profile diagnostic succeeded for both app engines.
- `host-6.log`: actual provisioner ran twice idempotently; both app backend/kernel
  measurements, private health, relay fetch and relay removal completed, rc=0.
- `host-11.log`: signed measured platform canary probes passed for both apps.
- `process-pair-10/`: real admitted single-service lifecycle passed between actual
  agent/controller executables in separate VMs over a private inherited socket
  pair, with no host NIC or route. Sequence: probe, create/readiness, inspect,
  logs, stop, inspect, remove, final signed clean probe. `result.json` has no
  errors, both QEMU exit codes zero and final clean probe verified.
- **`process-pair-12/`: the same complete sequence passed for the real two-service
  dependency fixture.** Web starts its HTTP server only after successfully
  fetching the dependency's health endpoint. This run includes the 14-check
  canary and nonroot-writable `/run`, relay sibling fix and new cleanup behavior.
- All earlier failed development runs/logs remain recorded. These are not hidden
  or promoted into passing full milestone gates.

Process VM teardown deliberately quits the exact owned disposable snapshot QEMU
processes after product stop/remove and the final signed clean probe. ACPI power
button delivery was ineffective without a guest power-event handler. The harness
records its teardown method and whether the final clean probe completed. A QEMU
exit alone never makes an incomplete lifecycle pass.

## Real M07/M08 handoff records and reproduction

The actual source build and scan run is not replaced by synthetic admissions.

- First functional single handoff: `m07-handoff-5/{metadata.db,handoff.json}`.
  Its actual pipeline run:
  `/var/lib/orchestrator-builder/m05-lab.4cac6wpp/m08.1793392379098667448`.
- Both current actual records:
  `m07-handoff-pair/m08-dockerfile/` and `m07-handoff-pair/m08-compose/`.
  Pipeline run:
  `/var/lib/orchestrator-builder/m05-lab.4cac6wpp/m08.1793394108463396945`.
  Both builds/scans admitted and both M08 plans normalized successfully; cleanup
  confirmed trust restoration, unchanged firewall and no remaining guest disks.
- The Compose plan has one built web image and a separately admitted dependency
  image. It preserves M08's single-build constraint. Separate real applications,
  deployments/repositories/branches avoid record identity collisions.
- `infra/runtime/experiments/merge-handoff.py` consolidates trusted metadata
  snapshots without changing admission/job/deployment/event IDs or payloads.
  Only local outbox integer surrogate sequence numbers can be reassigned.
  It checks every imported row's content and the foreign key graph.
- Actual opaque artifacts are in the pipeline run's `artifacts/` directory and
  copied opaquely to `controller-rootfs/var/lib/m09-process/artifacts/`.
- Lab exporter opt-in: `M09_HANDOFF_DIRECTORY`, with per-scenario private subdirs.
  Hook lives only in the real pipeline test/fixture. No production approval path.

Useful commands (fresh output directory each time):

```sh
umask 077
export TMPDIR=/var/tmp/tap-m09 GOCACHE=/tmp/tap-go-cache
python3 infra/runtime/experiments/process-pair.py \
  --runtime-root /var/lib/orchestrator-builder/m09-tools/rootfs \
  --controller-root /var/lib/orchestrator-builder/m09-tools/controller-rootfs \
  --output /var/lib/orchestrator-builder/m09-tools/process-pair-N \
  --kernel /boot/vmlinuz-6.12.113+deb13-amd64 \
  --initrd /boot/initrd.img-6.12.113+deb13-amd64
```

Compile changed executables into the trusted source root, chmod them 0755 and
update every `tools` digest in `rootfs/etc/tap-runtime/host.json` before generating
fresh images. Regenerate the platform canary archive/descriptor when its binary
changes. Never modify an image currently used by QEMU.

Current two-service slots: source app 333... reserves 64 MiB/100mCPU/32 PIDs;
app 222... reserves 512 MiB/1000mCPU/128 PIDs, fitting two 256 MiB/500mCPU/64-PID
services. Both include separate fixed daemon overhead and hard disk reservations.

Current transport fixture material: `process-trust-3/`; four-hour leaf certificates
under a six-hour lab CA. Generate new material with the lab `processlab prepare`
command if expired, copy private files into the proper trusted roots, preserve
UIDs 1000 (agent) and 1002 (controller), and regenerate images. Never log keys.

## Work still required before M09 can pass

1. Complete **real recovery/fault tests**: lost create/start/delete responses,
   kill agent at every durable-intent/resource/start/inspect/result/cleanup
   boundary; restart the agent on the same live VM/ledger; durable outbox retry;
   unknown engine objects retained; no duplicate effects or implicit adoption.
   Component fault tests for the GET-404 cleanup rule now pass; real VM fault
   injection remains outstanding.
2. Execute **real revocation/expiry** during operations and while idle: worker
   lease, certificate, approval, admission and current scan-policy changes;
   stop/quarantine owned workloads and drain ingress while retaining uncertainty.
   Exercise continuing authorization and finite restart allowance exhaustion,
   intentional stop fences and daemon/measurement-helper restart behavior.
3. Complete a **machine-enumerated R01–R10 constituent catalog and driver**.
   The current process-pair program is only a development happy-path driver.
   No constituent may be silently skipped, inferred from mocks or optionalized.
4. Execute real zero-mutation denial snapshots for every protocol/policy field,
   signature/key/worker/incarnation/app/expiry/generation/approval/cert/replay
   variant and concurrent duplicate race. Production agent remains outbound-only;
   use a distinct, fixed, private test fixture for injection, never generic exec.
5. Execute **network attacks with active positive controls**: actual management
   endpoint and inert host/metadata/external fixtures, IPv4/IPv6, cross-app,
   intra-app dependency, no public app ports, and confirmed relay removal. The
   platform canary's hardcoded blocked endpoints alone do not satisfy the full
   positive-control matrix.
6. Execute **resource exhaustion**: CPU, RAM/swap, PIDs, tmpfs and writable storage,
   image/unpacked cache, logs, deadlines and overlapping reservations. Demonstrate
   effective writable access before filling a quota; keep management responsive.
7. Execute actual **API/UI/account/credential/socket separation** and inventory
   permissions/mounts/processes, including Docker/libvirt/runtime credentials.
8. Deliver and test the **reproducible accepted runtime VM/host profile**. Current
   source roots use a development template hash and direct disposable QEMU lab
   launching. They are not an accepted production template or complete M04 host
   provisioning integration. Verify host-side VM cgroups/budgets/identity and
   preserve the separate management boundary; guest app limits alone are not
   complete host isolation acceptance.
9. Finish maintained-profile drift checks and actual failure variants. One pending
   improvement: verify managed `/etc/hosts`, `/etc/hostname`, `/etc/resolv.conf`
   readonly mount flags from kernel mountinfo, beyond hardener/configuration and
   nonroot write-denial checks. Treat any missing proof as non-ready.
10. Run the full M06/M07/M08 regression affected by Git permission normalization,
    plus full Go tests/vet, targeted races, bounded command fuzzing and reporter
    tests on final source. Freeze source/templates/policy, publish bounded safe
    evidence and refresh the source/evidence manifest and post-implementation test
    plan. Update required ledgers only from actual complete passing evidence.

The existing required ledger still has R01 FAIL and R02–R10 NOT_RUN. Its prose,
acceptance report and manifest mostly describe older increments and must be
updated carefully; do not erase failed evidence. The milestone reporter must
continue returning INCOMPLETE until every required constituent really passes.

## Immediate next implementation step

The six `Engine.Remove` component fault cases now pass under the race detector:
lost response after deletion, false success retaining the object, already absent,
inspection denied, foreign labels, and wrong app. Startup recovery now converts
pending commands to uncertain durable results, fences pending creates and retains
resources/capacity; its targeted recovery test passed. This recovery change still
needs real VM validation.

A fixed-enum disposable guest operator is partially implemented in
`infra/runtime/experiments/processlab/operator_linux.go`, with a bounded readonly
`Client.ObjectCounts` helper. The runtime guest script now invokes this operator.
**Do not run the changed pair harness until its host wiring is completed:** add a
private runtime serial control socket for guest `/dev/ttyS2`, hold the connection,
handle the controller's fixed restart request, and require actual changed agent
PIDs plus equal before/after object counts. Require final zero containers and
only the three builtin networks per app before disposable VM teardown. Record
proof in result JSON. Verify the new code compiles; rebuild trusted guest binaries
and refresh profile hashes. The last completed real VM run remains pair12, which
predates these recovery/operator changes. No QEMU process was running at save.

Then run the real same-ledger agent restart scenario, implement exact owned
abandoned-probe recovery, and extend bounded phase fault/revocation coverage.
Avoid unrelated product features or public control surfaces.

## Validation notes

Full Go tests/vet and targeted races/fuzz have passed at several development
checkpoints. New checks include durable candidate/restart budgets, cancellation
without engine callbacks, current grant refresh races and strict clock-offset
headroom, immutable admission binding, private Git content modes, and relay
sibling ownership. Re-run after the latest edits; old success is not a final
source freeze. Logs are under `/var/tmp/tap-m09/` (`full-tests-latest.log`,
`vet-latest.log`, `race-latest.log`, `fuzz-latest.log`, various trial logs).
