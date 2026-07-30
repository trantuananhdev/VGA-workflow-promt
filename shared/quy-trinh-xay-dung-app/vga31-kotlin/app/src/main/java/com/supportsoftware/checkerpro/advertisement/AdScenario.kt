package com.supportsoftware.checkerpro.advertisement

import android.content.Context
import android.content.SharedPreferences
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

/**
 * Port kịch bản hiển thị ad của RN (hàm cb7c1696):
 *  - showCount % ratio == 0  → đủ điều kiện hiện (TỈ LỆ xuất hiện).
 *  - showCountAd >= maxPerDay → chặn (SỐ LẦN tối đa/ngày).
 *  - Đếm theo ngày + type trong SharedPreferences (reset theo ngày qua khoá chứa date).
 *
 * [noCount] = true: chỉ kiểm tra, không tăng bộ đếm.
 */
object AdScenario {

    private const val PREFS = "ad_scenario"
    private val dateFmt = SimpleDateFormat("yyyy-MM-dd", Locale.US)
    private val DATE_RE = Regex("""\d{4}-\d{2}-\d{2}""")

    fun shouldShow(
        context: Context,
        type: String,
        ratio: Int,
        maxPerDay: Int,
        noCount: Boolean = false,
    ): Boolean {
        val p = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
        val today = dateFmt.format(Date())
        cleanupOld(p, today)   // dọn key đếm cũ >7 ngày (port AdFrequencyManager 23b)
        val showKey = "ad_show_count_${today}_$type"      // tổng số lần "cơ hội" trong ngày
        val showKeyAd = "ad_show_countad_${today}_$type"   // số lần ĐÃ hiện ad trong ngày

        var showCount = p.getInt(showKey, 0)
        var showCountAd = p.getInt(showKeyAd, 0)

        val r = if (ratio <= 0) 1 else ratio
        var check = showCount % r == 0
        if (showCountAd >= maxPerDay) check = false

        if (!noCount) {
            showCount++
            val e = p.edit().putInt(showKey, showCount)
            if (check) {
                showCountAd++
                e.putInt(showKeyAd, showCountAd)
            }
            e.apply()
        }
        return check
    }

    /** Xoá key đếm cũ hơn 7 ngày (tránh SharedPreferences phình vô hạn theo ngày). */
    private fun cleanupOld(prefs: SharedPreferences, today: String) {
        try {
            val todayMs = dateFmt.parse(today)?.time ?: return
            val e = prefs.edit()
            var removed = false
            for (key in prefs.all.keys) {
                if (!key.startsWith("ad_show_count")) continue
                val datePart = DATE_RE.find(key)?.value ?: continue
                val ms = try { dateFmt.parse(datePart)?.time } catch (ex: Exception) { null } ?: continue
                if ((todayMs - ms) / 86_400_000L > 7) { e.remove(key); removed = true }
            }
            if (removed) e.apply()
        } catch (ex: Exception) { /* bỏ qua */ }
    }
}
