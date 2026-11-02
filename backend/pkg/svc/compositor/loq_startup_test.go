package compositor

import (
	"strings"
	"testing"
)

func TestCustomStartupCommandPersistsIntoGeneratedConfig(t *testing.T) {
	t.Setenv("AMBXST_STARTUP_COMMAND", "/home/test/Ambxst/loq/launch")
	output := Render(Input{}, false)
	if !strings.Contains(output, `exec-once = "/home/test/Ambxst/loq/launch"`) {
		t.Fatal("custom launcher lost from generated config")
	}
	t.Setenv("AMBXST_STARTUP_COMMAND", "")
	if !strings.Contains(Render(Input{}, false), `exec-once = "ambxst"`) {
		t.Fatal("upstream default changed")
	}
}
