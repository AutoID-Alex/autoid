package ro.autoid.app

import android.content.Context
import android.content.Intent
import android.net.Uri
import androidx.browser.customtabs.CustomTabsIntent
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalClipboardManager
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.content.FileProvider
import coil.compose.AsyncImage
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import ro.autoid.app.data.AutoIdApi
import ro.autoid.app.data.Product
import ro.autoid.app.data.SessionStore
import ro.autoid.app.ui.theme.AutoIdOrange
import java.io.File
import java.net.HttpURLConnection
import java.net.URI
import java.nio.charset.StandardCharsets

private val RfqInk = Color(0xFF162033)
private val RfqMuted = Color(0xFF667085)
private val RfqSoft = Color(0xFFF5F7FA)
private val RfqBorder = Color(0xFFE4E7EC)
private val RfqGood = Color(0xFF087A55)

data class RfqDraftItemV130(val productId:Long,val sku:String,val name:String,val image:String?,val quantity:Int,val price:String,val url:String)
data class RfqSummaryV130(val id:Long,val reference:String,val status:String,val statusLabel:String,val createdAt:String,val value:Double,val currency:String,val itemCount:Int)
data class RfqRequesterV130(val firstName:String="",val lastName:String="",val email:String="",val phone:String="",val company:String="",val vat:String="")
data class RfqLineV130(val productId:Long,val sku:String,val name:String,val quantity:Int,val image:String?,val url:String,val lineValue:Double)
data class RfqTimelineV130(val key:String,val label:String,val at:String)
data class RfqDocumentV130(val kind:String,val label:String,val sentAt:String)
data class RfqIbanV130(val iban:String,val bank:String)
data class RfqPaymentV130(val type:String,val label:String,val reference:String="",val beneficiary:String="",val registration:String="",val vat:String="",val address:String="",val ibans:List<RfqIbanV130> = emptyList(),val url:String="")
data class RfqDetailV130(val id:Long,val reference:String,val status:String,val statusLabel:String,val createdAt:String,val value:Double,val currency:String,val lines:List<RfqLineV130>,val requester:RfqRequesterV130,val note:String,val timeline:List<RfqTimelineV130>,val documents:List<RfqDocumentV130>,val payments:List<RfqPaymentV130>,val canAccept:Boolean,val canReject:Boolean)
data class RfqPageV130(val items:List<RfqSummaryV130>,val page:Int,val pages:Int,val total:Int)

class RfqStoreV130(context:Context) {
    private val prefs=context.applicationContext.getSharedPreferences("autoid_rfq_v130",Context.MODE_PRIVATE)
    fun items():List<RfqDraftItemV130>{val a=runCatching{JSONArray(prefs.getString("items","[]"))}.getOrDefault(JSONArray());return(0 until a.length()).mapNotNull{i->a.optJSONObject(i)?.let{RfqDraftItemV130(it.optLong("product_id"),it.optString("sku"),it.optString("name"),it.optString("image").ifBlank{null},it.optInt("quantity",1).coerceIn(1,9999),it.optString("price"),it.optString("url"))}}}
    private fun save(rows:List<RfqDraftItemV130>){val a=JSONArray();rows.forEach{a.put(JSONObject().put("product_id",it.productId).put("sku",it.sku).put("name",it.name).put("image",it.image).put("quantity",it.quantity).put("price",it.price).put("url",it.url))};prefs.edit().putString("items",a.toString()).apply()}
    fun add(product:Product,quantity:Int=1):List<RfqDraftItemV130>{val rows=items().toMutableList();val i=rows.indexOfFirst{it.productId==product.id};if(i>=0)rows[i]=rows[i].copy(quantity=(rows[i].quantity+quantity).coerceIn(1,9999))else rows+=RfqDraftItemV130(product.id,product.sku,product.name,product.imageUrl,quantity.coerceIn(1,9999),product.priceRangeInclVat.ifBlank{product.currentInclVat.ifBlank{product.price}},product.permalink);save(rows);return rows}
    fun replace(rows:List<RfqDraftItemV130>){save(rows)}
    fun clear(){prefs.edit().remove("items").apply()}
}

