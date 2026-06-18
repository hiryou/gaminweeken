package io.retrodroid.emulatorbridge.bridge

sealed interface BridgeResult {
    val message: String
    val detail: String?

    data class Success(
        override val message: String,
        override val detail: String? = null,
    ) : BridgeResult

    data class Failure(
        override val message: String,
        override val detail: String? = null,
    ) : BridgeResult
}
