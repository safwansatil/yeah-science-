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

            var spacing = 36
            var cx = width / 2
            var cy = height / 2

            // Grid background pattern
            ctx.strokeStyle = "#16202c"
            ctx.lineWidth = 1

            for (var x = cx % spacing; x < width; x += spacing) {
                ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, height); ctx.stroke()
            }
            for (var y = cy % spacing; y < height; y += spacing) {
                ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(width, y); ctx.stroke()
            }

            // Tactical Center Crosshairs
            ctx.strokeStyle = "#27374a"
            ctx.lineWidth = 1.5
            ctx.beginPath(); ctx.moveTo(cx, 0); ctx.lineTo(cx, height); ctx.stroke()
            ctx.beginPath(); ctx.moveTo(0, cy); ctx.lineTo(width, cy); ctx.stroke()

            // Tactical Range Rings (1m, 2m, 3m radius)
            ctx.strokeStyle = "#1e2c3b"
            ctx.lineWidth = 1
            ctx.setLineDash([4, 4])
            for (var r = 1; r <= 3; r++) {
                ctx.beginPath()
                ctx.arc(cx, cy, spacing * r, 0, 2 * Math.PI)
                ctx.stroke()
            }
            ctx.setLineDash([])

            // Radial Compass Degree Rosette
            ctx.fillStyle = "#00e676"
            ctx.font = "bold 9px Consolas, monospace"
            ctx.textAlign = "center"
            ctx.fillText("000° [N]", cx, 16)
            ctx.fillText("180° [S]", cx, height - 8)
            ctx.fillText("270° [W]", 24, cy + 3)
            ctx.fillText("090° [E]", width - 24, cy + 3)

            // Range Ring Labels
            ctx.fillStyle = "#485b70"
            ctx.fillText("R=1.0m", cx + spacing + 14, cy - 4)
            ctx.fillText("R=2.0m", cx + spacing * 2 + 14, cy - 4)
        }
    }

    // Top Header HUD Banner
    Row {
        anchors { top: parent.top; left: parent.left; margins: 12 }
        spacing: 8
        Rectangle {
            width: 8; height: 8; radius: 4
            color: station.telemetryFresh ? "#00e676" : (station.connectionState === "stale" ? "#e63946" : "#f3c623")
            anchors.verticalCenter: parent.verticalCenter
        }
        Label {
            text: "TACTICAL HUD // POSE VISUALIZER"
            color: "#00e676"
            font.pixelSize: 10
            font.bold: true
            font.family: Qt.platform.os === "windows" ? "Consolas" : "monospace"
            font.letterSpacing: 1.5
        }
        Label {
            text: "[C10H15N]"
            color: "#f3c623"
            font.pixelSize: 9
            font.bold: true
            font.family: Qt.platform.os === "windows" ? "Consolas" : "monospace"
        }
    }

    // Animated/Positioned Rover Asset with Reticle Corner Brackets
    Item {
        id: rover
        width: 64; height: 50
        opacity: station.telemetryFresh ? 1.0 : 0.35
        x: field.width / 2 + field.readings.x * 36 - width / 2
        y: field.height / 2 - field.readings.y * 36 - height / 2

        // Tactical Target Tracking Corner Brackets
        Rectangle { x: 0; y: 0; width: 8; height: 2; color: "#00e676" }
        Rectangle { x: 0; y: 0; width: 2; height: 8; color: "#00e676" }
        Rectangle { x: parent.width - 8; y: 0; width: 8; height: 2; color: "#00e676" }
        Rectangle { x: parent.width - 2; y: 0; width: 2; height: 8; color: "#00e676" }
        Rectangle { x: 0; y: parent.height - 2; width: 8; height: 2; color: "#00e676" }
        Rectangle { x: 0; y: parent.height - 8; width: 2; height: 8; color: "#00e676" }
        Rectangle { x: parent.width - 8; y: parent.height - 2; width: 8; height: 2; color: "#00e676" }
        Rectangle { x: parent.width - 2; y: parent.height - 8; width: 2; height: 8; color: "#00e676" }

        Item {
            anchors.centerIn: parent
            width: 48; height: 36
            rotation: -field.readings.heading * 180 / Math.PI

            // Main Chassis Base
            Rectangle {
                anchors.centerIn: parent
                width: 34; height: 24
                radius: 3
                color: "#f3c623"
                border.color: "#0f151d"
                border.width: 2

                // Inner Lab Core Accent
                Rectangle {
                    anchors.centerIn: parent
                    width: 18; height: 12
                    radius: 1
                    color: "#16202c"
                }
            }

            // 4 Tread Wheels
            Repeater {
                model: 4
                Rectangle {
                    width: 13; height: 7; radius: 1
                    color: "#283747"
                    border.color: "#0a0e13"
                    border.width: 1
                    x: index % 2 === 0 ? 3 : 32
                    y: index < 2 ? 0 : 29
                }
            }

            // Sensor Pod Turret (Heading indicator)
            Rectangle {
                x: 34; y: 14
                width: 12; height: 8; radius: 2
                color: "#00e676"
                border.color: "#0f151d"
                border.width: 1
            }
        }
    }

    // Footnote Pose Coordinates Banner
    Label {
        anchors { bottom: parent.bottom; left: parent.left; margins: 12 }
        text: station.telemetryFresh
              ? ("POSE: X=" + field.readings.x.toFixed(2) + "m  Y=" + field.readings.y.toFixed(2) + "m  HDG=" + (field.readings.heading * 180 / Math.PI).toFixed(1) + "°")
              : (station.connectionState === "stale" ? "POSE: STALE (NO RECENT TELEMETRY)" : "POSE: UNAVAILABLE (AWAITING TELEMETRY)")
        color: station.connectionState === "stale" ? "#e63946" : "#7a8b9e"
        font.pixelSize: 10
        font.bold: true
        font.family: Qt.platform.os === "windows" ? "Consolas" : "monospace"
    }

    Rectangle {
        anchors { bottom: parent.bottom; right: parent.right; margins: 10 }
        width: 100; height: 18
        radius: 2
        color: "#182330"
        border.color: "#f3c623"
        border.width: 1
        Label {
            anchors.centerIn: parent
            text: "[ SIMULATION // LOOPBACK ]"
            color: "#f3c623"
            font.pixelSize: 8
            font.bold: true
            font.family: Qt.platform.os === "windows" ? "Consolas" : "monospace"
        }
    }
}
