package io.retrodroid.emulatorbridge.ps3

import android.content.Context
import android.net.Uri
import java.io.FileInputStream
import java.io.RandomAccessFile
import java.nio.channels.FileChannel
import java.nio.ByteBuffer
import java.nio.ByteOrder

data class Ps3IsoInfo(
    val titleId: String?,
    val title: String?,
    val debugLines: List<String>,
)

object Ps3IsoInspector {
    private const val SectorSize = 2048
    private val paramSfoPath = listOf("PS3_GAME", "PARAM.SFO")

    fun inspect(context: Context, uri: Uri?, pathHint: String?): Ps3IsoInfo {
        val lines = mutableListOf<String>()
        lines += "ISO uri: ${uri ?: "<none>"}"
        lines += "ISO path hint: ${pathHint ?: "<none>"}"

        val scheme = uri?.scheme?.lowercase()
        if (scheme == "file") {
            val filePath = uri.path
            if (!filePath.isNullOrBlank()) {
                lines += "Inspecting via file:// URI path."
                return inspectFilePath(filePath, lines)
            }
        }

        if (!pathHint.isNullOrBlank()) {
            lines += "Inspecting via rom_path_hint."
            return inspectFilePath(pathHint, lines)
        }

        requireNotNull(uri) { "No readable ISO source provided." }
        context.contentResolver.openFileDescriptor(uri, "r")?.use { pfd ->
            FileInputStream(pfd.fileDescriptor).channel.use { channel ->
                lines += "Inspecting via ContentResolver.openFileDescriptor."
                return inspectChannel(channel, lines)
            }
        }

        return Ps3IsoInfo(titleId = null, title = null, debugLines = lines + "Could not open ISO uri for reading.")
    }

    private fun inspectFilePath(path: String, seedLines: MutableList<String>): Ps3IsoInfo {
        RandomAccessFile(path, "r").channel.use { channel ->
            val lines = seedLines.toMutableList()
            lines += "Resolved file path: $path"
            return inspectChannel(channel, lines)
        }
    }

    private fun inspectChannel(channel: FileChannel, seedLines: MutableList<String>): Ps3IsoInfo {
        val lines = seedLines.toMutableList()
        lines += "ISO size bytes: ${channel.size()}"

        val primaryVolume = readPrimaryVolumeDescriptor(channel)
        lines += "Primary volume descriptor found."

        val root = parseDirectoryRecord(sliceBuffer(primaryVolume, 156, primaryVolume.size - 156))
        lines += "Root extent: lba=${root.extentLba}, size=${root.dataLength}"

        val paramRecord = findPath(channel, root, paramSfoPath, lines)
            ?: return Ps3IsoInfo(
                titleId = null,
                title = null,
                debugLines = lines + "Could not locate PS3_GAME/PARAM.SFO inside ISO.",
            )

        lines += "Found PARAM.SFO extent: lba=${paramRecord.extentLba}, size=${paramRecord.dataLength}"
        val paramBytes = readExtent(channel, paramRecord.extentLba, paramRecord.dataLength)
        val sfo = parseParamSfo(paramBytes)
        lines += "PARAM.SFO keys parsed: ${sfo.keys.sorted().joinToString()}"

        return Ps3IsoInfo(
            titleId = sfo["TITLE_ID"],
            title = sfo["TITLE"],
            debugLines = lines + listOf(
                "Parsed TITLE_ID: ${sfo["TITLE_ID"] ?: "<missing>"}",
                "Parsed TITLE: ${sfo["TITLE"] ?: "<missing>"}",
            ),
        )
    }

    private fun readPrimaryVolumeDescriptor(channel: java.nio.channels.FileChannel): ByteArray {
        val buffer = ByteBuffer.allocate(SectorSize)
        channel.position(16L * SectorSize)
        channel.read(buffer)
        val data = buffer.array()
        require(data[0].toInt() == 1) { "Primary volume descriptor missing at sector 16." }
        require(String(data, 1, 5) == "CD001") { "Unexpected ISO identifier in primary volume descriptor." }
        return data
    }

    private fun findPath(
        channel: java.nio.channels.FileChannel,
        root: DirectoryRecord,
        segments: List<String>,
        lines: MutableList<String>,
    ): DirectoryRecord? {
        var current = root
        for ((index, segment) in segments.withIndex()) {
            val children = readDirectory(channel, current)
            val next = children.firstOrNull { it.normalizedName.equals(segment, ignoreCase = true) }
            lines += "Lookup `${segment}` -> ${next?.normalizedName ?: "<missing>"}"
            if (next == null) {
                return null
            }
            if (index < segments.lastIndex && !next.isDirectory) {
                lines += "Path segment `${segment}` is not a directory."
                return null
            }
            current = next
        }
        return current
    }

