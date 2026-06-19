package io.retrodroid.emulatorbridge.handlers

import android.content.Context
import io.retrodroid.emulatorbridge.ps3.Ps3IsoInspector
import io.retrodroid.emulatorbridge.bridge.BridgeRequest
import io.retrodroid.emulatorbridge.bridge.BridgeResult
import io.retrodroid.emulatorbridge.bridge.EmulatorHandler

class RpcsxHandler : EmulatorHandler {

    override val key: String = "rpcsx"

    override fun handle(context: Context, request: BridgeRequest): BridgeResult {
        if (request.romUri == null && request.romPathHint.isNullOrBlank()) {
            return BridgeResult.Failure("RPCSX bridge received neither a ROM URI nor a ROM path hint.")
        }

        val isoInfo = runCatching { Ps3IsoInspector.inspect(context, request.romUri, request.romPathHint) }.getOrElse { error ->
            return BridgeResult.Failure(
                message = "RPCSX bridge could not inspect the selected ISO.",
                detail = error.stackTraceToString(),
            )
        }

        return BridgeResult.Success(
            message = "RPCSX bridge debug stage complete.",
            detail = buildString {
                appendLine("Incoming ROM URI: ${request.romUri ?: "<none>"}")
                appendLine("Incoming ROM path hint: ${request.romPathHint ?: "<none>"}")
                appendLine("Parsed TITLE_ID: ${isoInfo.titleId ?: "<missing>"}")
                appendLine("Parsed TITLE: ${isoInfo.title ?: "<missing>"}")
                appendLine()
                appendLine("ISO inspection details:")
                isoInfo.debugLines.forEach { appendLine(it) }
            },
        )
    }
}
