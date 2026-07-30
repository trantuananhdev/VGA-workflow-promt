package com.supportsoftware.checkerpro.data.repo

import com.supportsoftware.checkerpro.data.model.VersionCheckResult
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.jsoup.Jsoup
import android.content.Context
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Thay `react-native-check-version` (JS) — kiểm tra version mới trên Play Store bằng jsoup
 * (jsoup đã được base-application AAR bundle).
 *
 * ⚠️ Rủi ro: HTML Play Store hay đổi/obfuscate. Dùng nhiều regex fallback + luôn try/catch;
 * khi không lấy được storeVersion → needsUpdate=false (không chặn chức năng).
 */
@Singleton
class VersionCheckRepository @Inject constructor(
    @ApplicationContext private val context: Context,
) {
    private val userAgent =
        "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 (KHTML, like Gecko) " +
            "Chrome/120.0.0.0 Mobile Safari/537.36"

    // Các pattern version đã gặp trong HTML Play Store (mới → cũ).
    private val patterns = listOf(
        Regex("""\[\[\["([\d][\d.]*)"]]"""),                       // layout JSON mới
        Regex("""Current Version.*?>([\d][\d.]*)<""", RegexOption.DOT_MATCHES_ALL),
        Regex(""">([\d]+\.[\d.]+)<\s*/\s*span>""", RegexOption.DOT_MATCHES_ALL),
    )

    fun storeUrl(packageName: String): String =
        "https://play.google.com/store/apps/details?id=$packageName&hl=en&gl=US"

    /** Lấy version trên store; null nếu fail. */
    suspend fun fetchStoreVersion(packageName: String): String? = withContext(Dispatchers.IO) {
        runCatching {
            val html = Jsoup.connect(storeUrl(packageName))
                .userAgent(userAgent)
                .timeout(15_000)
                .ignoreHttpErrors(true)
                .ignoreContentType(true)
                .execute()
                .body()
            patterns.firstNotNullOfOrNull { it.find(html)?.groupValues?.getOrNull(1) }
                ?.takeIf { it.isNotBlank() && it.first().isDigit() }
        }.getOrNull()
    }

    /** So sánh version cài đặt vs store. */
    suspend fun check(packageName: String, currentVersion: String?): VersionCheckResult {
        val store = fetchStoreVersion(packageName)
        val needs = store != null && currentVersion != null &&
            compareVersions(store, currentVersion) > 0
        return VersionCheckResult(
            packageName = packageName,
            currentVersion = currentVersion,
            storeVersion = store,
            needsUpdate = needs,
            storeUrl = storeUrl(packageName),
        )
    }

    /** So sánh chuỗi version dạng "1.2.3". >0 nếu a>b. Phần không phải số → bỏ qua. */
    private fun compareVersions(a: String, b: String): Int {
        val pa = a.split(".").mapNotNull { it.trim().toIntOrNull() }
        val pb = b.split(".").mapNotNull { it.trim().toIntOrNull() }
        val n = maxOf(pa.size, pb.size)
        for (i in 0 until n) {
            val x = pa.getOrElse(i) { 0 }
            val y = pb.getOrElse(i) { 0 }
            if (x != y) return x - y
        }
        return 0
    }
}
