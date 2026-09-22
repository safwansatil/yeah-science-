import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ColumnLayout {
    spacing: 10
    Label { text: "MANUAL DRIVE"; color: "#94a9b7"; font.letterSpacing: 1.3; font.pixelSize: 11 }
    Label { text: "Hold a button to move"; color: "#e8eff1"; font.pixelSize: 17 }
    GridLayout {
        columns: 3
        rowSpacing: 6; columnSpacing: 6
        Item { Layout.preferredWidth: 74 }
        Button {
            objectName: "forwardButton"
            text: "Forward"; Layout.preferredWidth: 86; enabled: station.armed
            onPressed: station.setDrive(1, 1)
            onReleased: station.stop()
            onCanceled: station.stop()
        }
        Item { Layout.preferredWidth: 74 }
        Button {
            text: "Left"; Layout.preferredWidth: 74; enabled: station.armed
            onPressed: station.setDrive(-1, 1)
            onReleased: station.stop()
            onCanceled: station.stop()
        }
        Button {
            text: "STOP"; Layout.preferredWidth: 86
            onClicked: station.stop()
        }
        Button {
            text: "Right"; Layout.preferredWidth: 74; enabled: station.armed
            onPressed: station.setDrive(1, -1)
            onReleased: station.stop()
            onCanceled: station.stop()
        }
        Item { Layout.preferredWidth: 74 }
        Button {
            text: "Reverse"; Layout.preferredWidth: 86; enabled: station.armed
            onPressed: station.setDrive(-1, -1)
            onReleased: station.stop()
            onCanceled: station.stop()
        }
    }
    RowLayout {
        Label { text: "Speed"; color: "#94a9b7" }
        Slider {
            Layout.fillWidth: true; from: 0.1; to: 1; value: station.speed
            onMoved: station.setSpeed(value)
        }
        Label { text: Math.round(station.speed * 100) + "%"; color: "#e8eff1" }
    }
    Label {
        text: "Command L " + station.leftCommand.toFixed(2) + " / R " + station.rightCommand.toFixed(2)
        color: "#94a9b7"; font.family: "monospace"; font.pixelSize: 12
    }
    Label { text: "Keyboard control: awaiting implementation"; color: "#dcb372"; font.pixelSize: 11 }
}
