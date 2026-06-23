package io.retrodroid.emulatorbridge

import android.app.Activity
import android.content.Intent
import android.os.Bundle
import android.os.Environment
import android.util.Log
import io.retrodroid.emulatorbridge.bridge.BridgeRequest
import io.retrodroid.emulatorbridge.bridge.BridgeResult
import io.retrodroid.emulatorbridge.bridge.PortsApkBridge

class MainActivity : Activity() {
    private var pendingPackageName: String? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        logInfo("All files access: ${Environment.isExternalStorageManager()}")

        val request = BridgeRequest.fromIntent(intent)
        val result = if (request == null) {
            BridgeResult.Failure("Missing emulator bridge request.")
        } else if (request.emulatorKey != PortsApkBridge.KEY) {
            BridgeResult.Failure("Unsupported bridge key '${request.emulatorKey}'.")
        } else {
            PortsApkBridge.handle(this, request)
        }

        when (result) {
            is BridgeResult.Success -> {
                logInfo("${result.message} ${result.detail.orEmpty()}".trim())
                finish()
            }

            is BridgeResult.Failure -> {
                logError("${result.message} ${result.detail.orEmpty()}".trim())
                finish()
            }

            is BridgeResult.Pending -> {
                pendingPackageName = result.packageName
                logInfo("${result.message} ${result.detail.orEmpty()}".trim())
            }
        }
    }

    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)

        if (requestCode != PortsApkBridge.REQUEST_INSTALL_PACKAGE) {
            return
        }

        val packageName = pendingPackageName
        pendingPackageName = null

        if (resultCode != RESULT_OK || packageName.isNullOrBlank()) {
            logError("APK install was cancelled or failed.")
            finish()
            return
        }

        when (val result = PortsApkBridge.launchInstalledPackage(this, packageName)) {
            is BridgeResult.Success -> logInfo("${result.message} ${result.detail.orEmpty()}".trim())
            is BridgeResult.Failure -> logError("${result.message} ${result.detail.orEmpty()}".trim())
            is BridgeResult.Pending -> logError("Unexpected pending bridge result after install.")
        }

        finish()
    }

    private fun logInfo(message: String) {
        Log.i(TAG, message)
    }

    private fun logError(message: String) {
        Log.e(TAG, message)
    }

    private companion object {
        const val TAG = "EmulatorBridge"
    }
}
