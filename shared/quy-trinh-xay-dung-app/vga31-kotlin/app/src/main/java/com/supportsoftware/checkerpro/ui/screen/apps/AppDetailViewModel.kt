package com.supportsoftware.checkerpro.ui.screen.apps

import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.supportsoftware.checkerpro.data.model.AppInfo
import com.supportsoftware.checkerpro.data.model.AppPermissions
import com.supportsoftware.checkerpro.data.model.UsageInfo
import com.supportsoftware.checkerpro.data.model.VersionCheckResult
import com.supportsoftware.checkerpro.data.repo.AppInventoryRepository
import com.supportsoftware.checkerpro.data.repo.VersionCheckRepository
import com.supportsoftware.checkerpro.ui.nav.Screen
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import java.util.Calendar
import javax.inject.Inject

data class AppDetailState(
    val app: AppInfo? = null,
    val versionChecking: Boolean = false,
    val version: VersionCheckResult? = null,
    val permissions: AppPermissions? = null,
    val usage: UsageInfo? = null,
    val loading: Boolean = true,
)

/**
 * ViewModel chung cho DetailUserApp (version check) và DetailManagerApp (permissions + usage).
 * packageName lấy từ nav arg qua SavedStateHandle.
 */
@HiltViewModel
class AppDetailViewModel @Inject constructor(
    private val inventory: AppInventoryRepository,
    private val versionCheck: VersionCheckRepository,
    savedState: SavedStateHandle,
) : ViewModel() {

    val packageName: String = savedState.get<String>(Screen.ARG_PACKAGE).orEmpty()

    private val _state = MutableStateFlow(AppDetailState())
    val state: StateFlow<AppDetailState> = _state.asStateFlow()

    init {
        viewModelScope.launch {
            val app = inventory.getAppInfo(packageName)
            _state.value = _state.value.copy(app = app, loading = false)
        }
    }

    /** Màn DetailUserApp: kiểm tra version trên Play Store. */
    fun checkVersion() {
        val app = _state.value.app ?: return
        if (_state.value.version != null || _state.value.versionChecking) return
        viewModelScope.launch {
            _state.value = _state.value.copy(versionChecking = true)
            val result = versionCheck.check(app.packageName, app.versionName)
            _state.value = _state.value.copy(versionChecking = false, version = result)
        }
    }

    /** Màn DetailManagerApp: quyền (tab Quyền). */
    fun loadPermissions() {
        if (_state.value.permissions != null) return
        viewModelScope.launch {
            val perms = runCatching { inventory.getAppPermissions(packageName) }.getOrNull()
            _state.value = _state.value.copy(permissions = perms)
        }
    }

    fun hasUsageStats(): Boolean = inventory.hasUsageStatsPermission()

    fun usageAccessIntent() = inventory.buildUsageAccessSettingsIntent()

    /** Tab Usage: nạp thời gian dùng hôm nay (gọi khi vào tab + sau khi cấp quyền). */
    fun refreshUsage() {
        if (!inventory.hasUsageStatsPermission()) return
        viewModelScope.launch {
            val startOfDay = Calendar.getInstance().apply {
                set(Calendar.HOUR_OF_DAY, 0); set(Calendar.MINUTE, 0)
                set(Calendar.SECOND, 0); set(Calendar.MILLISECOND, 0)
            }.timeInMillis
            val usage = inventory.getUsageStatisticsByPackageName(packageName, startOfDay, System.currentTimeMillis())
            _state.value = _state.value.copy(usage = usage)
        }
    }
}
