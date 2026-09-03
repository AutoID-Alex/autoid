package ro.autoid.app

import androidx.compose.animation.core.animateDpAsState
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.RequestQuote
import androidx.compose.material3.Badge
import androidx.compose.material3.BadgedBox
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.delay
import ro.autoid.app.ui.theme.AutoIdOrange

@Composable
fun RfqHeaderActionV133(
    onClick: () -> Unit,
    tint: Color = Color(0xFF101828)
) {
    val context = LocalContext.current
    val count = RfqStoreV130(context).items().size
    var pulse by remember { mutableStateOf(false) }

    LaunchedEffect(count) {
        if (count > 0) {
            pulse = true
            delay(320)
            pulse = false
        }
    }

    val iconSize by animateDpAsState(
        targetValue = if (pulse) 28.dp else 23.dp,
        label = "rfqHeaderPulse"
    )

    IconButton(onClick = onClick) {
        BadgedBox(
            badge = {
                if (count > 0) {
                    Badge(containerColor = AutoIdOrange) {
                        Text(if (count > 99) "99+" else count.toString(), fontSize = 9.sp)
                    }
                }
            }
        ) {
            Surface(
                shape = CircleShape,
                color = if (pulse) Color(0xFFFFF1E8) else Color.Transparent
            ) {
                Icon(
                    Icons.Default.RequestQuote,
                    contentDescription = "Cerere de ofertă",
                    tint = if (pulse) AutoIdOrange else tint,
                    modifier = Modifier.padding(4.dp).size(iconSize)
                )
            }
        }
    }
}
