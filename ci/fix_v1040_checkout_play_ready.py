#!/usr/bin/env python3
"""RC8 / AutoID Mobile 1.1.30: checkout address save + Google Play readiness."""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
APP=ROOT/'android-v0.1/app/src/main/java/ro/autoid/app'
V114=APP/'V114CommerceUx.kt'
ACCOUNT=APP/'V135AccountUx.kt'
API=APP/'data/AutoIdApi.kt'
PLUGIN=ROOT/'wordpress/autoid-mobile-commerce/autoid-mobile-commerce.php'
MANIFEST=ROOT/'android-v0.1/app/src/main/AndroidManifest.xml'
GRADLE=ROOT/'android-v0.1/app/build.gradle.kts'


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

# -----------------------------------------------------------------------------
# 1) CHECKOUT: logged-in Delivery/Billing Edit must be a real account save.
# -----------------------------------------------------------------------------
v=V114.read_text()
ci,cj,checkout=function_block(v,'fun CheckoutV114')

state='var addressEdit by remember{mutableStateOf(false)}'
if state not in checkout: raise SystemExit('Checkout addressEdit state missing')
checkout=checkout.replace(state,state+'\n    var addressSaveBusyV140 by remember{mutableStateOf(false)}\n    var addressSaveMessageV140 by remember{mutableStateOf("")}\n    val addressSaveScopeV140=rememberCoroutineScope()',1)

# Move the Edit action from the bottom of the address card to the card header.
edit='TextButton(onClick={addressEdit=true},modifier=Modifier.align(Alignment.End)){Text("Editează",fontWeight=FontWeight.ExtraBold,color=C114Orange)}'
if edit not in checkout:
    # tolerate spacing produced by Compose formatter/migrations
    edit='TextButton(onClick={addressEdit=true}, modifier=Modifier.align(Alignment.End)){Text("Editează",fontWeight=FontWeight.ExtraBold,color=C114Orange)}'
if edit not in checkout: raise SystemExit('Checkout address Edit button anchor missing')
checkout=checkout.replace(edit,'',1)

branch='if(authMode=="authenticated"&&!addressEdit){'
bi=checkout.find(branch)
if bi<0: raise SystemExit('logged-in address summary branch missing')
col=checkout.find('Column(',bi)
brace=checkout.find('{',col)
if col<0 or brace<0: raise SystemExit('logged-in address summary Column missing')
header='''\n                                    Row(Modifier.fillMaxWidth(),verticalAlignment=Alignment.CenterVertically){
                                        Text("Adresele comenzii",fontSize=11.sp,fontWeight=FontWeight.ExtraBold,color=C114Ink,modifier=Modifier.weight(1f))
                                        TextButton(onClick={addressSaveMessageV140="";addressEdit=true}){Text("Editează",fontWeight=FontWeight.ExtraBold,color=C114Orange)}
                                    }'''
checkout=checkout[:brace+1]+header+checkout[brace+1:]

# Replace the old visual-only "Gata" with an actual /me/addresses save.
old_done='TextButton(onClick={addressEdit=false},modifier=Modifier.align(Alignment.End)){Text("Gata",fontWeight=FontWeight.ExtraBold,color=C114Orange)}'
if old_done not in checkout:
    old_done='TextButton(onClick={addressEdit=false}, modifier=Modifier.align(Alignment.End)){Text("Gata",fontWeight=FontWeight.ExtraBold,color=C114Orange)}'
if old_done not in checkout: raise SystemExit('Checkout address Gata anchor missing')

