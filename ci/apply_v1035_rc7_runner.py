#!/usr/bin/env python3
"""Temporary RC6 privacy contract extractor."""
from pathlib import Path
import base64
import zlib

payload=''.join(Path(f'ci/v128_fcm_privacy_payload.part{i}').read_text().strip() for i in range(1,5))
src=zlib.decompress(base64.b64decode(payload)).decode('utf-8','replace')
lines=src.splitlines()
keys=('privacy','consim','consent','notification','Confiden')
print('=== RC6 ORIGINAL PRIVACY CONTRACT ===')
seen=set()
for i,line in enumerate(lines):
    if any(k.lower() in line.lower() for k in keys):
        lo=max(0,i-4);hi=min(len(lines),i+8)
        for j in range(lo,hi):
            if j not in seen:
                print(f'PRIVACY_SRC {j+1}: {lines[j]}')
                seen.add(j)
print('=== END RC6 ORIGINAL PRIVACY CONTRACT ===')
raise SystemExit(99)
