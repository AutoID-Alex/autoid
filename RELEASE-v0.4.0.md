# AutoID Professional Solutions v0.4.0

## Focus
Product-family UX and product page restructuring around the same commercial grouping used on AutoID.ro.

## Implemented
- New Product Family API for each WooCommerce product.
- Native product tabs: Produs, Variante, Accesorii, Service, Software & Apps, Consumabile, Suport.
- Counts per family group returned by backend.
- Family group pagination, 20 products per request.
- Related SKU cards with image, SKU, price, stock and Add to Cart.
- Product model detection from model taxonomies, attributes, meta and product title fallback.
- Compatibility lookup across product taxonomies and compatibility-related metadata.
- Support resources grouped into Drivere, Firmware, Documentație, Video, Depanare, Software.
- Product-specific support endpoint.
- Stock AutoID / distributor fields exposed when available.
- Delivery label exposed by API.
- Rating/review count exposed when available.
- Product page redesigned as a Product Hub with persistent cart CTA.
- Existing auth, account, cart, orders, scanner, AI/search flows preserved.

## New endpoints
- GET /wp-json/autoid-app/v1/products/{id}/family
- GET /wp-json/autoid-app/v1/products/{id}/family/{group}?page=1&per_page=20
- GET /wp-json/autoid-app/v1/products/{id}/support

Family groups:
- variants
- accessories
- service
- software
- consumables

## Compatibility
The WordPress bridge continues to use namespace autoid-app/v1 and coexists with the existing authentication/order/payment plugin. No WooCommerce consumer secret is stored in the APK.

## Important QA
The family resolver uses AutoID product taxonomies/meta where present, with model/title fallback. After installing the plugin, validate several known models (for example ZT610) against the counts shown on the website. If a custom relation taxonomy/meta key used by the live site is not among the detected sources, add that exact key to the resolver rather than hardcoding product IDs.

## Next
- Match the exact live-site relationship taxonomy/meta after field-level QA.
- 2-column product listing grid and full filter bottom sheet.
- Native variation selector for variable products.
- Embedded PDF/video support viewer.
- Real AI chat endpoint and tool actions.
- Server-synced cart/wishlist and authenticated checkout.
