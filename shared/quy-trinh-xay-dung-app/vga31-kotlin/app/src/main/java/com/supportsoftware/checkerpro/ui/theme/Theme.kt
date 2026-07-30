package com.supportsoftware.checkerpro.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Typography
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

// Palette khớp app RN vga31b (styles/COLOR.js): THEME=#007BFF, THEME_SECOND=#00C9FF, BG=#F4F6F8
val Primary = Color(0xFF007BFF)          // THEME
val PrimaryDark = Color(0xFF0064D6)
val Secondary = Color(0xFF00C9FF)        // THEME_SECOND (vòng progress Scan, accent phụ)
val OnPrimary = Color(0xFFFFFFFF)
val BgLight = Color(0xFFF4F6F8)          // BG
val BgDark = Color(0xFF101418)
val TextPrimary = Color(0xFF212121)      // BLACK

private val LightColors = lightColorScheme(
    primary = Primary,
    onPrimary = OnPrimary,
    secondary = PrimaryDark,
    background = BgLight,
    surface = Color.White,
    onBackground = TextPrimary,
    onSurface = TextPrimary,
)

private val DarkColors = darkColorScheme(
    primary = Primary,
    onPrimary = OnPrimary,
    secondary = PrimaryDark,
    background = BgDark,
    surface = Color(0xFF1A1F24),
)

@Composable
fun AppTheme(
    // RN app KHÔNG có chế độ tối — ép nền sáng cố định, không theo dark mode hệ thống
    // (windowBackground native (themes.xml) không có bản night nên luôn trắng; nếu Compose
    // tự đổi theo isSystemInDarkTheme() thì onBackground/onSurface đổi sang tông sáng trong
    // khi nền thật vẫn trắng → chữ/icon xám, gần như không đọc được ở chế độ tối).
    darkTheme: Boolean = false,
    content: @Composable () -> Unit,
) {
    MaterialTheme(
        colorScheme = if (darkTheme) DarkColors else LightColors,
        typography = Typography(),
        content = content,
    )
}