save='''Column(Modifier.fillMaxWidth(),verticalArrangement=Arrangement.spacedBy(6.dp)){
                                    Button(
                                        onClick={
                                            val token=authToken
                                            if(token!=null&&!addressSaveBusyV140){
                                                addressSaveScopeV140.launch{
                                                    addressSaveBusyV140=true;addressSaveMessageV140=""
                                                    val billingSave=AccountAddress(firstName=bFirst,lastName=bLast,company=company,address1=bAddress1,address2=bAddress2,city=bCity,state=bState,postcode=bPostcode,country=bCountry,phone=phone,email=email)
                                                    val shippingSave=if(sameBilling)billingSave.copy(company="") else AccountAddress(firstName=sFirst,lastName=sLast,address1=sAddress1,address2=sAddress2,city=sCity,state=sState,postcode=sPostcode,country=sCountry)
                                                    runCatching{withContext(Dispatchers.IO){api.saveAccountAddresses(token,AccountAddresses(billingSave,shippingSave,vat))}}
                                                        .onSuccess{saved->
                                                            bFirst=saved.billing.firstName;bLast=saved.billing.lastName;company=saved.billing.company;bAddress1=saved.billing.address1;bAddress2=saved.billing.address2;bCity=saved.billing.city;bState=saved.billing.state;bPostcode=saved.billing.postcode;bCountry=saved.billing.country;phone=saved.billing.phone.ifBlank{phone};email=saved.billing.email.ifBlank{email};vat=saved.vatNumber
                                                            sFirst=saved.shipping.firstName;sLast=saved.shipping.lastName;sAddress1=saved.shipping.address1;sAddress2=saved.shipping.address2;sCity=saved.shipping.city;sState=saved.shipping.state;sPostcode=saved.shipping.postcode;sCountry=saved.shipping.country
                                                            addressEdit=false;addressSaveMessageV140="Datele de livrare și facturare au fost salvate."
                                                        }
                                                        .onFailure{addressSaveMessageV140=it.message?:"Datele nu au putut fi salvate."}
                                                    addressSaveBusyV140=false
                                                }
                                            }
                                        },
                                        enabled=!addressSaveBusyV140&&authToken!=null,
                                        modifier=Modifier.fillMaxWidth(),shape=RoundedCornerShape(10.dp)
                                    ){Text(if(addressSaveBusyV140)"Se salvează..." else "Salvează adresele")}
                                    TextButton(onClick={addressEdit=false;addressSaveMessageV140=""},enabled=!addressSaveBusyV140,modifier=Modifier.align(Alignment.CenterHorizontally)){Text("Renunță")}
                                    if(addressSaveMessageV140.isNotBlank())Text(addressSaveMessageV140,fontSize=10.sp,color=if(addressSaveMessageV140.contains("salvate"))C114Green else MaterialTheme.colorScheme.error)
                                }'''
checkout=checkout.replace(old_done,save,1)

# Display successful save message in the summary too.
summary_end='if(authMode=="authenticated"&&!addressEdit){'
# no extra structural replacement needed; state survives branch switch.
for required in ['Salvează adresele','api.saveAccountAddresses','Adresele comenzii','addressSaveBusyV140']:
    if required not in checkout: raise SystemExit('Checkout RC8 contract missing '+required)
v=v[:ci]+checkout+v[cj:]
V114.write_text(v)

# -----------------------------------------------------------------------------
# 2) API: authenticated account deletion request.
# -----------------------------------------------------------------------------
a=API.read_text()
api_anchor='    fun savedPaymentMethods(token:String):List<SavedPaymentMethod>{'
if api_anchor not in a: raise SystemExit('AutoIdApi account method anchor missing')
if 'requestAccountDeletionV140' not in a:
    method='''    fun requestAccountDeletionV140(token:String):String{
        val o=JSONObject(post("$MOBILE/me/account-deletion","{}",token))
        return o.optString("message","Solicitarea de ștergere a contului a fost înregistrată.")
    }

'''
    a=a.replace(api_anchor,method+api_anchor,1)
API.write_text(a)

# -----------------------------------------------------------------------------
# 3) Account UI: Play requires account deletion request in-app.
# -----------------------------------------------------------------------------
acc=ACCOUNT.read_text()
ai,aj,profile=function_block(acc,'private fun AccountProfileV135')
scope='val scope=rememberCoroutineScope()'
if scope not in profile: raise SystemExit('Account profile scope anchor missing')
profile=profile.replace(scope,scope+'\n    var deletionConfirmV140 by remember{mutableStateOf(false)}\n    var deletionBusyV140 by remember{mutableStateOf(false)}',1)

