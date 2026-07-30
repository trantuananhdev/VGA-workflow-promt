package com.supportsoftware.checkerpro.data.db

import androidx.room.Entity
import androidx.room.PrimaryKey

/**
 * 1 bản ghi lịch sử quét (port bảng History SQLite của RN: date, installed, updateApp).
 */
@Entity(tableName = "scan_history")
data class ScanHistory(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val date: Long,            // epoch millis lúc quét
    val installedCount: Int,   // tổng app đã quét
    val updateCount: Int,      // số app có bản cập nhật
)
