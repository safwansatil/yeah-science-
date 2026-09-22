import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ColumnLayout {
    spacing: 8

    RowLayout {
        spacing: 6
        Rectangle {
            width: 3; height: 12; color: "#f3c623"; radius: 1
        }
        Label {
            text: "TELEOPERATIONS CONSOLE"
            color: "#8a99ad"
            font.letterSpacing: 1.2
            font.pixelSize: 11
            font.bold: true
        }
    }

    Label {
        text: "Hold control pad button to drive"
        color: "#e2e8f0"
        font.pixelSize: 15
        font.bold: true
    }

    GridLayout {
        columns: 3
        rowSpacing: 6; columnSpacing: 6

        Item { Layout.preferredWidth: 74 }
        Button {
            objectName: "forwardButton"
            text: "Forward [W]"
            Layout.preferredWidth: 92
            enabled: station.armed
            onPressed: station.setDrive(1, 1)
            onReleased: station.stop()
            onCanceled: station.stop()
        }
        Item { Layout.preferredWidth: 74 }

        Button {
            text: "Left [A]"
            Layout.preferredWidth: 78
            enabled: station.armed
            onPressed: station.setDrive(-1, 1)
            onReleased: station.stop()
            onCanceled: station.stop()
        }
        Button {
            text: "ESTOP"
            Layout.preferredWidth: 92
            palette.button: "#e63946"
            palette.buttonText: "#ffffff"
            onClicked: station.stop()
        }
        Button {
            text: "Right [D]"
            Layout.preferredWidth: 78
            enabled: station.armed
            onPressed: station.setDrive(1, -1)
            onReleased: station.stop()
            onCanceled: station.stop()
        }

        Item { Layout.preferredWidth: 74 }
        Button {
            text: "Reverse [S]"
            Layout.preferredWidth: 92
            enabled: station.armed
            onPressed: station.setDrive(-1, -1)
            onReleased: station.stop()
            onCanceled: station.stop()
        }
        Item { Layout.preferredWidth: 74 }
    }

    RowLayout {
        spacing: 8
        Label { text: "THROTTLE"; color: "#8a99ad"; font.pixelSize: 10; font.bold: true }
        Slider {
            Layout.fillWidth: true
            from: 0.1; to: 1.0; value: station.speed
            onMoved: station.setSpeed(value)
        }
        Label {
            text: Math.round(station.speed * 100) + "%"
            color: "#f3c623"
            font.bold: true
            font.pixelSize: 12
            font.family: Qt.platform.os === "windows" ? "Consolas" : "monospace"
        }
    }

    Rectangle {
        Layout.fillWidth: true; height: 26
        color: "#161e27"
        radius: 4
        border.color: "#212c38"
        Label {
            anchors.centerIn: parent
            text: "CMD PWM  L: " + station.leftCommand.toFixed(2) + "  |  R: " + station.rightCommand.toFixed(2)
            color: "#00e676"
            font.family: Qt.platform.os === "windows" ? "Consolas" : "monospace"
            font.pixelSize: 11
            font.bold: true
        }
    }

    Rectangle {
        Layout.fillWidth: true; height: 24
        color: "#211b10"
        radius: 3
        border.color: "#f3c623"
        border.width: 1
        Label {
            anchors.centerIn: parent
            text: "KEYBOARD TELEOP: AWAITING IMPLEMENTATION"
            color: "#f3c623"
            font.pixelSize: 10
            font.bold: true
            font.letterSpacing: 0.5
        }
    }
}
