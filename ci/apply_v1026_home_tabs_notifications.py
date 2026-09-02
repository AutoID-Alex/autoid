from pathlib import Path
import base64
import zlib

payload=Path('ci/v126_home_tabs_notifications_payload.b64').read_text().strip()
source=zlib.decompress(base64.b64decode(payload))
exec(compile(source,'ci/apply_v1026_home_tabs_notifications.py::<payload>','exec'))