edit_button='OutlinedButton(onClick={editing=true}){Icon(Icons.Default.Edit,null);Spacer(Modifier.width(5.dp));Text("Editează")}'
if edit_button not in profile: raise SystemExit('Account profile edit button anchor missing')
profile=profile.replace(edit_button,edit_button+';HorizontalDivider(color=A135Border);TextButton(onClick={deletionConfirmV140=true},enabled=!deletionBusyV140){Icon(Icons.Default.DeleteForever,null,tint=MaterialTheme.colorScheme.error);Spacer(Modifier.width(5.dp));Text("Solicită ștergerea contului",color=MaterialTheme.colorScheme.error)}',1)

# Insert dialog before function close.
dialog='''
    if(deletionConfirmV140)AlertDialog(
        onDismissRequest={if(!deletionBusyV140)deletionConfirmV140=false},
        title={Text("Ștergere cont AutoID")},
        text={Text("Trimitem o solicitare verificată pentru ștergerea contului și a datelor asociate. Datele pe care trebuie să le păstrăm din motive legale sau fiscale pot fi reținute conform Politicii de confidențialitate.")},
        confirmButton={Button(onClick={scope.launch{deletionBusyV140=true;runCatching{withContext(Dispatchers.IO){api.requestAccountDeletionV140(token)}}.onSuccess{msg=it;deletionConfirmV140=false}.onFailure{msg=it.message?:"Solicitarea nu a putut fi trimisă."};deletionBusyV140=false}},enabled=!deletionBusyV140){Text(if(deletionBusyV140)"Se trimite..." else "Solicită ștergerea")}},
        dismissButton={TextButton(onClick={deletionConfirmV140=false},enabled=!deletionBusyV140){Text("Renunță")}}
    )
'''
profile=profile[:-1]+dialog+'}'
acc=acc[:ai]+profile+acc[aj:]
ACCOUNT.write_text(acc)

# -----------------------------------------------------------------------------
# 4) WordPress: authenticated deletion request + external verified web request.
# -----------------------------------------------------------------------------
p=PLUGIN.read_text()

# route
route_anchor="        register_rest_route(self::NS, '/me/orders', ['methods'=>'GET','callback'=>[__CLASS__,'me_orders'],'permission_callback'=>[__CLASS__,'auth_permission']]);"
if route_anchor not in p: raise SystemExit('plugin account route anchor missing')
route="        register_rest_route(self::NS, '/me/account-deletion', ['methods'=>'POST','callback'=>[__CLASS__,'me_account_deletion_v140'],'permission_callback'=>[__CLASS__,'auth_permission']]);"
if route not in p:p=p.replace(route_anchor,route_anchor+'\n'+route,1)

# boot hooks
boot_start=p.find('public static function boot')
if boot_start<0: raise SystemExit('plugin boot function missing')
boot_brace=p.find('{',boot_start)
boot_end=p.find('\n    }',boot_brace)
boot_block=p[boot_brace:boot_end]
hooks="""
        add_action('admin_init',[__CLASS__,'ensure_account_deletion_page_v140']);
        add_shortcode('autoid_account_deletion',[__CLASS__,'account_deletion_shortcode_v140']);"""
if 'ensure_account_deletion_page_v140' not in boot_block:
    p=p[:boot_brace+1]+hooks+p[boot_brace+1:]

