package io.retrodroid.emulatorbridge.bridge

import android.content.Context

interface EmulatorHandler {
    val key: String

    fun handle(context: Context, request: BridgeRequest): BridgeResult
}
