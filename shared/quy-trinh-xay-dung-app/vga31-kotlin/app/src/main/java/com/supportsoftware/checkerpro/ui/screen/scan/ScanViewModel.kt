package com.supportsoftware.checkerpro.ui.screen.scan

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.supportsoftware.checkerpro.data.db.ScanHistory
import com.supportsoftware.checkerpro.data.db.ScanHistoryDao
import com.supportsoftware.checkerpro.data.model.VersionCheckResult
import com.supportsoftware.checkerpro.data.repo.AppInventoryRepository
import com.supportsoftware.checkerpro.data.repo.ScanResultStore
import com.supportsoftware.checkerpro.data.repo.VersionCheckRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

data class ScanState(
    val scanning: Boolean = false,
    val scanned: Int = 0,
    val total: Int = 0,
    val updates: List<VersionCheckResult> = emptyList(),
    val done: Boolean = false,
) {
    val progress: Float get() = if (total == 0) 0f else scanned.toFloat() / total
}

@HiltViewModel
class ScanViewModel @Inject constructor(
    private val inventory: AppInventoryRepository,
    private val versionCheck: VersionCheckRepository,
    private val historyDao: ScanHistoryDao,
    private val store: ScanResultStore,
) : ViewModel() {

    private val _state = MutableStateFlow(ScanState())
    val state: StateFlow<ScanState> = _state.asStateFlow()

    fun startScan() {
        if (_state.value.scanning) return
        viewModelScope.launch {
            val apps = inventory.getInstalledApps(systemApps = false)
            _state.value = ScanState(scanning = true, total = apps.size)
            val updates = ArrayList<VersionCheckResult>()
            apps.forEachIndexed { index, app ->
                val result = versionCheck.check(app.packageName, app.versionName)
                if (result.needsUpdate) updates.add(result)
                _state.value = _state.value.copy(scanned = index + 1, updates = updates.toList())
            }
            // Lưu lịch sử + chia sẻ kết quả cho UpdateAvailable.
            historyDao.insert(
                ScanHistory(
                    date = System.currentTimeMillis(),
                    installedCount = apps.size,
                    updateCount = updates.size,
                )
            )
            store.lastUpdates = updates.toList()
            _state.value = _state.value.copy(scanning = false, done = true)
        }
    }
}
