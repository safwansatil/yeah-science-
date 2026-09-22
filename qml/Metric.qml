import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Panel {
    property string label: ""
    property string value: ""
    property string unit: ""
    implicitHeight: 96
    Column {
        anchors { left: parent.left; top: parent.top; margins: 16 }
        spacing: 8
        Label { text: label; color: "#94a9b7"; font.pixelSize: 11; font.letterSpacing: 1.3 }
        Row {
            spacing: 8
            Label { text: value; color: "#e8eff1"; font.pixelSize: 28; font.family: Qt.platform.os === "windows" ? "Consolas" : "monospace" }
            Label { text: unit; color: "#94a9b7"; anchors.bottom: parent.bottom; bottomPadding: 4 }
        }
    }
}
