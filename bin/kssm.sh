#!/bin/env bash
# Pull sitemaps from kingsoopers and store them in target file
# Need these headers to trick the WAF into thinking we are a browser of sorts
# Somehow requests with python will fail even if these requests are set
curl \
  -H 'authority: www.kingsoopers.com' \
  -H 'cache-control: max-age=0' \
  -H 'upgrade-insecure-requests: 1' \
  -H 'user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246' \
  -H 'accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9' \
  -H 'sec-gpc: 1' \
  -H 'sec-fetch-site: none' \
  -H 'sec-fetch-mode: navigate' \
  -H 'sec-fetch-user: ?1' \
  -H 'sec-fetch-dest: document' \
  -H 'accept-language: en-US,en;q=0.9' \
  --compressed \
  -sS \
  -o "$1" \
  'https://www.kingsoopers.com/pdp-sitemap/kingsoopers-product-details-sitemap-1.xml' \
  'https://www.kingsoopers.com/pdp-sitemap/kingsoopers-product-details-sitemap-2.xml' \
  'https://www.kingsoopers.com/pdp-sitemap/kingsoopers-product-details-sitemap-3.xml' \
  'https://www.kingsoopers.com/pdp-sitemap/kingsoopers-product-details-sitemap-4.xml' \
  'https://www.kingsoopers.com/pdp-sitemap/kingsoopers-product-details-sitemap-5.xml' \
  'https://www.kingsoopers.com/pdp-sitemap/kingsoopers-product-details-sitemap-6.xml' \
  > /dev/null
