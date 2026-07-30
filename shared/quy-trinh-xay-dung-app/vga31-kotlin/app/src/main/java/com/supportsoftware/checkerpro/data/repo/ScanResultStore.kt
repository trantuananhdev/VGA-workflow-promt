package com.supportsoftware.checkerpro.data.repo

import com.supportsoftware.checkerpro.data.model.VersionCheckResult
import javax.inject.Inject
import javax.inject.Singleton

/** Giữ kết quả lần quét gần nhất trong RAM để UpdateAvailable đọc lại (ScanNow → UpdateAvailable). */
@Singleton
class ScanResultStore @Inject constructor() {
    @Volatile
    var lastUpdates: List<VersionCheckResult> = emptyList()
}
