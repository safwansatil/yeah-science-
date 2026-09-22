import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: root
    width: 1180; height: 790
    minimumWidth: 980; minimumHeight: 720
    visible: true; color: "#0e1922"
    title: "Yeah, Science | Project Altair"
    palette.button: "#293e4b"
    palette.buttonText: "#e8eff1"
    palette.highlight: "#dbaf70"
    palette.text: "#e8eff1"
    palette.base: "#20323e"
    font.family: "Segoe UI"
    onActiveChanged: if (!active) station.stop()

    ColumnLayout {
        anchors.fill: parent; anchors.margins: 24; spacing: 16
        RowLayout {
            ColumnLayout {
                spacing: 3
                Label { text: "PROJECT ALTAIR / SOFTWARE RECRUITMENT"; color: "#dcb372"; font.pixelSize: 10; font.letterSpacing: 2 }
                Label { text: "Yeah, Science."; color: "#e8eff1"; font.pixelSize: 34; font.bold: true }
            }
            Item { Layout.fillWidth: true }
            ColumnLayout {
                spacing: 5
                Label { text: station.connected ? "CONNECTED" : "DISCONNECTED"; color: station.connected ? "#82cbb2" : "#94a9b7"; font.pixelSize: 12; font.bold: true }
                Label { text: station.endpoint; color: "#94a9b7"; font.family: "monospace"; font.pixelSize: 11 }
            }
            Button { objectName: "connectButton"; text: station.connected ? "Disconnect" : "Connect"; onClicked: station.connected ? station.disconnectLink() : station.connectLink() }
            Button { text: "Session notes"; onClicked: settings.open() }
        }
        RowLayout {
            spacing: 12
            Metric { Layout.fillWidth: true; label: "BATTERY"; value: station.telemetryData.battery.toFixed(2); unit: "V" }
            Metric { Layout.fillWidth: true; label: "HEADING"; value: (station.telemetryData.heading * 180 / Math.PI).toFixed(0); unit: "deg" }
            Metric { Layout.fillWidth: true; label: "LEFT WHEEL"; value: station.telemetryData.left.toFixed(2); unit: "m/s" }
            Metric { Layout.fillWidth: true; label: "RIGHT WHEEL"; value: station.telemetryData.right.toFixed(2); unit: "m/s" }
        }
        RowLayout {
            Layout.fillHeight: true; spacing: 16
            RoverView { Layout.fillWidth: true; Layout.fillHeight: true }
            Panel {
                Layout.preferredWidth: 306; Layout.fillHeight: true
                ColumnLayout {
                    anchors.fill: parent; anchors.margins: 20; spacing: 12
                    RowLayout {
                        Label { text: "CONTROL"; color: "#94a9b7"; font.pixelSize: 11; font.letterSpacing: 1 }
                        Item { Layout.fillWidth: true }
                        Label { text: station.armed ? "ENABLED" : "DISABLED"; color: station.armed ? "#82cbb2" : "#94a9b7"; font.pixelSize: 11 }
                    }
                    Button { objectName: "armButton"; Layout.fillWidth: true; text: station.armed ? "Disable drive" : "Enable drive"; enabled: station.connected; onClicked: station.toggleArm() }
                    DrivePad { Layout.fillWidth: true }
                    Item { Layout.fillHeight: true }
                    Label { text: "Rover watchdog: " + (station.telemetryData.failsafe ? "holding stop" : "receiving commands"); color: "#94a9b7"; font.pixelSize: 11 }
                }
            }
        }
        EventLog { Layout.fillWidth: true; Layout.preferredHeight: 148 }
        RowLayout {
            Label { text: "LOCAL TEST BENCH"; color: "#94a9b7"; font.pixelSize: 10; font.letterSpacing: 1.3 }
            Item { Layout.fillWidth: true }
            Label { text: "RX " + station.rxBytes + " B   /   TX " + station.txBytes + " B   /   rejected " + station.invalidPackets; color: "#94a9b7"; font.pixelSize: 11; font.family: "monospace" }
        }
    }
    SettingsPanel { id: settings }
}
