import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Popup {
    id: settings
    objectName: "settingsPanel"
    anchors.centerIn: parent
    width: 440; height: 280
    modal: true; focus: true
    onOpened: station.stop()
    background: Panel {}
    ColumnLayout {
        anchors.fill: parent; anchors.margins: 20; spacing: 12
        Label { text: "Session notes"; color: "#e8eff1"; font.pixelSize: 22 }
        Label { text: "Leave yourself a note for this run. Typing here should never drive the rover."; color: "#94a9b7"; wrapMode: Text.Wrap; Layout.fillWidth: true }
        TextField { objectName: "noteInput"; Layout.fillWidth: true; placeholderText: "What are you testing?" }
        Label { text: "Endpoint: " + station.endpoint + "\nEdit config/local.json and restart to change ports."; color: "#94a9b7"; font.pixelSize: 12 }
        Item { Layout.fillHeight: true }
        Button { text: "Back to station"; onClicked: settings.close() }
    }
}
