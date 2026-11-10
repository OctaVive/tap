#!/bin/sh
set -eu
set +x
[ -f /etc/m09-disposable-guest ]
exec >/dev/ttyS0 2>&1
finish() {
 rc=$?
 for app in 33333333-3333-4333-8333-333333333333 22222222-2222-4222-8222-222222222222; do
  for fs in /var/lib/tap-runtime/apps/$app/engine/containerd/daemon/io.containerd.snapshotter.v1.native/snapshots/*; do
   [ -d "$fs" ] || continue
   stat -c 'M09-PROCESS-ROOTFS mode=%a uid=%u gid=%g path=%n' "$fs" "$fs/bin" "$fs/bin/busybox" 2>/dev/null || true
  done
 done
 [ -z "${agent_pid:-}" ] || kill "$agent_pid" || true
 [ -z "${measure_pid:-}" ] || kill "$measure_pid" || true
 echo "M09-PROCESS-RUNTIME-END rc=$rc"
 sync
 systemctl poweroff --no-block
}
trap finish EXIT
trap 'exit 1' TERM INT
interface=$(ip -o link show | awk -F': ' '$2 != "lo" {print $2;exit}')
ip addr add 192.0.2.10/24 dev "$interface"
ip link set "$interface" up
ip -6 addr add fd00:9::10/64 dev "$interface" nodad
ip -6 route add fd00:ec2::254/128 via fd00:9::11 dev "$interface"
ip -6 route add 2001:db8:100::10/128 via fd00:9::11 dev "$interface"
# These two inert destination addresses live only on the disconnected peer VM.
# No interface or route connects this lab to the host network or Internet.
ip route add 169.254.169.254/32 via 192.0.2.11 dev "$interface"
ip route add 203.0.113.10/32 via 192.0.2.11 dev "$interface"
chmod 0666 /dev/net/tun /dev/fuse
apparmor_parser -r /etc/apparmor.d/tap-runtime
/usr/local/bin/tap-runtime-host
if [ -f /opt/m09/diagnostic.oci.tar ]; then
 runuser -u runtime -- env DOCKER_API_VERSION=1.47 DOCKER_HOST=unix:///run/tap-runtime/apps/33333333-3333-4333-8333-333333333333/docker.sock docker load -i /opt/m09/diagnostic.oci.tar
 for fs in /var/lib/tap-runtime/apps/33333333-3333-4333-8333-333333333333/engine/containerd/daemon/io.containerd.snapshotter.v1.native/snapshots/*; do
  [ -d "$fs" ] || continue
  stat -c 'M09-PROCESS-ROOTFS mode=%a uid=%u gid=%g path=%n' "$fs" "$fs/bin" "$fs/bin/busybox" 2>/dev/null || true
 done
fi
/usr/local/bin/tap-runtime-measure &
measure_pid=$!
for n in $(seq 1 20); do [ -S /run/tap-runtime/measure.sock ] && break; sleep 1; done
modprobe qemu_fw_cfg
/opt/m09/processlab operator &
agent_pid=$!
# External lab orchestration powers down this exact VM after the controller's
# recorded lifecycle. The timeout remains a separate fail-closed bound.
for n in $(seq 1 240); do kill -0 "$agent_pid"; sleep 1; done
exit 1
