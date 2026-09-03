package ro.autoid.app

import android.content.Context
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.Lock
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Send
import androidx.compose.material.icons.filled.SmartToy
import androidx.compose.material3.AssistChip
import androidx.compose.material3.CenterAlignedTopAppBar
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import ro.autoid.app.data.AiMessage
import ro.autoid.app.data.AutoIdApi
import ro.autoid.app.data.AutoIdHttpExceptionV129
import ro.autoid.app.data.ChatSessionV129
import ro.autoid.app.ui.theme.AutoIdOrange
import java.util.UUID

private val ChatInkV129 = Color(0xFF182230)
private val ChatMutedV129 = Color(0xFF667085)
private val ChatCanvasV129 = Color(0xFFF6F8FB)
private val ChatAssistantV129 = Color(0xFFFFFFFF)

private fun chatDeviceIdV129(context: Context): String {
    val prefs = context.getSharedPreferences("autoid_chat_v129", Context.MODE_PRIVATE)
    return prefs.getString("device_id", null) ?: UUID.randomUUID().toString().also {
        prefs.edit().putString("device_id", it).apply()
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun NativeAiChatScreen(api: AutoIdApi, productId: Long?, onBack: () -> Unit) {
    val context = LocalContext.current
    val deviceId = remember { chatDeviceIdV129(context) }
    val listState = rememberLazyListState()
    val scope = rememberCoroutineScope()
    var input by remember { mutableStateOf("") }
    var busy by remember { mutableStateOf(false) }
    var session by remember { mutableStateOf<ChatSessionV129?>(null) }
    var messages by remember {
        mutableStateOf(listOf(AiMessage(false, "Salut! Sunt asistentul AutoID. Spune-mi ce echipament cauți sau ce problemă tehnică vrei să rezolvi.")))
    }

    val suggestions = remember(productId) {
        if (productId != null) listOf("Detalii despre produs", "Compatibilitate și accesorii", "Ajutor pentru configurare")
        else listOf("Recomandă-mi un produs", "Ajutor tehnic", "Livrare și disponibilitate")
    }

    fun sendMessage(text: String = input) {
        val question = text.trim()
        if (question.isBlank() || busy) return
        input = ""
        messages = messages + AiMessage(true, question)
        busy = true
        scope.launch {
            val result = runCatching {
                withContext(Dispatchers.IO) {
                    var active = session?.takeIf { it.expiresAt > System.currentTimeMillis() / 1000L + 30L }
                        ?: api.chatTokenV129(deviceId).also { session = it }
                    try {
                        api.aiChatV129(question, productId, deviceId, active.token)
                    } catch (error: AutoIdHttpExceptionV129) {
                        if (error.status != 401) throw error
                        active = api.chatTokenV129(deviceId).also { session = it }
                        api.aiChatV129(question, productId, deviceId, active.token)
                    }
                }
            }
            val answer = result.getOrElse { error ->
                session = null
                when (error) {
                    is AutoIdHttpExceptionV129 -> error.message ?: "Serviciul de chat nu este disponibil momentan."
                    else -> "Nu pot contacta momentan asistentul AutoID. Verifică internetul și încearcă din nou."
                }
            }
            messages = messages + AiMessage(false, answer)
            busy = false
        }
    }

    LaunchedEffect(messages.size, busy) {
        if (messages.isNotEmpty()) listState.animateScrollToItem(messages.size + 1 + if (busy) 1 else 0)
    }

    Scaffold(
        containerColor = ChatCanvasV129,
        topBar = {
            CenterAlignedTopAppBar(
                title = {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Text("AutoID Support", fontWeight = FontWeight.ExtraBold)
                        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                            Box(Modifier.size(7.dp).background(Color(0xFF12B76A), CircleShape))
                            Text("Conectat securizat", fontSize = 11.sp, color = ChatMutedV129)
                        }
                    }
                },
                navigationIcon = { IconButton(onClick = onBack) { Icon(Icons.Default.ArrowBack, "Înapoi") } },
                actions = {
                    IconButton(onClick = { session = null }, enabled = !busy) {
                        Icon(Icons.Default.Refresh, "Reînnoiește sesiunea", tint = ChatMutedV129)
                    }
                }
            )
        },
        bottomBar = {
            Surface(shadowElevation = 10.dp, color = Color.White) {
                Column(Modifier.navigationBarsPadding().imePadding().padding(horizontal = 12.dp, vertical = 10.dp)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        OutlinedTextField(
                            value = input,
                            onValueChange = { if (it.length <= 2500) input = it },
                            modifier = Modifier.weight(1f),
                            placeholder = { Text("Scrie întrebarea ta…") },
                            maxLines = 4,
                            shape = RoundedCornerShape(18.dp),
                            enabled = !busy
                        )
                        Spacer(Modifier.width(8.dp))
                        Surface(shape = CircleShape, color = if (input.isNotBlank() && !busy) AutoIdOrange else Color(0xFFE4E7EC)) {
                            IconButton(onClick = { sendMessage() }, enabled = input.isNotBlank() && !busy) {
                                Icon(Icons.Default.Send, "Trimite", tint = if (input.isNotBlank() && !busy) Color.White else ChatMutedV129)
                            }
                        }
                    }
                    Row(Modifier.padding(top = 7.dp), verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(5.dp)) {
                        Icon(Icons.Default.Lock, null, Modifier.size(13.dp), tint = ChatMutedV129)
                        Text("Token temporar • niciun secret permanent în aplicație", fontSize = 10.sp, color = ChatMutedV129)
                    }
                }
            }
        }
    ) { padding ->
        LazyColumn(
            state = listState,
            modifier = Modifier.padding(padding).fillMaxSize().padding(horizontal = 14.dp),
            contentPadding = androidx.compose.foundation.layout.PaddingValues(vertical = 14.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp)
        ) {
            item {
                Surface(color = Color(0xFFFFF4ED), shape = RoundedCornerShape(18.dp), modifier = Modifier.fillMaxWidth()) {
                    Row(Modifier.padding(14.dp), verticalAlignment = Alignment.CenterVertically) {
                        Surface(shape = CircleShape, color = AutoIdOrange, modifier = Modifier.size(44.dp)) {
                            Box(contentAlignment = Alignment.Center) { Icon(Icons.Default.SmartToy, null, tint = Color.White) }
                        }
                        Spacer(Modifier.width(11.dp))
                        Column {
                            Text("Asistență pentru soluții AutoID", fontWeight = FontWeight.ExtraBold, color = ChatInkV129)
                            Text("Produse, compatibilitate și suport tehnic", fontSize = 12.sp, color = ChatMutedV129)
                        }
                    }
                }
            }
            item {
                LazyRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    items(suggestions) { suggestion ->
                        AssistChip(onClick = { sendMessage(suggestion) }, label = { Text(suggestion) }, enabled = !busy)
                    }
                }
            }
            items(messages) { message ->
                Row(Modifier.fillMaxWidth(), horizontalArrangement = if (message.fromUser) Arrangement.End else Arrangement.Start) {
                    Surface(
                        color = if (message.fromUser) AutoIdOrange else ChatAssistantV129,
                        shape = if (message.fromUser) RoundedCornerShape(18.dp, 18.dp, 4.dp, 18.dp) else RoundedCornerShape(18.dp, 18.dp, 18.dp, 4.dp),
                        shadowElevation = if (message.fromUser) 0.dp else 1.dp,
                        modifier = Modifier.widthIn(max = 330.dp)
                    ) {
                        Text(
                            message.text,
                            color = if (message.fromUser) Color.White else ChatInkV129,
                            modifier = Modifier.padding(horizontal = 14.dp, vertical = 11.dp),
                            lineHeight = 21.sp
                        )
                    }
                }
            }
            if (busy) {
                item {
                    Surface(color = Color.White, shape = RoundedCornerShape(18.dp), shadowElevation = 1.dp) {
                        Row(Modifier.padding(horizontal = 16.dp, vertical = 12.dp), verticalAlignment = Alignment.CenterVertically) {
                            CircularProgressIndicator(Modifier.size(17.dp), strokeWidth = 2.dp, color = AutoIdOrange)
                            Spacer(Modifier.width(9.dp))
                            Text("AutoID pregătește răspunsul…", fontSize = 12.sp, color = ChatMutedV129)
                        }
                    }
                }
            }
            item { Spacer(Modifier.height(2.dp)) }
        }
    }
}
