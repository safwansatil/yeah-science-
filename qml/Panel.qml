import QtQuick
import QtQuick.Controls

Rectangle {
    id: panelRect
    color: "#0f151d"
    radius: 4
    border.color: "#1f2c3a"
    border.width: 1

    // Top-left technical accent bar
    Rectangle {
        width: 16; height: 2
        color: "#00e676"
        anchors { left: parent.left; top: parent.top; leftMargin: 8; topMargin: -1 }
    }

    // Bottom-right technical accent bar
    Rectangle {
        width: 16; height: 2
        color: "#f3c623"
        anchors { right: parent.right; bottom: parent.bottom; rightMargin: 8; bottomMargin: -1 }
    }
}
