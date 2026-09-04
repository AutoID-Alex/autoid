package ro.autoid.app

import android.content.Context
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalUriHandler
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import org.json.JSONArray
import org.json.JSONObject
import ro.autoid.app.ui.theme.AutoIdOrange

private val N138Ink=Color(0xFF101828)
private val N138Muted=Color(0xFF667085)
private val N138Border=Color(0xFFE4E7EC)
private val N138Soft=Color(0xFFF7F8FA)

object NotificationInboxBusV138 {
    val version=mutableIntStateOf(0)
    fun bump(){version.intValue=version.intValue+1}
}

data class InboxNotificationV138(
    val id:String,
    val type:String,
    val title:String,
    val body:String,
    val createdAt:Long,
    val read:Boolean=false,
    val orderId:Long=0,
    val rfqId:Long=0,
    val productId:Long=0,
    val url:String=""
)

class NotificationInboxStoreV138(context:Context){
    private val prefs=context.applicationContext.getSharedPreferences("autoid_notification_inbox_v138",Context.MODE_PRIVATE)
    private fun raw():JSONArray=runCatching{JSONArray(prefs.getString("items","[]")?:"[]")}.getOrDefault(JSONArray())
    private fun save(items:List<InboxNotificationV138>){
        val a=JSONArray();items.take(100).forEach{n->a.put(JSONObject()
            .put("id",n.id).put("type",n.type).put("title",n.title).put("body",n.body)
            .put("created_at",n.createdAt).put("read",n.read).put("order_id",n.orderId)
            .put("rfq_id",n.rfqId).put("product_id",n.productId).put("url",n.url))}
        prefs.edit().putString("items",a.toString()).apply();NotificationInboxBusV138.bump()
    }
    fun all():List<InboxNotificationV138>{
        val a=raw();return (0 until a.length()).mapNotNull{i->a.optJSONObject(i)?.let{o->InboxNotificationV138(
            id=o.optString("id"),type=o.optString("type","general"),title=o.optString("title"),body=o.optString("body"),
            createdAt=o.optLong("created_at"),read=o.optBoolean("read"),orderId=o.optLong("order_id"),rfqId=o.optLong("rfq_id"),
            productId=o.optLong("product_id"),url=o.optString("url"))}}
            .sortedByDescending{it.createdAt}
    }
    fun unreadCount():Int=all().count{!it.read}
    fun addPush(data:Map<String,String>,notificationTitle:String?=null,notificationBody:String?=null){
        val type=(data["type"]?:"general").lowercase()
        val title=(data["title"]?:notificationTitle?:defaultTitle(type)).trim()
        val body=(data["body"]?:data["message"]?:notificationBody?:"").trim()
        if(title.isBlank()&&body.isBlank())return
        val orderId=(data["order_id"]?:data["orderId"]?:"0").toLongOrNull()?:0
        val rfqId=(data["rfq_id"]?:data["rfqId"]?:"0").toLongOrNull()?:0
        val productId=(data["product_id"]?:data["productId"]?:"0").toLongOrNull()?:0
        val url=data["url"]?:data["link"]?:data["deep_link"]?:""
        val id=data["notification_id"]?:data["id"]?:"push-${System.currentTimeMillis()}-${title.hashCode()}"
        add(InboxNotificationV138(id,type,title,body,System.currentTimeMillis(),false,orderId,rfqId,productId,url))
    }
    fun addLocal(type:String,title:String,body:String,orderId:Long=0,rfqId:Long=0,productId:Long=0,url:String="",id:String=""){
        add(InboxNotificationV138(id.ifBlank{"local-${System.currentTimeMillis()}-${title.hashCode()}"},type,title,body,System.currentTimeMillis(),false,orderId,rfqId,productId,url))
    }
    private fun add(item:InboxNotificationV138){
        val current=all().filterNot{it.id==item.id}.toMutableList();current.add(0,item);save(current)
    }
    fun markRead(id:String){save(all().map{if(it.id==id)it.copy(read=true)else it})}
    fun markAllRead(){save(all().map{it.copy(read=true)})}
    fun delete(id:String){save(all().filterNot{it.id==id})}
    fun clear(){save(emptyList())}
    private fun defaultTitle(type:String)=when{
        type.startsWith("rfq")->"Cerere de ofertă AutoID"
        type.startsWith("order")||type.contains("review")->"Comandă AutoID"
        type.contains("stock")->"Produs disponibil"
        type.startsWith("marketing")||type.contains("promo")->"AutoID"
        else->"Notificare AutoID"
    }
}

