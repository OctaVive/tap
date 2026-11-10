// processlab is an explicit disposable-lab issuer. It is not a product approval
// endpoint and cannot manufacture M07/M08 records or parse a workload archive.
package main

import (
	"context"
	"crypto/ed25519"
	"crypto/rand"
	"crypto/sha256"
	"crypto/x509"
	"crypto/x509/pkix"
	"database/sql"
	"encoding/base64"
	"encoding/hex"
	"encoding/json"
	"encoding/pem"
	"fmt"
	"math/big"
	"net"
	"net/url"
	"os"
	"path/filepath"
	"time"

	"dev-orchestrator/internal/contracts"
	"dev-orchestrator/internal/policy"
	"dev-orchestrator/internal/runtimeagent"
	"dev-orchestrator/internal/runtimehost"
	"dev-orchestrator/internal/runtimeisolation"
	"dev-orchestrator/internal/runtimeprocess"
	"dev-orchestrator/internal/storage"
)

const worker = "11111111-1111-4111-8111-111111111111"
const guestRoot = "/var/lib/m09-process"

type fixture struct {
	Scenario                                                  string `json:"scenario,omitempty"`
	WorkerID, Incarnation, InventoryPublic, WorkerFingerprint string
	RotationFingerprint                                       string
	CertificateUntil                                          time.Time
}
type handoffImage struct {
	Intent storage.BuildIntent `json:"intent"`
	Image  string              `json:"image"`
}
type handoff struct {
	External []handoffImage           `json:"external,omitempty"`
	Intent   storage.BuildIntent      `json:"intent"`
	Spec     contracts.RuntimeSpecV2  `json:"spec"`
	Result   contracts.ArtifactResult `json:"result"`
}

