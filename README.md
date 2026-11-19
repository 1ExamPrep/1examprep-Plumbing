# Pass Your Plumbing Exam

Site: https://passyourplumbingexam.com (GitHub Pages, branch `main`, repo 1ExamPrep/1examprep-Plumbing).
Making another site from this one? Read [NEW-SITE.md](NEW-SITE.md).

## What is here

- 759 products from the 1 Exam Prep store, every product whose title contains "Plumb" (the Shopify collection
  "Pass Your Plumbing Exam site", ID 497919655993), on 163 license pages in 46 states and DC, plus ICC national exams
  and plumbing code books.
  - `/<state>/` names the board that licenses plumbers and lists its licenses.
  - `/<license>/` compares every package for one license.
  - `/<license>/<package>/` is the product page with Buy now straight to checkout.
- Licenses are worked out from product titles in `tools/plclass.py`: the package wording is cut off the end of the
  title, the state is found, and what is left is the license. `ALIASES` merges spellings of the same license. Test it with
  `python3 tools/plclass.py tools/catalog-titles.txt`.
- State facts (boards, exam vendors, code) live in `tools/plcopy.py`, checked November 19, 2026. Anything not confirmed
  says "check your candidate bulletin" rather than guessing.
- `python3 tools/check_pages.py . https://passyourplumbingexam.com` grades every page against
  "What every page and post needs to pass". At launch all 972 pages passed.

## Where the products come from

Two ways, same output (`shared/catalog.js`, `store/products-full.json`):

1. **Pull plumbing catalog** workflow (`.github/workflows/pull-catalog.yml`, runs `tools/pull_storefront.py`): reads the
   public 1examprep.com product feed, no token needed. Runs every Monday and on demand (Actions, Run workflow).
2. **The dashboard** sync once the site is connected, with collection 497919655993.

Long Shopify descriptions are split into page sections by `sectionize()` in `build.py` so no section passes 400 words,
and any phone number in a description other than (877) 775-9400 is replaced with it.

## Design

Design 7, Plumbing Flow (`shared/themes/7.css`, `"design": 7` in `site-config.json`): a glass navy header, moving water
behind every hero (WebGL, `shared/flow.js`, off for reduced motion), a glass two-step finder, Inter Tight with Instrument
Serif italics, logo orange buttons and water blue accents. Reading sections stay light.

Logo: `brand/logo-source.png` (full logo) and `brand/icon-source.png` (the wrench and drop icon). The header and footer
use `shared/logo-nav-light.png`, a copy with the navy lettering turned white for the dark header.

## Still to do

- GitHub Pages: Settings, Pages, deploy from `main` / root, custom domain passyourplumbingexam.com, DNS (four A records
  185.199.108.153, .109.153, .110.153, .111.153 and a `www` CNAME to 1examprep.github.io), then Enforce HTTPS.
- Dashboard: connect the site with collection 497919655993, put the siteKey in `site-config.json`.
- First blog post (the blog index is ready).
