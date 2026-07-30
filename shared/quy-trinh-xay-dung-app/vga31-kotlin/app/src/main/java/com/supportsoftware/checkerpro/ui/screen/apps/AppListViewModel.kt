package com.supportsoftware.checkerpro.ui.screen.apps

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.supportsoftware.checkerpro.data.model.AppInfo
import com.supportsoftware.checkerpro.data.repo.AppInventoryRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

data class AppListState(
    val loading: Boolean = true,
    val apps: List<AppInfo> = emptyList(),
)

/** ViewModel chung cho UserApp / SystemApp / ManagerApp. */
@HiltViewModel
class AppListViewModel @Inject constructor(
    private val repo: AppInventoryRepository,
) : ViewModel() {

    private val _user = MutableStateFlow(AppListState())
    val user: StateFlow<AppListState> = _user.asStateFlow()

    private val _system = MutableStateFlow(AppListState())
    val system: StateFlow<AppListState> = _system.asStateFlow()

    fun loadUser() {
        if (_user.value.apps.isNotEmpty()) return
        viewModelScope.launch {
            _user.value = AppListState(loading = true)
            _user.value = AppListState(loading = false, apps = repo.getInstalledApps(systemApps = false))
        }
    }

    fun loadSystem() {
        if (_system.value.apps.isNotEmpty()) return
        viewModelScope.launch {
            _system.value = AppListState(loading = true)
            _system.value = AppListState(loading = false, apps = repo.getInstalledApps(systemApps = true))
        }
    }
}
