#!/bin/sh
set -eu
set +x
[ -f /etc/m09-disposable-guest ]
exec >/dev/ttyS0 2>&1
finish() {
 rc=$?
 [ -z "${controller_pid:-}" ] || kill "$controller_pid" || true
 [ -z "${targets_pid:-}" ] || kill "$targets_pid" || true
 echo "M09-PROCESS-CONTROLLER-END rc=$rc"
 sync
 systemctl poweroff --no-block
}
trap finish EXIT
interface=$(ip -o link show | awk -F': ' '$2 != "lo" {print $2;exit}')
ip addr add 192.0.2.11/24 dev "$interface"
ip link set "$interface" up
ip -6 addr add fd00:9::11/64 dev "$interface" nodad
modprobe qemu_fw_cfg
/opt/m09/processlab initialize-controller-clock
/opt/m09/processlab observe-controller-clock
if /opt/m09/processlab is-network; then
 ip addr add 169.254.169.254/32 dev lo
 ip addr add 203.0.113.10/32 dev lo
 ip -6 addr add fd00:ec2::254/128 dev lo nodad
 ip -6 addr add 2001:db8:100::10/128 dev lo nodad
 /opt/m09/processlab network-targets &
 targets_pid=$!
 for n in $(seq 1 20); do [ -f /run/m09-network-targets.ready ] && break; sleep .1; done
 [ -f /run/m09-network-targets.ready ]
fi
# This disposable fixture's controller only receives the fixed restart ack.
chown controller:controller /dev/ttyS1
chmod 0600 /dev/ttyS1
if /opt/m09/processlab is-denial; then
 runuser -u controller -- /opt/m09/processlab serve-denial &
else
 runuser -u controller -- /usr/local/bin/tap-runtime-controller -config /var/lib/m09-process/config.json &
fi
controller_pid=$!
runuser -u controller -- /opt/m09/processlab drive