methods=r'''
    private static function account_deletion_request_v140($uid,$source='app') {
        $uid=absint($uid);$user=$uid?get_userdata($uid):false;
        if(!$user)return new WP_Error('autoid_account_missing','Contul nu există.',['status'=>404]);
        $existing=(string)get_user_meta($uid,'_autoid_account_deletion_requested_at',true);
        if($existing===''){
            $at=current_time('mysql',true);
            update_user_meta($uid,'_autoid_account_deletion_requested_at',$at);
            update_user_meta($uid,'_autoid_account_deletion_source',sanitize_key((string)$source));
            update_user_meta($uid,'_autoid_account_deletion_status','pending');
            delete_user_meta($uid,'_autoid_fcm_token');
            delete_user_meta($uid,'_autoid_mobile_fcm_token');
            $subject='[AutoID] Solicitare ștergere cont #'.$uid;
            $body="Utilizator #{$uid}\nEmail: {$user->user_email}\nSursă: {$source}\nData UTC: {$at}\n\nȘterge contul și datele asociate care nu trebuie păstrate legal/fiscal. Datele de comandă/facturare păstrate din obligații legale trebuie tratate conform politicii de confidențialitate.";
            wp_mail((string)get_option('admin_email'),$subject,$body);
            wp_mail((string)$user->user_email,'Solicitarea de ștergere a contului AutoID a fost înregistrată',"Am primit solicitarea ta de ștergere a contului AutoID. O vom procesa conform Politicii de confidențialitate și obligațiilor legale aplicabile.");
        }
        return ['requested'=>true,'requested_at'=>$existing?:current_time('mysql',true),'message'=>'Solicitarea de ștergere a contului a fost înregistrată.'];
    }

    public static function me_account_deletion_v140(WP_REST_Request $r) {
        $uid=absint($r->get_param('_autoid_user_id'));if(!$uid)$uid=self::bearer_user_id($r);
        $result=self::account_deletion_request_v140($uid,'android_app');
        return is_wp_error($result)?$result:rest_ensure_response($result);
    }

    public static function ensure_account_deletion_page_v140() {
        if(!current_user_can('manage_options'))return;
        $existing=get_page_by_path('sterge-cont-autoid',OBJECT,'page');if($existing)return;
        wp_insert_post(['post_type'=>'page','post_status'=>'publish','post_title'=>'Ștergere cont AutoID','post_name'=>'sterge-cont-autoid','post_content'=>'[autoid_account_deletion]']);
    }

    public static function account_deletion_shortcode_v140() {
        $message='';$page_url=get_permalink();
        $uid=absint($_GET['autoid_delete_uid']??0);$token=sanitize_text_field((string)($_GET['autoid_delete_confirm']??''));
        if($uid>0&&$token!==''){
            $hash=(string)get_user_meta($uid,'_autoid_delete_token_hash',true);$exp=absint(get_user_meta($uid,'_autoid_delete_token_exp',true));
            if($hash!==''&&$exp>=time()&&hash_equals($hash,hash('sha256',$token))){
                self::account_deletion_request_v140($uid,'web_verified');delete_user_meta($uid,'_autoid_delete_token_hash');delete_user_meta($uid,'_autoid_delete_token_exp');
                $message='Solicitarea de ștergere a contului AutoID a fost confirmată.';
            }else $message='Linkul de confirmare nu mai este valid. Trimite o solicitare nouă.';
        }
        if($_SERVER['REQUEST_METHOD']==='POST'&&isset($_POST['autoid_delete_email'])){
            if(!isset($_POST['_autoid_delete_nonce'])||!wp_verify_nonce(sanitize_text_field(wp_unslash($_POST['_autoid_delete_nonce'])),'autoid_delete_account_v140'))$message='Solicitarea nu a putut fi verificată. Reîncarcă pagina și încearcă din nou.';
            else{
                $email=sanitize_email(wp_unslash($_POST['autoid_delete_email']));$user=$email?get_user_by('email',$email):false;
                if($user){
                    $raw=wp_generate_password(48,false,false);update_user_meta($user->ID,'_autoid_delete_token_hash',hash('sha256',$raw));update_user_meta($user->ID,'_autoid_delete_token_exp',time()+HOUR_IN_SECONDS);
                    $link=add_query_arg(['autoid_delete_uid'=>$user->ID,'autoid_delete_confirm'=>$raw],$page_url);
                    wp_mail($email,'Confirmă ștergerea contului AutoID',"Ai solicitat ștergerea contului AutoID. Confirmă solicitarea accesând linkul de mai jos (valabil o oră):\n\n{$link}\n\nDacă nu ai făcut această solicitare, ignoră mesajul.");
                }
                $message='Dacă există un cont pentru această adresă, am trimis un email de confirmare.';
            }
        }
        ob_start(); ?>
        <div class="autoid-account-delete" style="max-width:680px;margin:32px auto;padding:24px;border:1px solid #e4e7ec;border-radius:12px;background:#fff">
            <h1>Ștergere cont AutoID</h1>
            <p>Poți solicita ștergerea contului AutoID și a datelor asociate. Anumite date de comandă, facturare sau securitate pot fi păstrate dacă există obligații legale sau fiscale, conform Politicii de confidențialitate.</p>
            <?php if($message!==''): ?><p><strong><?php echo esc_html($message); ?></strong></p><?php endif; ?>
            <form method="post">
                <?php wp_nonce_field('autoid_delete_account_v140','_autoid_delete_nonce'); ?>
                <p><label for="autoid-delete-email"><strong>Email cont AutoID</strong></label></p>
                <p><input id="autoid-delete-email" type="email" name="autoid_delete_email" required autocomplete="email" style="width:100%;padding:12px"></p>
                <p><button type="submit" style="padding:12px 18px">Solicită ștergerea contului</button></p>
            </form>
            <p><a href="<?php echo esc_url(home_url('/politica-de-confidentialitate/')); ?>">Politica de confidențialitate</a></p>
        </div>
        <?php return (string)ob_get_clean();
    }

'''
method_anchor='    private static function support_center_info() {'
if method_anchor not in p: raise SystemExit('plugin helper insertion anchor missing')
if 'me_account_deletion_v140' not in p[p.find(method_anchor)-12000:p.find(method_anchor)]:
    p=p.replace(method_anchor,methods+method_anchor,1)