@Composable fun NotificationUnreadBadgeV138(){
    val context=LocalContext.current
    NotificationInboxBusV138.version.intValue
    val count=remember(context,NotificationInboxBusV138.version.intValue){NotificationInboxStoreV138(context).unreadCount()}
    if(count>0)Badge(containerColor=AutoIdOrange){Text(if(count>99)"99+" else count.toString())}
}

private fun notificationKindV138(type:String):String=when{
    type.startsWith("order")||type.contains("review")->"orders"
    type.startsWith("rfq")->"rfq"
    type.contains("stock")->"stock"
    type.startsWith("marketing")||type.contains("promo")||type.contains("offer")->"promo"
    else->"other"
}

@Composable private fun NotificationIconV138(n:InboxNotificationV138){
    val kind=notificationKindV138(n.type)
    val icon=when(kind){"orders"->Icons.Default.ReceiptLong;"rfq"->Icons.Default.RequestQuote;"stock"->Icons.Default.Inventory2;"promo"->Icons.Default.LocalOffer;else->Icons.Default.Notifications}
    val color=when(kind){"orders"->Color(0xFF2E90FA);"rfq"->AutoIdOrange;"stock"->Color(0xFF12B76A);"promo"->Color(0xFFF79009);else->N138Muted}
    Surface(shape=CircleShape,color=color.copy(alpha=.12f),modifier=Modifier.size(46.dp)){Box(contentAlignment=Alignment.Center){Icon(icon,null,tint=color,modifier=Modifier.size(23.dp))}}
}

private fun timeLabelV138(ts:Long):String{
    if(ts<=0)return ""
    val diff=(System.currentTimeMillis()-ts).coerceAtLeast(0)
    return when{
        diff<60_000->"acum"
        diff<60*60_000->"acum ${diff/60_000} min"
        diff<24*60*60_000->"acum ${diff/(60*60_000)} h"
        diff<48*60*60_000->"ieri"
        else->java.text.SimpleDateFormat("dd.MM.yyyy · HH:mm",java.util.Locale("ro","RO")).format(java.util.Date(ts))
    }
}

