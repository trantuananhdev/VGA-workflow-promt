package com.supportsoftware.checkerpro.ui.screen.settings

import android.content.Intent
import android.net.Uri
import androidx.compose.foundation.Image
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.fragment.app.FragmentActivity
import com.supportsoftware.checkerpro.R
import com.supportsoftware.checkerpro.core.IapOpener
import com.supportsoftware.checkerpro.core.MainActivity
import com.supportsoftware.checkerpro.ui.components.AppScreen
import com.supportsoftware.checkerpro.ui.components.findActivity
import com.brian.base_application.language.LanguageActivity

private const val PRIVACY_URL = "https://sites.google.com/view/vrenterprisellp/policy"

private data class SettingItem(@androidx.annotation.DrawableRes val iconRes: Int, val title: String, val onClick: () -> Unit)

@Composable
fun SettingScreen(onBack: () -> Unit) {
    val context = LocalContext.current

    val items = listOf(
        SettingItem(R.drawable.crown, stringResource(R.string.PremiumPackage)) { IapOpener.open(context, "settings") },
        // Đổi ngôn ngữ dùng LUÔN màn Language của lib AAR; chọn xong lib áp locale + về Home.
        SettingItem(R.drawable.ic_language, stringResource(R.string.lang)) {
            (context.findActivity() as? FragmentActivity)?.let {
                LanguageActivity.start(it, MainActivity::class.java)
            }
        },
        SettingItem(R.drawable.ic_rate, stringResource(R.string.rateApp)) {
            val pkg = context.packageName
            runCatching {
                context.startActivity(
                    Intent(Intent.ACTION_VIEW, Uri.parse("market://details?id=$pkg"))
                        .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                )
            }.onFailure {
                context.startActivity(
                    Intent(Intent.ACTION_VIEW, Uri.parse("https://play.google.com/store/apps/details?id=$pkg"))
                        .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                )
            }
        },
        SettingItem(R.drawable.ic_share, stringResource(R.string.share_app)) {
            val pkg = context.packageName
            val send = Intent(Intent.ACTION_SEND).apply {
                type = "text/plain"
                putExtra(
                    Intent.EXTRA_TEXT,
                    "Check out this app: https://play.google.com/store/apps/details?id=$pkg",
                )
            }
            runCatching { context.startActivity(Intent.createChooser(send, "Share").addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)) }
        },
        SettingItem(R.drawable.ic_policy, stringResource(R.string.privacyPolicy)) {
            runCatching {
                context.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(PRIVACY_URL)).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
            }
        },
    )

    AppScreen(title = stringResource(R.string.setting), onBack = onBack) { m ->
        LazyColumn(m.fillMaxSize()) {
            items(items) { item ->
                Row(
                    Modifier.fillMaxWidth().clickable { item.onClick() }.padding(20.dp, 16.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Image(painterResource(item.iconRes), item.title, Modifier.size(24.dp))
                    Text(item.title, Modifier.padding(start = 16.dp), fontWeight = FontWeight.Medium)
                }
                HorizontalDivider(thickness = 0.5.dp, color = Color(0x14000000))
            }
        }
    }
}

private data class Lang(val code: String, val name: String)

private val languages = listOf(
    Lang("en-US", "English"),
    Lang("de-DE", "Deutsch"),
    Lang("es-ES", "Español"),
    Lang("ar-SA", "العربية"),
    Lang("fr-FR", "Français"),
    Lang("hi-IN", "हिन्दी"),
    Lang("id-ID", "Indonesia"),
    Lang("it-IT", "Italiano"),
    Lang("ja-JP", "日本語"),
    Lang("ko-KR", "한국어"),
    Lang("vi-VN", "Tiếng Việt"),
    Lang("zh-CN", "中文"),
    Lang("pt-PT", "Português"),
    Lang("ru-RU", "Русский"),
    Lang("th-TH", "ไทย"),
    Lang("km-KH", "ខ្មែរ"),
)

@Composable
fun LanguageSettingScreen(onBack: () -> Unit) {
    val context = LocalContext.current
    AppScreen(title = "Language", onBack = onBack) { m ->
        LazyColumn(m.fillMaxSize()) {
            items(languages, key = { it.code }) { lang ->
                Row(
                    Modifier.fillMaxWidth().clickable {
                        val activity = context.findActivity()
                        if (activity != null) {
                            // Báo lib + áp locale, KHÔNG để lib tự chuyển màn (spec §8.2.2).
                            com.brian.base_application.language.LanguageRouter
                                .confirmLanguageSelection(activity, lang.code, navigate = false)
                            activity.recreate()
                        }
                    }.padding(20.dp, 16.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Text(lang.name, Modifier.weight(1f), fontWeight = FontWeight.Medium)
                }
                HorizontalDivider(thickness = 0.5.dp, color = Color(0x14000000))
            }
        }
    }
}
