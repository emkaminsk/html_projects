# Quick how-to for SEO-validation

  1. Meta tags & Open Graph

  - Facebook Sharing Debugger: https://developers.facebook.com/tools/debug/ — paste your
  URL, shows OG tags as Facebook sees them
  - Twitter Card Validator: https://cards-dev.twitter.com/validator — preview Twitter card
   rendering
  - LinkedIn Post Inspector: https://www.linkedin.com/post-inspector/ — check LinkedIn
  preview

  2. Schema.org structured data

  - Google Rich Results Test: https://search.google.com/test/rich-results — paste
  mkhome.byst.re/store.html, validates JSON-LD
  - Schema.org Validator: https://validator.schema.org/ — more detailed schema validation

  3. Sitemap & robots.txt

  - Google Search Console (recommended to set up): submit sitemap at
  mkhome.byst.re/sitemap.xml
  - Quick manual check: visit mkhome.byst.re/robots.txt and mkhome.byst.re/sitemap.xml in
  the browser

  4. General SEO audit

  - Google Lighthouse: open Chrome DevTools → Lighthouse tab → run "SEO" audit on each
  page
  - PageSpeed Insights: https://pagespeed.web.google.com/ — includes SEO scoring

  5. Crawlability check

  - Google Search Console → URL Inspection tool — paste each page URL to see how Google
  renders it (confirms the <noscript> content is visible to crawlers)