package com.supportsoftware.checkerpro.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.supportsoftware.checkerpro.ui.theme.Primary

/**
 * Header khớp RN: nền sáng (KHÔNG phải thanh gradient xanh), back đen + tiêu đề đen.
 * [centerTitle] = true (mặc định) cho màn con; false cho Home (tiêu đề canh trái, màu tuỳ [titleColor]).
 */
@Composable
fun AppHeader(
    title: String,
    onBack: (() -> Unit)? = null,
    centerTitle: Boolean = true,
    titleColor: Color = Color.Black,
    actions: @Composable () -> Unit = {},
) {
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .statusBarsPadding()
            .height(56.dp)
            .padding(horizontal = 6.dp),
    ) {
        if (onBack != null) {
            IconButton(onClick = onBack, modifier = Modifier.align(Alignment.CenterStart)) {
                Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back", tint = Color.Black)
            }
        }
        Text(
            text = title,
            color = titleColor,
            fontSize = 20.sp,
            fontWeight = FontWeight.Bold,
            maxLines = 1,
            overflow = TextOverflow.Ellipsis,
            modifier = if (centerTitle) {
                Modifier.align(Alignment.Center).padding(horizontal = 48.dp)
            } else {
                Modifier.align(Alignment.CenterStart).padding(start = 10.dp, end = 96.dp)
            },
        )
        Row(modifier = Modifier.align(Alignment.CenterEnd), verticalAlignment = Alignment.CenterVertically) {
            actions()
        }
    }
}

/** Khung màn chuẩn: header + nền trang xanh nhạt (khớp RN). */
@Composable
fun AppScreen(
    title: String? = null,
    onBack: (() -> Unit)? = null,
    actions: @Composable () -> Unit = {},
    content: @Composable (Modifier) -> Unit,
) {
    Column(Modifier.fillMaxSize().background(MaterialTheme.colorScheme.background)) {
        if (title != null) AppHeader(title, onBack, actions = actions)
        content(Modifier.fillMaxSize())
    }
}

/**
 * Tab kiểu pill (khớp RN): chọn = nền xanh chữ trắng; chưa chọn = nền trắng viền xanh chữ xanh.
 */
@Composable
fun PillTabs(
    options: List<String>,
    selected: Int,
    onSelect: (Int) -> Unit,
    modifier: Modifier = Modifier,
) {
    Row(
        modifier = modifier.fillMaxWidth().padding(horizontal = 12.dp, vertical = 10.dp),
        horizontalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        options.forEachIndexed { i, label ->
            val sel = i == selected
            Box(
                modifier = Modifier
                    .weight(1f)
                    .height(46.dp)
                    .clip(RoundedCornerShape(24.dp))
                    .background(if (sel) Primary else Color.White)
                    .border(1.5.dp, Primary, RoundedCornerShape(24.dp))
                    .clickable { onSelect(i) },
                contentAlignment = Alignment.Center,
            ) {
                Text(
                    label,
                    color = if (sel) Color.White else Primary,
                    fontWeight = FontWeight.SemiBold,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                )
            }
        }
    }
}

/** Placeholder khi màn chưa làm xong. */
@Composable
fun ComingSoon(name: String, onBack: (() -> Unit)? = null) {
    AppScreen(title = name, onBack = onBack) { m ->
        Box(m, contentAlignment = Alignment.Center) {
            Column(horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.Center) {
                Text(name, fontSize = 20.sp, fontWeight = FontWeight.Bold)
                Text("Đang xây dựng", color = Color.Gray)
            }
        }
    }
}