object RfqApiV130 {
    private const val mobile=AutoIdApi.MOBILE
    private fun request(method:String,path:String,token:String?=null,body:JSONObject?=null):String{
        val c=(URI(mobile+path).toURL().openConnection() as HttpURLConnection).apply{requestMethod=method;connectTimeout=15000;readTimeout=30000;setRequestProperty("Accept","application/json");setRequestProperty("User-Agent","AutoID-Android/1.0.30");if(!token.isNullOrBlank())setRequestProperty("Authorization","Bearer $token");if(body!=null){doOutput=true;setRequestProperty("Content-Type","application/json; charset=UTF-8");outputStream.use{it.write(body.toString().toByteArray(StandardCharsets.UTF_8))}}}
        val status=c.responseCode;val text=(if(status in 200..299)c.inputStream else c.errorStream)?.bufferedReader()?.use{it.readText()}.orEmpty();if(status !in 200..299){val msg=runCatching{val o=JSONObject(text);o.optString("message").ifBlank{o.optString("code")}}.getOrDefault("").ifBlank{"HTTP $status"};throw ro.autoid.app.data.AutoIdHttpExceptionV129(status,msg)};return text
    }
    private fun requester(o:JSONObject)=RfqRequesterV130(o.optString("first_name"),o.optString("last_name"),o.optString("email"),o.optString("phone"),o.optString("company"),o.optString("vat"))
    private fun summary(o:JSONObject)=RfqSummaryV130(o.optLong("id"),o.optString("reference"),o.optString("status"),o.optString("status_label"),o.optString("created_at"),o.optDouble("estimated_value"),o.optString("currency","RON"),o.optInt("item_count"))
    private fun detail(o:JSONObject):RfqDetailV130{
        val la=o.optJSONArray("items")?:JSONArray();val lines=(0 until la.length()).mapNotNull{i->la.optJSONObject(i)?.let{RfqLineV130(it.optLong("product_id"),it.optString("sku"),it.optString("name"),it.optInt("quantity",1),it.optString("image").ifBlank{null},it.optString("url"),it.optDouble("line_value"))}}
        val ta=o.optJSONArray("timeline")?:JSONArray();val timeline=(0 until ta.length()).mapNotNull{i->ta.optJSONObject(i)?.let{RfqTimelineV130(it.optString("key"),it.optString("label"),it.optString("at"))}}
        val da=o.optJSONArray("documents")?:JSONArray();val docs=(0 until da.length()).mapNotNull{i->da.optJSONObject(i)?.let{RfqDocumentV130(it.optString("kind"),it.optString("label"),it.optString("sent_at"))}}
        val pa=o.optJSONArray("payments")?:JSONArray();val payments=(0 until pa.length()).mapNotNull{i->pa.optJSONObject(i)?.let{p->val ia=p.optJSONArray("ibans")?:JSONArray();RfqPaymentV130(p.optString("type"),p.optString("label"),p.optString("reference"),p.optString("beneficiary"),p.optString("registration"),p.optString("vat"),p.optString("address"),(0 until ia.length()).mapNotNull{j->ia.optJSONObject(j)?.let{RfqIbanV130(it.optString("iban"),it.optString("bank"))}},p.optString("url"))}}
        return RfqDetailV130(o.optLong("id"),o.optString("reference"),o.optString("status"),o.optString("status_label"),o.optString("created_at"),o.optDouble("estimated_value"),o.optString("currency","RON"),lines,requester(o.optJSONObject("requester")?:JSONObject()),o.optString("note"),timeline,docs,payments,o.optBoolean("can_accept"),o.optBoolean("can_reject"))
    }
    fun create(token:String?,rows:List<RfqDraftItemV130>,who:RfqRequesterV130,note:String):RfqDetailV130{val a=JSONArray();rows.forEach{a.put(JSONObject().put("product_id",it.productId).put("quantity",it.quantity))};val b=JSONObject().put("items",a).put("first_name",who.firstName).put("last_name",who.lastName).put("email",who.email).put("phone",who.phone).put("company",who.company).put("vat",who.vat).put("note",note);return detail(JSONObject(request("POST","/rfqs",token,b)))}
    fun list(token:String,page:Int=1):RfqPageV130{val o=JSONObject(request("GET","/me/rfqs?page=$page&per_page=10",token));val a=o.optJSONArray("items")?:JSONArray();return RfqPageV130((0 until a.length()).mapNotNull{a.optJSONObject(it)?.let(::summary)},o.optInt("page",page),o.optInt("pages",1),o.optInt("total"))}
    fun detail(token:String,id:Long)=detail(JSONObject(request("GET","/me/rfqs/$id",token)))
    fun action(token:String,id:Long,action:String)=detail(JSONObject(request("POST","/me/rfqs/$id/action",token,JSONObject().put("action",action))))
    fun download(context:Context,token:String,id:Long,kind:String):Uri{
        val c=(URI("$mobile/me/rfqs/$id/documents/$kind").toURL().openConnection() as HttpURLConnection).apply{requestMethod="GET";connectTimeout=15000;readTimeout=45000;setRequestProperty("Authorization","Bearer $token");setRequestProperty("Accept","application/pdf")};val status=c.responseCode;if(status !in 200..299)throw IllegalStateException("Documentul nu este disponibil (HTTP $status).");val dir=File(context.cacheDir,"rfq-documents").also{it.mkdirs()};val file=File(dir,"RFQ-$id-$kind.pdf");c.inputStream.use{input->file.outputStream().use{input.copyTo(it)}};return FileProvider.getUriForFile(context,"${context.packageName}.files",file)
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable fun RfqDraftScreenV130(api:AutoIdApi,session:SessionStore,rows:List<RfqDraftItemV130>,onRows:(List<RfqDraftItemV130>)->Unit,onBack:()->Unit,onOpenProduct:(Long)->Unit,onSuccess:()->Unit){
    val scope=rememberCoroutineScope();var who by remember{mutableStateOf(RfqRequesterV130(email=session.customerEmail))};var note by remember{mutableStateOf("")};var busy by remember{mutableStateOf(false)};var error by remember{mutableStateOf("")};var sent by remember{mutableStateOf<RfqDetailV130?>(null)}
    LaunchedEffect(session.accessToken){val t=session.accessToken;if(t!=null)runCatching{withContext(Dispatchers.IO){api.accountProfile(t) to api.accountAddresses(t)}}.onSuccess{(p,a)->who=RfqRequesterV130(p.firstName,p.lastName,p.email,a.billing.phone,a.billing.company,a.vatNumber)}}
    sent?.let{d->Scaffold(containerColor=RfqSoft,topBar={CenterAlignedTopAppBar(title={Text("Cerere înregistrată")},navigationIcon={IconButton(onClick=onBack){Icon(Icons.Default.Close,"Închide")}})}){pad->Column(Modifier.padding(pad).fillMaxSize().padding(20.dp),horizontalAlignment=Alignment.CenterHorizontally,verticalArrangement=Arrangement.spacedBy(14.dp)){Surface(shape=RoundedCornerShape(50),color=Color(0xFFE7F8F1)){Icon(Icons.Default.Check, null,Modifier.padding(18.dp).size(36.dp),tint=RfqGood)};Text("Mulțumim!",fontSize=28.sp,fontWeight=FontWeight.ExtraBold,color=RfqInk);Text("Cererea ta a fost salvată în sistemul AutoID.",color=RfqMuted);RfqKeyValue("Referință",d.reference);RfqKeyValue("Status",d.statusLabel);RfqKeyValue("Valoare estimată",if(d.value>0)"%.2f %s".format(d.value,d.currency) else "Se calculează în ofertă");Button(onClick=onBack,modifier=Modifier.fillMaxWidth().height(48.dp),shape=RoundedCornerShape(8.dp)){Text("Continuă cumpărăturile")}}};return}
    Scaffold(containerColor=RfqSoft,topBar={CenterAlignedTopAppBar(title={Column(horizontalAlignment=Alignment.CenterHorizontally){Text("Cerere de ofertă",fontWeight=FontWeight.ExtraBold);Text("${rows.sumOf{it.quantity}} produse",fontSize=11.sp,color=RfqMuted)}},navigationIcon={IconButton(onClick=onBack){Icon(Icons.Default.ArrowBack,"Înapoi")}})}){pad->LazyColumn(Modifier.padding(pad).fillMaxSize(),contentPadding=PaddingValues(14.dp),verticalArrangement=Arrangement.spacedBy(12.dp)){
        item{RfqSection("Produse solicitate"){if(rows.isEmpty())Text("Nu ai produse în cerere.",color=RfqMuted) else rows.forEach{line->Row(Modifier.fillMaxWidth().padding(vertical=7.dp),verticalAlignment=Alignment.CenterVertically){AsyncImage(line.image,line.name,Modifier.size(64.dp));Spacer(Modifier.width(10.dp));Column(Modifier.weight(1f)){Text(line.name,maxLines=2,overflow=TextOverflow.Ellipsis,fontWeight=FontWeight.Bold,color=RfqInk,fontSize=13.sp);Text("SKU: ${line.sku.ifBlank{"—"}}",fontSize=10.sp,color=RfqMuted);Text(line.price,color=AutoIdOrange,fontSize=11.sp,fontWeight=FontWeight.Bold);Row(verticalAlignment=Alignment.CenterVertically){IconButton(onClick={onRows(rows.map{if(it.productId==line.productId)it.copy(quantity=(it.quantity-1).coerceAtLeast(1))else it})},modifier=Modifier.size(40.dp)){Icon(Icons.Default.Remove,"Minus")};Text(line.quantity.toString(),fontWeight=FontWeight.Bold);IconButton(onClick={onRows(rows.map{if(it.productId==line.productId)it.copy(quantity=(it.quantity+1).coerceAtMost(9999))else it})},modifier=Modifier.size(40.dp)){Icon(Icons.Default.Add,"Plus")};TextButton(onClick={onOpenProduct(line.productId)}){Text("Produs",fontSize=10.sp)};IconButton(onClick={onRows(rows.filterNot{it.productId==line.productId})},modifier=Modifier.size(40.dp)){Icon(Icons.Default.Delete,"Șterge",tint=MaterialTheme.colorScheme.error)}}}}}}}
        item{RfqSection("Solicitant"){Row(horizontalArrangement=Arrangement.spacedBy(8.dp)){RfqField(who.firstName,{who=who.copy(firstName=it)},"Prenume *",Modifier.weight(1f));RfqField(who.lastName,{who=who.copy(lastName=it)},"Nume *",Modifier.weight(1f))};RfqField(who.email,{who=who.copy(email=it)},"Email *",keyboard=KeyboardType.Email);RfqField(who.phone,{who=who.copy(phone=it)},"Telefon *",keyboard=KeyboardType.Phone);RfqField(who.company,{who=who.copy(company=it)},"Companie (opțional)");RfqField(who.vat,{who=who.copy(vat=it)},"Cod TVA (opțional)")}}
        item{RfqSection("Detalii cerere"){OutlinedTextField(note,{if(it.length<=4000)note=it},label={Text("Notă comandă *")},supportingText={Text("Descrie configurația, termenul sau cerințele speciale.")},modifier=Modifier.fillMaxWidth(),minLines=4,shape=RoundedCornerShape(8.dp));if(error.isNotBlank())Text(error,color=MaterialTheme.colorScheme.error,fontSize=12.sp)}}
        item{Button(onClick={scope.launch{busy=true;error="";runCatching{withContext(Dispatchers.IO){RfqApiV130.create(session.accessToken,rows,who,note)}}.onSuccess{sent=it;onSuccess()}.onFailure{error=it.message?:"Cererea nu a putut fi trimisă."};busy=false}},enabled=!busy&&rows.isNotEmpty()&&who.firstName.isNotBlank()&&who.lastName.isNotBlank()&&who.email.contains("@")&&who.phone.isNotBlank()&&note.isNotBlank(),modifier=Modifier.fillMaxWidth().height(50.dp),shape=RoundedCornerShape(8.dp),colors=ButtonDefaults.buttonColors(containerColor=AutoIdOrange)){if(busy)CircularProgressIndicator(Modifier.size(20.dp),strokeWidth=2.dp,color=Color.White)else Text("Trimite cererea de ofertă",fontWeight=FontWeight.ExtraBold)}}
    }}
}

@Composable private fun RfqField(value:String,onValue:(String)->Unit,label:String,modifier:Modifier=Modifier.fillMaxWidth(),keyboard:KeyboardType=KeyboardType.Text){OutlinedTextField(value,onValue,label={Text(label)},modifier=modifier,keyboardOptions=KeyboardOptions(keyboardType=keyboard),singleLine=true,shape=RoundedCornerShape(8.dp))}
@Composable private fun RfqSection(title:String,content:@Composable ColumnScope.()->Unit){Surface(shape=RoundedCornerShape(8.dp),color=Color.White,shadowElevation=1.dp,modifier=Modifier.fillMaxWidth()){Column(Modifier.padding(15.dp),verticalArrangement=Arrangement.spacedBy(8.dp)){Text(title,fontWeight=FontWeight.ExtraBold,color=RfqInk,fontSize=16.sp);HorizontalDivider(color=RfqBorder);content()}}}
@Composable private fun RfqKeyValue(label:String,value:String){Surface(shape=RoundedCornerShape(8.dp),color=Color.White,modifier=Modifier.fillMaxWidth()){Row(Modifier.padding(14.dp)){Text(label,Modifier.weight(1f),color=RfqMuted);Text(value,fontWeight=FontWeight.ExtraBold,color=RfqInk)}}}

@OptIn(ExperimentalMaterial3Api::class)
@Composable fun RfqAccountScreenV130(session:SessionStore,onBack:()->Unit,onOpenProduct:(Long)->Unit,initialId:Long=0){
    val token=session.accessToken;if(token==null){LaunchedEffect(Unit){onBack()};return};val context=LocalContext.current;val clipboard=LocalClipboardManager.current;val scope=rememberCoroutineScope();var page by remember{mutableIntStateOf(1)};var pages by remember{mutableIntStateOf(1)};var list by remember{mutableStateOf<List<RfqSummaryV130>>(emptyList())};var selected by remember{mutableStateOf<RfqDetailV130?>(null)};var busy by remember{mutableStateOf(false)};var error by remember{mutableStateOf("")};var confirm by remember{mutableStateOf<String?>(null)}
    fun loadList(reset:Boolean=false){scope.launch{busy=true;error="";val target=if(reset)1 else page;runCatching{withContext(Dispatchers.IO){RfqApiV130.list(token,target)}}.onSuccess{list=if(target==1)it.items else list+it.items;page=it.page;pages=it.pages}.onFailure{error=it.message?:"RFQ-urile nu pot fi încărcate."};busy=false}}
    fun loadDetail(id:Long){scope.launch{busy=true;error="";runCatching{withContext(Dispatchers.IO){RfqApiV130.detail(token,id)}}.onSuccess{selected=it}.onFailure{error=it.message?:"Cererea nu poate fi încărcată."};busy=false}}
    LaunchedEffect(initialId){if(initialId>0)loadDetail(initialId)else loadList(true)}
    confirm?.let{action->AlertDialog(onDismissRequest={confirm=null},title={Text(if(action=="accept")"Acceptă oferta?" else "Refuză oferta?")},text={Text("Răspunsul va fi înregistrat imediat în RFQ.")},confirmButton={Button(onClick={val id=selected?.id?:return@Button;confirm=null;scope.launch{busy=true;runCatching{withContext(Dispatchers.IO){RfqApiV130.action(token,id,action)}}.onSuccess{selected=it}.onFailure{error=it.message?:"Răspunsul nu a putut fi salvat."};busy=false}}){Text("Confirmă")}},dismissButton={TextButton(onClick={confirm=null}){Text("Anulează")}})}
    Scaffold(containerColor=RfqSoft,topBar={CenterAlignedTopAppBar(title={Text(selected?.reference?:"Cererile mele",fontWeight=FontWeight.ExtraBold)},navigationIcon={IconButton(onClick={if(selected!=null){selected=null;loadList(true)}else onBack()}){Icon(Icons.Default.ArrowBack,"Înapoi")}},actions={IconButton(onClick={if(selected!=null)loadDetail(selected!!.id)else loadList(true)}){Icon(Icons.Default.Refresh,"Reîncarcă")}})}){pad->
        if(selected==null)LazyColumn(Modifier.padding(pad).fillMaxSize(),contentPadding=PaddingValues(14.dp),verticalArrangement=Arrangement.spacedBy(10.dp)){if(busy&&list.isEmpty())items(4){Surface(Modifier.fillMaxWidth().height(94.dp),RoundedCornerShape(8.dp),color=Color(0xFFE9EDF2)){} };if(error.isNotBlank())item{RfqError(error){loadList(true)}};if(!busy&&error.isBlank()&&list.isEmpty())item{RfqSection("Nicio cerere"){Text("RFQ-urile trimise din aplicație vor apărea aici.",color=RfqMuted)}};items(list,key={it.id}){r->Surface(Modifier.fillMaxWidth().clickable{loadDetail(r.id)},RoundedCornerShape(8.dp),color=Color.White,shadowElevation=1.dp){Row(Modifier.padding(15.dp),verticalAlignment=Alignment.CenterVertically){Column(Modifier.weight(1f)){Text(r.reference,fontWeight=FontWeight.ExtraBold,color=RfqInk);Text(r.statusLabel,fontSize=11.sp,color=AutoIdOrange,fontWeight=FontWeight.Bold);Text("${r.itemCount} produse · ${r.createdAt.take(10)}",fontSize=10.sp,color=RfqMuted)};if(r.value>0)Text("%.2f %s".format(r.value,r.currency),fontWeight=FontWeight.Bold,color=RfqInk,fontSize=11.sp);Icon(Icons.Default.ChevronRight,null,tint=RfqMuted)}}};if(page<pages)item{OutlinedButton(onClick={page++;loadList()},enabled=!busy,modifier=Modifier.fillMaxWidth().height(48.dp)){Text("Încarcă mai multe")}}}
        else RfqDetailContentV130(Modifier.padding(pad),selected!!,busy,error,onOpenProduct,{confirm=it},{doc->scope.launch{busy=true;runCatching{withContext(Dispatchers.IO){RfqApiV130.download(context,token,selected!!.id,doc.kind)}}.onSuccess{uri->context.startActivity(Intent(Intent.ACTION_VIEW).setDataAndType(uri,"application/pdf").addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION))}.onFailure{error=it.message?:"PDF-ul nu poate fi deschis."};busy=false}},{url->CustomTabsIntent.Builder().build().launchUrl(context,Uri.parse(url))},{value->clipboard.setText(AnnotatedString(value))})
    }
}

@Composable private fun RfqError(message:String,retry:()->Unit){Surface(shape=RoundedCornerShape(8.dp),color=Color(0xFFFFF1F0)){Column(Modifier.fillMaxWidth().padding(14.dp)){Text(message,color=MaterialTheme.colorScheme.error);TextButton(onClick=retry){Text("Încearcă din nou")}}}}

@Composable private fun RfqDetailContentV130(modifier:Modifier,d:RfqDetailV130,busy:Boolean,error:String,onOpenProduct:(Long)->Unit,onDecision:(String)->Unit,onDocument:(RfqDocumentV130)->Unit,onCard:(String)->Unit,onCopy:(String)->Unit){LazyColumn(modifier.fillMaxSize(),contentPadding=PaddingValues(14.dp),verticalArrangement=Arrangement.spacedBy(12.dp)){item{Surface(shape=RoundedCornerShape(8.dp),color=RfqInk){Column(Modifier.fillMaxWidth().padding(18.dp)){Text(d.reference,color=Color.White,fontWeight=FontWeight.ExtraBold,fontSize=21.sp);Text(d.statusLabel,color=Color(0xFFFFB38A),fontWeight=FontWeight.Bold);Text(if(d.value>0)"Valoare estimată: %.2f %s".format(d.value,d.currency) else "Valoarea se stabilește în ofertă",color=Color(0xFFD0D5DD),fontSize=11.sp)}}};if(busy)item{LinearProgressIndicator(Modifier.fillMaxWidth())};if(error.isNotBlank())item{Text(error,color=MaterialTheme.colorScheme.error)};item{RfqSection("Flux RFQ"){d.timeline.forEachIndexed{i,e->Row{Surface(shape=RoundedCornerShape(50),color=if(i==d.timeline.lastIndex)AutoIdOrange else RfqGood,modifier=Modifier.size(22.dp)){Box(contentAlignment=Alignment.Center){Text((i+1).toString(),color=Color.White,fontSize=9.sp)}};Spacer(Modifier.width(9.dp));Column{Text(e.label,fontWeight=FontWeight.Bold,color=RfqInk,fontSize=12.sp);if(e.at.isNotBlank())Text(e.at.replace('T',' ').take(16),fontSize=9.sp,color=RfqMuted)}}}}};item{RfqSection("Produse"){d.lines.forEach{line->Row(Modifier.fillMaxWidth().clickable{onOpenProduct(line.productId)}.padding(vertical=6.dp),verticalAlignment=Alignment.CenterVertically){AsyncImage(line.image,line.name,Modifier.size(52.dp));Spacer(Modifier.width(9.dp));Column(Modifier.weight(1f)){Text(line.name,fontWeight=FontWeight.Bold,color=RfqInk,fontSize=12.sp,maxLines=2);Text("${line.quantity} × · SKU ${line.sku.ifBlank{"—"}}",fontSize=10.sp,color=RfqMuted)};Icon(Icons.Default.ChevronRight,null,tint=RfqMuted)}}}};item{RfqSection("Solicitant și notă"){Text("${d.requester.firstName} ${d.requester.lastName}",fontWeight=FontWeight.Bold);Text(d.requester.email,color=RfqMuted,fontSize=11.sp);Text(d.requester.phone,color=RfqMuted,fontSize=11.sp);if(d.requester.company.isNotBlank())Text("${d.requester.company} · ${d.requester.vat}",color=RfqMuted,fontSize=11.sp);HorizontalDivider(color=RfqBorder);Text(d.note,color=RfqInk)}};if(d.documents.isNotEmpty())item{RfqSection("Documente comerciale"){d.documents.forEach{doc->OutlinedButton(onClick={onDocument(doc)},modifier=Modifier.fillMaxWidth().height(48.dp),shape=RoundedCornerShape(8.dp)){Icon(Icons.Default.PictureAsPdf,null);Spacer(Modifier.width(8.dp));Text("Deschide ${doc.label}")}}}};if(d.canAccept||d.canReject)item{RfqSection("Răspuns ofertă"){if(d.canAccept)Button(onClick={onDecision("accept")},modifier=Modifier.fillMaxWidth().height(48.dp),colors=ButtonDefaults.buttonColors(containerColor=RfqGood),shape=RoundedCornerShape(8.dp)){Text("Acceptă oferta")};if(d.canReject)OutlinedButton(onClick={onDecision("reject")},modifier=Modifier.fillMaxWidth().height(48.dp),shape=RoundedCornerShape(8.dp)){Text("Refuză oferta",color=MaterialTheme.colorScheme.error)}}};if(d.payments.isNotEmpty())item{RfqSection("Opțiuni de plată"){d.payments.forEach{p->Text(p.label,fontWeight=FontWeight.ExtraBold,color=RfqInk);if(p.type=="bank_transfer"){Text("${p.beneficiary} · ${p.vat}",fontSize=11.sp,color=RfqMuted);Text(p.address,fontSize=10.sp,color=RfqMuted);p.ibans.forEach{iban->Surface(shape=RoundedCornerShape(8.dp),color=RfqSoft){Row(Modifier.fillMaxWidth().padding(10.dp),verticalAlignment=Alignment.CenterVertically){Column(Modifier.weight(1f)){Text(iban.iban,fontWeight=FontWeight.Bold,fontSize=11.sp);Text(iban.bank,fontSize=9.sp,color=RfqMuted)};IconButton(onClick={onCopy(iban.iban)}){Icon(Icons.Default.ContentCopy,"Copiază IBAN")}}}};Row(verticalAlignment=Alignment.CenterVertically){Text("Referință: ${p.reference}",Modifier.weight(1f),fontWeight=FontWeight.Bold,fontSize=11.sp);IconButton(onClick={onCopy(p.reference)}){Icon(Icons.Default.ContentCopy,"Copiază referința")}}}else if(p.url.isNotBlank())Button(onClick={onCard(p.url)},modifier=Modifier.fillMaxWidth().height(48.dp),colors=ButtonDefaults.buttonColors(containerColor=AutoIdOrange),shape=RoundedCornerShape(8.dp)){Text("Plătește securizat cu cardul")}}}}}
}
