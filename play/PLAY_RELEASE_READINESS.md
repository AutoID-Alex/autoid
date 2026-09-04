# AutoID Android — Google Play release readiness

App name: **AutoID**  
Tagline: **Professional Solutions**  
Package: `ro.autoid.app`  
Primary market: Romania / B2B AutoID equipment and support  
Website: `https://www.autoid.ro/`

## Already implemented before Play Console account

- Native Android app with target SDK 36.
- HTTPS-only network policy (`usesCleartextTraffic=false`).
- App backup disabled for account/session data (`allowBackup=false`).
- No broad contacts/SMS/call-log/location/media-library permissions.
- Google Credential Manager login.
- Stripe / Google Pay for physical goods checkout.
- WooCommerce account, orders, RFQ and address management.
- Native privacy/consent controls.
- Native notification permission/FCM support and in-app notification inbox.
- Native account deletion request from Account details.
- External account deletion web page: `https://www.autoid.ro/sterge-cont-autoid/` (created by AutoID Mobile 1.1.30 after plugin activation/admin bootstrap).
- Privacy policy: `https://www.autoid.ro/politica-de-confidentialitate/`.
- Release workflow prepared for APK + Android App Bundle (AAB).
- Production signing workflow designed to consume an upload keystore only from GitHub Actions secrets.

## Play Console values to use when the account exists

### App identity
- App name: AutoID
- Default language: Romanian (ro-RO)
- App or game: App
- Free or paid: Free
- Category: Shopping (secondary positioning: Business)
- Contains ads: No

### Contact
- Website: https://www.autoid.ro/
- Privacy policy: https://www.autoid.ro/politica-de-confidentialitate/
- Account deletion URL: https://www.autoid.ro/sterge-cont-autoid/
- Support email: use the monitored AutoID support/contact mailbox selected by the company for Play Console.

### App access
The public catalog, product pages, cart, RFQ entry and AI/support entry can be inspected without mandatory login. Account-only functions (order history, saved addresses, RFQ history) require an AutoID account. Before review, provide Google with one non-privileged test account if Play Console requests credentials for account-only functionality.

### Payments
The app sells physical products/services. Checkout uses the merchant's payment processor (Stripe / Google Pay) and not Google Play Billing.

## Data Safety draft — verify against the final production build before submitting

The following categories are used by core commerce/account functionality and are transmitted over HTTPS:

- Personal info: name, email address, phone number.
- Address: shipping/billing address.
- Purchase history: WooCommerce orders and order status.
- Financial/payment info: payment processing is handled by the payment provider; the app should not claim to store full card numbers.
- User content: RFQ notes and AI/support chat messages supplied by the user.
- App activity: product/cart/RFQ interactions needed for app functionality; optional analytics must remain governed by consent.
- Device/app identifiers: FCM token / app-install identifiers for push notifications and service security.

Primary purposes:
- App functionality / account management.
- Order and RFQ fulfilment.
- Fraud prevention / security.
- Customer support.
- Optional analytics/personalization/marketing only after the corresponding consent.

Third-party/service processors to account for in the final Data Safety questionnaire:
- Google services used by Android (Credential Manager / Google Identity, Firebase Cloud Messaging, Google Pay as applicable).
- Stripe for card/payment processing where enabled.
- OpenAI-backed AutoID Support functionality is called server-side; no permanent OpenAI key exists in the APK. Review the final server-side data flow and privacy disclosure before filing Data Safety.

## Account deletion behavior

In-app path:
`Contul meu -> Detalii cont -> Solicita stergerea contului`

External path:
`https://www.autoid.ro/sterge-cont-autoid/`

The external flow verifies ownership through a one-time email confirmation link. The WordPress gateway records a deletion request and notifies the user/admin. Data that must be retained for accounting, tax, legal, anti-fraud or transaction-record obligations is not promised to be immediately erased and remains subject to the published privacy policy.

## Signing setup required once we decide the upload key

Create an upload keystore outside the repository and configure these GitHub Actions secrets:

- `PLAY_UPLOAD_KEYSTORE_B64`
- `PLAY_UPLOAD_KEY_ALIAS`
- `PLAY_UPLOAD_STORE_PASSWORD`
- `PLAY_UPLOAD_KEY_PASSWORD`

Never commit the production/upload keystore or passwords to Git.

When the Play Console account is created, opt into Play App Signing and register the upload certificate generated from this upload key. Google will manage the app-signing key; the CI upload key signs bundles submitted to Play.

## Before first production submission

- Create/verify organization developer account and company identity.
- Create app in Play Console with package `ro.autoid.app`.
- Enable Play App Signing.
- Add production upload-key certificate.
- Configure Google OAuth Android client with package `ro.autoid.app` and the correct Play/app-signing SHA fingerprints if required by the final authentication setup.
- Configure Google Pay production environment/merchant details if not already production-enabled.
- Complete App Content questionnaires: Data Safety, Privacy Policy, Ads, App Access, Content Rating, Target Audience, News/Health/Financial declarations only if applicable.
- Upload phone screenshots and graphics.
- Run internal/closed testing on the Play-delivered build before production.
- Test fresh install, update, Google login, account deletion, checkout, notifications, deep links, RFQ and AI chat using the Play-signed build.
