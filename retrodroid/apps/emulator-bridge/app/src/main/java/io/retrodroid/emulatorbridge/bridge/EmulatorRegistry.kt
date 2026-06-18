package io.retrodroid.emulatorbridge.bridge

import io.retrodroid.emulatorbridge.handlers.RpcsxHandler
import io.retrodroid.emulatorbridge.handlers.Vita3kHandler

object EmulatorRegistry {
    private val handlers: List<EmulatorHandler> = listOf(
        RpcsxHandler(),
        Vita3kHandler(),
    )

    fun find(key: String): EmulatorHandler? = handlers.firstOrNull { it.key == key }
}
