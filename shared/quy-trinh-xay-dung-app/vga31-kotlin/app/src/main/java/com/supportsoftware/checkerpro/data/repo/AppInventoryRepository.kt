package com.supportsoftware.checkerpro.data.repo

import android.app.AppOpsManager
import android.app.usage.UsageEvents
import android.app.usage.UsageStatsManager
import android.content.Context
import android.content.Intent
import android.content.pm.ApplicationInfo
import android.content.pm.PackageInfo
import android.content.pm.PackageManager
import android.graphics.drawable.Drawable
import android.net.Uri
import android.os.Build
import android.os.Process
import android.provider.Settings
import com.supportsoftware.checkerpro.data.model.AppInfo
import com.supportsoftware.checkerpro.data.model.AppPermissions
import com.supportsoftware.checkerpro.data.model.UsageInfo
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.File
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Port Kotlin của native module `software-update-module` (PackageManager / UsageStatsManager / AppOps).
 *
 * Khác bản RN:
 *  - KHÔNG base64 icon — dùng [getAppIcon] load Drawable lazy ở UI.
 *  - Tác vụ cần Activity (uninstall / mở Settings) trả Intent để màn tự launch qua ActivityResultLauncher.
 */
@Singleton
class AppInventoryRepository @Inject constructor(
    @ApplicationContext private val context: Context,
) {
    private val pm: PackageManager get() = context.packageManager

    // ---------------------------------------------------------------------
    // Danh sách app
    // ---------------------------------------------------------------------

    /** Tất cả app đã cài. [systemApps] = null: tất cả; true: chỉ system; false: chỉ user. */
    suspend fun getInstalledApps(systemApps: Boolean? = null): List<AppInfo> =
        withContext(Dispatchers.IO) {
            val packages = pm.getInstalledPackages(0)
            packages.mapNotNull { info ->
                val appInfo = info.applicationInfo ?: return@mapNotNull null
                // Khớp RN getInstalledApps: phân loại system bằng cờ FLAG_SYSTEM đơn giản
                // (KHÔNG dùng logic FLAG_UPDATED_SYSTEM_APP), để danh sách User/System trùng bản cũ.
                val isSystem = isSystemSimple(appInfo)
                if (systemApps != null && systemApps != isSystem) return@mapNotNull null
                AppInfo(
                    packageName = info.packageName,
                    appName = runCatching { appInfo.loadLabel(pm).toString().trim() }
                        .getOrDefault(info.packageName),
                    isSystemApp = isSystem,
                    versionName = info.versionName,
                    versionCode = packageInfoVersionCode(info),
                    firstInstallTime = info.firstInstallTime,
                    lastUpdateTime = info.lastUpdateTime,
                    apkDir = appInfo.publicSourceDir,
                    sizeBytes = runCatching { File(appInfo.publicSourceDir).length() }.getOrDefault(0L),
                )
            }.sortedBy { it.appName.lowercase() }
        }

    /** Thông tin 1 app theo packageName (null nếu không cài). */
    suspend fun getAppInfo(packageName: String): AppInfo? = withContext(Dispatchers.IO) {
        val info = runCatching { pm.getPackageInfo(packageName, 0) }.getOrNull() ?: return@withContext null
        val appInfo = info.applicationInfo ?: return@withContext null
        AppInfo(
            packageName = info.packageName,
            appName = runCatching { appInfo.loadLabel(pm).toString().trim() }.getOrDefault(packageName),
            isSystemApp = isSystemSimple(appInfo),
            versionName = info.versionName,
            versionCode = packageInfoVersionCode(info),
            firstInstallTime = info.firstInstallTime,
            lastUpdateTime = info.lastUpdateTime,
            apkDir = appInfo.publicSourceDir,
            sizeBytes = runCatching { File(appInfo.publicSourceDir).length() }.getOrDefault(0L),
        )
    }

    /** Icon của 1 app (load lazy, không cache — UI nên cache theo item hiển thị). */
    fun getAppIcon(packageName: String): Drawable? =
        runCatching { pm.getApplicationIcon(packageName) }.getOrNull()

    fun packageExists(packageName: String): Boolean =
        runCatching { pm.getApplicationInfo(packageName, 0); true }.getOrDefault(false)

    // ---------------------------------------------------------------------
    // Quyền của app
    // ---------------------------------------------------------------------

    suspend fun getAppPermissions(packageName: String): AppPermissions =
        withContext(Dispatchers.IO) {
            val pkg = pm.getPackageInfo(packageName, PackageManager.GET_PERMISSIONS)
            val requested = pkg.requestedPermissions ?: return@withContext AppPermissions(emptyList(), emptyList())
            val granted = ArrayList<String>()
            val denied = ArrayList<String>()
            requested.forEach { perm ->
                val isGranted = pm.checkPermission(perm, packageName) == PackageManager.PERMISSION_GRANTED
                if (isGranted) granted.add(perm) else denied.add(perm)
            }
            AppPermissions(granted, denied)
        }

    // ---------------------------------------------------------------------
    // Usage stats (thuật toán pairing E0/E1 — port nguyên bản RN)
    // ---------------------------------------------------------------------

    /** Thống kê dùng của tất cả user-app trong [startTime, endTime]. */
    suspend fun getUsageStatistics(startTime: Long, endTime: Long): List<UsageInfo> =
        withContext(Dispatchers.IO) {
            val usm = context.getSystemService(Context.USAGE_STATS_SERVICE) as? UsageStatsManager
                ?: return@withContext emptyList()
            val grouped = HashMap<String, MutableList<UsageEvents.Event>>()
            val events = usm.queryEvents(startTime, endTime)
            while (events.hasNextEvent()) {
                val e = UsageEvents.Event()
                events.getNextEvent(e)
                if (e.eventType == UsageEvents.Event.ACTIVITY_RESUMED ||
                    e.eventType == UsageEvents.Event.ACTIVITY_PAUSED
                ) {
                    grouped.getOrPut(e.packageName) { ArrayList() }.add(e)
                }
            }
            grouped.entries.mapNotNull { (pkg, evs) ->
                val (time, launches) = aggregate(evs, startTime, endTime)
                val appInfo = runCatching { pm.getApplicationInfo(pkg, 0) }.getOrNull()
                    ?: return@mapNotNull null
                if (isSystemPackage(appInfo)) return@mapNotNull null
                UsageInfo(pkg, appInfo.loadLabel(pm).toString().trim(), time, launches)
            }
        }

    /** Thống kê dùng của 1 package cụ thể trong [startTime, endTime]. */
    suspend fun getUsageStatisticsByPackageName(
        packageName: String,
        startTime: Long,
        endTime: Long,
    ): UsageInfo? = withContext(Dispatchers.IO) {
        val usm = context.getSystemService(Context.USAGE_STATS_SERVICE) as? UsageStatsManager
            ?: return@withContext null
        val evs = ArrayList<UsageEvents.Event>()
        val events = usm.queryEvents(startTime, endTime)
        while (events.hasNextEvent()) {
            val e = UsageEvents.Event()
            events.getNextEvent(e)
            if ((e.eventType == UsageEvents.Event.ACTIVITY_RESUMED ||
                    e.eventType == UsageEvents.Event.ACTIVITY_PAUSED) &&
                e.packageName == packageName
            ) {
                evs.add(e)
            }
        }
        if (evs.isEmpty()) return@withContext null
        val (time, launches) = aggregate(evs, startTime, endTime)
        val appInfo = runCatching { pm.getApplicationInfo(packageName, 0) }.getOrNull()
            ?: return@withContext null
        UsageInfo(packageName, appInfo.loadLabel(pm).toString().trim(), time, launches)
    }

    /** Trả (totalTimeInForeground, launchCount) từ chuỗi event RESUMED/PAUSED đã sắp xếp. */
    private fun aggregate(
        evs: List<UsageEvents.Event>,
        startTime: Long,
        endTime: Long,
    ): Pair<Long, Int> {
        var time = 0L
        var launches = 0
        val total = evs.size
        for (i in 0 until total - 1) {
            val e0 = evs[i]
            val e1 = evs[i + 1]
            if (e1.eventType == UsageEvents.Event.ACTIVITY_RESUMED ||
                e0.eventType == UsageEvents.Event.ACTIVITY_RESUMED
            ) {
                launches++
            }
            if (e0.eventType == UsageEvents.Event.ACTIVITY_RESUMED &&
                e1.eventType == UsageEvents.Event.ACTIVITY_PAUSED
            ) {
                time += e1.timeStamp - e0.timeStamp
            }
        }
        if (evs.first().eventType == UsageEvents.Event.ACTIVITY_PAUSED) {
            time += evs.first().timeStamp - startTime
        }
        if (evs.last().eventType == UsageEvents.Event.ACTIVITY_RESUMED) {
            time += endTime - evs.last().timeStamp
        }
        return time to launches
    }

    // ---------------------------------------------------------------------
    // Quyền usage-stats
    // ---------------------------------------------------------------------

    fun hasUsageStatsPermission(): Boolean = runCatching {
        val appOps = context.getSystemService(Context.APP_OPS_SERVICE) as AppOpsManager
        val mode = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            appOps.unsafeCheckOpNoThrow(
                AppOpsManager.OPSTR_GET_USAGE_STATS, Process.myUid(), context.packageName
            )
        } else {
            @Suppress("DEPRECATION")
            appOps.checkOpNoThrow(
                AppOpsManager.OPSTR_GET_USAGE_STATS, Process.myUid(), context.packageName
            )
        }
        if (mode == AppOpsManager.MODE_DEFAULT) {
            context.checkCallingOrSelfPermission(android.Manifest.permission.PACKAGE_USAGE_STATS) ==
                PackageManager.PERMISSION_GRANTED
        } else {
            mode == AppOpsManager.MODE_ALLOWED
        }
    }.getOrDefault(false)

    // ---------------------------------------------------------------------
    // Tác vụ cần Activity → trả Intent để màn launch
    // ---------------------------------------------------------------------

    /** Mở app khác. Dùng applicationContext (đã thêm FLAG_ACTIVITY_NEW_TASK). */
    fun openApp(packageName: String): Boolean {
        val intent = pm.getLaunchIntentForPackage(packageName) ?: return false
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        return runCatching { context.startActivity(intent); true }.getOrDefault(false)
    }

    fun buildUninstallIntent(packageName: String): Intent =
        Intent(Intent.ACTION_DELETE, Uri.parse("package:$packageName"))

    fun buildUsageAccessSettingsIntent(): Intent =
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            Intent(Settings.ACTION_USAGE_ACCESS_SETTINGS, Uri.parse("package:${context.packageName}"))
        } else {
            Intent(Settings.ACTION_USAGE_ACCESS_SETTINGS)
        }

    fun buildSystemUpdateIntent(): Intent = Intent("android.settings.SYSTEM_UPDATE_SETTINGS")

    // ---------------------------------------------------------------------
    // Helpers
    // ---------------------------------------------------------------------

    /** Phân loại system đơn giản — KHỚP RN getInstalledApps (chỉ xét FLAG_SYSTEM). */
    private fun isSystemSimple(info: ApplicationInfo): Boolean =
        info.flags and ApplicationInfo.FLAG_SYSTEM != 0

    /** Phân loại system nhiều tầng — dùng cho lọc usage stats (khớp RN getUsageStatistics). */
    private fun isSystemPackage(info: ApplicationInfo): Boolean = when {
        info.flags and ApplicationInfo.FLAG_UPDATED_SYSTEM_APP != 0 -> false
        info.flags and ApplicationInfo.FLAG_SYSTEM != 0 -> true
        info.flags and ApplicationInfo.FLAG_INSTALLED != 0 -> false
        else -> true
    }

    @Suppress("DEPRECATION")
    private fun packageInfoVersionCode(info: PackageInfo): Long =
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) info.longVersionCode
        else info.versionCode.toLong()
}
