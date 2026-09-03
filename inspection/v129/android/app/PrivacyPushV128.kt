package ro.autoid.app

import android.app.Application
import android.content.Context
import android.content.Intent
import android.graphics.BitmapFactory
import android.net.Uri
import android.os.Build
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import com.google.firebase.FirebaseApp
import com.google.firebase.FirebaseOptions
import com.google.firebase.messaging.FirebaseMessaging
import com.google.firebase.messaging.FirebaseMessagingService
import com.google.firebase.messaging.RemoteMessage
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import ro.autoid.app.data.AutoIdApi
import ro.autoid.app.data.PrivacyPrefsV128
import ro.autoid.app.data.PushConfigV128
import ro.autoid.app.data.SessionStore

class AutoIdApplicationV128:Application(){override fun onCreate(){super.onCreate();FirebaseBootstrapV128.initializeFromCache(this)}}

class PrivacyConsentStoreV128(context:Context){
    private val p=context.applicationContext.getSharedPreferences("autoid_privacy_v128",Context.MODE_PRIVATE)
    fun get()=PrivacyPrefsV128(p.getBoolean("transactional",true),p.getBoolean("analytics",false),p.getBoolean("personalization",false),p.getBoolean("marketing",false))
    fun save(v:PrivacyPrefsV128){p.edit().putBoolean("transactional",v.transactionalNotifications).putBoolean("analytics",v.analytics).putBoolean("personalization",v.personalization).putBoolean("marketing",v.marketing).putBoolean("decided",true).apply()}
    fun hasDecision()=p.getBoolean("decided",false)
}

object FirebaseBootstrapV128{
    private const val PREF="autoid_firebase_v128"
    private fun cache(context:Context,c:PushConfigV128){context.getSharedPreferences(PREF,Context.MODE_PRIVATE).edit().putBoolean("enabled",c.enabled).putString("project",c.projectId).putString("app",c.applicationId).putString("api",c.apiKey).putString("sender",c.senderId).apply()}
    private fun cached(context:Context):PushConfigV128{val p=context.getSharedPreferences(PREF,Context.MODE_PRIVATE);return PushConfigV128(p.getBoolean("enabled",false),p.getString("project","")?:"",p.getString("app","")?:"",p.getString("api","")?:"",p.getString("sender","")?:"")}
    private fun valid(c:PushConfigV128)=c.enabled&&c.projectId.isNotBlank()&&c.applicationId.isNotBlank()&&c.apiKey.isNotBlank()&&c.senderId.isNotBlank()
    fun initializeFromCache(context:Context):Boolean=initialize(context,cached(context))
    private fun initialize(context:Context,c:PushConfigV128):Boolean{
        if(!valid(c))return false
        if(FirebaseApp.getApps(context).isEmpty()) FirebaseApp.initializeApp(context,FirebaseOptions.Builder().setProjectId(c.projectId).setApplicationId(c.applicationId).setApiKey(c.apiKey).setGcmSenderId(c.senderId).build())
        return FirebaseApp.getApps(context).isNotEmpty()
    }
    fun refreshAndRegister(context:Context,api:AutoIdApi,session:SessionStore){CoroutineScope(Dispatchers.IO).launch{runCatching{api.pushConfigV128()}.onSuccess{c->cache(context,c);if(initialize(context,c)){val prefs=PrivacyConsentStoreV128(context).get();FirebaseMessaging.getInstance().isAutoInitEnabled=prefs.transactionalNotifications||prefs.marketing;if(prefs.transactionalNotifications||prefs.marketing)FirebaseMessaging.getInstance().token.addOnSuccessListener{registerToken(context,api,session,it,prefs)}}}}}
    fun registerToken(context:Context,api:AutoIdApi,session:SessionStore,fcm:String,prefs:PrivacyPrefsV128=PrivacyConsentStoreV128(context).get()){if(fcm.isBlank())return;context.getSharedPreferences(PREF,Context.MODE_PRIVATE).edit().putString("token",fcm).apply();val auth=session.accessToken?:return;CoroutineScope(Dispatchers.IO).launch{runCatching{api.registerPushV128(auth,fcm,prefs)}}}
    fun currentToken(context:Context)=context.getSharedPreferences(PREF,Context.MODE_PRIVATE).getString("token","")?:""
    fun applyConsent(context:Context,api:AutoIdApi,session:SessionStore,prefs:PrivacyPrefsV128){PrivacyConsentStoreV128(context).save(prefs);val fcm=currentToken(context);val auth=session.accessToken;if(prefs.transactionalNotifications||prefs.marketing){if(initializeFromCache(context)){FirebaseMessaging.getInstance().isAutoInitEnabled=true;FirebaseMessaging.getInstance().token.addOnSuccessListener{registerToken(context,api,session,it,prefs)}}}else{runCatching{if(FirebaseApp.getApps(context).isNotEmpty())FirebaseMessaging.getInstance().isAutoInitEnabled=false};if(auth!=null&&fcm.isNotBlank())CoroutineScope(Dispatchers.IO).launch{runCatching{api.unregisterPushV128(auth,fcm)}}}}
    fun unregisterForLogout(context:Context,api:AutoIdApi,auth:String){val fcm=currentToken(context);if(fcm.isNotBlank())CoroutineScope(Dispatchers.IO).launch{runCatching{api.unregisterPushV128(auth,fcm)}}}
}

