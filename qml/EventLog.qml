import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Panel {
    ColumnLayout {
        anchors.fill: parent; anchors.margins: 14; spacing: 6
        RowLayout {
            Label { text: "EVENT CONSOLE"; color: "#94a9b7"; font.pixelSize: 11; font.letterSpacing: 1 }
            Item { Layout.fillWidth: true }
            Button { text: "Clear"; flat: true; onClicked: station.clearEvents() }
        }
        ListView {
            id: lines
            Layout.fillWidth: true; Layout.fillHeight: true
            clip: true; model: station.eventLines; spacing: 5
            onCountChanged: positionViewAtEnd()
            ScrollBar.vertical: ScrollBar {}
            delegate: Label {
                required property string modelData
                width: lines.width - 14
                text: modelData; textFormat: Text.PlainText
                wrapMode: Text.Wrap; color: "#c5d2d9"; font.family: "monospace"; font.pixelSize: 12
            }
        }
    }
}
