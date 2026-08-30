from pathlib import Path

ROOT=Path('.')
UI=ROOT/'android-v0.1/app/src/main/java/ro/autoid/app/V100Screens.kt'
API=ROOT/'android-v0.1/app/src/main/java/ro/autoid/app/data/AutoIdApi.kt'
GRADLE=ROOT/'android-v0.1/app/build.gradle.kts'

s=UI.read_text()

old='''        if(loading) LinearProgressIndicator(Modifier.fillMaxWidth(),color=AutoIdOrange)\n        val visible=if(q.isBlank())categories else categories.filter{it.name.contains(q,true)}\n        LazyVerticalGrid(\n            columns=GridCells.Fixed(2),\n            horizontalArrangement=Arrangement.spacedBy(10.dp),\n            verticalArrangement=Arrangement.spacedBy(10.dp),\n            contentPadding=PaddingValues(bottom=110.dp)\n        ){\n            gridItems(visible,key={it.id}){c->\n                ElevatedCard(Modifier.height(175.dp).clickable{onCategory(c)},shape=RoundedCornerShape(18.dp)){\n                    Column(Modifier.fillMaxSize().padding(12.dp),horizontalAlignment=Alignment.CenterHorizontally){\n                        Box(Modifier.weight(1f).fillMaxWidth(),contentAlignment=Alignment.Center){\n                            if(c.imageUrl!=null)AsyncImage(c.imageUrl,c.name,Modifier.fillMaxSize().padding(8.dp),contentScale=ContentScale.Fit)\n                            else Icon(Icons.Default.Inventory2,null,Modifier.size(42.dp),tint=Muted)\n                        }\n                        Text(c.name,fontWeight=FontWeight.Bold,maxLines=2,overflow=TextOverflow.Ellipsis,textAlign=androidx.compose.ui.text.style.TextAlign.Center)\n                    }\n                }\n            }\n        }'''
new='''        val visible=if(q.isBlank())categories else categories.filter{it.name.contains(q,true)}\n        Box(Modifier.weight(1f).fillMaxWidth()) {\n            if (loading) {\n                AutoIdPulseLoaderV112(\n                    modifier = Modifier.fillMaxSize(),\n                    label = "Încărcăm categoriile AutoID"\n                )\n            } else {\n                LazyVerticalGrid(\n                    columns=GridCells.Fixed(2),\n                    horizontalArrangement=Arrangement.spacedBy(10.dp),\n                    verticalArrangement=Arrangement.spacedBy(10.dp),\n                    contentPadding=PaddingValues(bottom=110.dp)\n                ){\n                    gridItems(visible,key={it.id}){c->\n                        ElevatedCard(Modifier.height(175.dp).clickable{onCategory(c)},shape=RoundedCornerShape(18.dp)){\n                            Column(Modifier.fillMaxSize().padding(12.dp),horizontalAlignment=Alignment.CenterHorizontally){\n                                Box(Modifier.weight(1f).fillMaxWidth(),contentAlignment=Alignment.Center){\n                                    if(c.imageUrl!=null)AsyncImage(c.imageUrl,c.name,Modifier.fillMaxSize().padding(8.dp),contentScale=ContentScale.Fit)\n                                    else Icon(Icons.Default.Inventory2,null,Modifier.size(42.dp),tint=Muted)\n                                }\n                                Text(c.name,fontWeight=FontWeight.Bold,maxLines=2,overflow=TextOverflow.Ellipsis,textAlign=androidx.compose.ui.text.style.TextAlign.Center)\n                            }\n                        }\n                    }\n                }\n            }\n        }'''
if old not in s:
    raise SystemExit('v1.0.12 Categories loader anchor missing')
s=s.replace(old,new,1)

old='''                        Box(Modifier.fillMaxWidth().height(58.dp), contentAlignment = Alignment.Center) {\n                            CircularProgressIndicator(Modifier.size(24.dp), strokeWidth = 2.dp, color = AutoIdOrange)\n                        }'''
new='''                        AutoIdPulseLoaderV112(\n                            modifier = Modifier.fillMaxWidth().height(72.dp),\n                            compact = true,\n                            label = ""\n                        )'''
if old not in s:
    raise SystemExit('v1.0.12 infinite loader anchor missing')
s=s.replace(old,new,1)

old='''            if (loading && products.isEmpty()) CircularProgressIndicator(Modifier.align(Alignment.Center), color = AutoIdOrange)'''
new='''            if (loading && products.isEmpty()) {\n                AutoIdPulseLoaderV112(\n                    modifier = Modifier.fillMaxSize(),\n                    label = "Încărcăm produsele"\n                )\n            }'''
if old not in s:
    raise SystemExit('v1.0.12 initial catalog loader anchor missing')
s=s.replace(old,new,1)

if 'if (filters) FilterSheetV105(' not in s:
    raise SystemExit('v1.0.12 filter call anchor missing')
s=s.replace('if (filters) FilterSheetV105(', 'if (filters) FilterSheetV112(', 1)
UI.write_text(s)

a=API.read_text()
if 'AutoID-Android/1.0.11' not in a:
    raise SystemExit('v1.0.12 API version anchor missing')
a=a.replace('AutoID-Android/1.0.11','AutoID-Android/1.0.12',1)
API.write_text(a)

g=GRADLE.read_text()
if 'versionCode = 11400' not in g or 'versionName = "1.0.11"' not in g:
    raise SystemExit('v1.0.12 Gradle version anchor missing')
g=g.replace('versionCode = 11400','versionCode = 11500',1).replace('versionName = "1.0.11"','versionName = "1.0.12"',1)
GRADLE.write_text(g)
print('Applied Android v1.0.12 centered branded loader and 2026 filter UX')
