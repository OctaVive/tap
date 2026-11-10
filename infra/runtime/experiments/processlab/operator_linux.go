package main

import (
	"bufio"
	"context"
	"database/sql"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net"
	"net/http"
	"os"
	"os/exec"
	"strconv"
	"strings"
	"syscall"
	"time"

	"dev-orchestrator/internal/runtimeagent"
	"dev-orchestrator/internal/runtimeengine"
	"dev-orchestrator/internal/runtimehost"
	"dev-orchestrator/internal/runtimeisolation"
	"dev-orchestrator/internal/runtimenet"
	"golang.org/x/sys/unix"
)

type operatorAgent struct {
	cmd  *exec.Cmd
	done chan struct{}
}

var operatorOutput io.Writer = os.Stdout

func startOperatorAgent() *operatorAgent {
	cmd := exec.Command("/usr/local/bin/tap-runtime-agent")
	cmd.Env = []string{"PATH=/usr/local/bin:/usr/bin:/bin", "LANG=C"}
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	cmd.SysProcAttr = &syscall.SysProcAttr{Credential: &syscall.Credential{Uid: 1000, Gid: 1000, Groups: []uint32{}}, Pdeathsig: syscall.SIGKILL}
	must(cmd.Start())
	child := &operatorAgent{cmd: cmd, done: make(chan struct{})}
	go func() { _ = cmd.Wait(); close(child.done) }()
	return child
}
func (a *operatorAgent) stop() {
	_ = a.cmd.Process.Kill()
	select {
	case <-a.done:
	case <-time.After(3 * time.Second):
		must(runtimeagent.ErrUncertain)
	}
}
func operatorSnapshot(profile runtimehost.Profile, phase string) {
	for _, app := range profile.Apps {
		ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
		enrollment, err := runtimeisolation.ReadEnrollment(app.ID)
		must(err)
		live, err := runtimeisolation.CollectBackend(ctx, profile.WorkerID, profile.Incarnation, app.Reservation())
		must(err)
		if live != enrollment {
			must(runtimeagent.ErrDenied)
		}
		client, err := runtimeengine.NewClient(enrollment.Backend.Socket)
		must(err)
		containers, networks, running, err := client.ObjectStateCounts(ctx)
		client.Close()
		cancel()
		must(err)
		raw, err := json.Marshal(struct {
			Phase      string `json:"phase"`
			AppID      string `json:"app_id"`
			Containers int    `json:"containers"`
			Networks   int    `json:"networks"`
			Running    int    `json:"running"`
		}{phase, app.ID, containers, networks, running})
		must(err)
		fmt.Fprintln(operatorOutput, "M09-OPERATOR-STATE", string(raw))
	}
}

// This fixed enum fixture exists only in disposable lab roots. No payload can
// select a PID, executable, shell, filesystem path, socket or Docker API.
func labControl(device string) *os.File {
	fd, err := unix.Open(device, unix.O_RDWR|unix.O_NOCTTY|unix.O_NONBLOCK, 0)
	must(err)
	terminal, err := unix.IoctlGetTermios(fd, unix.TCGETS)
	must(err)
	terminal.Iflag = unix.IGNPAR
	terminal.Oflag = 0
	terminal.Lflag = 0
	terminal.Cflag = unix.CS8 | unix.CLOCAL | unix.CREAD | unix.B115200
	terminal.Cc[unix.VMIN] = 1
	terminal.Cc[unix.VTIME] = 0
	must(unix.IoctlSetTermios(fd, unix.TCSETS, terminal))
	must(unix.SetNonblock(fd, false))
	return os.NewFile(uintptr(fd), "private-lab-control")
}

func awaitOperator(ctx context.Context, request, reply string) {
	control := labControl("/dev/ttyS1")
	defer control.Close()
	done := make(chan bool, 1)
	go func() {
		scanner := bufio.NewScanner(control)
		scanner.Buffer(make([]byte, 128), 128)
		done <- scanner.Scan() && scanner.Text() == reply
	}()
	fmt.Println("M09-PROCESS-REQUEST", request)
	budget := 20 * time.Second
	if request == "verify-network-dual-stack" {
		budget = 50 * time.Second
	}
	if request == "verify-network-ipv4" {
		budget = 30 * time.Second
	}
	select {
	case ok := <-done:
		if !ok {
			must(runtimeagent.ErrDenied)
		}
	case <-ctx.Done():
		must(ctx.Err())
	case <-time.After(budget):
		must(runtimeagent.ErrUncertain)
	}
}

func relayFixture(removed bool) {
	// Fixed admitted two-service fixture only. No command selects a URL, owner,
	// path, app or Unix socket. This is independent of the engine adapter.
	path := runtimenet.Socket(runtimenet.Configuration{AppID: "22222222-2222-4222-8222-222222222222", OwnerID: "66666666-6666-4666-8666-000000000002"})
	if removed {
		deadline := time.Now().Add(12 * time.Second)
		for time.Now().Before(deadline) {
			_, err := os.Lstat(path)
			if os.IsNotExist(err) {
				conn, err := net.DialTimeout("unix", path, time.Second)
				if conn != nil {
					conn.Close()
				}
				if errors.Is(err, syscall.ENOENT) {
					fmt.Fprintln(operatorOutput, "M09-OPERATOR-ACK relay-removed")
					return
				}
			}
			time.Sleep(100 * time.Millisecond)
		}
		must(runtimeagent.ErrUncertain)
	}
	transport := &http.Transport{Proxy: nil, MaxResponseHeaderBytes: 4096, DialContext: func(ctx context.Context, _, _ string) (net.Conn, error) {
		return (&net.Dialer{Timeout: time.Second}).DialContext(ctx, "unix", path)
	}}
	defer transport.CloseIdleConnections()
	client := &http.Client{Transport: transport, Timeout: 3 * time.Second, CheckRedirect: func(*http.Request, []*http.Request) error { return runtimeagent.ErrDenied }}
	response, err := client.Get("http://private-fixture/health")
	must(err)
	defer response.Body.Close()
	n, err := io.Copy(io.Discard, io.LimitReader(response.Body, 1025))
	must(err)
	if response.StatusCode != 200 || n > 1024 {
		must(runtimeagent.ErrDenied)
	}
	fmt.Fprintln(operatorOutput, "M09-OPERATOR-ACK relay-live status=200")
}

