package com.supportsoftware.checkerpro.data.db

import androidx.room.Database
import androidx.room.RoomDatabase

@Database(
    entities = [ScanHistory::class],
    version = 1,
    exportSchema = false,
)
abstract class AppDatabase : RoomDatabase() {
    abstract fun scanHistoryDao(): ScanHistoryDao
}
