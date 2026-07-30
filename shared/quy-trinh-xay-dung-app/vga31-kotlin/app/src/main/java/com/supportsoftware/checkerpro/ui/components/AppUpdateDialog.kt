package com.supportsoftware.checkerpro.ui.components

import android.content.Intent
import android.net.Uri
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.wrapContentHeight
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.window.Dialog
import com.google.android.play.core.appupdate.AppUpdateManagerFactory
import com.google.android.play.core.install.model.UpdateAvailability

/**
 * Kiểm tra bản cập nhật CỦA CHÍNH APP (port RN expo-in-app-updates → theo cách vga_48).
 * Dùng Play Core AppUpdateManager: nếu UPDATE_AVAILABLE → hiện dialog mời cập nhật.
 * Gọi 1 lần ở màn Home.
 */
@Composable
fun CheckForAppUpdateWithDialog() {
    val context = LocalContext.current
    var showDialog by remember { mutableStateOf(false) }
    val checked = remember { mutableStateOf(false) }

    LaunchedEffect(Unit) {
        if (checked.value) return@LaunchedEffect
        runCatching {
            val manager = AppUpdateManagerFactory.create(context)
            manager.appUpdateInfo
                .addOnSuccessListener { info ->
                    if (info.updateAvailability() == UpdateAvailability.UPDATE_AVAILABLE) {
                        showDialog = true
                    }
                    checked.value = true
                }
                .addOnFailureListener { checked.value = true }
        }.onFailure { checked.value = true }
    }

    if (showDialog) {
        AppUpdateDialog(onDismiss = { showDialog = false })
    }
}

@Composable
private fun AppUpdateDialog(onDismiss: () -> Unit) {
    val context = LocalContext.current
    Dialog(onDismissRequest = onDismiss) {
        Card(
            modifier = Modifier.fillMaxWidth().wrapContentHeight(),
            shape = RoundedCornerShape(16.dp),
            colors = CardDefaults.cardColors(containerColor = Color.White),
        ) {
            Column(
                modifier = Modifier.fillMaxWidth().padding(20.dp),
                horizontalAlignment = Alignment.CenterHorizontally,
            ) {
                Text("🔄", fontSize = 56.sp)
                Spacer(Modifier.height(16.dp))
                Text(
                    "New version available",
                    fontSize = 20.sp,
                    fontWeight = FontWeight.SemiBold,
                    textAlign = TextAlign.Center,
                    color = Color.Black,
                )
                Spacer(Modifier.height(8.dp))
                Text(
                    "Please update the app to the latest version to continue.",
                    fontSize = 14.sp,
                    textAlign = TextAlign.Center,
                    color = Color.Gray,
                )
                Spacer(Modifier.height(24.dp))
                Button(
                    onClick = {
                        val pkg = context.packageName
                        runCatching {
                            context.startActivity(
                                Intent(Intent.ACTION_VIEW, Uri.parse("market://details?id=$pkg"))
                                    .setPackage("com.android.vending")
                                    .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                            )
                        }.onFailure {
                            context.startActivity(
                                Intent(Intent.ACTION_VIEW, Uri.parse("https://play.google.com/store/apps/details?id=$pkg"))
                                    .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                            )
                        }
                        onDismiss()
                    },
                    modifier = Modifier.fillMaxWidth().height(48.dp),
                    shape = RoundedCornerShape(24.dp),
                ) {
                    Text("Update now", color = Color.White, fontSize = 18.sp, fontWeight = FontWeight.Bold)
                }
                Spacer(Modifier.height(8.dp))
                Text(
                    "Maybe later",
                    fontSize = 14.sp,
                    color = Color.Black,
                    modifier = Modifier.clickable { onDismiss() }.padding(8.dp),
                )
            }
        }
    }
}
