from pathlib import Path

p=Path('android-v0.1/app/src/main/java/ro/autoid/app/OrderNotificationV126.kt')
s=p.read_text()
old=s
s=s.replace('private const val CHANNEL="autoid_orders"','const val CHANNEL="autoid_orders"',1)
s=s.replace('private const val CHANNEL = "autoid_orders"','const val CHANNEL = "autoid_orders"',1)
if s==old:
    raise SystemExit('v1.0.28 notification CHANNEL visibility anchor not found')
p.write_text(s)
print('fixed v1.0.28 notification channel visibility')
