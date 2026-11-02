pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Services.UPower
Singleton {
    id: root
    readonly property bool enabled: Quickshell.env("AMBXST_LOQ_PROFILE") === "1"
    readonly property bool critical: UPower.displayDevice.ready && UPower.onBattery && UPower.displayDevice.percentage <= 0.15
    function applySupply() {
        if (!enabled || !UPower.displayDevice.ready || !PowerProfileClient.isAvailable) return;
        PowerProfileClient.setProfile(UPower.onBattery ? "power-saver" : "balanced");
    }
    onCriticalChanged: if (enabled && critical && PowerProfileClient.isAvailable) PowerProfileClient.setProfile("power-saver")
    Component.onCompleted: applySupply()
    Connections { target: UPower; function onOnBatteryChanged() { root.applySupply(); } }
    Connections { target: UPower.displayDevice; function onReadyChanged() { root.applySupply(); } }
    Connections { target: PowerProfileClient; function onIsAvailableChanged() { root.applySupply(); } }
}
