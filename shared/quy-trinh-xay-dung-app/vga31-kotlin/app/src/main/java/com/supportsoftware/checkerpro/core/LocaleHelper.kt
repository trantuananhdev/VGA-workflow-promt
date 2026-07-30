package com.supportsoftware.checkerpro.core

import android.app.LocaleManager
import android.content.Context
import android.os.Build
import android.os.LocaleList
import androidx.appcompat.app.AppCompatDelegate
import androidx.core.os.LocaleListCompat

/**
 * Áp per-app locale — mirror vga_48 (uti/LocaleHelper.kt).
 * API 33+ (TIRAMISU): LocaleManager.applicationLocales; cũ hơn: AppCompatDelegate.setApplicationLocales.
 */
object LocaleHelper {
    fun updateLocale(context: Context, languageCode: String) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            context.getSystemService(LocaleManager::class.java).applicationLocales =
                LocaleList.forLanguageTags(languageCode)
        } else {
            AppCompatDelegate.setApplicationLocales(LocaleListCompat.forLanguageTags(languageCode))
        }
    }
}
