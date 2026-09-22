import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Panel {
    ColumnLayout {
        anchors.fill: parent; anchors.margins: 12; spacing: 6
        RowLayout {
            spacing: 6
            Rectangle {
                width: 3; height: 10; color: "#00e676"; radius: 1
            }
            Label {
                text: "SYSTEM & LINK EVENT CONSOLE"
                color: "#8a99ad"
                font.pixelSize: 10
                font.bold: true
                font.letterSpacing: 1.2
            }
            Item { Layout.fillWidth: true }
            Button {
                text: "Clear Console"
                font.pixelSize: 11
                onClicked: station.clearEvents()
            }
        }
        Rectangle {
            Layout.fillWidth: true; Layout.fillHeight: true
            color: "#0a0e13"
            radius: 4
            border.color: "#182029"
            ListView {
                id: lines
                anchors.fill: parent; anchors.margins: 8
                clip: true; model: station.eventLines; spacing: 4
                onCountChanged: positionViewAtEnd()
                ScrollBar.vertical: ScrollBar {}
                delegate: Label {
                    required property string modelData
                    width: lines.width - 14
                    text: modelData
                    textFormat: Text.PlainText
                    wrapMode: Text.Wrap
                    color: "#00e676"
                    font.family: Qt.platform.os === "windows" ? "Consolas" : "monospace"
                    font.pixelSize: 11
                }
            }
        }
    }
}
