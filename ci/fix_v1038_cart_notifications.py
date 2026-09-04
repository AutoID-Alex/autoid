#!/usr/bin/env python3
"""RC7.3: fix active CartV114 top inset and ship persistent notification inbox."""
from pathlib import Path
import re, shutil

ROOT=Path(__file__).resolve().parents[1]
APP=ROOT/'android-v0.1/app/src/main/java/ro/autoid/app'
V100=APP/'V100Screens.kt'
V114=APP/'V114CommerceUx.kt'
ACCOUNT=APP/'V135AccountUx.kt'
PUSH=APP/'PrivacyPushV128.kt'
ORDER=APP/'OrderNotificationV126.kt'
GRADLE=ROOT/'android-v0.1/app/build.gradle.kts'
ASSET=ROOT/'ci/v138/NotificationInboxV138.kt'
TARGET=APP/'NotificationInboxV138.kt'

shutil.copyfile(ASSET,TARGET)

def function_block(text,needle):
    i=text.find(needle)
    if i<0: raise SystemExit(needle+' function missing')
    brace=text.find('{',i)
    if brace<0: raise SystemExit(needle+' opening brace missing')
    depth=0
    for j in range(brace,len(text)):
        if text[j]=='{': depth+=1
        elif text[j]=='}':
            depth-=1
            if depth==0:return i,j+1,text[i:j+1]
    raise SystemExit(needle+' closing brace missing')

# 1. Fix the actually routed cart implementation. RC7.2 only fixed CartV100,
# while AutoIdAppV100 routes V100Tab.Cart to CartV114.
v114=V114.read_text()
ci,cj,cart=function_block(v114,'fun CartV114')
cart_old='Column(Modifier.fillMaxSize().background(C114Soft).statusBarsPadding())'
cart_new='Column(Modifier.fillMaxSize().background(C114Soft))'
if cart_old not in cart: raise SystemExit('active CartV114 status inset anchor missing')
cart=cart.replace(cart_old,cart_new,1)
if '.statusBarsPadding()' in cart: raise SystemExit('CartV114 still has duplicate top inset after targeted fix')
v114=v114[:ci]+cart+v114[cj:]
V114.write_text(v114)

# 2. Persist every accepted FCM push before showing the Android system notification.
p=PUSH.read_text()
old='override fun onMessageReceived(message:RemoteMessage){super.onMessageReceived(message);val d=message.data;val type=d["type"]?:"order_status";val prefs=PrivacyConsentStoreV128(this).get();if(type.startsWith("marketing")&&!prefs.marketing)return;if(!type.startsWith("marketing")&&!prefs.transactionalNotifications)return;PushNotificationV128.markOrderState(this,d);PushNotificationV128.show(this,d)}'
new='override fun onMessageReceived(message:RemoteMessage){super.onMessageReceived(message);val d=message.data;val type=d["type"]?:"order_status";val prefs=PrivacyConsentStoreV128(this).get();if(type.startsWith("marketing")&&!prefs.marketing)return;if(!type.startsWith("marketing")&&!prefs.transactionalNotifications)return;NotificationInboxStoreV138(this).addPush(d,message.notification?.title,message.notification?.body);PushNotificationV128.markOrderState(this,d);PushNotificationV128.show(this,d)}'
if old not in p: raise SystemExit('FCM onMessageReceived anchor missing')
p=p.replace(old,new,1)
PUSH.write_text(p)

# 3. Persist locally generated order/AWB/review notifications too, with order id.
o=ORDER.read_text()
old_sig='fun notify(context:Context,id:Int,title:String,text:String,reviewOrderId:Long=0){if(Build.VERSION.SDK_INT>=33&&context.checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)!=PackageManager.PERMISSION_GRANTED)return;'
new_sig='fun notify(context:Context,id:Int,title:String,text:String,reviewOrderId:Long=0,orderId:Long=0){NotificationInboxStoreV138(context).addLocal("order",title,text,orderId=if(orderId>0)orderId else reviewOrderId,id="order-$id");if(Build.VERSION.SDK_INT>=33&&context.checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)!=PackageManager.PERMISSION_GRANTED)return;'
if old_sig not in o: raise SystemExit('OrderNotification notify signature anchor missing')
o=o.replace(old_sig,new_sig,1)

awb='OrderNotificationV126.notify(applicationContext,(o.id%Int.MAX_VALUE).toInt(),"Comanda #${o.number} a plecat din depozitul AutoID","AWB ${o.trackingNumber} a fost generat. Urmărește livrarea.")'
awb_new='OrderNotificationV126.notify(applicationContext,(o.id%Int.MAX_VALUE).toInt(),"Comanda #${o.number} a plecat din depozitul AutoID","AWB ${o.trackingNumber} a fost generat. Urmărește livrarea.",orderId=o.id)'
if awb not in o: raise SystemExit('AWB notification call anchor missing')
o=o.replace(awb,awb_new,1)

