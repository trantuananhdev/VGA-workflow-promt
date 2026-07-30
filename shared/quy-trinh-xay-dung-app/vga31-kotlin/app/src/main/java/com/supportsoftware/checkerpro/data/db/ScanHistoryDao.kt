package com.supportsoftware.checkerpro.data.db

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.Query
import kotlinx.coroutines.flow.Flow

@Dao
interface ScanHistoryDao {

    @Insert
    suspend fun insert(history: ScanHistory): Long

    @Query("SELECT * FROM scan_history ORDER BY date DESC")
    fun observeAll(): Flow<List<ScanHistory>>

    @Query("SELECT * FROM scan_history ORDER BY date DESC LIMIT :limit OFFSET :offset")
    suspend fun page(limit: Int, offset: Int): List<ScanHistory>

    @Query("DELETE FROM scan_history")
    suspend fun deleteAll()
}