    private fun readDirectory(
        channel: java.nio.channels.FileChannel,
        record: DirectoryRecord,
    ): List<DirectoryRecord> {
        val bytes = readExtent(channel, record.extentLba, record.dataLength)
        val children = mutableListOf<DirectoryRecord>()
        var offset = 0
        while (offset < bytes.size) {
            val length = bytes[offset].toInt() and 0xFF
            if (length == 0) {
                offset = ((offset / SectorSize) + 1) * SectorSize
                continue
            }
            val slice = sliceBuffer(bytes, offset, length)
            val child = parseDirectoryRecord(slice)
            if (child.normalizedName != "." && child.normalizedName != "..") {
                children += child
            }
            offset += length
        }
        return children
    }

    private fun readExtent(
        channel: java.nio.channels.FileChannel,
        extentLba: Int,
        dataLength: Int,
    ): ByteArray {
        val buffer = ByteBuffer.allocate(dataLength)
        channel.position(extentLba.toLong() * SectorSize)
        channel.read(buffer)
        return buffer.array()
    }

    private fun parseDirectoryRecord(buffer: ByteBuffer): DirectoryRecord {
        buffer.order(ByteOrder.LITTLE_ENDIAN)
        val recordLength = buffer.get(0).toInt() and 0xFF
        require(recordLength > 0) { "Empty directory record." }
        val extentLba = buffer.getInt(2)
        val dataLength = buffer.getInt(10)
        val flags = buffer.get(25).toInt() and 0xFF
        val fileIdLength = buffer.get(32).toInt() and 0xFF
        val nameBytes = ByteArray(fileIdLength)
        for (index in 0 until fileIdLength) {
            nameBytes[index] = buffer.get(33 + index)
        }
        val rawName = when {
            fileIdLength == 1 && nameBytes[0].toInt() == 0 -> "."
            fileIdLength == 1 && nameBytes[0].toInt() == 1 -> ".."
            else -> String(nameBytes)
        }
        val normalizedName = rawName.substringBefore(';')
        return DirectoryRecord(
            extentLba = extentLba,
            dataLength = dataLength,
            isDirectory = (flags and 0x02) != 0,
            normalizedName = normalizedName,
        )
    }

    private fun parseParamSfo(bytes: ByteArray): Map<String, String> {
        val buffer = ByteBuffer.wrap(bytes).order(ByteOrder.LITTLE_ENDIAN)
        val magic = buffer.int
        require(magic == 0x46535000) { "PARAM.SFO magic mismatch." }
        buffer.int
        val keyTableStart = buffer.int
        val dataTableStart = buffer.int
        val entryCount = buffer.int

        val result = linkedMapOf<String, String>()
        for (index in 0 until entryCount) {
            val entryOffset = 20 + (index * 16)
            val keyOffset = littleShort(bytes, entryOffset)
            val dataFormat = littleShort(bytes, entryOffset + 2)
            val dataLength = littleInt(bytes, entryOffset + 4)
            val dataOffset = littleInt(bytes, entryOffset + 12)
            val key = readCString(bytes, keyTableStart + keyOffset)
            if (dataFormat == 0x0204 || dataFormat == 0x0004) {
                val valueBytes = bytes.copyOfRange(dataTableStart + dataOffset, dataTableStart + dataOffset + dataLength)
                result[key] = valueBytes.toString(Charsets.UTF_8).trimEnd('\u0000')
            }
        }
        return result
    }

    private fun littleShort(bytes: ByteArray, offset: Int): Int {
        return (bytes[offset].toInt() and 0xFF) or ((bytes[offset + 1].toInt() and 0xFF) shl 8)
    }

    private fun sliceBuffer(bytes: ByteArray, offset: Int, length: Int): ByteBuffer {
        val buffer = ByteBuffer.wrap(bytes)
        buffer.position(offset)
        buffer.limit(offset + length)
        return buffer.slice()
    }

    private fun littleInt(bytes: ByteArray, offset: Int): Int {
        return (bytes[offset].toInt() and 0xFF) or
            ((bytes[offset + 1].toInt() and 0xFF) shl 8) or
            ((bytes[offset + 2].toInt() and 0xFF) shl 16) or
            ((bytes[offset + 3].toInt() and 0xFF) shl 24)
    }

    private fun readCString(bytes: ByteArray, offset: Int): String {
        var end = offset
        while (end < bytes.size && bytes[end] != 0.toByte()) {
            end += 1
        }
        return String(bytes, offset, end - offset, Charsets.UTF_8)
    }

    private data class DirectoryRecord(
        val extentLba: Int,
        val dataLength: Int,
        val isDirectory: Boolean,
        val normalizedName: String,
    )
}
