package com.supportsoftware.checkerpro.ui.screen.onboarding

import android.content.Intent
import androidx.lifecycle.ViewModel
import com.supportsoftware.checkerpro.data.repo.AppInventoryRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject

@HiltViewModel
class PermissionViewModel @Inject constructor(
    private val repo: AppInventoryRepository,
) : ViewModel() {
    fun hasUsageStats(): Boolean = repo.hasUsageStatsPermission()
    fun usageAccessIntent(): Intent = repo.buildUsageAccessSettingsIntent()
}