func must(e error) {
	if e != nil {
		fmt.Println("M09-PROCESS-ERROR", e)
		os.Exit(1)
	}
}
func write(path string, raw []byte) { must(os.WriteFile(path, raw, 0600)) }
func jsonFile(path string, v any)   { b, e := json.Marshal(v); must(e); write(path, b) }
func readJSON[T any](path string) T {
	b, e := os.Open(path)
	must(e)
	defer b.Close()
	v, e := contracts.DecodeConfiguration[T](b)
	must(e)
	return v
}
func hash(b []byte) string { h := sha256.Sum256(b); return hex.EncodeToString(h[:]) }
func generate(dir string) {
	must(os.Mkdir(dir, 0700))
	must(os.Mkdir(filepath.Join(dir, "agent"), 0700))
	must(os.Mkdir(filepath.Join(dir, "controller"), 0700))
	must(os.Mkdir(filepath.Join(dir, "agent-rotation"), 0700))
	caPub, caKey, e := ed25519.GenerateKey(rand.Reader)
	must(e)
	now := time.Now()
	ca := &x509.Certificate{SerialNumber: big.NewInt(1), Subject: pkix.Name{CommonName: "M09 isolated lab CA"}, NotBefore: now.Add(-time.Minute), NotAfter: now.Add(6 * time.Hour), IsCA: true, BasicConstraintsValid: true, KeyUsage: x509.KeyUsageCertSign}
	caDER, e := x509.CreateCertificate(rand.Reader, ca, ca, caPub, caKey)
	must(e)
	issue := func(name, uri string, serial int64, usage x509.ExtKeyUsage) ([]byte, ed25519.PrivateKey) {
		pub, key, e := ed25519.GenerateKey(rand.Reader)
		must(e)
		u, e := url.Parse(uri)
		must(e)
		c := &x509.Certificate{SerialNumber: big.NewInt(serial), Subject: pkix.Name{CommonName: name}, NotBefore: now.Add(-time.Minute), NotAfter: now.Add(4 * time.Hour), KeyUsage: x509.KeyUsageDigitalSignature, ExtKeyUsage: []x509.ExtKeyUsage{usage}, URIs: []*url.URL{u}}
		if usage == x509.ExtKeyUsageServerAuth {
			c.IPAddresses = []net.IP{net.ParseIP("192.0.2.11"), net.ParseIP("fd00:9::11")}
			c.DNSNames = []string{"runtime-controller.m09.invalid"}
		}
		der, e := x509.CreateCertificate(rand.Reader, c, ca, pub, caKey)
		must(e)
		return der, key
	}
	server, serverKey := issue("runtime controller", "spiffe://tap/runtime-controller", 2, x509.ExtKeyUsageServerAuth)
	agent, agentKey := issue("runtime agent", "spiffe://tap/runtime-agent/"+worker, 3, x509.ExtKeyUsageClientAuth)
	rotated, rotatedKey := issue("runtime agent rotated", "spiffe://tap/runtime-agent/"+worker, 4, x509.ExtKeyUsageClientAuth)
	reportPub, reportKey, e := ed25519.GenerateKey(rand.Reader)
	must(e)
	commandPub, commandKey, e := ed25519.GenerateKey(rand.Reader)
	must(e)
	material := func(sub string, cert []byte, key ed25519.PrivateKey) {
		p := filepath.Join(dir, sub)
		write(filepath.Join(p, "ca.pem"), pem.EncodeToMemory(&pem.Block{Type: "CERTIFICATE", Bytes: caDER}))
		write(filepath.Join(p, "cert.pem"), pem.EncodeToMemory(&pem.Block{Type: "CERTIFICATE", Bytes: cert}))
		raw, e := x509.MarshalPKCS8PrivateKey(key)
		must(e)
		write(filepath.Join(p, "key.pem"), pem.EncodeToMemory(&pem.Block{Type: "PRIVATE KEY", Bytes: raw}))
	}
	material("agent", agent, agentKey)
	material("agent-rotation", rotated, rotatedKey)
	material("controller", server, serverKey)
	write(filepath.Join(dir, "agent/inventory.key"), []byte(base64.StdEncoding.EncodeToString(reportKey)))
	write(filepath.Join(dir, "controller/command.key"), []byte(base64.StdEncoding.EncodeToString(commandKey)))
	keys := map[string]string{"fixture": base64.StdEncoding.EncodeToString(commandPub)}
	cert, e := x509.ParseCertificate(server)
	must(e)
	jsonFile(filepath.Join(dir, "agent/config.json"), runtimeprocess.AgentConfiguration{Origin: "https://192.0.2.11:9443", ServerName: "runtime-controller.m09.invalid", ControllerURI: "spiffe://tap/runtime-controller", ControllerSPKI: hash(cert.RawSubjectPublicKeyInfo), AllowedControllerCertificates: []string{hash(server)}, CA: "/var/lib/tap-runtime/agent/ca.pem", Certificate: "/var/lib/tap-runtime/agent/cert.pem", Key: "/var/lib/tap-runtime/agent/key.pem", InventoryKey: "/var/lib/tap-runtime/agent/inventory.key", CommandKeys: keys})
	jsonFile(filepath.Join(dir, "controller/config.json"), map[string]any{"database": guestRoot + "/metadata.db", "artifacts": guestRoot + "/artifacts", "listen": "192.0.2.11:9443", "ca": guestRoot + "/ca.pem", "certificate": guestRoot + "/cert.pem", "key": guestRoot + "/key.pem", "command_keys": keys})
	workerCert, e := x509.ParseCertificate(agent)
	must(e)
	jsonFile(filepath.Join(dir, "controller/fixture.json"), fixture{WorkerID: worker, Incarnation: worker, InventoryPublic: base64.StdEncoding.EncodeToString(reportPub), WorkerFingerprint: hash(agent), RotationFingerprint: hash(rotated), CertificateUntil: workerCert.NotAfter})
	fmt.Println("M09-PROCESS-TRUST-PREPARED")
}
func drive() {
	if os.Geteuid() != 1002 {
		must(runtimeagent.ErrDenied)
	}
	_, e := os.Stat("/etc/m09-disposable-guest")
	must(e)
	ctx, cancel := context.WithTimeout(context.Background(), 4*time.Minute)
	defer cancel()
	f := readJSON[fixture](guestRoot + "/fixture.json")
	h := readJSON[handoff](guestRoot + "/handoff.json")
	if f.Scenario == "network-ipv4" || f.Scenario == "network-dual-stack" {
		matched := false
		for i := range h.Spec.Services {
			if f.Scenario == "network-dual-stack" && h.Spec.Services[i].Name == "db" {
				h.Spec.Services[i].Entrypoint = nil
				h.Spec.Services[i].Command = []string{"/bin/busybox", "httpd", "-f", "-p", "[::]:8081", "-h", "/srv"}
			}
			if h.Spec.Services[i].Name == "web" {
				h.Spec.Services[i].Entrypoint = nil
				h.Spec.Services[i].Command = []string{"/bin/busybox", "nc", "-ll", "-p", "8080", "-e", "/bin/busybox", "sh", "-c", networkWorkload}
				matched = true
			}
		}
		if !matched {
			must(runtimeagent.ErrDenied)
		}
	}
	enrollments := readJSON[struct {
		Enrollments []runtimeisolation.Enrollment `json:"enrollments"`
	}](guestRoot + "/enrollments.json").Enrollments
	key, e := runtimeprocess.PrivateKey(guestRoot + "/command.key")
	must(e)
	pub := key.Public().(ed25519.PublicKey)
	report, e := base64.StdEncoding.Strict().DecodeString(f.InventoryPublic)
	must(e)
	state, e := storage.Open(ctx, guestRoot+"/metadata.db")
	must(e)
	defer state.Close()
	var leaseUntil time.Time
	renew := func() {
		leaseUntil = time.Now().Add(55 * time.Second)
		must(state.EnrollRuntimeWorker(ctx, storage.RuntimeWorker{WorkerID: f.WorkerID, Incarnation: f.Incarnation, InventoryKey: ed25519.PublicKey(report), LeaseUntil: leaseUntil}))
	}
	renew()
	must(state.EnrollRuntimeCertificate(ctx, f.WorkerID, f.Incarnation, f.WorkerFingerprint, f.CertificateUntil))
	for _, enrollment := range enrollments {
		if enrollment.WorkerID != f.WorkerID || enrollment.Incarnation != f.Incarnation {
			must(runtimeagent.ErrDenied)
		}
		must(state.EnrollRuntimeBackend(ctx, f.WorkerID, f.Incarnation, enrollment.Backend.AppID, enrollment.Backend.Hash()))
	}
	must(state.SetRuntimeScanPolicy(ctx, h.Intent.Job.Policy))
	for _, service := range h.Spec.Services {
		intent := h.Intent
		for _, external := range h.External {
			if external.Image == service.Image {
				intent = external.Intent
			}
		}
		admission, err := state.EnrollRuntimeImage(ctx, intent, service.Image)
		must(err)
		if admission.ID != service.AdmissionID {
			must(runtimeagent.ErrDenied)
		}
	}
	must(state.IssueRuntimeApproval(ctx, f.WorkerID, f.Incarnation, 1, h.Spec, time.Now().Add(10*time.Minute)))
	db, e := sql.Open("sqlite", guestRoot+"/metadata.db")
	must(e)
	defer db.Close()
	createID := "66666666-6666-4666-8666-000000000002"
	revoked := false
	operations := []string{"probe", "create", "inspect", "logs", "stop", "inspect", "remove", "probe"}
	if f.Scenario == "corrupt-archive" {
		operations = []string{"probe", "create", "remove", "probe"}
	}
	for i, operation := range operations {
		renew()
		c := runtimeagent.Command{Version: 3, Operation: operation, ID: fmt.Sprintf("66666666-6666-4666-8666-%012d", i+1), WorkerID: f.WorkerID, Incarnation: f.Incarnation, AppID: h.Spec.AppID, DeploymentID: h.Spec.DeploymentID, Generation: 1, Nonce: fmt.Sprintf("%064x", i+1000), KeyID: "fixture", ExpiresAt: time.Now().UTC().Add(4 * time.Minute).Format(time.RFC3339Nano), PolicyHash: policy.Hash(), SpecHash: policy.SpecHash(h.Spec)}
		if operation == "create" {
			c.Spec = &h.Spec
		} else if operation != "probe" {
			c.Target = createID
		}
		if operation == "logs" {
			c.LogLimit = 4096
		}
		must(c.Sign(key))
		if operation == "create" && isDenial(f.Scenario) {
			awaitOperator(ctx, "verify-denial-baseline", "denial-baseline-confirmed")
		}
		if operation == "create" && f.Scenario == "deny-matrix" {
			jsonFile(guestRoot+"/denial-case.json", denialMarker{Index: 0})
		}
		must(state.QueueRuntimeCommand(ctx, c, map[string]ed25519.PublicKey{"fixture": pub}))
		if operation == "create" && isDenial(f.Scenario) {
			if f.Scenario == "deny-matrix" {
				runDenialMatrix(ctx)
			} else {
				waitDenialInjected(ctx)
				awaitOperator(ctx, "verify-denial-after", "denial-after-confirmed")
			}
			write(guestRoot+"/denial-release", []byte("allow exact original valid signed command"))
		}
		nextRenew := time.Now().Add(15 * time.Second)
		for {
			if ctx.Err() != nil {
				must(ctx.Err())
			}
			if time.Now().After(nextRenew) {
				renew()
				nextRenew = time.Now().Add(15 * time.Second)
			}
			var raw []byte
			e = db.QueryRowContext(ctx, "SELECT result_json FROM runtime_queue WHERE command=?", c.ID).Scan(&raw)
			must(e)
			if len(raw) > 0 {
				var result runtimeagent.Result
				must(json.Unmarshal(raw, &result))
				fmt.Printf("M09-PROCESS-RESULT operation=%s code=%s\n", operation, result.Code)
				if i == 0 && f.Scenario == "probe-crash" {
					if result.Code != "uncertain" || result.Inventory != nil {
						must(runtimeagent.ErrDenied)
					}
					break
				}
				if operation == "create" && f.Scenario == "corrupt-archive" {
					if result.Code != "uncertain" || result.Inventory != nil {
						must(runtimeagent.ErrDenied)
					}
					awaitOperator(ctx, "verify-no-image-effects", "no-image-effects-confirmed")
					break
				}
				if result.Code != "ok" {
					must(runtimeagent.ErrDenied)
				}
				if operation == "probe" && result.Inventory == nil {
					must(runtimeagent.ErrDenied)
				}
				if operation == "inspect" {
					expected := "running"
					if revoked || i > 2 {
						expected = "stopped"
					}
					if result.State != expected {
						must(runtimeagent.ErrDenied)
					}
					fmt.Printf("M09-PROCESS-STATE operation=inspect state=%s\n", result.State)
				}
				if operation == "create" {
					if f.Scenario == "approval-revoke" || f.Scenario == "admission-revoke" || f.Scenario == "scan-policy-change" || f.Scenario == "lease-expiry" || f.Scenario == "certificate-revoke-rotate" {
						awaitOperator(ctx, "verify-relay-live", "relay-live-confirmed")
					}
					switch f.Scenario {
					case "lease-expiry":
						timer := time.NewTimer(time.Until(leaseUntil) + 200*time.Millisecond)
						select {
						case <-timer.C:
						case <-ctx.Done():
							must(ctx.Err())
						}
						revoked = true
					case "certificate-revoke-rotate":
						must(state.RevokeRuntimeCertificate(ctx, f.WorkerFingerprint))
						revoked = true
					case "approval-revoke":
						must(state.RevokeRuntimeApproval(ctx, h.Spec.AppID, 1))
						revoked = true
					case "admission-revoke":
						must(state.RevokeRuntimeImage(ctx, h.Spec.Services[0].AdmissionID))
						revoked = true
					case "scan-policy-change":
						next := h.Intent.Job.Policy
						// A stricter current trusted scan policy invalidates the old
						// exact admission; no immutable M07 record is rewritten.
						next.DatabaseMaxAgeSeconds /= 2
						must(state.SetRuntimeScanPolicy(ctx, next))
						revoked = true
					}
					if revoked {
						fmt.Println("M09-PROCESS-REVOKED", f.Scenario)
						// The idle supervisor must stop/drain before any explicit stop
						// command is queued. Inspect below proves its observed state.
						awaitOperator(ctx, "verify-relay-removed", "relay-removed-confirmed")
						if f.Scenario == "lease-expiry" || f.Scenario == "certificate-revoke-rotate" {
							awaitOperator(ctx, "verify-owned-stopped", "owned-stopped-confirmed")
							if f.Scenario == "certificate-revoke-rotate" {
								must(state.EnrollRuntimeCertificate(ctx, f.WorkerID, f.Incarnation, f.RotationFingerprint, f.CertificateUntil))
								awaitOperator(ctx, "rotate-agent-certificate", "certificate-provisioned")
								fmt.Println("M09-PROCESS-CERTIFICATE-ROTATED")
							}
							renew()
						}
					}
				}
				if operation == "create" && f.Scenario == "agent-restart" {
					awaitOperator(ctx, "restart-agent", "restart-complete")
				}
				if operation == "create" && (f.Scenario == "network-ipv4" || f.Scenario == "network-dual-stack") {
					awaitOperator(ctx, "verify-relay-live", "relay-live-confirmed")
					renew()
					if f.Scenario == "network-dual-stack" {
						awaitOperator(ctx, "verify-network-dual-stack", "network-dual-stack-confirmed")
					} else {
						awaitOperator(ctx, "verify-network-ipv4", "network-ipv4-confirmed")
					}
				}
				if operation == "remove" && (f.Scenario == "network-ipv4" || f.Scenario == "network-dual-stack") {
					awaitOperator(ctx, "verify-relay-removed", "relay-removed-confirmed")
				}
				break
			}
			time.Sleep(200 * time.Millisecond)
		}
	}
	fmt.Println("M09-PROCESS-COMPLETE scope=real-M07-stateless-lifecycle-only")
}
func enroll() {
	if os.Geteuid() != 0 {
		must(runtimeagent.ErrDenied)
	}
	_, e := os.Stat("/etc/m09-disposable-guest")
	must(e)
	p, e := runtimehost.Load()
	must(e)
	var entries []runtimeisolation.Enrollment
	for _, app := range p.Apps {
		v, e := runtimeisolation.ReadEnrollment(app.ID)
		must(e)
		entries = append(entries, v)
	}
	raw, e := json.Marshal(entries)
	must(e)
	fmt.Fprintln(operatorOutput, "M09-PROCESS-ENROLLMENTS", string(raw))
}
func main() {
	if len(os.Args) == 2 && os.Args[1] == "initialize-controller-clock" {
		control := labControl("/dev/ttyS1")
		defer control.Close()
		initializeVMClock(control, "controller")
		return
	}
	if len(os.Args) == 2 && os.Args[1] == "observe-controller-clock" {
		observeControllerClock()
		return
	}
	if len(os.Args) == 2 && os.Args[1] == "capture-fixture6" {
		captureFixture(false, true)
		return
	}
	if len(os.Args) == 2 && os.Args[1] == "capture-fixture6-entered" {
		captureFixture(true, true)
		return
	}
	if len(os.Args) == 2 && os.Args[1] == "is-network" {
		scenario := readJSON[fixture](guestRoot + "/fixture.json").Scenario
		if scenario != "network-ipv4" && scenario != "network-dual-stack" {
			os.Exit(1)
		}
		return
	}
	if len(os.Args) == 2 && os.Args[1] == "network-targets" {
		networkTargets()
		return
	}
	if len(os.Args) == 2 && os.Args[1] == "capture-fixture" {
		captureFixture(false, false)
		return
	}
	if len(os.Args) == 2 && os.Args[1] == "capture-fixture-entered" {
		captureFixture(true, false)
		return
	}
	if len(os.Args) == 2 && os.Args[1] == "is-denial" {
		if !isDenial(readJSON[fixture](guestRoot + "/fixture.json").Scenario) {
			os.Exit(1)
		}
		return
	}
	if len(os.Args) == 2 && os.Args[1] == "serve-denial" {
		serveDenial()
		return
	}
	if len(os.Args) == 2 && os.Args[1] == "operator" {
		operator()
		return
	}
	if len(os.Args) == 2 && os.Args[1] == "enroll" {
		enroll()
		return
	}
	if len(os.Args) == 3 && os.Args[1] == "prepare" {
		generate(os.Args[2])
		return
	}
	if len(os.Args) == 2 && os.Args[1] == "drive" {
		drive()
		return
	}
	must(runtimeagent.ErrDenied)
}
