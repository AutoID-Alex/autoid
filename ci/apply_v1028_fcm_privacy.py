from pathlib import Path
import base64
import zlib

payload=Path('ci/v128_fcm_privacy_payload.b64').read_text().strip()
source=zlib.decompress(base64.b64decode(payload))
exec(compile(source,'ci/apply_v1028_fcm_privacy.py::<payload>','exec'))