# bump 1.1.29 -> 1.1.30
for old,new in [(' * Version: 1.1.29',' * Version: 1.1.30'),("'version'=>'1.1.29',","'version'=>'1.1.30',"),('AutoID-Mobile-WordPress/1.1.29','AutoID-Mobile-WordPress/1.1.30')]:
    if old in p:p=p.replace(old,new)
for req in ['Version: 1.1.30','/me/account-deletion','sterge-cont-autoid','autoid_account_deletion','web_verified']:
    if req not in p: raise SystemExit('Play account deletion backend contract missing '+req)
PLUGIN.write_text(p)

# -----------------------------------------------------------------------------
# 5) Manifest hardening for release.
# -----------------------------------------------------------------------------
m=MANIFEST.read_text()
if 'android:allowBackup="true"' in m:m=m.replace('android:allowBackup="true"','android:allowBackup="false"',1)
elif 'android:allowBackup="false"' not in m:
    app=m.find('<application');end=m.find('>',app)
    if app<0 or end<0:raise SystemExit('manifest application tag missing')
    m=m[:end]+' android:allowBackup="false"'+m[end:]
if 'android:usesCleartextTraffic=' not in m:
    app=m.find('<application');end=m.find('>',app);m=m[:end]+' android:usesCleartextTraffic="false"'+m[end:]
for forbidden in ['READ_CONTACTS','READ_SMS','READ_CALL_LOG','ACCESS_FINE_LOCATION','ACCESS_COARSE_LOCATION','READ_MEDIA_IMAGES','READ_MEDIA_VIDEO']:
    if forbidden in m:raise SystemExit('Play preflight: unnecessary sensitive permission '+forbidden)
MANIFEST.write_text(m)

# -----------------------------------------------------------------------------
# 6) Android release code.
# -----------------------------------------------------------------------------
g=GRADLE.read_text()
if 'targetSdk = 36' not in g:raise SystemExit('Play preflight: targetSdk 36 missing')
if 'versionCode = 13306' not in g:raise SystemExit('RC8 version code anchor missing')
g=g.replace('versionCode = 13306','versionCode = 13307',1)
GRADLE.write_text(g)

print('RC8 Play-ready patch applied: checkout save, account deletion, manifest hardening, code 13307, plugin 1.1.30')
