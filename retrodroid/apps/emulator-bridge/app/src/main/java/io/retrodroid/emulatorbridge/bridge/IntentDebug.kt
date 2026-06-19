package io.retrodroid.emulatorbridge.bridge

import android.content.Intent
import android.net.Uri
import android.os.Bundle

object IntentDebug {
    fun summarize(intent: Intent): List<String> {
        val lines = mutableListOf<String>()
        lines += "Intent action: ${intent.action}"
        lines += "Intent data: ${intent.dataString}"
        lines += "Intent type: ${intent.type}"
        lines += "Intent component: ${intent.component?.flattenToShortString()}"
        lines += "Intent flags: 0x${intent.flags.toString(16)}"
        lines += "Intent categories: ${intent.categories?.sorted()?.joinToString() ?: "<none>"}"

        val extras = intent.extras
        if (extras == null || extras.isEmpty) {
            lines += "Intent extras: <none>"
        } else {
            lines += "Intent extras:"
            lines += bundleLines(extras).map { "  $it" }
        }

        val clipData = intent.clipData
        if (clipData == null) {
            lines += "Intent clipData: <none>"
        } else {
            lines += "Intent clipData items: ${clipData.itemCount}"
            for (index in 0 until clipData.itemCount) {
                val item = clipData.getItemAt(index)
                lines += "  [$index] uri=${item.uri} text=${item.text}"
            }
        }

        return lines
    }

    private fun bundleLines(bundle: Bundle): List<String> {
        return bundle.keySet().sorted().map { key ->
            val value = bundle.get(key)
            "$key = ${formatValue(value)}"
        }
    }

    private fun formatValue(value: Any?): String {
        return when (value) {
            null -> "null"
            is Uri -> value.toString()
            is Array<*> -> value.joinToString(prefix = "[", postfix = "]") { formatValue(it) }
            is IntArray -> value.joinToString(prefix = "[", postfix = "]")
            is LongArray -> value.joinToString(prefix = "[", postfix = "]")
            is BooleanArray -> value.joinToString(prefix = "[", postfix = "]")
            is FloatArray -> value.joinToString(prefix = "[", postfix = "]")
            is DoubleArray -> value.joinToString(prefix = "[", postfix = "]")
            else -> value.toString()
        }
    }
}
