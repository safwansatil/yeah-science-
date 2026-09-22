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

            // Grid background pattern
            ctx.strokeStyle = "#1b2430"
            ctx.lineWidth = 1
            var spacing = 36

            for (var x = (width / 2) % spacing; x < width; x += spacing) {
                ctx.beginPath()
                ctx.moveTo(x, 0)
                ctx.lineTo(x, height)
                ctx.stroke()
            }
            for (var y = (height / 2) % spacing; y < height; y += spacing) {
                ctx.beginPath()
                ctx.moveTo(0, y)
                ctx.lineTo(width, y)
                ctx.stroke()
            }

            // Tactical Center Axes & Range Rings
            ctx.strokeStyle = "#2d3c4d"
            ctx.lineWidth = 1.5
            ctx.beginPath(); ctx.moveTo(width / 2, 0); ctx.lineTo(width / 2, height); ctx.stroke()
            ctx.beginPath(); ctx.moveTo(0, height / 2); ctx.lineTo(width, height / 2); ctx.stroke()

            // Outer range ring
            ctx.strokeStyle = "#243242"
            ctx.beginPath()
            ctx.arc(width / 2, height / 2, spacing * 4, 0, 2 * Math.PI)
            ctx.stroke()

            // Compass Rose Labels
            ctx.fillStyle = "#566b82"
            ctx.font = "bold 11px Segoe UI, sans-serif"
            ctx.textAlign = "center"
            ctx.fillText("N", width / 2, 18)
            ctx.fillText("S", width / 2, height - 10)
            ctx.fillText("W", 16, height / 2 + 4)
            ctx.fillText("E", width - 16, height / 2 + 4)
        }
    }

    // Top Header Banner
    Row {
        anchors { top: parent.top; left: parent.left; margins: 14 }
        spacing: 8
        Rectangle {
            width: 8; height: 8; radius: 4
            color: "#00e676"
            anchors.verticalCenter: parent.verticalCenter
        }
        Label {
            text: "FIELD VIEW // TACTICAL TELEMETRY"
            color: "#8a99ad"
            font.pixelSize: 11
            font.bold: true
            font.letterSpacing: 1.2
        }
    }

    // Animated/Positioned Rover Asset
    Item {
        id: rover
        width: 52; height: 40
        x: field.width / 2 + field.readings.x * 36 - width / 2
        y: field.height / 2 - field.readings.y * 36 - height / 2
        rotation: -field.readings.heading * 180 / Math.PI

        // Main Chassis Base
        Rectangle {
            anchors.centerIn: parent
            width: 36; height: 26
            radius: 4
            color: "#f3c623"
            border.color: "#121820"
            border.width: 2

            // Inner Metallic Core
            Rectangle {
                anchors.centerIn: parent
                width: 22; height: 14
                radius: 2
                color: "#1a232e"
            }
        }

        // 4 Wheels / Treads
        Repeater {
            model: 4
            Rectangle {
                width: 14; height: 8; radius: 2
                color: "#2a3644"
                border.color: "#0b0e14"
                border.width: 1
                x: index % 2 === 0 ? 3 : 35
                y: index < 2 ? 0 : 32
            }
        }

        // Front Camera / Sensor Turret (Heading indicator)
        Rectangle {
            x: 36; y: 16
            width: 14; height: 8; radius: 2
            color: "#00e676"
            border.color: "#0b0e14"
            border.width: 1
        }
    }

    // Footnote Details
    Label {
        anchors { bottom: parent.bottom; left: parent.left; margins: 14 }
        text: "1 GRID SQUARE = 1.0 METER   |   ORIGIN (0,0) CENTER"
        color: "#566b82"
        font.pixelSize: 10
        font.bold: true
        font.family: Qt.platform.os === "windows" ? "Consolas" : "monospace"
    }

    Rectangle {
        anchors { bottom: parent.bottom; right: parent.right; margins: 12 }
        width: 90; height: 20
        radius: 3
        color: "#1e2936"
        border.color: "#f3c623"
        border.width: 1
        Label {
            anchors.centerIn: parent
            text: "SIMULATION"
            color: "#f3c623"
            font.pixelSize: 9
            font.bold: true
            font.letterSpacing: 1
        }
    }
}
