package ro.autoid.app

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import ro.autoid.app.ui.theme.AutoIdOrange

private val StatusInkV121=Color(0xFF101828)
private val StatusMutedV121=Color(0xFF667085)
private val StatusTrackV121=Color(0xFFEFF1F4)

fun orderIsTerminalV121(statusCode:String):Boolean = statusCode in listOf("cancelled","failed","refunded")

fun orderStageV121(statusCode:String,trackingNumber:String):Int = when {
    orderIsTerminalV121(statusCode) -> 0
    statusCode=="completed" -> 3
    trackingNumber.isNotBlank() -> 2
    else -> 1
}

fun orderDisplayStatusV121(statusCode:String,trackingNumber:String,fallback:String=""):String = when {
    orderIsTerminalV121(statusCode) -> fallback.ifBlank{statusCode}
    statusCode=="completed" -> "Comanda finalizată"
    trackingNumber.isNotBlank() -> "Livrare"
    else -> "Procesare"
}

@Composable
fun OrderStatusProgressV121(statusCode:String,trackingNumber:String){
    val stage=orderStageV121(statusCode,trackingNumber)
    if(stage<=0)return
    LinearProgressIndicator(
        progress={stage/3f},
        modifier=Modifier.fillMaxWidth().height(7.dp).clip(RoundedCornerShape(50)),
        color=AutoIdOrange,
        trackColor=StatusTrackV121
    )
    Spacer(Modifier.height(7.dp))
    Row(Modifier.fillMaxWidth()){
        val labels=listOf("Procesare","Livrare","Comanda finalizată")
        labels.forEachIndexed{i,label->
            val active=i<stage
            Text(
                label,
                modifier=Modifier.weight(1f),
                fontSize=8.sp,
                textAlign=when(i){0->TextAlign.Start;2->TextAlign.End;else->TextAlign.Center},
                color=if(active)StatusInkV121 else StatusMutedV121,
                fontWeight=if(active)FontWeight.Bold else FontWeight.Normal
            )
        }
    }
}