@Composable fun NotificationsInboxV138(
    onBack:()->Unit,
    onCart:()->Unit,
    onOrder:(Long)->Unit,
    onRfq:(Long)->Unit,
    onProduct:(Long)->Unit
){
    val context=LocalContext.current
    val uri=LocalUriHandler.current
    val store=remember{NotificationInboxStoreV138(context)}
    NotificationInboxBusV138.version.intValue
    var filter by remember{mutableStateOf("all")}
    var menu by remember{mutableStateOf(false)}
    val all=remember(NotificationInboxBusV138.version.intValue){store.all()}
    val shown=remember(all,filter){if(filter=="all")all else all.filter{notificationKindV138(it.type)==filter}}
    val unread=all.count{!it.read}

    Column(Modifier.fillMaxSize().background(Color.White)){
        Row(Modifier.fillMaxWidth().padding(horizontal=10.dp,vertical=8.dp),verticalAlignment=Alignment.CenterVertically){
            IconButton(onClick=onBack){Icon(Icons.Default.ArrowBack,"Înapoi")}
            Column(Modifier.weight(1f)){Text("Notificări",fontSize=24.sp,fontWeight=FontWeight.ExtraBold,color=N138Ink);Text(if(unread==0)"Ești la zi" else "$unread necitite",fontSize=10.sp,color=N138Muted)}
            if(unread>0)TextButton(onClick={store.markAllRead()}){Text("Citește toate",fontSize=10.sp)}
            Box{IconButton(onClick={menu=true}){Icon(Icons.Default.MoreVert,"Opțiuni")};DropdownMenu(menu,{menu=false}){DropdownMenuItem(text={Text("Șterge toate notificările")},leadingIcon={Icon(Icons.Default.DeleteSweep,null)},onClick={store.clear();menu=false})}}
            IconButton(onClick=onCart){Icon(Icons.Default.ShoppingCart,"Coș")}
        }
        HorizontalDivider(color=N138Border)
        LazyRow(contentPadding=PaddingValues(horizontal=14.dp,vertical=10.dp),horizontalArrangement=Arrangement.spacedBy(7.dp)){
            val filters=listOf("all" to "Toate","orders" to "Comenzi","rfq" to "Cereri ofertă","stock" to "Stoc","promo" to "Promoții")
            items(filters){(key,label)->FilterChip(selected=filter==key,onClick={filter=key},label={Text(label,fontSize=10.sp)})}
        }
        if(shown.isEmpty()){
            Box(Modifier.fillMaxSize(),contentAlignment=Alignment.Center){Column(horizontalAlignment=Alignment.CenterHorizontally,verticalArrangement=Arrangement.spacedBy(9.dp)){Surface(shape=CircleShape,color=Color(0xFFFFF1E8),modifier=Modifier.size(76.dp)){Box(contentAlignment=Alignment.Center){Icon(Icons.Default.NotificationsNone,null,tint=AutoIdOrange,modifier=Modifier.size(34.dp))}};Text(if(all.isEmpty())"Nu ai notificări încă" else "Nu sunt notificări în această categorie",fontSize=18.sp,fontWeight=FontWeight.ExtraBold,color=N138Ink);if(all.isEmpty())Text("Actualizările despre comenzi, RFQ, stoc și promoții vor apărea aici.",fontSize=11.sp,color=N138Muted)}}
        }else LazyColumn(Modifier.fillMaxSize().background(N138Soft),contentPadding=PaddingValues(horizontal=14.dp,vertical=10.dp),verticalArrangement=Arrangement.spacedBy(8.dp)){
            items(shown,key={it.id}){n->
                ElevatedCard(modifier=Modifier.fillMaxWidth().clickable{
                    store.markRead(n.id)
                    when{
                        n.rfqId>0->onRfq(n.rfqId)
                        n.orderId>0->onOrder(n.orderId)
                        n.productId>0->onProduct(n.productId)
                        n.url.startsWith("http")->uri.openUri(n.url)
                    }
                },shape=RoundedCornerShape(14.dp),colors=CardDefaults.elevatedCardColors(containerColor=Color.White),elevation=CardDefaults.elevatedCardElevation(defaultElevation=if(n.read)0.dp else 2.dp)){
                    Row(Modifier.fillMaxWidth().padding(13.dp),verticalAlignment=Alignment.Top){
                        NotificationIconV138(n);Spacer(Modifier.width(11.dp));Column(Modifier.weight(1f),verticalArrangement=Arrangement.spacedBy(3.dp)){Row(verticalAlignment=Alignment.CenterVertically){if(!n.read)Box(Modifier.size(7.dp).background(AutoIdOrange,CircleShape));if(!n.read)Spacer(Modifier.width(6.dp));Text(n.title,fontWeight=if(n.read)FontWeight.SemiBold else FontWeight.ExtraBold,fontSize=13.sp,color=N138Ink,maxLines=2,overflow=TextOverflow.Ellipsis)};if(n.body.isNotBlank())Text(n.body,fontSize=11.sp,color=N138Muted,maxLines=4,overflow=TextOverflow.Ellipsis);Text(timeLabelV138(n.createdAt),fontSize=9.sp,color=N138Muted)}
                        IconButton(onClick={store.delete(n.id)},modifier=Modifier.size(32.dp)){Icon(Icons.Default.Close,"Șterge",tint=N138Muted,modifier=Modifier.size(16.dp))}
                    }
                }
            }
        }
    }
}
