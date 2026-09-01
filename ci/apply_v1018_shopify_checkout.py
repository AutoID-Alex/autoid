from pathlib import Path
import re

ROOT=Path('.')
APP=ROOT/'android-v0.1/app'
SRC=APP/'src/main/java/ro/autoid/app'
V100=SRC/'V100Screens.kt'
V114=SRC/'V114CommerceUx.kt'
API=SRC/'data/AutoIdApi.kt'
GRADLE=APP/'build.gradle.kts'

# Android semantic version.
s=GRADLE.read_text()
if 'versionCode = 12000' not in s or 'versionName = "1.0.17"' not in s:
    raise SystemExit('Expected Android v1.0.17 Gradle base is missing')
s=s.replace('versionCode = 12000','versionCode = 12100',1)
s=s.replace('versionName = "1.0.17"','versionName = "1.0.18"',1)
GRADLE.write_text(s)

s=API.read_text()
if 'AutoID-Android/1.0.17' not in s:
    raise SystemExit('Android 1.0.17 user-agent anchor missing')
s=s.replace('AutoID-Android/1.0.17','AutoID-Android/1.0.18',1)
API.write_text(s)

# Home: Quick categories -> View all must actually open the complete product catalog.
s=V100.read_text()
pattern=r'SectionHead\("Categorii rapide","Vezi toate"\)\{.*?\};\s*LazyRow'
replacement='SectionHead("Categorii rapide","Vezi toate"){onCategory(ProductCategory(0,"Categorii de produse",0))};LazyRow'
s,n=re.subn(pattern,replacement,s,count=1,flags=re.S)
if n==0:
    raise SystemExit('Quick categories View all structural anchor missing')
V100.write_text(s)

s=V114.read_text()

# URI handler is used by the password recovery action.
if 'import androidx.compose.ui.platform.LocalUriHandler\n' not in s:
    anchor='import androidx.compose.ui.platform.LocalContext\n'
    if anchor in s:
        s=s.replace(anchor,anchor+'import androidx.compose.ui.platform.LocalUriHandler\n',1)
    else:
        anchor='import androidx.compose.ui.unit.dp\n'
        if anchor not in s: raise SystemExit('Compose import anchor missing')
        s=s.replace(anchor,'import androidx.compose.ui.platform.LocalUriHandler\n'+anchor,1)

# Checkout must open as guest checkout. Login is an optional disclosure, not a competing checkout path.
s,n=re.subn(r'var\s+authMode\s+by\s+remember\s*\{\s*mutableStateOf\("(?:login|guest)"\)\s*\}',
            'var authMode by remember{mutableStateOf("guest")}',s,count=1)
if n==0 and 'var authMode by remember{mutableStateOf("guest")}' not in s:
    raise SystemExit('Checkout authMode state anchor missing')

# Replace the v1.0.17 continuation selector with a compact Shopify-like account disclosure.
start_anchor='            item{SectionV114(Icons.Default.Person,"Informații de contact","Autentificare sau checkout rapid"){' 
if start_anchor not in s:
    raise SystemExit('v1.0.17 checkout auth block anchor missing')
