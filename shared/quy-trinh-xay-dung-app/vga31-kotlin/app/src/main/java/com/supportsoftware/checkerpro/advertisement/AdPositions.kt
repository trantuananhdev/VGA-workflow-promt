package com.supportsoftware.checkerpro.advertisement

import com.supportsoftware.checkerpro.firebase.Remote
import com.brian.base_iap.utils.IAPUtils
import org.json.JSONArray

/**
 * positionIntrol (Intro) — port kịch bản RN vga31b: mảng các BIẾN THỂ, mỗi biến thể là danh sách vị trí.
 * Chọn NGẪU NHIÊN 1 biến thể (A/B như RN). Quy ước:
 *   - số N  (1..4)      → native INLINE dưới slide N.
 *   - số NN (11/22/33/44) → native MODAL toàn màn khi RỜI slide N.
 * Premium → rỗng (không ads).
 */
object AdPositions {

    private const val DEFAULT = "[[1,22,3,4],[1,2,33,4],[1,2,3,4]]"

    fun selected(): List<Int> {
        if (IAPUtils.isPremium()) return emptyList()
        val raw = runCatching { Remote.instance.getString("positionIntrol") }.getOrNull()
            .let { if (it.isNullOrBlank()) DEFAULT else it }
        return parsePositions(raw)
    }

    private fun parsePositions(raw: String): List<Int> = try {
        val arr = JSONArray(raw)
        if (arr.length() == 0) emptyList()
        else {
            val chosen = if (arr.opt(0) is JSONArray) arr.getJSONArray((0 until arr.length()).random()) else arr
            (0 until chosen.length()).map { chosen.getInt(it) }
        }
    } catch (e: Exception) { emptyList() }
}
