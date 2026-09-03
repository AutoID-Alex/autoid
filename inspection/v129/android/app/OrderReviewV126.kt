package ro.autoid.app

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.OpenInNew
import androidx.compose.material.icons.filled.Star
import androidx.compose.material.icons.filled.StarBorder
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalUriHandler
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import coil.compose.AsyncImage
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import ro.autoid.app.data.*
import ro.autoid.app.ui.theme.AutoIdOrange

private const val GOOGLE_REVIEW_V126="https://share.google/9DGE1LfVVLWj7gjjP"

@Composable fun OrderReviewScreenV126(api:AutoIdApi,session:SessionStore,orderId:Long,onBack:()->Unit){var detail by remember{mutableStateOf<OrderDetail?>(null)};var error by remember{mutableStateOf("")};var selected by remember{mutableStateOf<OrderLineItem?>(null)};var rating by remember{mutableIntStateOf(5)};var text by remember{mutableStateOf("")};var busy by remember{mutableStateOf(false)};var msg by remember{mutableStateOf("")};val uri=LocalUriHandler.current
LaunchedEffect(orderId){val token=session.accessToken;if(token==null){error="Autentifică-te pentru a revizui această comandă."}else runCatching{withContext(Dispatchers.IO){api.orderDetail(token,orderId)}}.onSuccess{detail=it}.onFailure{error=it.message?:"Comanda nu a putut fi încărcată."}}
LaunchedEffect(busy){if(busy){val p=selected;val token=session.accessToken;if(p!=null&&token!=null)runCatching{withContext(Dispatchers.IO){api.submitProductReview(p.productId,rating,text,token=token)}}.onSuccess{msg="Mulțumim! Recenzia pentru ${p.name} a fost trimisă.";text="";selected=null}.onFailure{msg=it.message?:"Recenzia nu a putut fi trimisă."};busy=false}}
LazyColumn(Modifier.fillMaxSize().padding(16.dp).statusBarsPadding(),verticalArrangement=Arrangement.spacedBy(12.dp),contentPadding=PaddingValues(bottom=30.dp)){item{Row{IconButton(onClick=onBack){Icon(Icons.Default.ArrowBack,"Înapoi")};Column(Modifier.weight(1f)){Text("Revizuiește comanda",fontSize=23.sp,fontWeight=FontWeight.ExtraBold);Text("#${detail?.number?:orderId}",fontSize=12.sp,color=Color(0xFF667085))}}};if(error.isNotBlank())item{Text(error,color=MaterialTheme.colorScheme.error)};detail?.let{d->item{ElevatedCard(shape=androidx.compose.foundation.shape.RoundedCornerShape(14.dp)){Column(Modifier.padding(15.dp),verticalArrangement=Arrangement.spacedBy(7.dp)){Text("Cum a fost experiența cu AutoID?",fontSize=18.sp,fontWeight=FontWeight.ExtraBold);Text("Review-ul Google ne ajută foarte mult. Poți lăsa separat și recenzii produselor comandate.",fontSize=12.sp,color=Color(0xFF667085));Button(onClick={uri.openUri(GOOGLE_REVIEW_V126)},modifier=Modifier.fillMaxWidth(),shape=androidx.compose.foundation.shape.RoundedCornerShape(10.dp)){Icon(Icons.Default.OpenInNew,null);Spacer(Modifier.width(7.dp));Text("Lasă review pe Google",fontWeight=FontWeight.ExtraBold)}}}};item{Text("Produsele comandate",fontSize=18.sp,fontWeight=FontWeight.ExtraBold)};d.items.filter{it.productId>0}.forEach{line->item{OutlinedCard(shape=androidx.compose.foundation.shape.RoundedCornerShape(12.dp),onClick={selected=line;rating=5;text=""}){Row(Modifier.fillMaxWidth().padding(11.dp)){AsyncImage(line.imageUrl,line.name,Modifier.size(58.dp));Spacer(Modifier.width(10.dp));Column(Modifier.weight(1f)){Text(line.name,fontSize=12.sp,fontWeight=FontWeight.Bold);Text("Cantitate ${line.quantity}",fontSize=10.sp,color=Color(0xFF667085));Text("Scrie o recenzie →",fontSize=11.sp,fontWeight=FontWeight.Bold,color=AutoIdOrange)}}}}};selected?.let{p->item{ElevatedCard(shape=androidx.compose.foundation.shape.RoundedCornerShape(14.dp)){Column(Modifier.padding(14.dp),verticalArrangement=Arrangement.spacedBy(8.dp)){Text("Recenzie · ${p.name}",fontWeight=FontWeight.ExtraBold);Row{(1..5).forEach{i->IconButton(onClick={rating=i},modifier=Modifier.size(36.dp)){Icon(if(i<=rating)Icons.Default.Star else Icons.Default.StarBorder,"$i stele",tint=Color(0xFFFDB022))}}};OutlinedTextField(text,{text=it},label={Text("Recenzia ta")},modifier=Modifier.fillMaxWidth(),minLines=3);Button(onClick={busy=true},enabled=!busy&&text.trim().length>=3,modifier=Modifier.fillMaxWidth(),shape=androidx.compose.foundation.shape.RoundedCornerShape(10.dp)){Text(if(busy)"Se trimite..." else "Trimite recenzia")}}}}};if(msg.isNotBlank())item{Text(msg,color=Color(0xFF16803A),fontSize=11.sp)}}}
}
