from pathlib import Path
p=Path('wordpress/autoid-mobile-commerce/autoid-mobile-commerce.php')
s=p.read_text()
a=s.find('public static function me_order_action_v127')
b=s.find('private static function account_address_payload',a)
if a<0 or b<0:
    raise SystemExit('v1.0.27 PHP action block not found')
start=max(0,a-16)
segment=s[start:b]
segment=segment.replace('\\n','\n')
s=s[:start]+segment+s[b:]
p.write_text(s)
print('fixed v1.0.27 PHP generated newlines')
