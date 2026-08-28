package ro.autoid.app.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

val AutoIdOrange = Color(0xFFF7630C)
private val Colors = lightColorScheme(
    primary = AutoIdOrange,
    secondary = Color(0xFF111827),
    background = Color.White,
    surface = Color.White
)

@Composable
fun AutoIdTheme(content: @Composable () -> Unit) {
    MaterialTheme(colorScheme = Colors, content = content)
}
