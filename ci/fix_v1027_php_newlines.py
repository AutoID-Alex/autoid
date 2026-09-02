from pathlib import Path
p=Path('wordpress/autoid-mobile-commerce/autoid-mobile-commerce.php')
s=p.read_text()
start=s.find('\\n    public static function me_order_action_v127')
end=s.find('\\n    private static function account_address_payload',start)
if start<0 or end<0:
    raise SystemExit('v1.0.27 PHP action newline markers not found')
segment=s[start:end].replace('\\n','\n')
s=s[:start]+segment+s[end:].replace('\\n    private static function account_address_payload','\n    private static function account_address_payload',1)
p.write_text(s)
print('fixed v1.0.27 PHP generated newlines')