// This is a fixed readonly barrier on the disposable agent's private ledger.
// It never creates an intent, modifies a record or adopts an engine object.
func waitRecordedProbe(agent *operatorAgent) (string, []string) {
	ctx, cancel := context.WithTimeout(context.Background(), 120*time.Second)
	defer cancel()
	db, err := sql.Open("sqlite", "file:"+runtimehost.Root+"/agent/ledger.sqlite?mode=ro")
	must(err)
	defer db.Close()
	for ctx.Err() == nil {
		// Freeze the owned process while reading the barrier. It cannot finish
		// the command between our durable-state observation and the kill.
		must(agent.cmd.Process.Signal(syscall.SIGSTOP))
		var command string
		err := db.QueryRowContext(ctx, "SELECT c.id FROM commands c WHERE c.operation='probe' AND c.state='pending' AND EXISTS(SELECT 1 FROM resources r WHERE r.owner=c.id AND r.kind='container') ORDER BY c.rowid LIMIT 1").Scan(&command)
		if err == nil {
			rows, err := db.QueryContext(ctx, "SELECT id FROM resources WHERE owner=? ORDER BY kind,id", command)
			must(err)
			var ids []string
			for rows.Next() {
				var id string
				must(rows.Scan(&id))
				ids = append(ids, id)
			}
			must(rows.Err())
			rows.Close()
			if len(ids) == 2 {
				return command, ids
			}
		}
		must(agent.cmd.Process.Signal(syscall.SIGCONT))
		time.Sleep(5 * time.Millisecond)
	}
	must(runtimeagent.ErrUncertain)
	return "", nil
}

func operator() {
	if os.Geteuid() != 0 {
		must(runtimeagent.ErrDenied)
	}
	_, err := os.Stat("/etc/m09-disposable-guest")
	must(err)
	profile, err := runtimehost.Load()
	must(err)
	control := labControl("/dev/ttyS2")
	defer control.Close()
	// Only this fixed root fixture writes the private protocol. Console/kernel
	// output may interleave on ttyS0 and is never parsed as structured proof.
	operatorOutput = io.MultiWriter(control, os.Stdout)
	initializeVMClock(control, "runtime")
	enroll()
	agent := startOperatorAgent()
	defer func() { agent.stop() }()
	fmt.Fprintln(operatorOutput, "M09-OPERATOR-READY")
	scanner := bufio.NewScanner(control)
	scanner.Buffer(make([]byte, 128), 128)
	for scanner.Scan() {
		if strings.HasPrefix(scanner.Text(), "probe-denial-step-") {
			index, err := strconv.Atoi(strings.TrimPrefix(scanner.Text(), "probe-denial-step-"))
			must(err)
			denialMatrixSnapshot(profile, index)
			continue
		}
		switch scanner.Text() {
		case "sample-clock":
			fmt.Fprintf(operatorOutput, "M09-CLOCK %d\n", time.Now().UnixNano())
		case "probe-network-dual-stack":
			networkProof(profile, true)
		case "probe-network-ipv4":
			networkProof(profile, false)
		case "probe-denial-baseline":
			noApplicationEffects(profile, "baseline")
		case "probe-denial-after":
			noApplicationEffects(profile, "after")
		case "probe-no-image-effects":
			noImageEffects(profile)
		case "probe-owned-stopped":
			ownedStopped(profile)
		case "rotate-agent-certificate":
			rotateCertificate(agent)
		case "probe-relay-live":
			relayFixture(false)
		case "probe-relay-removed":
			relayFixture(true)
		case "arm-probe-crash":
			command, ids := waitRecordedProbe(agent)
			before := agent.cmd.Process.Pid
			agent.stop()
			// Record the barrier after the process is dead, before starting recovery.
			raw, err := json.Marshal(map[string]any{"command_id": command, "resource_ids": ids, "old_pid": before})
			must(err)
			fmt.Fprintln(operatorOutput, "M09-OPERATOR-FAULT", string(raw))
			agent = startOperatorAgent()
			fmt.Fprintf(operatorOutput, "M09-OPERATOR-ACK crash-probe old=%d new=%d\n", before, agent.cmd.Process.Pid)
		case "restart-agent":
			operatorSnapshot(profile, "before-restart")
			before := agent.cmd.Process.Pid
			agent.stop()
			agent = startOperatorAgent()
			operatorSnapshot(profile, "after-restart")
			fmt.Fprintf(operatorOutput, "M09-OPERATOR-ACK restart-agent old=%d new=%d\n", before, agent.cmd.Process.Pid)
		case "snapshot":
			operatorSnapshot(profile, "final")
			fmt.Fprintln(operatorOutput, "M09-OPERATOR-ACK snapshot")
		default:
			must(runtimeagent.ErrDenied)
		}
	}
	if scanner.Err() != nil {
		must(runtimeagent.ErrDenied)
	}
}
