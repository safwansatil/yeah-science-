import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: root
    width: 1180; height: 860
    minimumWidth: 1020; minimumHeight: 820
    visible: true; color: "#0b0e14"
    title: "Yeah, Science | Project Altair Ground Control"
    palette.button: "#1a232e"
    palette.buttonText: "#e2e8f0"
    palette.highlight: "#f3c623"
    palette.text: "#e2e8f0"
    palette.base: "#121820"
    font.family: "Segoe UI"
    onActiveChanged: if (!active) station.stop()

    ColumnLayout {
        anchors.fill: parent; anchors.margins: 20; spacing: 14
        RowLayout {
            spacing: 12
            RowLayout {
                spacing: 6
                // Periodic Table Element Badge: Y (Yttrium 39)
                Rectangle {
                    width: 38; height: 38; radius: 4
                    color: "#16202c"
                    border.color: "#f3c623"; border.width: 1.5
                    Column {
                        anchors.centerIn: parent; spacing: -2
                        Label { text: "39"; color: "#f3c623"; font.pixelSize: 8; font.bold: true; anchors.horizontalCenter: parent.horizontalCenter }
                        Label { text: "Y"; color: "#f3c623"; font.pixelSize: 18; font.bold: true; anchors.horizontalCenter: parent.horizontalCenter }
                    }
                }
                // Periodic Table Element Badge: Se (Selenium 34)
                Rectangle {
                    width: 38; height: 38; radius: 4
                    color: "#16202c"
                    border.color: "#00e676"; border.width: 1.5
                    Column {
                        anchors.centerIn: parent; spacing: -2
                        Label { text: "34"; color: "#00e676"; font.pixelSize: 8; font.bold: true; anchors.horizontalCenter: parent.horizontalCenter }
                        Label { text: "Se"; color: "#00e676"; font.pixelSize: 18; font.bold: true; anchors.horizontalCenter: parent.horizontalCenter }
                    }
                }
            }

            ColumnLayout {
                spacing: 1
                Label { text: "PROJECT ALTAIR // GROUND CONTROL UNIT"; color: "#8a99ad"; font.pixelSize: 10; font.bold: true; font.letterSpacing: 2 }
                Label { text: "Yeah, Science."; color: "#f3c623"; font.pixelSize: 28; font.bold: true }
            }

            Item { Layout.fillWidth: true }

            RowLayout {
                spacing: 8
                Rectangle {
                    width: 10; height: 10; radius: 5
                    color: station.connected ? "#00e676" : "#4a5568"
                    Layout.alignment: Qt.AlignVCenter
                }
                ColumnLayout {
                    spacing: 2
                    Label { text: station.connected ? "CONNECTED" : "DISCONNECTED"; color: station.connected ? "#00e676" : "#8a99ad"; font.pixelSize: 12; font.bold: true }
                    Label { text: station.endpoint; color: "#566b82"; font.family: Qt.platform.os === "windows" ? "Consolas" : "monospace"; font.pixelSize: 11 }
                }
            }

            Button {
                objectName: "connectButton"
                text: station.connected ? "Disconnect" : "Connect Link"
                onClicked: station.connected ? station.disconnectLink() : station.connectLink()
            }
            Button { text: "Session Notes"; onClicked: settings.open() }
        }

        RowLayout {
            spacing: 12
            Metric { Layout.fillWidth: true; label: "BATTERY"; value: station.telemetryData.battery.toFixed(2); unit: "V" }
            Metric { Layout.fillWidth: true; label: "HEADING"; value: (station.telemetryData.heading * 180 / Math.PI).toFixed(0); unit: "deg" }
            Metric { Layout.fillWidth: true; label: "LEFT WHEEL"; value: station.telemetryData.left.toFixed(2); unit: "m/s" }
            Metric { Layout.fillWidth: true; label: "RIGHT WHEEL"; value: station.telemetryData.right.toFixed(2); unit: "m/s" }
        }

        RowLayout {
            Layout.fillHeight: true; spacing: 14
            RoverView { Layout.fillWidth: true; Layout.fillHeight: true }
            Panel {
                Layout.preferredWidth: 320; Layout.fillHeight: true
                ColumnLayout {
                    anchors.fill: parent; anchors.margins: 16; spacing: 10
                    RowLayout {
                        Label { text: "DRIVE SYSTEM"; color: "#8a99ad"; font.pixelSize: 11; font.bold: true; font.letterSpacing: 1 }
                        Item { Layout.fillWidth: true }
                        Rectangle {
                            width: 72; height: 20; radius: 3
                            color: station.armed ? "#102e1f" : "#241818"
                            border.color: station.armed ? "#00e676" : "#e63946"
                            Label {
                                anchors.centerIn: parent
                                text: station.armed ? "ARMED" : "DISARMED"
                                color: station.armed ? "#00e676" : "#e63946"
                                font.pixelSize: 9; font.bold: true
                            }
                        }
                    }
                    Button {
                        objectName: "armButton"
                        Layout.fillWidth: true
                        text: station.armed ? "Disable Drive" : "Enable Drive"
                        enabled: station.connected
                        onClicked: station.toggleArm()
                    }
                    DrivePad { Layout.fillWidth: true }
                    Item { Layout.fillHeight: true }
                    Label {
                        text: "Watchdog: " + (station.telemetryData.failsafe ? "holding stop" : "receiving commands")
                        color: "#566b82"
                        font.pixelSize: 11
                        font.bold: true
                    }
                }
            }
        }

        EventLog { Layout.fillWidth: true; Layout.preferredHeight: 128 }

        RowLayout {
            Label { text: "LOCAL TEST BENCH // LOOPBACK UDP"; color: "#566b82"; font.pixelSize: 10; font.bold: true; font.letterSpacing: 1.2 }
            Item { Layout.fillWidth: true }
            Label {
                text: "RX " + station.rxBytes + " B  |  TX " + station.txBytes + " B  |  REJECTED " + station.invalidPackets
                color: "#8a99ad"
                font.pixelSize: 11
                font.family: Qt.platform.os === "windows" ? "Consolas" : "monospace"
            }
        }
    }

    SettingsPanel { id: settings }
}
