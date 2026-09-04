#!/usr/bin/env python3
from pathlib import Path

p=Path('android-v0.1/app/src/main/java/ro/autoid/app/V114CommerceUx.kt')
s=p.read_text()

# Normalize only the address summary Edit action produced by v1.0.19.
old='TextButton(onClick={addressEdit=true},modifier=Modifier.align(Alignment.End)){Text("Editează",fontWeight=FontWeight.ExtraBold,color=AutoIdOrange)}'
new='TextButton(onClick={addressEdit=true},modifier=Modifier.align(Alignment.End)){Text("Editează",fontWeight=FontWeight.ExtraBold,color=C114Orange)}'
if old not in s:
    raise SystemExit('RC8 pre-normalize: checkout address Edit anchor missing')
s=s.replace(old,new,1)

# Normalize the visual-only Gata action so RC8 can replace it with Save/Cancel.
old='TextButton(onClick={addressEdit=false},modifier=Modifier.align(Alignment.End)){Text("Gata")}'
new='TextButton(onClick={addressEdit=false},modifier=Modifier.align(Alignment.End)){Text("Gata",fontWeight=FontWeight.ExtraBold,color=C114Orange)}'
if old not in s:
    raise SystemExit('RC8 pre-normalize: checkout address Gata anchor missing')
s=s.replace(old,new,1)

p.write_text(s)
print('RC8 checkout anchors normalized')
