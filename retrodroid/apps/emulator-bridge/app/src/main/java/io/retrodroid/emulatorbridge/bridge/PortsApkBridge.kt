package io.retrodroid.emulatorbridge.bridge

import android.app.Activity
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import androidx.core.content.FileProvider
import java.io.File
import java.io.FileOutputStream
import java.util.zip.ZipInputStream

object PortsApkBridge {
    const val KEY = "ports-apk"
    const val REQUEST_INSTALL_PACKAGE = 1001
    private const val FILE_PROVIDER_AUTHORITY = "io.retrodroid.emulatorbridge.fileprovider"

    fun handle(activity: Activity, request: BridgeRequest): BridgeResult {
        val romUri = request.romUri
            ?: return BridgeResult.Failure("Ports bridge received no package URI.")

        val stagedPackage = runCatching { stagePackage(activity, request, romUri) }.getOrElse { error ->
            return BridgeResult.Failure(
                message = "Ports bridge could not stage the package for inspection.",
                detail = error.message,
            )
        }

        val packageName = readPackageName(activity.packageManager, stagedPackage.apkFile)
            ?: return BridgeResult.Failure("Ports bridge could not read the package name.")

        if (isInstalled(activity.packageManager, packageName)) {
            return launchInstalledPackage(activity, packageName)
        }

        val installIntent = Intent(Intent.ACTION_INSTALL_PACKAGE).apply {
            setDataAndType(stagedPackage.installUri, "application/vnd.android.package-archive")
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            putExtra(Intent.EXTRA_RETURN_RESULT, true)
        }

        activity.startActivityForResult(installIntent, REQUEST_INSTALL_PACKAGE)
        return BridgeResult.Pending(
            message = "Started package install flow.",
            detail = packageName,
            packageName = packageName,
        )
    }

    fun launchInstalledPackage(activity: Activity, packageName: String): BridgeResult {
        val launchIntent = activity.packageManager.getLaunchIntentForPackage(packageName)
            ?: return BridgeResult.Failure(
                message = "Installed package has no launchable activity.",
                detail = packageName,
            )

        activity.startActivity(
            launchIntent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_RESET_TASK_IF_NEEDED),
        )

        return BridgeResult.Success(
            message = "Launched installed package.",
            detail = packageName,
        )
    }

    private fun isInstalled(packageManager: PackageManager, packageName: String): Boolean {
        return runCatching {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                packageManager.getPackageInfo(packageName, PackageManager.PackageInfoFlags.of(0))
            } else {
                @Suppress("DEPRECATION")
                packageManager.getPackageInfo(packageName, 0)
            }
        }.isSuccess
    }

    private fun readPackageName(packageManager: PackageManager, apkFile: File): String? {
        val packageInfo = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            packageManager.getPackageArchiveInfo(
                apkFile.absolutePath,
                PackageManager.PackageInfoFlags.of(PackageManager.GET_ACTIVITIES.toLong()),
            )
        } else {
            @Suppress("DEPRECATION")
            packageManager.getPackageArchiveInfo(apkFile.absolutePath, PackageManager.GET_ACTIVITIES)
        }

        return packageInfo?.packageName
    }

    private fun stagePackage(activity: Activity, request: BridgeRequest, romUri: Uri): StagedPortsPackage {
        val fileNameHint = sequenceOf(
            request.romPathHint,
            romUri.lastPathSegment,
        ).filterNotNull().firstOrNull().orEmpty().lowercase()

        return if (fileNameHint.endsWith(".xapk")) {
            stageXapk(activity, romUri)
        } else {
            val apkFile = cacheApk(activity, romUri)
            StagedPortsPackage(
                apkFile = apkFile,
                installUri = romUri,
            )
        }
    }

    private fun cacheApk(activity: Activity, romUri: Uri): File {
        val target = File(activity.cacheDir, "ports-launch.apk")
        activity.contentResolver.openInputStream(romUri).use { input ->
            requireNotNull(input) { "Could not open package URI: $romUri" }
            target.outputStream().use { output -> input.copyTo(output) }
        }
        return target
    }

    private fun stageXapk(activity: Activity, romUri: Uri): StagedPortsPackage {
        val apkTarget = File(activity.cacheDir, "ports-launch-from-xapk.apk")
        apkTarget.delete()

        var foundApk = false
        activity.contentResolver.openInputStream(romUri).use { input ->
            requireNotNull(input) { "Could not open XAPK URI: $romUri" }
            ZipInputStream(input).use { zip ->
                generateSequence { zip.nextEntry }.forEach { entry ->
                    if (entry.isDirectory) {
                        zip.closeEntry()
                        return@forEach
                    }

                    when {
                        entry.name.endsWith(".apk", ignoreCase = true) && !foundApk -> {
                            FileOutputStream(apkTarget).use { output -> zip.copyTo(output) }
                            foundApk = true
                        }

                        entry.name.startsWith("Android/", ignoreCase = true) -> {
                            copyZipEntryToExternalStorage(zip, entry.name)
                        }
                    }

                    zip.closeEntry()
                }
            }
        }

        require(foundApk) { "No APK file found inside the XAPK." }
        val installUri = FileProvider.getUriForFile(activity, FILE_PROVIDER_AUTHORITY, apkTarget)
        return StagedPortsPackage(
            apkFile = apkTarget,
            installUri = installUri,
        )
    }

    private fun copyZipEntryToExternalStorage(zip: ZipInputStream, entryName: String) {
        val relativePath = entryName.removePrefix("/")
        val target = File("/sdcard", relativePath)
        target.parentFile?.mkdirs()
        FileOutputStream(target).use { output -> zip.copyTo(output) }
    }

    private data class StagedPortsPackage(
        val apkFile: File,
        val installUri: Uri,
    )
}
