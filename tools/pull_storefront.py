#!/usr/bin/env python3
"""Pull every plumbing product from the public 1examprep.com storefront feed and rebuild the catalog.

No Shopify token needed: it reads https://1examprep.com/products.json (products published to the Online Store),
keeps the ones whose title matches the "Pass Your Plumbing Exam site" collection rule (title contains "Plumb"),
turns them into the same product nodes tools/sync_shopify.py makes, and runs tools/build_catalog.py.

The dashboard sync (Admin API, collection 497919655993) does the same job once the site is connected; either one
can run, the catalog files are the same shape.

Usage:  python3 tools/pull_storefront.py      exit 0 = unchanged, 3 = catalog changed, other = error
"""
import json, os, re, sys, time, subprocess, urllib.request, urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORE = os.environ.get("STORE_URL", "https://1examprep.com").rstrip("/")
MATCH = re.compile(os.environ.get("TITLE_MATCH", r"plumb"), re.I)

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "passyourplumbingexam-catalog/1.0", "Accept": "application/json"})
    for attempt in range(6):
        try:
            with urllib.request.urlopen(req, timeout=60) as r: return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code in (429, 430, 503) and attempt < 5: time.sleep(3 + attempt * 4); continue
            raise

def strip_html(h):
    t = re.sub(r"<[^>]+>", " ", h or "")
    t = t.replace("&nbsp;", " ").replace("&amp;", "&").replace("&#39;", "'").replace("&quot;", '"')
    return re.sub(r"\s+", " ", t).strip()

products, page = [], 1
while True:
    d = get("%s/products.json?limit=250&page=%d" % (STORE, page))
    batch = d.get("products") or []
    if not batch: break
    products += batch; page += 1
    time.sleep(0.6)
print("storefront products: %d" % len(products))

nodes = []
for p in products:
    if not MATCH.search(p.get("title", "")): continue
    tags = p.get("tags") or []
    if isinstance(tags, str): tags = [x.strip() for x in tags.split(",") if x.strip()]
    imgs = [{"node": {"url": i.get("src", ""), "altText": i.get("alt")}} for i in (p.get("images") or [])[:6]]
    vs = p.get("variants") or []
    prices = [float(v.get("price") or 0) for v in vs] or [0.0]
    nodes.append({
        "id": "gid://shopify/Product/%s" % p["id"], "title": p["title"], "handle": p["handle"], "status": "ACTIVE",
        "productType": p.get("product_type", ""), "vendor": p.get("vendor", ""), "tags": tags,
        "onlineStoreUrl": "%s/products/%s" % (STORE, p["handle"]),
        "description": strip_html(p.get("body_html"))[:700], "descriptionHtml": p.get("body_html") or "",
        "featuredImage": imgs[0]["node"] if imgs else None, "images": {"edges": imgs},
        "priceRangeV2": {"minVariantPrice": {"amount": "%.2f" % min(prices)}, "maxVariantPrice": {"amount": "%.2f" % max(prices)}},
        "variants": {"edges": [{"node": {"id": "gid://shopify/ProductVariant/%s" % v["id"], "title": v.get("title", ""), "price": v.get("price"),
                                         "compareAtPrice": v.get("compare_at_price"), "availableForSale": v.get("available", True)}} for v in vs[:5]]},
    })
print("plumbing products: %d" % len(nodes))
if len(nodes) < 50:
    print("Too few products; refusing to rebuild from a suspicious pull."); sys.exit(4)

raw = os.path.join(ROOT, "tools", "raw-products.json")
json.dump(nodes, open(raw, "w", encoding="utf-8"))
titles = os.path.join(ROOT, "tools", "catalog-titles.txt")
open(titles, "w", encoding="utf-8").write("\n".join(sorted(n["title"] for n in nodes)) + "\n")
out = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "build_catalog.py"), raw], capture_output=True, text=True)
print(out.stdout.strip()); os.remove(raw)
if out.returncode != 0: print(out.stderr); sys.exit(out.returncode)
sys.exit(0 if out.stdout.startswith("unchanged") else 3)
