package dev.mcmusic.app

import android.os.Build
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.kyant.backdrop.backdrops.layerBackdrop
import com.kyant.backdrop.backdrops.rememberLayerBackdrop
import dev.mcmusic.app.ui.liquidGlass

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            MaterialTheme(
                colorScheme = darkColorScheme(
                    background = Color(0xFF0B0B10),
                    surface = Color(0xFF16161E),
                    primary = Color(0xFF8AB4FF),
                    onBackground = Color(0xFFF2F2F7),
                    onSurface = Color(0xFFF2F2F7),
                ),
            ) {
                Surface(Modifier.fillMaxSize(), color = Color(0xFF0B0B10)) {
                    SkeletonScreen()
                }
            }
        }
    }
}

/**
 * Scaffolding only: a bright stage with two glass panels over it, so the
 * refraction is visible and the toolchain is proven end to end. Real screens
 * replace this once the GUI is specified.
 */
@Composable
private fun SkeletonScreen() {
    val glassLive = Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU
    val backdrop = if (glassLive) rememberLayerBackdrop() else null

    Box(Modifier.fillMaxSize()) {
        Stage(
            Modifier
                .fillMaxSize()
                .then(if (backdrop != null) Modifier.layerBackdrop(backdrop) else Modifier),
        )

        Column(
            modifier = Modifier
                .align(Alignment.BottomCenter)
                .fillMaxWidth()
                .padding(20.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .liquidGlass(backdrop),
            ) {
                Column(Modifier.padding(22.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    Text(
                        text = "New GUI",
                        color = Color.White,
                        fontSize = 26.sp,
                        fontWeight = FontWeight.SemiBold,
                    )
                    Text(
                        text = "Backdrop ${if (glassLive) "live" else "fallback"}" +
                            " · API ${Build.VERSION.SDK_INT}",
                        color = Color.White.copy(alpha = 0.72f),
                        fontSize = 13.sp,
                    )
                }
            }

            Column(
                modifier = Modifier
                    .size(width = 168.dp, height = 56.dp)
                    .liquidGlass(backdrop, shape = androidx.compose.foundation.shape.RoundedCornerShape(28.dp)),
            ) {
                Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    Text(
                        text = "tap target",
                        color = Color.White.copy(alpha = 0.85f),
                        fontSize = 14.sp,
                    )
                }
            }
        }
    }
}

/** Colour and shape behind the glass; its whole job is to look different from pixel to pixel. */
@Composable
private fun Stage(modifier: Modifier = Modifier) {
    Canvas(modifier) {
        drawRect(
            Brush.linearGradient(
                colors = listOf(Color(0xFF2B1055), Color(0xFF7597DE), Color(0xFF1C1C2E)),
                start = Offset(0f, 0f),
                end = Offset(size.width, size.height),
            ),
        )
        drawCircle(Color(0xFFFF6B6B), radius = size.minDimension * 0.30f, center = Offset(size.width * 0.22f, size.height * 0.24f))
        drawCircle(Color(0xFF4ECDC4), radius = size.minDimension * 0.24f, center = Offset(size.width * 0.82f, size.height * 0.36f))
        drawCircle(Color(0xFFFFE66D), radius = size.minDimension * 0.16f, center = Offset(size.width * 0.58f, size.height * 0.72f))
    }
}
