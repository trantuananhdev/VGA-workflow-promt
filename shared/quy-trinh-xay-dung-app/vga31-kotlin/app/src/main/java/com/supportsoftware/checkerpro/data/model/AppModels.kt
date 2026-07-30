package com.supportsoftware.checkerpro.data.model

/**
 * Thông tin 1 app đã cài (port từ software-update-module getInstalledApps/getInstalledPackages).
 * KHÔNG nhúng base64 icon như bản RN (tốn RAM) — icon load lazy qua [AppInventoryRepository.getAppIcon].
 */
data class AppInfo(
    val packageName: String,
    val appName: String,
    val isSystemApp: Boolean,
    val versionName: String?,
    val versionCode: Long,
    val firstInstallTime: Long,
    val lastUpdateTime: Long,
    val apkDir: String?,
    val sizeBytes: Long,
)

/** Thống kê sử dụng app trong khoảng thời gian (port getUsageStatistics*). */
data class UsageInfo(
    val packageName: String,
    val appName: String,
    val totalTimeInForeground: Long,
    val launchCount: Int,
)

/** Quyền của 1 app (port getAppPermissions). */
data class AppPermissions(
    val granted: List<String>,
    val denied: List<String>,
)

/** Kết quả so sánh version với Play Store (thay react-native-check-version). */
data class VersionCheckResult(
    val packageName: String,
    val currentVersion: String?,   // version đang cài
    val storeVersion: String?,     // version trên Play Store (null nếu không lấy được)
    val needsUpdate: Boolean,
    val storeUrl: String,
)
