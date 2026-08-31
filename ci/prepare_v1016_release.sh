#!/usr/bin/env bash
set -euo pipefail

bash ci/prepare_v1015_release.sh
python3 ci/apply_v1016_checkout_account.py
base64 -d ci/autoid-dev-keystore.b64 > android-v0.1/autoid-dev.keystore

rm -rf autoid-mobile
mkdir -p autoid-mobile
cp wordpress/autoid-mobile-commerce/autoid-mobile-commerce.php autoid-mobile/autoid-mobile.php
python3 ci/patch_mobile_v117_checkout.py
cp autoid-mobile/autoid-mobile.php wordpress/autoid-mobile-commerce/autoid-mobile-commerce.php
rm -rf autoid-mobile

php -l wordpress/autoid-mobile-commerce/autoid-mobile-commerce.php

echo 'Prepared AutoID Android v1.0.16 + AutoID Mobile v1.1.7'
