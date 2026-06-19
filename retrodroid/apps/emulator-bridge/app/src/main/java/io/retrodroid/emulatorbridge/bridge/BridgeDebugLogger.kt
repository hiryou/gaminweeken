package io.retrodroid.emulatorbridge.bridge

import android.content.Context
import android.util.Log
import java.io.File
import java.time.Instant
import java.time.ZoneOffset
import java.time.format.DateTimeFormatter

object BridgeDebugLogger {
    private const val TAG = "EmulatorBridge"
    private val timestampFormat: DateTimeFormatter =
        DateTimeFormatter.ofPattern("yyyy-MM-dd'T'HH:mm:ss.SSS'Z'").withZone(ZoneOffset.UTC)

    fun log(context: Context, lines: List<String>) {
        val timestamp = timestampFormat.format(Instant.now())
        val payload = buildString {
            appendLine("=== $timestamp ===")
            lines.forEach { appendLine(it) }
            appendLine()
        }

        Log.i(TAG, payload.trimEnd())

        val logDir = File(context.getExternalFilesDir(null), "logs")
        if (!logDir.exists()) {
            logDir.mkdirs()
        }

        File(logDir, "bridge.log").appendText(payload)
    }
}
