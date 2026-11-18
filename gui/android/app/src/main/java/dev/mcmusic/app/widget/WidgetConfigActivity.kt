package dev.mcmusic.app.widget

import android.app.Activity
import android.appwidget.AppWidgetManager
import android.content.Intent
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import dev.mcmusic.app.data.Api
import dev.mcmusic.app.data.Prefs
import dev.mcmusic.app.ui.design.DesignLanguage
import dev.mcmusic.app.ui.design.LocalDesign
import dev.mcmusic.app.ui.design.McTheme
import dev.mcmusic.app.ui.design.mcSurface

/**
 * Shown when a widget is placed: pick whose listening it shows. The colours
 * come from the app's palette, so a widget always matches the theme.
 */
class WidgetConfigActivity : ComponentActivity() {
    private var widgetId = AppWidgetManager.INVALID_APPWIDGET_ID

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        Prefs.init(applicationContext)
        Api.init(applicationContext)
        widgetId = intent?.extras?.getInt(
            AppWidgetManager.EXTRA_APPWIDGET_ID,
            AppWidgetManager.INVALID_APPWIDGET_ID,
        ) ?: AppWidgetManager.INVALID_APPWIDGET_ID

        if (widgetId == AppWidgetManager.INVALID_APPWIDGET_ID) {
            setResult(Activity.RESULT_CANCELED)
            finish()
            return
        }
        setResult(Activity.RESULT_CANCELED)

        setContent {
            McTheme(Prefs.palette, DesignLanguage.from(Prefs.language)) {
                var name by remember { mutableStateOf(Prefs.widgetUser ?: Prefs.username.orEmpty()) }
                ConfigScreen(
                    name = name,
                    onName = { name = it },
                    onCancel = { finish() },
                    onSave = {
                        Prefs.saveWidgetUser(name)
                        Widgets.refresh(applicationContext)
                        setResult(
                            Activity.RESULT_OK,
                            Intent().putExtra(AppWidgetManager.EXTRA_APPWIDGET_ID, widgetId),
                        )
                        finish()
                    },
                )
            }
        }
    }

    @androidx.compose.runtime.Composable
    private fun ConfigScreen(
        name: String,
        onName: (String) -> Unit,
        onCancel: () -> Unit,
        onSave: () -> Unit,
    ) {
        val design = LocalDesign.current
        Box(
            Modifier
                .fillMaxSize()
                .background(design.palette.bg)
                .padding(20.dp),
            contentAlignment = Alignment.Center,
        ) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .mcSurface(RoundedCornerShape(design.cardRadius))
                    .padding(20.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                Text("Listening widget", color = design.fg, fontSize = 20.sp, fontWeight = FontWeight.SemiBold)
                Text(
                    "Whose listening should this show? Leave it empty to follow the signed-in account.",
                    color = design.dim,
                    fontSize = 13.sp,
                    lineHeight = 18.sp,
                )
                OutlinedTextField(
                    value = name,
                    onValueChange = onName,
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(16.dp),
                    label = { Text("Username", fontSize = 12.sp) },
                    placeholder = { Text(Prefs.username ?: "username", fontSize = 13.sp) },
                    singleLine = true,
                    keyboardOptions = KeyboardOptions(imeAction = ImeAction.Done),
                    textStyle = androidx.compose.ui.text.TextStyle(fontSize = 15.sp),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedBorderColor = design.accent,
                        unfocusedBorderColor = design.hairline,
                        focusedTextColor = design.fg,
                        unfocusedTextColor = design.fg,
                        cursorColor = design.accent,
                        focusedLabelColor = design.accent,
                        unfocusedLabelColor = design.dim,
                        focusedContainerColor = design.palette.bg2.copy(alpha = 0.35f),
                        unfocusedContainerColor = design.palette.bg2.copy(alpha = 0.35f),
                    ),
                )
                Text(
                    "Colours follow the palette in Settings; the surface uses the same seven themes as the web embeds.",
                    color = design.dim,
                    fontSize = 11.sp,
                    lineHeight = 16.sp,
                )
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Box(Modifier.weight(1f))
                    Box(
                        Modifier
                            .clip(RoundedCornerShape(50))
                            .clickable { onCancel() }
                            .padding(horizontal = 14.dp, vertical = 9.dp),
                    ) {
                        Text("Cancel", color = design.dim, fontSize = 13.sp)
                    }
                    Box(
                        Modifier
                            .height(38.dp)
                            .clip(RoundedCornerShape(50))
                            .background(design.accent)
                            .clickable { onSave() }
                            .padding(horizontal = 18.dp),
                        contentAlignment = Alignment.Center,
                    ) {
                        Text("Add widget", color = design.palette.bg2, fontSize = 13.sp, fontWeight = FontWeight.SemiBold)
                    }
                }
            }
        }
    }
}
