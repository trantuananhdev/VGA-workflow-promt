package com.supportsoftware.checkerpro.core

import android.content.Context
import android.net.Uri
import android.util.Log
import com.android.installreferrer.api.InstallReferrerClient
import com.android.installreferrer.api.InstallReferrerStateListener
import java.net.URLDecoder

/**
 * Xác định install có phải từ chiến dịch quảng cáo không — port AppLifecycleModule.isAdsCampaign
 * (module_native/pushnotic của RN). Query InstallReferrer 1 lần rồi cache vào [AppStorage]
 * (nguồn cài không đổi). Dùng để gate màn Intro (xem MainActivity.resolveStartRoute).
 *
 * NGỮ NGHĨA GIỮ ĐÚNG BẢN RN: mọi nhánh lỗi/không xác định → coi là ads (true).
 *  - có `gclid`                          → ads
 *  - không có utm_medium / "(not set)"   → organic
 *  - utm_medium == "organic"             → organic
 *  - còn lại (cpc, banner, …)            → ads
 */
object InstallReferrerHelper {

    private const val TAG = "InstallReferrer"

    /** Cache in-memory: đọc/kết nối 1 lần cho mỗi tiến trình, các lần sau tái dùng biến này. */
    @Volatile
    private var cached: Boolean? = null

    /**
     * Nguồn cài có phải ads không — ưu tiên biến in-memory, chưa có thì đọc prefs (đã resolve từ
     * lần mở trước) rồi cache lại. KHÔNG kết nối InstallReferrer ở đây (không block).
     */
    fun isAdsCampaign(context: Context): Boolean =
        cached ?: AppStorage.isAdsCampaign(context).also { cached = it }

    /** Query bất đồng bộ + cache. Bỏ qua nếu đã resolve trước đó (chỉ kết nối 1 lần trong đời app). */
    fun resolve(context: Context) {
        if (AppStorage.isAdsCampaignResolved(context)) {
            cached = AppStorage.isAdsCampaign(context)   // hâm nóng in-memory từ giá trị đã lưu
            return
        }
        val app = context.applicationContext
        val client = InstallReferrerClient.newBuilder(app).build()
        try {
            client.startConnection(object : InstallReferrerStateListener {
                override fun onInstallReferrerSetupFinished(responseCode: Int) {
                    val isAds = try {
                        if (responseCode == InstallReferrerClient.InstallReferrerResponse.OK) {
                            val raw = runCatching { client.installReferrer.installReferrer }
                                .getOrNull().orEmpty()
                            Log.d(TAG, "rawRef='$raw'")
                            decideIsAds(raw)
                        } else {
                            Log.d(TAG, "non-OK response=$responseCode → ads")
                            true
                        }
                    } catch (e: Exception) {
                        Log.e(TAG, "isAdsCampaign error", e)
                        true
                    }
                    Log.d(TAG, "isAds decision=$isAds")
                    cached = isAds
                    AppStorage.setAdsCampaign(app, isAds)
                    runCatching { client.endConnection() }
                }

                override fun onInstallReferrerServiceDisconnected() {
                    Log.w(TAG, "service disconnected → ads")
                    cached = true
                    AppStorage.setAdsCampaign(app, true)
                }
            })
        } catch (e: Exception) {
            Log.e(TAG, "startConnection failed → ads", e)
            cached = true
            AppStorage.setAdsCampaign(app, true)
        }
    }

    private fun decideIsAds(rawRef: String): Boolean {
        val decoded = try { URLDecoder.decode(rawRef, "UTF-8") } catch (e: Exception) { rawRef }
        val uri = try { Uri.parse("https://dummy?$decoded") } catch (e: Exception) { Uri.EMPTY }
        val gclid = uri.getQueryParameter("gclid")
        val utmMedium = uri.getQueryParameter("utm_medium")?.lowercase()
        return when {
            !gclid.isNullOrEmpty() -> true                                  // có gclid → chắc chắn ads
            utmMedium.isNullOrEmpty() || utmMedium == "(not set)" -> false  // không có medium → organic
            utmMedium == "organic" -> false                                 // organic
            else -> true                                                    // cpc/banner/… → ads
        }
    }
}
