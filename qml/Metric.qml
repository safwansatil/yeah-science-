import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Panel {
    property string label: ""
    property string value: ""
    property string unit: ""
    property int metricIndex: 1
    implicitHeight: 102

    Column {
        anchors { left: parent.left; leftMargin: 16; top: parent.top; topMargin: 12; right: parent.right; rightMargin: 16 }
        spacing: 6

        Row {
            spacing: 6
            Label {
                text: "// 0" + metricIndex
                color: "#00e676"
                font.pixelSize: 10
                font.bold: true
                font.family: Qt.platform.os === "windows" ? "Consolas" : "monospace"
            }
            Label {
                text: label
                color: "#7a8b9e"
                font.pixelSize: 10
                font.bold: true
                font.letterSpacing: 1.5
            }
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
                color: "#7a8b9e"
                font.pixelSize: 11
                font.bold: true
                anchors.bottom: parent.bottom
                bottomPadding: 4
            }
        }

        // 8-Segment LED Bar Visualizer
        Row {
            spacing: 3
            Repeater {
                model: 10
                Rectangle {
                    width: 14; height: 3; radius: 1
                    color: index < 6 ? "#00e676" : (index < 8 ? "#f3c623" : "#202d3d")
                    opacity: index < 7 ? 0.9 : 0.3
                }
            }
        }
    }
}