review='OrderNotificationV126.notify(applicationContext,((o.id+100000)%Int.MAX_VALUE).toInt(),"Revizuiește comanda #${o.number}","Cum a fost experiența cu AutoID? Lasă-ne un review pe Google și, dacă dorești, recenzii produselor comandate.",o.id)'
review_new='OrderNotificationV126.notify(applicationContext,((o.id+100000)%Int.MAX_VALUE).toInt(),"Revizuiește comanda #${o.number}","Cum a fost experiența cu AutoID? Lasă-ne un review pe Google și, dacă dorești, recenzii produselor comandate.",o.id,orderId=o.id)'
if review not in o: raise SystemExit('review notification call anchor missing')
o=o.replace(review,review_new,1)

status='OrderNotificationV126.notify(applicationContext,((o.id+200000)%Int.MAX_VALUE).toInt(),"Comanda #${o.number} · ${o.status}","Statusul comenzii tale AutoID a fost actualizat.")'
status_new='OrderNotificationV126.notify(applicationContext,((o.id+200000)%Int.MAX_VALUE).toInt(),"Comanda #${o.number} · ${o.status}","Statusul comenzii tale AutoID a fost actualizat.",orderId=o.id)'
if status not in o: raise SystemExit('order status notification call anchor missing')
o=o.replace(status,status_new,1)
ORDER.write_text(o)

# 4. Route the existing Notifications entry to the real inbox and support native
# destinations for order, RFQ and product notifications.
v=V100.read_text()
state_anchor='var reviewOrderId by remember{mutableLongStateOf(session.pendingReviewOrderId)}'
if state_anchor not in v: raise SystemExit('root review order state anchor missing')
v=v.replace(state_anchor,state_anchor+'\n    var notificationOrderIdV138 by remember{mutableLongStateOf(0L)}',1)

route_anchor='if(reviewOrderId>0){OrderReviewScreenV126(api,session,reviewOrderId,{session.pendingReviewOrderId=0;reviewOrderId=0});return}'
route_new=route_anchor+'\n    if(notificationOrderIdV138>0&&session.accessToken!=null){OrderDetailV120(api,session.accessToken!!,notificationOrderIdV138,onBack={notificationOrderIdV138=0});return}'
if route_anchor not in v: raise SystemExit('root order route anchor missing')
v=v.replace(route_anchor,route_new,1)

old_call='''                    notifications -> NotificationsV100(
                        { notifications = false },
                        { tab = V100Tab.Cart; notifications = false }
                    )'''
new_call='''                    notifications -> NotificationsInboxV138(
                        onBack={notifications=false},
                        onCart={tab=V100Tab.Cart;notifications=false},
                        onOrder={id->notifications=false;if(session.accessToken!=null)notificationOrderIdV138=id else tab=V100Tab.Account},
                        onRfq={id->notifications=false;session.pendingRfqIdV130=id;rfqAccountV130=true},
                        onProduct={id->notifications=false;rfqScopeV130.launch{runCatching{withContext(Dispatchers.IO){api.product(id)}}.onSuccess{openProduct(it)}}}
                    )'''
if old_call not in v: raise SystemExit('legacy NotificationsV100 root call anchor missing')
v=v.replace(old_call,new_call,1)
if 'notifications -> NotificationsInboxV138(' not in v: raise SystemExit('real inbox route missing')
V100.write_text(v)

# 5. Replace hard-coded notification badge "3" in known header implementations
# with the persistent unread count. Do not touch other badges (cart/RFQ).
def replace_badges(text):
    patterns=[
        r'Badge\(containerColor\s*=\s*AutoIdOrange\)\s*\{\s*Text\("3"\)\s*\}',
        r'Badge\(containerColor=AutoIdOrange\)\{Text\("3"\)\}',
    ]
    total=0
    for pat in patterns:
        text,n=re.subn(pat,'NotificationUnreadBadgeV138()',text)
        total+=n
    return text,total

files=[V100,V114,ACCOUNT]
replaced=0
for f in files:
    text=f.read_text();text,n=replace_badges(text);replaced+=n;f.write_text(text)
if replaced<2: raise SystemExit(f'expected at least 2 hard-coded notification badges, replaced {replaced}')

# 6. Android-only release code.
g=GRADLE.read_text()
if 'versionCode = 13305' not in g: raise SystemExit('RC7.3 version code anchor missing')
g=g.replace('versionCode = 13305','versionCode = 13306',1)
GRADLE.write_text(g)

# Contracts.
for required in ['NotificationInboxStoreV138','NotificationsInboxV138','NotificationUnreadBadgeV138']:
    if required not in TARGET.read_text(): raise SystemExit('inbox asset missing '+required)
_,_,cart_final=function_block(V114.read_text(),'fun CartV114')
if '.statusBarsPadding()' in cart_final: raise SystemExit('CartV114 still has duplicate top inset')
if 'NotificationInboxStoreV138(this).addPush' not in PUSH.read_text(): raise SystemExit('FCM inbox persistence missing')
if 'NotificationInboxStoreV138(context).addLocal' not in ORDER.read_text(): raise SystemExit('local order inbox persistence missing')
print(f'RC7.3: active CartV114 inset fixed; persistent notification inbox enabled; {replaced} fake badges replaced; code 13306')
