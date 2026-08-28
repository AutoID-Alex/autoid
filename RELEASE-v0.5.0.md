# AutoID Android v0.5.0

## Focus
Search, commercial metadata, stock-prioritized product families, category ordering, cleaner UI icons, AutoID branding and website-hosted AI.

## Search
- Mobile product search now tries the installed FiboSearch AJAX engine first (`dgwt_wcas_ajax_search`).
- FiboSearch result order is preserved for search queries.
- Safe WooCommerce fallback remains available if FiboSearch cannot answer.
- Search continues to support product names, model/SKU relevance through the store search index.

## Product commercial metadata
The mobile bridge exposes the AutoID product metadata used on the website:
- `pret_lista` / formatted MSRP EUR
- `pret_autoid_euro` / formatted AutoID EUR ex. VAT
- WooCommerce regular/current price including VAT for "Comandă acum"
- `stock_autoid`
- `stock_distributie`

The native product hub and product cards show MSRP, AutoID EUR ex. VAT, current WooCommerce price incl. VAT, AutoID stock and manufacturer/distribution stock.

## Product family ordering
- Family/group products are limited to published products visible in the WooCommerce catalog.
- Grouped products sort by `stock_autoid` descending first.
- Ties sort by `stock_distributie` descending.

## Categories
Top-level WooCommerce categories use WooCommerce `menu_order` ascending so the mobile category order follows the configured website order instead of product count.

## UIX
- Replaces text-symbol navigation icons with Material icons.
- Uses the supplied AutoID website logo in the native header.
- Cleaner cart, favorites, scanner and AI iconography.
- AI is removed from bottom navigation and becomes a persistent AutoID-orange chat bubble.

## AutoID AI
The APK no longer attempts to duplicate the AI assistant prompts/instructions. The chat bubble launches a WebView shell to the AutoID Support experience on `autoid.ro`, so assistant instructions and technical context remain managed centrally on the website.

## Compatibility
- Package: `ro.autoid.app`
- Version code: 5
- Version name: 0.5.0
- Android target SDK: 36
- Java: 17
- Existing auth/orders/payment API remains untouched.

## WordPress
Plugin: AutoID Mobile Commerce Bridge 0.5.0

The bridge is read-only for catalog/search/product-family/support routes and coexists with the existing AutoID Mobile API auth/order/payment endpoints.
