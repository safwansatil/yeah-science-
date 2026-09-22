import QtQuick
import QtQuick.Controls

Panel {
    id: field
    property var readings: station.telemetryData
    clip: true
    Canvas {
        id: grid
        anchors.fill: parent
        onWidthChanged: requestPaint()
        onHeightChanged: requestPaint()
        onPaint: {
            var ctx = getContext("2d")
            ctx.clearRect(0, 0, width, height)
            ctx.strokeStyle = "#263640"; ctx.lineWidth = 1
            for (var x = width / 2 % 36; x < width; x += 36) {
                ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, height); ctx.stroke()
            }
            for (var y = height / 2 % 36; y < height; y += 36) {
                ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(width, y); ctx.stroke()
            }
            ctx.strokeStyle = "#486171"
            ctx.beginPath(); ctx.moveTo(width/2, 0); ctx.lineTo(width/2, height); ctx.stroke()
            ctx.beginPath(); ctx.moveTo(0, height/2); ctx.lineTo(width, height/2); ctx.stroke()
        }
    }
    Label {
        anchors { top: parent.top; left: parent.left; margins: 16 }
        text: "FIELD VIEW / RECEIVED TELEMETRY"; color: "#94a9b7"; font.pixelSize: 11; font.letterSpacing: 1
    }
    Item {
        id: rover
        width: 48; height: 36
        x: field.width / 2 + field.readings.x * 36 - width / 2
        y: field.height / 2 - field.readings.y * 36 - height / 2
        rotation: -field.readings.heading * 180 / Math.PI
        Rectangle { anchors.centerIn: parent; width: 34; height: 24; radius: 5; color: "#dfb574" }
        Repeater {
            model: 4
            Rectangle {
                width: 13; height: 7; radius: 2; color: "#9eafb8"
                x: index % 2 === 0 ? 4 : 29
                y: index < 2 ? 0 : 29
            }
        }
        Rectangle { x: 34; y: 14; width: 14; height: 7; radius: 2; color: "#fff0d5" }
    }
    Label {
        anchors { bottom: parent.bottom; left: parent.left; margins: 16 }
        text: "1 square = 1 metre   |   +X right / +Y up"
        color: "#94a9b7"; font.pixelSize: 11
    }
    Label {
        anchors { bottom: parent.bottom; right: parent.right; margins: 16 }
        text: "SIMULATION"; color: "#dcb372"; font.pixelSize: 11
    }
}
