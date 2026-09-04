#!/usr/bin/env python3
from pathlib import Path

ROOT=Path('android-v0.1/app/src/main/java/ro/autoid/app')

def block(text, needle):
    i=text.find(needle)
    if i<0:return f'NOT FOUND: {needle}'
    start=text.rfind('\n',0,i)+1
    brace=text.find('{',i)
    if brace<0:return text[start:start+2500]
    depth=0
    for j in range(brace,len(text)):
        c=text[j]
        if c=='{':depth+=1
        elif c=='}':
            depth-=1
            if depth==0:return text[start:j+1]
    return text[start:start+6000]

v100=(ROOT/'V100Screens.kt').read_text()
print('=== CART_V100 ===')
print(block(v100,'fun CartV100'))
print('=== NOTIFICATIONS_V100 ===')
print(block(v100,'fun NotificationsV100'))

for p in sorted(ROOT.glob('*.kt')):
    txt=p.read_text(errors='replace')
    if 'onMessageReceived' in txt or 'FirebaseMessagingService' in txt or 'NotificationCompat' in txt:
        print(f'=== NOTIFICATION_FILE {p.name} ===')
        if 'onMessageReceived' in txt:
            print(block(txt,'onMessageReceived'))
        else:
            print(txt[:7000])
