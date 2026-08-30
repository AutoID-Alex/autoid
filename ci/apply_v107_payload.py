from pathlib import Path
import base64,zlib
root=Path(__file__).parent
parts=[(root/f"v107_payload_{i}.txt").read_text().strip() for i in range(1,6)]
if len(parts[0]) == 3799:
    parts[0]=parts[0].replace('O+jXNg829iGy','O+jXNgA829iGy',1)
lengths=[len(x) for x in parts]
print('v1.0.7 payload lengths:', lengths, 'total=', sum(lengths))
if lengths != [3800,3800,3800,3800,468]:
    raise SystemExit(f'Unexpected v1.0.7 payload lengths: {lengths}')
data=''.join(parts)
exec(zlib.decompress(base64.b64decode(data)).decode())
