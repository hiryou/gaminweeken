package io.retrodroid.emulatorbridge.bridge

import android.content.Intent
import android.net.Uri

data class BridgeRequest(
    val emulatorKey: String,
    val romUri: Uri?,
    val romPathHint: String?,
) {
    companion object {
        fun fromIntent(intent: Intent): BridgeRequest? {
            val emulatorKey = intent.getStringExtra(BridgeExtras.EMULATOR)?.trim()?.lowercase()
                ?: return null

            return BridgeRequest(
                emulatorKey = emulatorKey,
                romUri = intent.data,
                romPathHint = intent.getStringExtra(BridgeExtras.ROM_PATH_HINT),
            )
        }
    }
}

object BridgeExtras {
    const val EMULATOR = "emulator"
    const val ROM_PATH_HINT = "rom_path_hint"
}
