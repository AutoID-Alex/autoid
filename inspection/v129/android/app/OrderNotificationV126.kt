package ro.autoid.app

import android.Manifest
import android.app.*
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import androidx.work.*
import ro.autoid.app.data.AutoIdApi
import ro.autoid.app.data.SessionStore
import java.util.concurrent.TimeUnit

object OrderNotificationV126 {
    const val CHANNEL="autoid_orders_v126"
    fun schedule(context:Context){ensureChannel(context);val req=PeriodicWorkRequestBuilder<OrderNotificationWorkerV126>(15,TimeUnit.MINUTES).setConstraints(Constraints.Builder().setRequiredNetworkType(NetworkType.CONNECTED).build()).build();WorkManager.getInstance(context).enqueueUniquePeriodicWork("autoid-order-watch-v126",ExistingPeriodicWorkPolicy.UPDATE,req)}
    fun syncNow(context:Context){ensureChannel(context);WorkManager.getInstance(context).enqueueUniqueWork("autoid-order-sync-now-v126",ExistingWorkPolicy.REPLACE,OneTimeWorkRequestBuilder<OrderNotificationWorkerV126>().setConstraints(Constraints.Builder().setRequiredNetworkType(NetworkType.CONNECTED).build()).build())}
    fun ensureChannel(context:Context){if(Build.VERSION.SDK_INT>=26)(context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager).createNotificationChannel(NotificationChannel(CHANNEL,"Comenzi AutoID",NotificationManager.IMPORTANCE_DEFAULT).apply{description="Actualizări despre status, AWB și invitații de review"})}
    fun notify(context:Context,id:Int,title:String,text:String,reviewOrderId:Long=0){if(Build.VERSION.SDK_INT>=33&&context.checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)!=PackageManager.PERMISSION_GRANTED)return;val intent=Intent(context,MainActivity::class.java).apply{flags=Intent.FLAG_ACTIVITY_CLEAR_TOP or Intent.FLAG_ACTIVITY_SINGLE_TOP;if(reviewOrderId>0)putExtra("review_order_id",reviewOrderId)};val pi=PendingIntent.getActivity(context,id,intent,PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE);NotificationManagerCompat.from(context).notify(id,NotificationCompat.Builder(context,CHANNEL).setSmallIcon(R.drawable.ic_autoid_notification_v127).setContentTitle(title).setContentText(text).setStyle(NotificationCompat.BigTextStyle().bigText(text)).setAutoCancel(true).setContentIntent(pi).build())}
}

class OrderNotificationWorkerV126(appContext:Context,params:WorkerParameters):Worker(appContext,params){override fun doWork():Result{
    if(!PrivacyConsentStoreV128(applicationContext).get().transactionalNotifications)return Result.success()
    val session=SessionStore(applicationContext);val token=session.accessToken?:return Result.success()
    val orders=runCatching{AutoIdApi().orders(token)}.getOrElse{return Result.retry()}
    val prefs=applicationContext.getSharedPreferences("autoid_order_watch_v126",Context.MODE_PRIVATE);val initialized=prefs.getBoolean("initialized",false);val edit=prefs.edit();val now=System.currentTimeMillis()
    for(o in orders){
        val base="order_${o.id}_";val oldStatus=prefs.getString(base+"status",null);val oldTracking=prefs.getString(base+"tracking","")?:"";val seen=prefs.getBoolean(base+"seen",false)
        val created=runCatching{java.time.OffsetDateTime.parse(o.dateCreated).toInstant().toEpochMilli()}.getOrDefault(0L);val recent=created>0L && now-created<48L*60L*60L*1000L
        val shouldNotifyAwb=o.trackingNumber.isNotBlank()&&oldTracking.isBlank()&&(initialized||seen||recent)
        if(shouldNotifyAwb){OrderNotificationV126.notify(applicationContext,(o.id%Int.MAX_VALUE).toInt(),"Comanda #${o.number} a plecat din depozitul AutoID","AWB ${o.trackingNumber} a fost generat. Urmărește livrarea.")}
        if((initialized||seen)&&o.statusCode=="completed"&&oldStatus!="completed"&&o.reviewConsent){OrderNotificationV126.notify(applicationContext,((o.id+100000)%Int.MAX_VALUE).toInt(),"Revizuiește comanda #${o.number}","Cum a fost experiența cu AutoID? Lasă-ne un review pe Google și, dacă dorești, recenzii produselor comandate.",o.id)}else if((initialized||seen)&&oldStatus!=null&&oldStatus!=o.statusCode&&o.statusCode!="completed"&&o.trackingNumber.isBlank()){OrderNotificationV126.notify(applicationContext,((o.id+200000)%Int.MAX_VALUE).toInt(),"Comanda #${o.number} · ${o.status}","Statusul comenzii tale AutoID a fost actualizat.")}
        edit.putBoolean(base+"seen",true).putString(base+"status",o.statusCode).putString(base+"tracking",o.trackingNumber)
    }
    edit.putBoolean("initialized",true).apply();return Result.success()
}}
