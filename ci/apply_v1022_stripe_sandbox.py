from pathlib import Path
import base64
import zlib

payload=Path('ci/v122_stripe_patch_payload.b64').read_text().strip()
source=zlib.decompress(base64.b64decode(payload))
exec(compile(source,'ci/apply_v1022_stripe_sandbox.py::<payload>','exec'))

# Stripe Android 22.6.1 exposes Completed/Canceled as classes, not singleton objects.
ux=Path('android-v0.1/app/src/main/java/ro/autoid/app/V114CommerceUx.kt')
ux_text=ux.read_text()
ux_text=ux_text.replace('PaymentSheetResult.Completed->{','is PaymentSheetResult.Completed->{')
ux_text=ux_text.replace('PaymentSheetResult.Canceled->{','is PaymentSheetResult.Canceled->{')
ux.write_text(ux_text)

# Keep the security invariant human-readable next to the generated PHP implementation.
plugin=Path('wordpress/autoid-mobile-commerce/autoid-mobile-commerce.php')
text=plugin.read_text()
needle="        if((int)($pi['metadata']['order_id']??0)!==$order->get_id())"
if needle in text and "metadata['order_id'] is verified" not in text:
    text=text.replace(needle,"        // Stripe metadata['order_id'] is verified against the WooCommerce order before payment_complete().\n"+needle,1)
    plugin.write_text(text)