start=s.index(start_anchor)
end=s.index('            item{ElevatedCard(Modifier.fillMaxWidth().clickable{summaryOpen=!summaryOpen}',start)
new_auth='''            item{
                ElevatedCard(
                    modifier=Modifier.fillMaxWidth(),
                    shape=RoundedCornerShape(18.dp),
                    colors=CardDefaults.elevatedCardColors(containerColor=Color.White),
                    elevation=CardDefaults.elevatedCardElevation(defaultElevation=1.dp)
                ){
                    Column(Modifier.fillMaxWidth().padding(horizontal=16.dp,vertical=12.dp),verticalArrangement=Arrangement.spacedBy(10.dp)){
                        if(authMode=="authenticated"){
                            Row(Modifier.fillMaxWidth(),verticalAlignment=Alignment.CenterVertically){
                                Surface(shape=CircleShape,color=C114GoodSoft,modifier=Modifier.size(34.dp)){Box(contentAlignment=Alignment.Center){Icon(Icons.Default.VerifiedUser,null,tint=C114Good,modifier=Modifier.size(18.dp))}}
                                Spacer(Modifier.width(10.dp))
                                Column(Modifier.weight(1f)){Text("Cont AutoID conectat",fontSize=12.sp,fontWeight=FontWeight.ExtraBold,color=C114Ink);Text(session.customerEmail.ifBlank{email},fontSize=10.sp,color=C114Muted)}
                                TextButton(onClick={session.clear();authToken=null;authMode="guest";message=""}){Text("Schimbă",fontWeight=FontWeight.Bold)}
                            }
                        }else{
                            Row(Modifier.fillMaxWidth(),verticalAlignment=Alignment.CenterVertically){
                                Text("Ai cont AutoID?",fontSize=12.sp,fontWeight=FontWeight.SemiBold,color=C114Ink,modifier=Modifier.weight(1f))
                                TextButton(onClick={authMode=if(authMode=="login")"guest" else "login";message=""}){Text(if(authMode=="login")"Închide" else "Autentificare",fontWeight=FontWeight.ExtraBold,color=AutoIdOrange)}
                            }
                            AnimatedVisibility(visible=authMode=="login"){
                                Column(verticalArrangement=Arrangement.spacedBy(10.dp)){
                                    HorizontalDivider(color=C114Border)
                                    OutlinedTextField(login,{login=it},label={Text("User / Email")},singleLine=true,modifier=Modifier.fillMaxWidth(),shape=RoundedCornerShape(13.dp))
                                    OutlinedTextField(pass,{pass=it},label={Text("Parolă")},singleLine=true,visualTransformation=PasswordVisualTransformation(),modifier=Modifier.fillMaxWidth(),shape=RoundedCornerShape(13.dp))
                                    val uriHandler=LocalUriHandler.current
                                    Row(Modifier.fillMaxWidth(),verticalAlignment=Alignment.CenterVertically){
                                        TextButton(onClick={uriHandler.openUri("https://www.autoid.ro/contul-meu/lost-password/")},contentPadding=PaddingValues(0.dp)){Text("Ai uitat parola?",fontSize=11.sp,fontWeight=FontWeight.SemiBold,color=C114Muted)}
                                        Spacer(Modifier.weight(1f))
                                    }
                                    Button(onClick={authBusy=true},enabled=!authBusy&&login.isNotBlank()&&pass.isNotBlank(),modifier=Modifier.fillMaxWidth().height(50.dp),shape=RoundedCornerShape(13.dp)){Text(if(authBusy)"Se conectează..." else "Autentificare",fontWeight=FontWeight.ExtraBold)}
                                    GoogleButtonV114(clientId=cfg.googleClientId,api=api,session=session,onSuccess={r->authToken=r.accessToken;authMode="authenticated";email=r.customer?.email.orEmpty().ifBlank{email};message="Autentificare Google reușită."},onError={message=it},modifier=Modifier.fillMaxWidth())
                                }
                            }
                        }
                    }
                }
            }
'''
s=s[:start]+new_auth+s[end:]

# Contact section copy: clearer hierarchy and order-update purpose.
contact_pattern=r'SectionV114\((Icons\.Default\.[A-Za-z0-9_]+),"Contact","[^"]*"\)'
replacement=r'SectionV114(\1,"Informații de contact","Pentru confirmare și actualizările comenzii.")'
s,n=re.subn(contact_pattern,replacement,s,count=1)
if n==0:
    s,n=re.subn(r'"Contact","[^"]*"\)\{', '"Informații de contact","Pentru confirmare și actualizările comenzii."){', s, count=1)
if n==0:
    raise SystemExit('Checkout Contact section anchor missing')

# Small visual refinement: tighter, calmer radii while retaining all fields and checkboxes.
s=s.replace('shape=RoundedCornerShape(18.dp),colors=CardDefaults.elevatedCardColors(containerColor=Color.White),elevation=CardDefaults.elevatedCardElevation(defaultElevation=1.dp)',
            'shape=RoundedCornerShape(16.dp),colors=CardDefaults.elevatedCardColors(containerColor=Color.White),elevation=CardDefaults.elevatedCardElevation(defaultElevation=1.dp)')
s=s.replace('shape=RoundedCornerShape(14.dp)', 'shape=RoundedCornerShape(13.dp)')

V114.write_text(s)
print('Applied Android v1.0.18: working quick categories link and Shopify-style checkout disclosure')
