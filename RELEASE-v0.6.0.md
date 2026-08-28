# AutoID Android v0.6.0

## Core fixes
- Exact catalog search: SKU and canonical `model` taxonomy first, then title/SKU matching, FiboSearch only as enrichment.
- Product family uses the live AutoID `model` taxonomy when present instead of fuzzy title matching.
- Grouped products remain filtered to visible published products and stock-prioritized.
- `pret_lista` and `pret_autoid_euro` use the same visual size.
- Availability combines AutoID and distributor stock in the same visual row.
- Header gets a native menu backed by the live WordPress navigation structure.
- Add-to-cart now shows immediate confirmation feedback.
- AutoID AI is native in the APK; Bridge proxies to the AI route already registered by the website, so prompts/API keys stay server-side.

## Bridge endpoints added
- GET `/wp-json/autoid-app/v1/navigation`
- POST `/wp-json/autoid-app/v1/ai/chat`

## QA priorities
1. Search `ZT610` and verify only ZT610/model-relevant products rank first.
2. Verify a product with both `stock_autoid` and `stock_distributie`.
3. Verify product family tabs against the live product/model page.
4. Verify hamburger menu order against the website header.
5. Verify native AI after installing the Bridge; if the website AI uses a non-REST internal hook, connect it via the `autoid_mobile_ai_chat` WordPress filter.
