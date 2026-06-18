package io.retrodroid.emulatorbridge.handlers

import android.content.Context
import io.retrodroid.emulatorbridge.bridge.BridgeRequest
import io.retrodroid.emulatorbridge.bridge.BridgeResult
import io.retrodroid.emulatorbridge.bridge.EmulatorHandler

class Vita3kHandler : EmulatorHandler {

    override val key: String = "vita3k"

    override fun handle(context: Context, request: BridgeRequest): BridgeResult {
        return BridgeResult.Success(
            message = "Vita3K bridge scaffold reached.",
            detail = "Handler stub only. No emulator-specific launch logic is implemented yet.",
        )
    }
}
