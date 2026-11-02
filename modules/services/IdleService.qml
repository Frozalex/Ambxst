pragma Singleton

import QtQuick
import QtQml
import Quickshell
import Quickshell.Wayland as Wayland
import qs.config

Singleton {
    id: root

    // General Idle Settings
    property string lockCmd: Config.system.idle.general.lock_cmd ?? "ambxst lock"
    property string beforeSleepCmd: Config.system.idle.general.before_sleep_cmd ?? "loginctl lock-session"
    property string afterSleepCmd: Config.system.idle.general.after_sleep_cmd ?? "ambxst screen on"

    // Sleep/Lock monitoring is handled by the Go daemon (login1 DBus).
    // The daemon executes the configured commands itself and emits
    // SUSPEND/WAKE/LOCK events that drive the QML state below.
    property int sleepSubscription: -1

    // Keep the daemon command config in sync.
    function syncSleepCommands() {
        BackendService.call("sleep.setCommands", {
            before: root.beforeSleepCmd,
            after: root.afterSleepCmd,
            lock: root.lockCmd
        });
    }

    function handleSleepEvent(service, data) {
        if (service !== "sleep" || !data) return;
        const event = data.event;
        if (event === "SUSPEND") {
            root.lockBeforeSleep();
            SuspendManager.onPrepareForSleep();
        } else if (event === "WAKE") {
            SuspendManager.onWakingUp();
        } else if (event === "LOCK") {
            root.lockBeforeSleep();
        }
    }

    Component.onCompleted: {
        root.sleepSubscription = BackendService.addSubscription(["sleep"], (service, data) => root.handleSleepEvent(service, data));
        syncSleepCommands();
    }

    // Each timeout is owned by the compositor's idle protocol. No per-second
    // timer and no repeated axctl processes are needed while the desktop is idle.
    property QtObject listenerMonitors: Instantiator {
        model: Config.system.idle.listeners
        delegate: Wayland.IdleMonitor {
            required property var modelData
            property bool fired: false
            timeout: Math.max(1, modelData.timeout || 60)
            respectInhibitors: true
            onIsIdleChanged: {
                if (isIdle) {
                    fired = true;
                    if (modelData.onTimeout) root.executeCommand(modelData.onTimeout);
                } else if (fired) {
                    fired = false;
                    if (modelData.onResume) root.executeCommand(modelData.onResume);
                }
            }
        }
    }

    function executeCommand(cmd) {
        if (!cmd) return;
        
        // Escape backslashes and quotes for the QML string
        let escapedCmd = cmd.replace(/\\/g, "\\\\").replace(/"/g, '\\"');
        
        try {
            let proc = Qt.createQmlObject(`
                import Quickshell.Io
                Process {
                    command: ["sh", "-c", "${escapedCmd}"]
                    running: true
                    onExited: destroy()
                }
            `, root, "dynamicProc");
        } catch (e) {
            console.error("Failed to create process for command:", cmd, e);
        }
    }

    function shouldUseInternalSleepLock() {
        const cmd = (root.beforeSleepCmd || "").trim();
        return cmd === "loginctl lock-session"
            || cmd === "loginctl lock-sessions"
            || cmd === "ambxst lock";
    }

    function lockBeforeSleep() {
        if (root.shouldUseInternalSleepLock()) {
            LockscreenService.lock();
        }
    }

}
