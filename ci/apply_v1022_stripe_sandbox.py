from pathlib import Path
import base64
import zlib

payload=Path('ci/v122_stripe_patch_payload.b64').read_text().strip()
source=zlib.decompress(base64.b64decode(payload))
exec(compile(source,'ci/apply_v1022_stripe_sandbox.py::<payload>','exec'))

# Keep the security invariant human-readable next to the generated PHP implementation.
plugin=Path('wordpress/autoid-mobile-commerce/autoid-mobile-commerce.php')
text=plugin.read_text()
needle="        if((int)($pi['metadata']['order_id']??0)!==$order->get_id())"
if needle in text and "metadata['order_id'] is verified" not in text:
    text=text.replace(needle,"        // Stripe metadata['order_id'] is verified against the WooCommerce order before payment_complete().\n"+needle,1)
    plugin.write_text(text)
