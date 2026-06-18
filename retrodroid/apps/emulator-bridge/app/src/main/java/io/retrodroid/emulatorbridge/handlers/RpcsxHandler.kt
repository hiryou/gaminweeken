package io.retrodroid.emulatorbridge.handlers

import android.content.Context
import io.retrodroid.emulatorbridge.bridge.BridgeRequest
import io.retrodroid.emulatorbridge.bridge.BridgeResult
import io.retrodroid.emulatorbridge.bridge.EmulatorHandler

class RpcsxHandler : EmulatorHandler {

    override val key: String = "rpcsx"

    override fun handle(context: Context, request: BridgeRequest): BridgeResult {
        return BridgeResult.Success(
            message = "RPCSX bridge scaffold reached.",
            detail = buildString {
                appendLine("Next implementation steps:")
                appendLine("- resolve the PS3 serial from the selected ISO")
                appendLine("- map it to the imported RPCSX game directory")
                appendLine("- launch net.rpcsx/.RPCSXActivity with the expected extras")
                appendLine()
                append("Incoming ROM URI: ${request.romUri}")
            },
        )
    }
}
