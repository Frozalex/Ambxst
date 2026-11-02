//go:build linux

package systemmonitor

import (
	"os"
	"path/filepath"
	"testing"
)

func TestNvidiaMetricsOptOutNeverRunsSMI(t *testing.T) {
	dir := t.TempDir()
	marker := filepath.Join(dir, "called")
	script := "#!/bin/sh\necho called > '" + marker + "'\necho '7.5, 42'\n"
	if err := os.WriteFile(filepath.Join(dir, "nvidia-smi"), []byte(script), 0755); err != nil {
		t.Fatal(err)
	}
	t.Setenv("PATH", dir)
	t.Setenv("AMBXST_NVIDIA_METRICS", "0")
	usage, temp := nvidiaQuery("fake")
	if usage != -1 || temp != -1 {
		t.Fatalf("unavailable metrics not represented: %v %v", usage, temp)
	}
	if _, err := os.Stat(marker); !os.IsNotExist(err) {
		t.Fatal("nvidia-smi was executed")
	}
	t.Setenv("AMBXST_NVIDIA_METRICS", "1")
	usage, temp = nvidiaQuery("fake")
	if usage != 7.5 || temp != 42 {
		t.Fatalf("opt-in query broken: %v %v", usage, temp)
	}
}
func TestNvidiaRuntimeStateFailsClosed(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "runtime_status")
	if nvidiaRuntimeActive("") || nvidiaRuntimeActive(path) {
		t.Fatal("unknown state permitted probing")
	}
	for _, state := range []string{"suspended", "suspending", "resuming", "", "unsupported"} {
		os.WriteFile(path, []byte(state), 0644)
		if nvidiaRuntimeActive(path) {
			t.Fatalf("state %q permitted probing", state)
		}
	}
	os.WriteFile(path, []byte("active\n"), 0644)
	if !nvidiaRuntimeActive(path) {
		t.Fatal("active device rejected")
	}
}
