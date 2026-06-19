package io.retrodroid.emulatorbridge

import android.app.Activity
import android.os.Bundle
import android.os.Environment
import android.util.Log
import io.retrodroid.emulatorbridge.bridge.BridgeDebugLogger
import io.retrodroid.emulatorbridge.bridge.BridgeRequest
import io.retrodroid.emulatorbridge.bridge.BridgeResult
import io.retrodroid.emulatorbridge.bridge.EmulatorRegistry
import io.retrodroid.emulatorbridge.bridge.IntentDebug

class MainActivity : Activity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        BridgeDebugLogger.log(this, IntentDebug.summarize(intent))
        BridgeDebugLogger.log(this, listOf("All files access: ${Environment.isExternalStorageManager()}"))

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
                BridgeDebugLogger.log(this, listOf(result.message, result.detail.orEmpty()))
                Log.i(TAG, "${result.message} ${result.detail.orEmpty()}".trim())
            }

            is BridgeResult.Failure -> {
                BridgeDebugLogger.log(this, listOf(result.message, result.detail.orEmpty()))
                Log.e(TAG, "${result.message} ${result.detail.orEmpty()}".trim())
            }
        }

        finish()
    }

    private companion object {
        const val TAG = "EmulatorBridge"
    }
}
