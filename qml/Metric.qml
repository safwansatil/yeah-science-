import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Panel {
    property string label: ""
    property string value: ""
    property string unit: ""
    implicitHeight: 96

    Rectangle {
        width: 3; height: parent.height - 24
        anchors { left: parent.left; top: parent.top; margins: 12 }
        color: "#00e676"
        radius: 1
    }

    Column {
        anchors { left: parent.left; leftMargin: 24; top: parent.top; topMargin: 14 }
        spacing: 6
        Label {
            text: label
            color: "#8a99ad"
            font.pixelSize: 10
            font.bold: true
            font.letterSpacing: 1.5
        }
        Row {
            spacing: 6
            Label {
                text: value
                color: "#f3c623"
                font.pixelSize: 26
                font.bold: true
                font.family: Qt.platform.os === "windows" ? "Consolas" : "monospace"
            }
            Label {
                text: unit
                color: "#8a99ad"
                font.pixelSize: 11
                font.bold: true
                anchors.bottom: parent.bottom
                bottomPadding: 4
            }
        }
    }
}
