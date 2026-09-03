package ro.autoid.app

import android.content.Context
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.DeleteSweep
import androidx.compose.material.icons.filled.Lock
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Send
import androidx.compose.material.icons.filled.SmartToy
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import ro.autoid.app.data.*
import ro.autoid.app.ui.theme.AutoIdOrange
import java.util.UUID

private val ChatInkV135 = Color(0xFF182230)
private val ChatMutedV135 = Color(0xFF667085)
private val ChatCanvasV135 = Color(0xFFF6F8FB)
private val ChatAssistantV135 = Color.White

private fun chatDeviceIdV135(context: Context): String {
    val prefs = context.getSharedPreferences("autoid_chat_v129", Context.MODE_PRIVATE)
    return prefs.getString("device_id", null) ?: UUID.randomUUID().toString().also { prefs.edit().putString("device_id", it).apply() }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PersistentAiChatScreenV135(api: AutoIdApi, productId: Long?, onBack: () -> Unit) {
    val context = LocalContext.current
    val deviceId = remember { chatDeviceIdV135(context) }
    val listState = rememberLazyListState()
    val scope = rememberCoroutineScope()
    var input by remember { mutableStateOf("") }
    var busy by remember { mutableStateOf(false) }
    var loading by remember { mutableStateOf(true) }
    var resetting by remember { mutableStateOf(false) }
    var session by remember { mutableStateOf<ChatSessionV129?>(null) }
    var mode by remember { mutableStateOf("ai") }
    var messages by remember { mutableStateOf<List<AiMessage>>(emptyList()) }

    fun greeting() = listOf(AiMessage(false, "Salut! Sunt asistentul AutoID. Spune-mi ce echipament cauți sau ce problemă tehnică vrei să rezolvi."))

    suspend fun activeSession(): ChatSessionV129 {
        val now = System.currentTimeMillis() / 1000L
        session?.takeIf { it.expiresAt > now + 30L }?.let { return it }
        return withContext(Dispatchers.IO) { api.chatTokenV129(deviceId) }.also { session = it }
    }

    suspend fun syncHistory(showLoader:Boolean=false) {
        if(showLoader) loading=true
        try {
            var active=activeSession()
            val history=try { withContext(Dispatchers.IO){api.aiHistoryV134(deviceId,active.token)} }
            catch(error:AutoIdHttpExceptionV129){
                if(error.status!=401)throw error
                active=withContext(Dispatchers.IO){api.chatTokenV129(deviceId)}.also{session=it}
                withContext(Dispatchers.IO){api.aiHistoryV134(deviceId,active.token)}
            }
            mode=history.mode
            messages=if(history.messages.isEmpty())greeting() else history.messages
        } catch(_:Throwable) { if(messages.isEmpty())messages=greeting() }
        finally { loading=false }
    }

    val suggestions=remember(productId){if(productId!=null)listOf("Detalii despre produs","Compatibilitate și accesorii","Ajutor pentru configurare") else listOf("Recomandă-mi un produs","Ajutor tehnic","Livrare și disponibilitate")}

    fun resetConversation(){
        if(resetting||busy)return
        resetting=true
        scope.launch{
            val result=runCatching{
                var active=activeSession()
                try{withContext(Dispatchers.IO){api.aiResetV135(deviceId,productId,active.token)}}
                catch(error:AutoIdHttpExceptionV129){if(error.status!=401)throw error;active=withContext(Dispatchers.IO){api.chatTokenV129(deviceId)}.also{session=it};withContext(Dispatchers.IO){api.aiResetV135(deviceId,productId,active.token)}}
            }
            result.onSuccess{mode="ai";messages=greeting();input="";syncHistory(false)}
                .onFailure{messages=messages+AiMessage(false,it.message?:"Conversația nouă nu a putut fi inițializată.")}
            resetting=false
        }
    }

    fun sendMessage(text:String=input){
        val question=text.trim();if(question.isBlank()||busy||mode=="closed")return
        input="";messages=messages+AiMessage(true,question);busy=true
        scope.launch{
            val result=runCatching{
                var active=activeSession()
                try{withContext(Dispatchers.IO){api.aiChatV134(question,productId,deviceId,active.token)}}
                catch(error:AutoIdHttpExceptionV129){if(error.status!=401)throw error;active=withContext(Dispatchers.IO){api.chatTokenV129(deviceId)}.also{session=it};withContext(Dispatchers.IO){api.aiChatV134(question,productId,deviceId,active.token)}}
            }
            result.onSuccess{reply->mode=reply.mode;if(reply.answer.isNotBlank()&&!reply.pending)messages=messages+AiMessage(false,reply.answer);syncHistory(false)}
                .onFailure{error->messages=messages+AiMessage(false,if(error is AutoIdHttpExceptionV129)error.message?:"Serviciul de chat nu este disponibil momentan." else "Nu pot contacta momentan asistentul AutoID. Verifică internetul și încearcă din nou.")}
            busy=false
        }
    }

    LaunchedEffect(deviceId){syncHistory(true);while(true){delay(3000);if(!busy&&!resetting)syncHistory(false)}}
    LaunchedEffect(messages.size,busy){if(messages.isNotEmpty())runCatching{listState.animateScrollToItem(messages.size+4)}}

    Scaffold(containerColor=ChatCanvasV135,topBar={CenterAlignedTopAppBar(title={Column(horizontalAlignment=Alignment.CenterHorizontally){Text("AutoID Support",fontWeight=FontWeight.ExtraBold);Row(verticalAlignment=Alignment.CenterVertically,horizontalArrangement=Arrangement.spacedBy(4.dp)){Box(Modifier.size(7.dp).background(if(mode=="closed")Color(0xFF98A2B3) else Color(0xFF12B76A),CircleShape));Text(when(mode){"human"->"Consultant AutoID conectat";"closed"->"Conversație închisă";else->"AutoID AI conectat"},fontSize=11.sp,color=ChatMutedV135)}}},navigationIcon={IconButton(onClick=onBack){Icon(Icons.Default.ArrowBack,"Înapoi")}},actions={IconButton(onClick={scope.launch{syncHistory(true)}},enabled=!busy&&!resetting){Icon(Icons.Default.Refresh,"Sincronizează conversația",tint=ChatMutedV135)}})},bottomBar={Surface(shadowElevation=10.dp,color=Color.White){Column(Modifier.navigationBarsPadding().imePadding().padding(horizontal=12.dp,vertical=10.dp)){
        if(mode=="closed"){
            Button(onClick={resetConversation()},enabled=!resetting,modifier=Modifier.fillMaxWidth().height(50.dp),shape=RoundedCornerShape(14.dp)){Icon(Icons.Default.DeleteSweep,null);Spacer(Modifier.width(7.dp));Text(if(resetting)"Se pornește conversația…" else "Pornește o conversație nouă",fontWeight=FontWeight.ExtraBold)}
            Text("Conversația închisă rămâne arhivată pentru suport; în aplicație începi un chat nou.",fontSize=10.sp,color=ChatMutedV135,modifier=Modifier.padding(top=7.dp))
        }else{
            Row(verticalAlignment=Alignment.CenterVertically){OutlinedTextField(value=input,onValueChange={if(it.length<=2500)input=it},modifier=Modifier.weight(1f),placeholder={Text(if(mode=="human")"Scrie consultantului AutoID…" else "Scrie întrebarea ta…")},maxLines=4,shape=RoundedCornerShape(18.dp),enabled=!busy);Spacer(Modifier.width(8.dp));Surface(shape=CircleShape,color=if(input.isNotBlank()&&!busy)AutoIdOrange else Color(0xFFE4E7EC)){IconButton(onClick={sendMessage()},enabled=input.isNotBlank()&&!busy){Icon(Icons.Default.Send,"Trimite",tint=if(input.isNotBlank()&&!busy)Color.White else ChatMutedV135)}}}
            Row(Modifier.padding(top=7.dp),verticalAlignment=Alignment.CenterVertically,horizontalArrangement=Arrangement.spacedBy(5.dp)){Icon(Icons.Default.Lock,null,Modifier.size(13.dp),tint=ChatMutedV135);Text("Conversația este salvată și sincronizată securizat",fontSize=10.sp,color=ChatMutedV135)}
        }
    }}}){padding->LazyColumn(state=listState,modifier=Modifier.padding(padding).fillMaxSize().padding(horizontal=14.dp),contentPadding=PaddingValues(vertical=14.dp),verticalArrangement=Arrangement.spacedBy(10.dp)){
        item{Surface(color=if(mode=="human")Color(0xFFEAF4FF) else if(mode=="closed")Color(0xFFF2F4F7) else Color(0xFFFFF4ED),shape=RoundedCornerShape(18.dp),modifier=Modifier.fillMaxWidth()){Row(Modifier.padding(14.dp),verticalAlignment=Alignment.CenterVertically){Surface(shape=CircleShape,color=if(mode=="closed")Color(0xFF98A2B3) else AutoIdOrange,modifier=Modifier.size(44.dp)){Box(contentAlignment=Alignment.Center){Icon(Icons.Default.SmartToy,null,tint=Color.White)}};Spacer(Modifier.width(11.dp));Column{Text(when(mode){"human"->"Conversație preluată de AutoID";"closed"->"Această conversație este închisă";else->"Asistență pentru soluții AutoID"},fontWeight=FontWeight.ExtraBold,color=ChatInkV135);Text(when(mode){"human"->"Un consultant îți răspunde direct în acest chat.";"closed"->"Poți porni imediat o conversație nouă din butonul de jos.";else->"Produse, compatibilitate și suport tehnic"},fontSize=12.sp,color=ChatMutedV135)}}}}
        if(mode=="ai")item{LazyRow(horizontalArrangement=Arrangement.spacedBy(8.dp)){items(suggestions){suggestion->AssistChip(onClick={sendMessage(suggestion)},label={Text(suggestion)},enabled=!busy)}}}
        if(loading&&messages.isEmpty())item{Box(Modifier.fillMaxWidth().padding(24.dp),contentAlignment=Alignment.Center){CircularProgressIndicator(color=AutoIdOrange)}}
        items(messages){message->Row(Modifier.fillMaxWidth(),horizontalArrangement=if(message.fromUser)Arrangement.End else Arrangement.Start){Surface(color=if(message.fromUser)AutoIdOrange else ChatAssistantV135,shape=if(message.fromUser)RoundedCornerShape(18.dp,18.dp,4.dp,18.dp) else RoundedCornerShape(18.dp,18.dp,18.dp,4.dp),shadowElevation=if(message.fromUser)0.dp else 1.dp,modifier=Modifier.widthIn(max=330.dp)){Text(message.text,color=if(message.fromUser)Color.White else ChatInkV135,modifier=Modifier.padding(horizontal=14.dp,vertical=11.dp),lineHeight=21.sp)}}}
        if(busy)item{Surface(color=Color.White,shape=RoundedCornerShape(18.dp),shadowElevation=1.dp){Row(Modifier.padding(horizontal=16.dp,vertical=12.dp),verticalAlignment=Alignment.CenterVertically){CircularProgressIndicator(Modifier.size(17.dp),strokeWidth=2.dp,color=AutoIdOrange);Spacer(Modifier.width(9.dp));Text(if(mode=="human")"Mesajul se trimite consultantului…" else "AutoID pregătește răspunsul…",fontSize=12.sp,color=ChatMutedV135)}}}
        item{Spacer(Modifier.height(2.dp))}
    }}
}
