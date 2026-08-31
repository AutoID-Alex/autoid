#!/usr/bin/env bash
set -euo pipefail

bash ci/prepare_v1016_release.sh
python3 ci/apply_v1017_account_checkout.py
python3 ci/patch_mobile_v118_account.py
php -l wordpress/autoid-mobile-commerce/autoid-mobile-commerce.php

echo 'Prepared AutoID Android v1.0.17 + AutoID Mobile v1.1.8'
