from pathlib import Path

p=Path('wordpress/autoid-mobile-commerce/autoid-mobile-commerce.php')
s=p.read_text()
repls=[
    ('Version: 1.0.4.2','Version: 1.0.4.3'),
    ('final class AutoID_Mobile_Commerce_Bridge_1042','final class AutoID_Mobile_Commerce_Bridge_1043'),
    ('AutoID_Mobile_Commerce_Bridge_1042::boot();','AutoID_Mobile_Commerce_Bridge_1043::boot();'),
    ("'version'=>'1.0.4.2'", "'version'=>'1.0.4.3'"),
]
for old,new in repls:
    if old not in s:
        raise SystemExit(f'Bridge v1.0.4.3 anchor missing: {old}')
    s=s.replace(old,new,1)
needle="            'special_category'=>$is_liquidation?'liquidation':''\n"
replacement="            'special_category'=>$is_liquidation?'liquidation':'',\n            'bridge_version'=>'1.0.4.3'\n"
if needle not in s:
    raise SystemExit('catalog facets special_category response anchor missing')
s=s.replace(needle,replacement,1)
p.write_text(s)
print('Patched AutoID Mobile Commerce Bridge v1.0.4.3 with diagnostic bridge_version marker')
