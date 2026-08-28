# AutoID — Professional Solutions v0.3.0

## Major release scope

E-commerce + B2B foundation + AI Shopping/Technical Assistant UX + AutoID Support Center integration.

## Implemented in Android

- Native Compose design system, light-first, AutoID orange accent.
- Permanent bottom navigation: Acasă, Categorii, AI, Coș, Cont.
- Home with search, hero, quick categories, AI CTA, in-stock products, recently viewed and Support CTA.
- Product catalog with 20 products/page, search, category filtering, sort chips and load more.
- Barcode / QR / DataMatrix / UPC / Code128 scan-to-search.
- Native product page with gallery area, brand, SKU, price, stock, quantity, sticky Add to Cart, favorites, AI/support context, collapsible description and technical attributes.
- Local persistent cart with quantity changes and remove.
- Local persistent wishlist IDs.
- Recently viewed products.
- Cart CRO summary and checkout review entry point.
- AutoID AI UI with shopping/support quick actions, product recommendations and support-resource results.
- Account login preserved via existing v1 auth endpoint.
- Existing order listing preserved via existing v1 order endpoint.
- Support resource discovery inside the app flow.

## WordPress bridge

Plugin: `AutoID Mobile Commerce Bridge` v0.3.0.

The bridge is additive and designed to coexist with the existing AutoID Mobile API plugin. It does not replace or modify existing auth/order/payment routes.

### New endpoints

- `GET /wp-json/autoid-app/v1/home`
- `GET /wp-json/autoid-app/v1/products`
- `GET /wp-json/autoid-app/v1/products/{id}`
- `GET /wp-json/autoid-app/v1/categories`
- `GET /wp-json/autoid-app/v1/search?q=`
- `GET /wp-json/autoid-app/v1/support?search=`
- `GET /wp-json/autoid-app/v1/brands`

### Existing endpoints preserved

- `GET /wp-json/autoid-app/v1/health`
- `GET /wp-json/autoid-app/v1/app-config`
- `POST /wp-json/autoid-app/v1/auth/login`
- `POST /wp-json/autoid-app/v1/auth/google`
- `POST /wp-json/autoid-app/v1/auth/refresh`
- `POST /wp-json/autoid-app/v1/auth/logout`
- `GET /wp-json/autoid-app/v1/me`
- `GET /wp-json/autoid-app/v1/me/orders`
- `GET /wp-json/autoid-app/v1/me/orders/{id}`
- existing address and Stripe routes from the current bridge

## Deferred / requires further server integration

- Server-synchronized cart between devices.
- Secure checkout write endpoint / order creation.
- Stripe PaymentSheet and Google Pay flow in the Android client.
- Google Credential Manager UI in Android (server-side Google token verification remains preserved in existing bridge).
- Server-synchronized wishlist.
- Full variation selector and variation pricing.
- Attribute filter bottom sheet generated dynamically from WooCommerce attributes.
- Reviews and ratings.
- Coupons.
- RFQ write flow.
- Company/VAT lookup/autofill.
- FCM push notifications + Notification Center backend.
- AWB / tracking / invoices endpoint integration.
- LLM `/ai/chat` endpoint connected to the existing AutoID AI service. v0.3 AI UI already performs contextual product and support retrieval; generative answers and tool actions remain to be connected server-side.
- AI tool actions such as add-to-cart directly from a model response.
- Embedded PDF/video native viewer.
- Product comparison table and AI comparison explanation.
- Analytics provider wiring. Event taxonomy is reserved for GA4/Firebase implementation.

## Security

- No WooCommerce consumer secret in APK.
- Catalog routes are read-only.
- Sensitive existing routes remain token-authenticated in the existing AutoID Mobile API.
- Checkout write is intentionally not enabled until authenticated server-side validation is integrated and tested.

## Breaking changes

None intended. The v0.3 commerce plugin is additive and the Android package remains `ro.autoid.app`.
