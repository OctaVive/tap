// Package runtimeengine implements a bounded Docker Engine HTTP adapter. It has
// no shell, caller-selected API path, host path, Docker options or exec endpoint.
package runtimeengine

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"io"
	"net"
	"net/http"
	"net/url"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"time"

	"dev-orchestrator/internal/runtimeagent"
)

// API 1.47 is an explicit minimum contract; deployment must pin/test the daemon.
const APIVersion = "1.47"
const maxResponse = 1 << 20

var errObjectAbsent = errors.New("runtime_object_absent")

var objectID = regexp.MustCompile(`^[a-f0-9]{64}$`)

type Client struct{ http *http.Client }

func NewClient(socket string) (*Client, error) {
	if !filepath.IsAbs(socket) || filepath.Clean(socket) != socket || strings.IndexByte(socket, 0) >= 0 {
		return nil, runtimeagent.ErrDenied
	}
	t := &http.Transport{Proxy: nil, MaxIdleConns: 2, MaxConnsPerHost: 2, ResponseHeaderTimeout: 5 * time.Second, DialContext: func(ctx context.Context, _, _ string) (net.Conn, error) {
		return (&net.Dialer{Timeout: 5 * time.Second}).DialContext(ctx, "unix", socket)
	}}
	return &Client{http: &http.Client{Transport: t, Timeout: 30 * time.Second, CheckRedirect: func(*http.Request, []*http.Request) error { return runtimeagent.ErrDenied }}}, nil
}
func (c *Client) call(ctx context.Context, method, path string, body, out any) error {
	var r io.Reader
	if body != nil {
		b, e := json.Marshal(body)
		if e != nil || len(b) > 128<<10 {
			return runtimeagent.ErrDenied
		}
		r = bytes.NewReader(b)
	}
	req, e := http.NewRequestWithContext(ctx, method, "http://engine/v"+APIVersion+path, r)
	if e != nil {
		return runtimeagent.ErrDenied
	}
	req.Header.Set("Content-Type", "application/json")
	res, e := c.http.Do(req)
	if e != nil {
		return runtimeagent.ErrUncertain
	}
	defer res.Body.Close()
	if res.StatusCode < 200 || res.StatusCode >= 300 {
		if res.StatusCode == http.StatusNotFound {
			return errObjectAbsent
		}
		if method == "POST" && (strings.HasSuffix(path, "/start") || strings.HasPrefix(path, "/containers/create")) {
			raw, _ := io.ReadAll(io.LimitReader(res.Body, 8192))
			reason := "unknown"
			for _, candidate := range []struct{ needle, code string }{{"runtime_bundle_denied", "bundle"}, {"no such file or directory", "missing_file"}, {"permission denied", "permission"}, {"apparmor", "mac"}, {"seccomp", "seccomp"}, {"memory", "memory"}} {
				if strings.Contains(strings.ToLower(string(raw)), candidate.needle) {
					reason = candidate.code
					break
				}
			}
			os.Stderr.WriteString("runtime_engine_request_" + reason + "_denied\n")
		}
		return runtimeagent.ErrDenied
	}
	b, e := io.ReadAll(io.LimitReader(res.Body, maxResponse+1))
	if e != nil || len(b) > maxResponse {
		return runtimeagent.ErrDenied
	}
	if out != nil {
		if json.Unmarshal(b, out) != nil {
			return runtimeagent.ErrDenied
		}
	}
	return nil
}
func escape(s string) string { return url.PathEscape(s) }

func (c *Client) close() {
	if t, ok := c.http.Transport.(guardedTransport); ok {
		if base, ok := t.next.(*http.Transport); ok {
			base.CloseIdleConnections()
		}
	} else {
		c.http.CloseIdleConnections()
	}
}

// InspectContainer is a bounded read-only primitive for the fixed VM measurement
// helper. There is no arbitrary API path or command forwarding interface.
func (c *Client) InspectContainer(ctx context.Context, id string) (Inspected, error) {
	var got Inspected
	if !objectID.MatchString(id) || c.call(ctx, "GET", "/containers/"+id+"/json", nil, &got) != nil || got.ID != id {
		return Inspected{}, runtimeagent.ErrDenied
	}
	return got, nil
}

// ImagePresent is a fixed readonly digest lookup for private lab observations.
func (c *Client) ImagePresent(ctx context.Context, digest string) (bool, error) {
	if !strings.HasPrefix(digest, "sha256:") || !objectID.MatchString(strings.TrimPrefix(digest, "sha256:")) {
		return false, runtimeagent.ErrDenied
	}
	var image struct {
		ID string `json:"Id"`
	}
	err := c.call(ctx, "GET", "/images/"+escape(digest)+"/json", nil, &image)
	if err == errObjectAbsent {
		return false, nil
	}
	if err != nil || image.ID != digest {
		return false, runtimeagent.ErrUnsupported
	}
	return true, nil
}

// Close releases only this client's idle connections; it cannot stop a daemon.
func (c *Client) Close() { c.close() }

// ObjectCounts is a bounded read-only inventory primitive for the private VM
// operator fixture. It returns no commands, environment, mounts or logs.
func (c *Client) ObjectCounts(ctx context.Context) (int, int, error) {
	containers, networks, _, err := c.ObjectStateCounts(ctx)
	return containers, networks, err
}

// ObjectStateCounts additionally observes running objects for the fixed lab
// restart proof. It exposes no configurable API path or workload payload.
func (c *Client) ObjectStateCounts(ctx context.Context) (int, int, int, error) {
	var containers []struct {
		ID    string `json:"Id"`
		State string
	}
	var networks []struct {
		ID string `json:"Id"`
	}
	if c.call(ctx, "GET", "/containers/json?all=true", nil, &containers) != nil || len(containers) > 128 {
		return 0, 0, 0, runtimeagent.ErrUnsupported
	}
	if c.call(ctx, "GET", "/networks", nil, &networks) != nil || len(networks) > 128 {
		return 0, 0, 0, runtimeagent.ErrUnsupported
	}
	running := 0
	seen := map[string]bool{}
	for _, object := range containers {
		if !objectID.MatchString(object.ID) || seen[object.ID] {
			return 0, 0, 0, runtimeagent.ErrUnsupported
		}
		seen[object.ID] = true
		switch object.State {
		case "running":
			running++
		case "created", "restarting", "removing", "paused", "exited", "dead":
		default:
			return 0, 0, 0, runtimeagent.ErrUnsupported
		}
	}
	for _, object := range networks {
		if !objectID.MatchString(object.ID) || seen[object.ID] {
			return 0, 0, 0, runtimeagent.ErrUnsupported
		}
		seen[object.ID] = true
	}
	return len(containers), len(networks), running, nil
}
