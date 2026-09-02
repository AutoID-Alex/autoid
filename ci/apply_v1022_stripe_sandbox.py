from pathlib import Path
import base64
import zlib

payload=Path('ci/v122_stripe_patch_payload.b64').read_text().strip()
source=zlib.decompress(base64.b64decode(payload))
exec(compile(source,'ci/apply_v1022_stripe_sandbox.py::<payload>','exec'))