class AutoIdMessagingServiceV128:FirebaseMessagingService(){
    override fun onNewToken(token:String){super.onNewToken(token);FirebaseBootstrapV128.registerToken(this,AutoIdApi(),SessionStore(this),token)}
    override fun onMessageReceived(message:RemoteMessage){super.onMessageReceived(message);val d=message.data;val type=d["type"]?:"order_status";val prefs=PrivacyConsentStoreV128(this).get();if(type.startsWith("marketing")&&!prefs.marketing)return;if(!type.startsWith("marketing")&&!prefs.transactionalNotifications)return;PushNotificationV128.markOrderState(this,d);PushNotificationV128.show(this,d)}
}

object PushNotificationV128{
    fun markOrderState(context:Context,d:Map<String,String>){val id=d["order_id"]?.toLongOrNull()?:return;val p=context.getSharedPreferences("autoid_order_watch_v126",Context.MODE_PRIVATE);val e=p.edit().putBoolean("initialized",true).putBoolean("order_${id}_seen",true);d["tracking_number"]?.takeIf{it.isNotBlank()}?.let{e.putString("order_${id}_tracking",it)};d["status"]?.takeIf{it.isNotBlank()}?.let{e.putString("order_${id}_status",it)};e.apply()}
    fun show(context:Context,d:Map<String,String>){
        OrderNotificationV126.ensureChannel(context)
        if(Build.VERSION.SDK_INT>=33&&context.checkSelfPermission(android.Manifest.permission.POST_NOTIFICATIONS)!=android.content.pm.PackageManager.PERMISSION_GRANTED)return
        val id=(d["notification_id"]?.toIntOrNull()?:System.currentTimeMillis().toInt()) and Int.MAX_VALUE
        val type=d["type"]?:"order_status";val orderId=d["order_id"]?.toLongOrNull()?:0L
        val title=d["title"]?:"AutoID";val body=d["body"]?:"Ai o actualizare nouă."
        val intent=when{
            type=="order_awb"&&!d["tracking_url"].isNullOrBlank()->Intent(Intent.ACTION_VIEW,Uri.parse(d["tracking_url"]))
            type=="order_review"&&orderId>0->Intent(context,MainActivity::class.java).putExtra("review_order_id",orderId)
            else->Intent(context,MainActivity::class.java)
        }.apply{addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP or Intent.FLAG_ACTIVITY_SINGLE_TOP)}
        val pi=android.app.PendingIntent.getActivity(context,id,intent,android.app.PendingIntent.FLAG_UPDATE_CURRENT or android.app.PendingIntent.FLAG_IMMUTABLE)
        val large=runCatching{BitmapFactory.decodeResource(context.resources,R.drawable.autoid_icon_v100)}.getOrNull()
        val b=NotificationCompat.Builder(context,OrderNotificationV126.CHANNEL).setSmallIcon(R.drawable.ic_autoid_notification_v127).setContentTitle(title).setContentText(body).setStyle(NotificationCompat.BigTextStyle().bigText(body)).setAutoCancel(true).setContentIntent(pi).setPriority(NotificationCompat.PRIORITY_HIGH)
        if(large!=null)b.setLargeIcon(large)
        NotificationManagerCompat.from(context).notify(id,b.build())
    }
}
