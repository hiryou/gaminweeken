package io.retrodroid.emulatorbridge

import android.app.Activity
import android.os.Bundle
import android.util.Log
import io.retrodroid.emulatorbridge.bridge.BridgeRequest
import io.retrodroid.emulatorbridge.bridge.BridgeResult
import io.retrodroid.emulatorbridge.bridge.EmulatorRegistry

class MainActivity : Activity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val request = BridgeRequest.fromIntent(intent)
        val result = if (request == null) {
            BridgeResult.Failure("Missing emulator bridge request.")
        } else {
            val handler = EmulatorRegistry.find(request.emulatorKey)
            if (handler == null) {
                BridgeResult.Failure("No handler registered for '${request.emulatorKey}'.")
            } else {
                handler.handle(this, request)
            }
        }

        when (result) {
            is BridgeResult.Success -> {
                Log.i(TAG, "${result.message} ${result.detail.orEmpty()}".trim())
            }

            is BridgeResult.Failure -> {
                Log.e(TAG, "${result.message} ${result.detail.orEmpty()}".trim())
            }
        }

        finish()
    }

    private companion object {
        const val TAG = "EmulatorBridge"
    }
}
