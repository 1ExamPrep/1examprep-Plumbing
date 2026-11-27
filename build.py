#!/usr/bin/env python3
"""Build passyourplumbingexam.com (plumber, plumbing contractor and inspector exam prep, grouped by state).

  python3 build.py

Pages:
  /                               every license, grouped (contractor, business, trades, officials, codes)
  /<license>/                     one page per license class with all its packages, a comparison table and an FAQ
  /<license>/<package>/           one page per product, Buy now goes straight to checkout
  /faq/  /blog/  /search/  /admin/  robots.txt  llms.txt  agents.md  sitemap.xml  index.md copies

Products come from shared/catalog.js + store/products-full.json (written by the dashboard sync or by
tools/sync_shopify.py). Classes and package types are worked out from the titles by tools/vaclass.py,
and the license copy lives in tools/vacopy.py. Previously generated folders are removed first.
"""
import json, os, re, sys, shutil, html, datetime, collections

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import schemakit
import blogkit
import plclass as vaclass, plcopy as vacopy  # the Virginia names are kept so the shared code reads the same in every repo

tpl = open(os.path.join(ROOT, "store", "template.html"), encoding="utf-8").read()
ptpl = open(os.path.join(ROOT, "store", "product.html"), encoding="utf-8").read()
FULL = json.load(open(os.path.join(ROOT, "store", "products-full.json"), encoding="utf-8"))
cat_js = open(os.path.join(ROOT, "shared", "catalog.js"), encoding="utf-8").read()
_end = cat_js.index(";\nwindow.CATALOG_STATES") if ";\nwindow.CATALOG_STATES" in cat_js else cat_js.rindex(";")
CATALOG = json.loads(cat_js[cat_js.index("window.CATALOG=") + len("window.CATALOG="):_end])
CFG = json.load(open(os.path.join(ROOT, "site-config.json"), encoding="utf-8"))
SITE = CFG["siteUrl"].rstrip("/") + "/" if CFG.get("siteUrl") else None
BRAND = CFG.get("brand", "1 Exam Prep")
FUL = CFG.get("fulfillment") or {"name": "1 Exam Prep", "url": CFG.get("storeUrl", "https://1examprep.com"), "note": ""}
STORE = CFG.get("storeUrl", "https://1examprep.com").rstrip("/")
WM = CFG.get("wordmark") or [BRAND, "", ""]
_nb = lambda x: html.escape(x).replace(" ", "&nbsp;")
WORDMARK_TEXT = "%s<span>%s</span>%s" % (_nb(WM[0]), _nb(WM[1]), _nb(WM[2])) if WM[1] else html.escape(WM[0])
LOGO_NAV = CFG.get("logoNav") if CFG.get("logoNav") and os.path.exists(os.path.join(ROOT, CFG.get("logoNav"))) else None
HAS_PNG_ICONS = os.path.exists(os.path.join(ROOT, "shared", "favicon.png"))
NAV_W, NAV_H = 140, 52
if LOGO_NAV:
    try:
        from PIL import Image as _I
        _w, _h = _I.open(os.path.join(ROOT, LOGO_NAV)).size; NAV_W = round(_w * NAV_H / _h)
    except Exception: pass
TODAY = datetime.date.today().isoformat()
LAUNCH = CFG.get("launched", TODAY)

# ---------- products, classes ----------
PRODUCTS = vaclass.assign([p for p in CATALOG if p.get("variants")])
for _p in PRODUCTS:
    if not _p.get("image"): _p["image"] = "/shared/logo-mark.png"  # stand-in catalog has no photos
GROUP_NAME = {g: n for g, n, _ in vaclass.GROUPS}
GROUP_BLURB = {g: b for g, _, b in vaclass.GROUPS}
CLASSES = {}  # slug -> dict
for p in PRODUCTS:
    c = CLASSES.setdefault(p["cls"], {"slug": p["cls"], "name": p["clsName"], "group": p["group"], "products": []})
    c["products"].append(p)
for c in CLASSES.values():
    c["products"].sort(key=lambda p: (p["region"] != vaclass.STATE, p["rank"], float(p["price"]), p["title"]))
    c["lo"] = min(float(p["price"]) for p in c["products"]); c["hi"] = max(float(p["price"]) for p in c["products"])
def _lic_key(c):
    n = c["name"].lower(); city = 1 if re.match(r"^(commerce city|minneapolis|st\. paul|chicago|kansas city|springfield|reading|casper|cleveland)", n) else 0
    lvl = 0 if "journey" in n else 1 if "master" in n else 2 if "contractor" in n or "class" in n else 3 if ("inspector" in n or "examiner" in n) else 2
    return (city, lvl, -len(c["products"]), c["name"])
ORDER = [c["slug"] for g, _, _ in vaclass.GROUPS for c in sorted([x for x in CLASSES.values() if x["group"] == g], key=_lic_key)]
NONSTATE = ("books", "icc")
def classes_in(group): return [CLASSES[s] for s in ORDER if s in CLASSES and CLASSES[s]["group"] == group]
STATE_SLUG = {g: (vaclass.STATE_NAME[g].lower().replace(" ", "-") if g in vaclass.STATE_NAME else None) for g, _, _ in vaclass.GROUPS}
def state_url(g, rel=""):
    """The state page for a group, or the license page for groups without one (reference books)."""
    if STATE_SLUG.get(g): return "%s%s/" % (rel, STATE_SLUG[g])
    cl = classes_in(g); return "%s%s/" % (rel, cl[0]["slug"]) if cl else rel or "./"
def state_name(g): return vaclass.STATE_NAME.get(g, GROUP_NAME.get(g, ""))
UNCLASSIFIED = [p["title"] for p in PRODUCTS if p["cls"] == "other" or p["type"] == "other"]

# ---------- helpers ----------
def wordmark(rel):
    if LOGO_NAV: return '<img class="brand-img" src="%s%s" alt="%s" width="%d" height="%d" decoding="async">' % (rel, LOGO_NAV, html.escape(BRAND), NAV_W, NAV_H)
    return WORDMARK_TEXT
def promo_html():
    return ('<div class="tx-promo" role="note"><div class="wrap"><span>%s</span><span>Books ship from %s</span><span>Questions? <a href="tel:%s">%s</a></span></div></div>'
            % (esc(vacopy.PROMO), esc(FUL["name"]), CFG["phoneTel"], esc(CFG["phone"])))
def rail_html(rel):
    """Every license in one list, for designs that show a side index. Hidden unless a design turns it on."""
    out = []
    for g, gname, _ in vaclass.GROUPS:
        cl = classes_in(g)
        if not cl: continue
        out.append('<p class="tx-rail-h">%s</p><ul>%s</ul>' % (esc(gname), "".join('<li><a href="%s%s/">%s</a></li>' % (rel, c["slug"], esc(c["name"])) for c in cl)))
    return '<nav class="tx-rail" aria-label="Every plumbing license">%s</nav>' % "".join(out)
def brand_tokens(out, rel=None):
    if rel is None:
        m = re.search(r'href="(/|(?:\.\./)*)shared/base\.css"', out); rel = m.group(1) if m else ""
    if 'class="tx-promo"' not in out:
        out = out.replace('<a class="skip" href="#main">Skip to content</a>', '<a class="skip" href="#main">Skip to content</a>\n' + promo_html() + "\n" + rail_html(rel), 1)
    return (out.replace("{{WORDMARK}}", wordmark(rel)).replace("{{BRAND}}", html.escape(BRAND)).replace("{{FULFILL_NAME}}", html.escape(FUL["name"]))
               .replace("{{FULFILL_URL}}", html.escape(FUL["url"])).replace("{{PHONE}}", html.escape(CFG["phone"])).replace("{{PHONE_TEL}}", CFG["phoneTel"]))
def nice_day(d):
    try: return datetime.date.fromisoformat(d[:10]).strftime("%B %-d, %Y")
    except Exception: return d
def span(lo, hi):
    return ("at %s" % money(lo)) if abs(float(lo) - float(hi)) < 0.005 else ("from %s to %s" % (money(lo), money(hi)))


def money(v):
    v = float(v); return ("$%s" % format(int(v), ",")) if v == int(v) else ("$%s" % format(v, ",.2f"))
def esc(s): return html.escape(str(s))
def trim_desc(d, n=158):
    d = re.sub(r"\s+", " ", d).strip()
    if len(d) <= n: return d
    cut = d[:n].rsplit(" ", 1)[0].rstrip(",;:")
    return cut + ("" if cut.endswith(".") else ".")
def fit_title(*options, lo=30, hi=60):
    for o in options:
        o = re.sub(r"\s+", " ", o).strip()
        if lo <= len(o) <= hi: return o
    o = re.sub(r"\s+", " ", options[-1]).strip()
    return o[:hi].rsplit(" ", 1)[0] if len(o) > hi else o
def anchor_ids(out):
    out = brand_tokens(out)
    seen = set(re.findall(r'\sid="([^"]+)"', out))
    def rep(m):
        tag, attrs, inner = m.group(1), m.group(2) or "", m.group(3)
        if re.search(r'\sid=', attrs): return m.group(0)
        base = re.sub(r"[^a-z0-9]+", "-", html.unescape(re.sub(r"<[^>]+>", "", inner)).lower()).strip("-")[:60] or "section"
        i, hid = 1, base
        while hid in seen: i += 1; hid = "%s-%d" % (base, i)
        seen.add(hid)
        return '<%s%s id="%s">%s</%s>' % (tag, attrs, hid, inner, tag)
    return finalize(re.sub(r"<(h[23])(\s[^>]*)?>(.*?)</\1>", rep, out, flags=re.S))

SKIP_URL = re.compile(r"^(?:[a-z][a-z0-9+.-]*:|//|/|#|\?|\{\{)", re.I)
def finalize(out):
    """Last pass over every page before it is written.
    Relative links and asset paths (../license/package/) become root-relative (/license/package/), so tools that count
    internal links by a leading slash see them, and an article:published_time / article:modified_time pair is added for
    tools that look for a date outside the schema. Pages without a canonical URL (noindex pages) keep relative links."""
    from urllib.parse import urljoin, urlsplit
    m = re.search(r'<link rel="canonical" href="(https?://[^"]+)"', out)
    if m:
        base = m.group(1)
        def root(mm):
            attr, q, url = mm.group(1), mm.group(2), mm.group(3)
            if not url or SKIP_URL.match(url): return mm.group(0)
            u = urlsplit(urljoin(base, url))
            return "%s=%s%s%s%s%s" % (attr, q, u.path or "/", ("?" + u.query) if u.query else "", ("#" + u.fragment) if u.fragment else "", q)
        out = re.sub(r'\b(href|src)=(["\'])([^"\']*)\2', root, out)
    if 'property="article:modified_time"' not in out:
        out = out.replace("</head>", '<meta property="article:published_time" content="%s">\n<meta property="article:modified_time" content="%s">\n</head>' % (LAUNCH, TODAY), 1)
    return out
def absurl(path): return (SITE + path) if SITE else "/" + path
def ld(obj): return '<script type="application/ld+json">%s</script>\n' % json.dumps(obj, ensure_ascii=False)
def org_ld():
    o = {"@context": "https://schema.org", "@type": "Organization", "name": BRAND, "legalName": CFG.get("legalName", BRAND), "url": SITE or STORE,
         "logo": CFG.get("logo"), "telephone": CFG.get("phoneTel"), "email": CFG.get("email"), "sameAs": [v for v in CFG.get("social", {}).values() if v],
         "parentOrganization": {"@type": "Organization", "name": FUL["name"], "url": FUL["url"]} if FUL["name"] != BRAND else None,
         "areaServed": {"@type": "Country", "name": "United States"},
         "contactPoint": [{"@type": "ContactPoint", "telephone": CFG.get("phoneTel"), "email": CFG.get("email"), "contactType": "sales", "areaServed": "US", "availableLanguage": "English"}]}
    return {k: v for k, v in o.items() if v}
def publisher_ld():
    o = {"@type": "Organization", "name": BRAND, "url": SITE or STORE, "logo": {"@type": "ImageObject", "url": CFG.get("logo")} if CFG.get("logo") else None,
         "telephone": CFG.get("phoneTel"), "email": CFG.get("email")}
    return {k: v for k, v in o.items() if v}
def website_ld():
    return {"@context": "https://schema.org", "@type": "WebSite", "name": BRAND, "url": SITE or "/", "publisher": publisher_ld(),
            "potentialAction": {"@type": "SearchAction", "target": {"@type": "EntryPoint", "urlTemplate": absurl("search/?q={search_term_string}")}, "query-input": "required name=search_term_string"}}
def crumbs_ld(items):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "item": absurl(pth)} for i, (n, pth) in enumerate(items)]}
def faq_ld(pairs):
    return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": re.sub(r"<[^>]+>", "", a)}} for q, a in pairs]}

def head_extra(path, title, desc, image, rel, noindex=False, extra_ld=(), page_type="WebPage", about="Plumbing license exams"):
    desc = trim_desc(desc)
    url = absurl(path) if SITE else None
    h = ['<meta name="robots" content="%s">' % ("noindex, nofollow" if noindex else "index, follow, max-image-preview:large")]
    if url: h.append('<meta property="og:url" content="%s">' % esc(url))
    if url and not noindex: h.append('<link rel="alternate" type="text/markdown" title="Markdown version for AI assistants" href="%s">' % esc(url + "index.md"))
    h += ['<meta property="og:site_name" content="%s">' % esc(BRAND), '<meta property="og:locale" content="en_US">', '<meta name="twitter:card" content="summary_large_image">',
          '<meta name="twitter:title" content="%s">' % esc(title), '<meta name="twitter:description" content="%s">' % esc(desc)]
    if image: h.append('<meta name="twitter:image" content="%s">' % esc(image))
    if CFG.get("social", {}).get("twitter"): h.append('<meta name="twitter:site" content="@%s">' % CFG["social"]["twitter"].rstrip("/").split("/")[-1])
    h.append('<meta name="theme-color" content="#020c1b">')
    h.append('<script>window.SITE=%s;</script>' % json.dumps({"brand": BRAND, "storeUrl": STORE, "fulfillment": FUL["name"], "cartTag": CART_TAG, "phone": CFG.get("phone", ""), "aiFinder": CFG.get("aiFinderUrl", "")}))
    if not LOGO_NAV: h.append('<style>.nav .brand{font-size:1.05rem;line-height:1.05;max-width:46vw}@media (max-width:720px){.nav .brand{font-size:.9rem}}</style>')
    h.append('<link rel="icon" href="%sshared/%s">' % (rel, "favicon.png\" type=\"image/png\" sizes=\"64x64" if HAS_PNG_ICONS else "favicon.svg\" type=\"image/svg+xml"))
    h.append('<link rel="apple-touch-icon" href="%sshared/apple-touch-icon.png">' % rel); h.append('<link rel="manifest" href="%smanifest.webmanifest">' % rel)
    if CFG.get("googleSiteVerification"): h.append('<meta name="google-site-verification" content="%s">' % esc(CFG["googleSiteVerification"]))
    if CFG.get("gtagId"): h.append('<script async src="https://www.googletagmanager.com/gtag/js?id=%s"></script><script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag("js",new Date());gtag("config","%s",{"send_page_view":true});</script>' % (CFG["gtagId"], CFG["gtagId"]))
    if CFG.get("gtmId"): h.append("<script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],j=d.createElement(s);j.async=true;j.src='https://www.googletagmanager.com/gtm.js?id='+i;f.parentNode.insertBefore(j,f);})(window,document,'script','dataLayer','%s');</script>" % CFG["gtmId"])
    if CFG.get("metaPixelId"): h.append("<script>!function(f,b,e,v,n,t,s){if(f.fbq)return;n=f.fbq=function(){n.callMethod?n.callMethod.apply(n,arguments):n.queue.push(arguments)};if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;t.src=v;s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}(window,document,'script','https://connect.facebook.net/en_US/fbevents.js');fbq('init','%s');fbq('track','PageView');</script>" % CFG["metaPixelId"])
    if CFG.get("dashboardUrl") and CFG.get("siteKey"): h.append('<script>window.__dashCustom=true;</script>')  # the tracker itself goes before </body>, see the end of this file
    for o in extra_ld: h.append(ld(o).rstrip())
    if url and not noindex and page_type:
        h.append(ld({"@context": "https://schema.org", "@type": page_type, "@id": url, "url": url, "name": title, "description": desc, "inLanguage": "en-US", "datePublished": LAUNCH, "dateModified": TODAY,
                     "isPartOf": {"@type": "WebSite", "url": SITE, "name": BRAND}, "publisher": publisher_ld(), "about": {"@type": "Thing", "name": about}}).rstrip())
    return "\n".join(h) + "\n"

ICON_PHONE = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1.9.4 1.8.7 2.7a2 2 0 0 1-.5 2.1L8 9.8a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.9.3 1.8.6 2.7.7a2 2 0 0 1 1.7 2z"/></svg>'
ICON_SEARCH = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>'
def nav_tools(cta_html):
    es = ('<a class="nav-lang" data-lang href="https://translate.google.com/translate?sl=en&amp;tl=es&amp;u=%s" hreflang="es" lang="es" rel="nofollow noopener" aria-label="Ver esta p&aacute;gina en espa&ntilde;ol">'
          '<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.5 2.7 3.8 5.7 3.8 9s-1.3 6.3-3.8 9c-2.5-2.7-3.8-5.7-3.8-9S9.5 5.7 12 3z"/></svg><span>Espa&ntilde;ol</span></a>' % esc(SITE or "https://passyourplumbingexam.com/"))
    return ('<div class="nav-tools">' + es + '<a class="nav-phone" href="tel:%s" aria-label="Call %s">%s<span>%s</span></a>'
            '<button type="button" class="nav-search" data-sopen aria-label="Search the site">%s</button>%s</div>' % (CFG["phoneTel"], CFG["phone"], ICON_PHONE, esc(CFG["phone"]), ICON_SEARCH, cta_html))
POPULAR = ["texas-journeyman-plumber", "florida-plumbing-contractor", "arizona-plumbing-commercial-contractor-c-37", "georgia-master-plumber-class-ii-unrestricted", "north-carolina-plumbing-class-i-contractor", "icc-journeyman-plumber-icc-g25-n"]
def footer(rel):
    return _footer(rel).replace("{{FOOTLOGO}}", '<img class="brand-img" src="%sshared/logo-nav-light.png" alt="%s" width="208" height="69" decoding="async">' % (rel or "/", esc(BRAND)))
def _footer(rel):
    home = rel or "./"
    soc = "".join('<li><a href="%s" rel="noopener" target="_blank">%s</a></li>' % (esc(u), k.capitalize()) for k, u in CFG.get("social", {}).items() if u)
    pop = "".join('<li><a href="%s%s/">%s</a></li>' % (rel, s_, esc(state_name(CLASSES[s_]["group"]) + " " + CLASSES[s_]["name"].split(" (")[0])) for s_ in POPULAR if s_ in CLASSES)
    sts = "".join('<li><a href="%s">%s</a></li>' % (state_url(g, rel), esc(n)) for g, n, _ in vaclass.GROUPS if g not in NONSTATE and classes_in(g))
    return ('<footer class="site-footer"><div class="wrap"><div class="cols">'
            '<div><a class="brand" href="%s">{{FOOTLOGO}}</a><p>%s</p><p class="contact"><a href="tel:%s">%s</a><a href="mailto:%s">%s</a></p></div>'
            '<nav aria-label="Popular licenses"><h2>Popular licenses</h2><ul>%s<li><a href="%s#states">All %d licenses</a></li></ul></nav>'
            '<nav aria-label="States" class="foot-states"><h2>States</h2><ul>%s</ul></nav>'
            '<nav aria-label="Help"><h2>Help</h2><ul><li><a href="%sfaq/">FAQ</a></li><li><a href="%sblog/">Blog</a></li><li><a href="%splumbing-code-books/">Code books</a></li><li><a href="%ssearch/">Search</a></li>%s</ul></nav></div>'
            '<p class="fine"><strong>%s</strong> &copy; <span data-year>%s</span> &middot; %s Prices and availability come from the fulfillment store and were last checked <time datetime="%s">%s</time>; the price at checkout is the one that applies. Not affiliated with any state licensing board, city, PSI, Pearson VUE, Prov, GITS, ICC or IAPMO. Buying study material does not grant exam eligibility or a license.</p></div></footer>'
            % (home, esc(CFG.get("tagline", "")), CFG["phoneTel"], esc(CFG["phone"]), CFG["email"], CFG["email"], pop, home, len(CLASSES), sts, rel, rel, rel, rel, soc,
               esc(BRAND), TODAY[:4], esc(FUL.get("note") or ("Orders are processed and shipped by %s, our fulfillment center." % FUL["name"])), TODAY, nice_day(TODAY)))
_footer_base = footer
def footer(rel):
    return _footer_base(rel).replace('faq/">FAQ</a></li>', 'faq/">FAQ</a></li><li><a href="%sreviews/">Customer reviews</a></li>' % rel, 1)
def takeaways_html(items, title="Key takeaways", hid="key-takeaways"):
    items = [i for i in items if i][:5]
    if not items: return ""
    return ('<aside class="takeaways" aria-labelledby="%s"><h2 id="%s">%s</h2><ul>%s</ul><p class="upd">Updated <time datetime="%s">%s</time> · prices checked against the %s store</p></aside>'
            % (hid, hid, title, "".join("<li>%s</li>" % esc(i) for i in items), TODAY, nice_day(TODAY), esc(FUL["name"])))
def faq_html(pairs, open_first=True):
    return '<div class="faq">%s</div>' % "".join('<details%s><summary>%s</summary><p>%s</p></details>' % (" open" if open_first and i == 0 else "", esc(q), a if "<a " in a else esc(a)) for i, (q, a) in enumerate(pairs))
def sources_html(group, extra=()):
    items = list(vacopy.SOURCES.get(group, vacopy.MAIN_SOURCES)) + [x for x in extra if x not in vacopy.SOURCES.get(group, vacopy.MAIN_SOURCES)]
    return ('<section class="wrap sources" aria-labelledby="h-sources"><h2 id="h-sources">Sources</h2><ul>%s</ul><p class="upd">Licensing facts checked against these pages; last updated <time datetime="%s">%s</time>. Rules change, so confirm with the board before you apply.</p></section>'
            % ("".join('<li><a href="%s" rel="noopener" target="_blank">%s</a></li>' % (esc(u), esc(n)) for n, u in items), TODAY, nice_day(TODAY)))
SITE_HOST = re.sub(r"^www\.", "", (SITE or "").split("//")[-1].strip("/"))
CART_TAG = ("?attributes%%5BSite%%5D=%s&ref=%s" % (SITE_HOST, SITE_HOST)) if SITE_HOST else ""  # tags the Shopify order with this site so the dashboard counts it here
def cart(vid):
    if str(vid).startswith("pv-"): return "%s/search?type=product&q=%s" % (STORE, str(vid)[3:])  # stand-in catalog: no variant ids yet
    return "%s/cart/%s:1%s" % (STORE, vid, CART_TAG)
def region_note(p): return "" if p["region"] == vaclass.STATE else (" (%s edition)" % p["region"] if p["region"] != "Nationwide" else " (any state)")

def card_html(p, rel):
    c, n = float(p.get("compareAt") or 0), float(p["price"])
    save = ('<s class="pc-was">%s</s><span class="pc-save">Save %d%%</span>' % (money(c), round((c - n) / c * 100))) if c > n else ""
    more = ('<small style="color:var(--muted)"> to %s</small>' % money(p["maxPrice"])) if p.get("maxPrice") and float(p["maxPrice"]) > n else ""
    return ('<div class="sg" data-id="%s"><a class="pc-img" href="%s%s"><img src="%s" alt="%s" loading="lazy"></a><div class="pc-body"><span class="pc-tier">%s%s</span><p class="pc-name"><a href="%s%s" style="color:inherit;text-decoration:none">%s</a></p><p class="pc-what">%s.</p>'
            '<div class="pc-price"><span class="pc-now">%s</span>%s%s</div><div class="pc-actions"><a class="btn btn-buy" href="%s" rel="noopener" data-buy="%s">Buy now</a><a class="btn btn-details" href="%s%s">Details</a></div></div></div>'
            % (p["id"], rel, p["path"], esc(p["image"]), esc(p["short"]), esc(p["typeName"]), esc(region_note(p)), rel, p["path"], esc(p["short"]), esc(vacopy.TYPE_BLURB.get(p["type"], "exam prep").capitalize()), money(n), save, more, cart(p["variants"][0]["id"]), p["id"], rel, p["path"]))

def render(path_parts, title, desc, main, og_image=None, extra_ld=(), page_type="WebPage", route=None, sticky="", cta=None):
    rel = "../" * len(path_parts); path = "/".join(path_parts) + ("/" if path_parts else "")
    url = absurl(path) if SITE else None
    out = (tpl.replace("{{MAIN}}", main).replace("{{STICKY}}", sticky)
           .replace("{{ASSETS_HEAD}}", assets_head(rel))
           .replace("{{ASSETS_SEARCH}}", '<script src="%sshared/site-index.js" defer></script>\n<script src="%sshared/search.js" defer></script>\n<script src="%sshared/track.js" defer></script>\n<script src="%sshared/va.js" defer></script>' % (rel, rel, rel, rel))
           .replace("{{HEAD_EXTRA}}", head_extra(path, title, desc, og_image, rel, False, extra_ld, page_type))
           .replace("{{NAV_TOOLS}}", nav_tools(cta or '<a class="btn btn-buy" href="%s#states">Find my license</a>' % (rel or "./")))
           .replace("{{FOOTER}}", footer(rel)).replace("{{TITLE}}", esc(title)).replace("{{DESC}}", esc(trim_desc(desc)))
           .replace("{{CANONICAL}}", ('<link rel="canonical" href="%s">\n' % url) if url else "")
           .replace("{{OGIMAGE}}", ('<meta property="og:image" content="%s">\n' % esc(og_image)) if og_image else "")
           .replace("{{REL}}", rel).replace("{{HOME}}", rel or "./").replace("{{ROUTE}}", json.dumps(route or {"depth": len(path_parts)})))
    d = os.path.join(ROOT, *path_parts) if path_parts else ROOT
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(anchor_ids(out))
    return url

FAMILY = {}
for _f, _ts in [("Online courses and practice", ["online-practice-exams", "online-course", "study-guide-online-course"]),
                ("Study guides, books and tabs", ["tabs", "study-guide", "study-guide-flash-cards", "code-book", "book-package", "highlighted-tabbed", "study-guide-nec-tabs", "study-guide-calculations-nec"]),
                ("Combos and complete packages", ["super-combo", "jump-start-package", "complete-package", "ultimate-combo", "nec-course-package", "ultimate-package", "exam-prep-package"]),
                ("Live training and rentals", ["live-training", "rental-package", "ultimate-rental"]),
                ("All-inclusive and licensing services", ["licensing-service", "the-1-package"])]:
    for _t in _ts: FAMILY[_t] = _f

THEMES = json.load(open(os.path.join(ROOT, "shared", "themes", "themes.json"), encoding="utf-8"))
DESIGN = str(CFG.get("design", 0) or 0)
def assets_head(rel):
    """Stylesheets, then the chosen design. Any page can preview another design with ?design=1..5 (0 = original);
    the choice is kept for the browser session so you can click around the site in it."""
    base = '<link rel="stylesheet" href="%sshared/base.css">\n<link rel="stylesheet" href="%sshared/store.css">\n<link rel="stylesheet" href="%sshared/va.css">' % (rel, rel, rel)
    t = THEMES.get(DESIGN)
    static = ('\n<link rel="stylesheet" id="dFont" href="%s">\n<link rel="stylesheet" id="dCss" href="%sshared/themes/%s.css">' % (t["fonts"], rel, DESIGN)) if t else ""
    loader = ('\n<script>(function(){var T=%s,d="%s",m=location.search.match(/[?&]design=(\\d)/);try{if(m)sessionStorage.setItem("vaDesign",m[1]);d=sessionStorage.getItem("vaDesign")||d;}catch(e){}'
              'if(d==="%s")return;var a=document.getElementById("dCss"),b=document.getElementById("dFont");if(a)a.remove();if(b)b.remove();var t=T[d];if(!t)return;'
              'document.write(\'<link rel="stylesheet" href="\'+t+\'"><link rel="stylesheet" href="%sshared/themes/\'+d+\'.css">\');})();</script>'
              % (json.dumps({k: v["fonts"] for k, v in THEMES.items()}), DESIGN, DESIGN, rel))
    ls = str(CFG.get("licenseList", 1) or 1)
    lsw = ('\n<script>(function(){var L=%s,d="%s",ds="%s",m=location.search.match(/[?&]list=(\\d)/);try{ds=sessionStorage.getItem("vaDesign")||ds;if(m)sessionStorage.setItem("vaList",m[1]);d=sessionStorage.getItem("vaList")||L[ds]||d;}catch(e){}var h=document.documentElement;h.setAttribute("data-list",d);h.setAttribute("data-design",ds);})();</script>'
           % (json.dumps({k: str(v.get("list", "")) for k, v in THEMES.items() if v.get("list")}), ls, DESIGN))
    return base + static + loader + lsw + '\n<script src="%sshared/flow.js" defer></script>' % rel

# ---------- copy helpers ----------
def scope(c):
    if c["group"] == "officials": return vacopy.OFFICIAL_SCOPE.format(name=c["name"])
    return vacopy.SCOPE.get(c["slug"], ("The %s %s license comes from %s." % (state_name(c["group"]), c["name"], vacopy.WHO_ISSUES[c["group"]])) if c["group"] != "books" else "Plumbing code books and references that appear on many state exam reference lists.")
def count_words(s): return len(re.sub(r"<[^>]+>", " ", s).split())
def plural(n, w): return "%d %s%s" % (n, w, "" if n == 1 else "s")
def cheapest(c): return min(c["products"], key=lambda p: float(p["price"]))
def priciest(c): return max(c["products"], key=lambda p: float(p["price"]))
def is_online(p): return p["type"] in ("online-course", "online-practice-exams", "licensing-service") or "Online" in p["title"]
def has_books(p): return p["type"] not in ("online-course", "online-practice-exams", "licensing-service")
def delivery(p):
    if p["type"] in ("online-course", "online-practice-exams"): return "Online access arrives by email after purchase"
    if p["type"] == "licensing-service": return "The service starts after purchase; we contact you for the details"
    if p["type"] in ("live-training", "rental-package", "ultimate-rental", "the-1-package", "study-guide-online-course", "complete-package", "ultimate-combo", "nec-course-package", "jump-start-package"):
        return "Books ship from our fulfillment center; online parts arrive by email"
    return "Books ship from our fulfillment center, %s" % FUL["name"]
def who_issues(c): return vacopy.WHO_ISSUES[c["group"]]
def open_book(c): return vacopy.OPEN_BOOK[c["group"]]
def facts_for(c): return vacopy.CLASS_FACTS.get(c["slug"], []) + vacopy.GROUP_FACTS[c["group"]]
def old_code(c, p):
    """Packages written to the 2021 IPC, older than the 2024 editions in the 2026 packages."""
    return p.get("year") and p["year"] < "2026" and p["region"] in (vaclass.STATE, "Nationwide")
OLD_CODE_NOTE = "Check the code edition in your candidate bulletin: many exams now use the 2024 editions, which the 2026 packages cover."
def class_faq(c):
    ps = c["products"]; n = c["name"]
    price_list = "; ".join("%s %s" % (p["typeName"] + region_note(p), money(p["price"])) for p in ps[:6]) + ("; and %d more" % (len(ps) - 6) if len(ps) > 6 else "")
    q = [("How much does %s exam prep cost?" % n, "%s exam prep runs %s across %s: %s." % (n, span(c["lo"], c["hi"]), plural(len(ps), "option"), price_list)),
         ("Is the %s exam open book?" % n, open_book(c)),
         ("Who issues the %s license in %s?" % (n, state_name(c["group"])), "It comes from %s. Buying a package here does not register you or make you eligible; the board approves you first, and the exam vendor schedules the test." % who_issues(c))]
    for qq, aa in vacopy.GROUP_FAQ.get(c["group"], []): q.append((qq.format(name=n), aa))
    cf = vacopy.CLASS_FACTS.get(c["slug"])
    if cf: q.append(("What is the %s exam like?" % n, " ".join(cf)))
    q.append(("Are these the real exam questions?", "No. Licensing exam questions are confidential. The courses and practice exams are original material written to the same subjects and format, with explanations that point to the reference section."))
    q.append(("How do the books and courses arrive?", "Printed and rental books ship from our fulfillment center, %s. Online courses and practice exams arrive by email after purchase, so you can start the same day. Call %s with any question first." % (FUL["name"], CFG["phone"])))
    return q
def choose_text(c):
    ps = c["products"]; by = {p["type"]: p for p in ps}; n = c["name"]
    lo, hi = cheapest(c), priciest(c)
    parts = ["The %s at %s is the lightest way into the %s exam: %s." % (lo["typeName"], money(lo["price"]), n, vacopy.TYPE_BLURB.get(lo["type"], "exam prep"))]
    if "highlighted-tabbed" in by:
        h = by["highlighted-tabbed"]; parts.append("Highlighted and Tabbed Books at %s are the biggest time saver on an open-book test, because the references arrive ready for the exam room." % money(h["price"]))
    if "online-course" in by: parts.append("The Online Exam Prep Course at %s adds timed practice you can run on a phone between jobs." % money(by["online-course"]["price"]))
    if "live-training" in by: parts.append("Live Virtual Training at %s suits people who learn better with an instructor and a fixed schedule." % money(by["live-training"]["price"]))
    if hi["id"] != lo["id"]: parts.append("The %s at %s is the most complete option: %s." % (hi["typeName"], money(hi["price"]), vacopy.TYPE_BLURB.get(hi["type"], "everything in one order")))
    if len(parts) < 3: parts.append("Candidates who fail usually run out of time rather than knowledge, so pick the option that gets you fastest through the references, and call %s if you are unsure." % CFG["phone"])
    return " ".join(parts)

# ---------- remove previously generated folders ----------
manifest = os.path.join(ROOT, "generated-pages.txt")
KEEP = {"shared", "store", "content", "tools", "brand", "designs", ".git", ".github"}
if os.path.exists(manifest):
    for line in open(manifest):
        top = line.strip().split("/")[0]
        if top and top not in KEEP and os.path.isdir(os.path.join(ROOT, top)): shutil.rmtree(os.path.join(ROOT, top))
generated, urls = [], []

# ---------- home ----------
n_cls, n_prod = len(CLASSES), len(PRODUCTS)
lowest = min(float(p["price"]) for p in PRODUCTS)
GRID = {"AK": (0, 0), "ME": (11, 0), "WI": (6, 1), "VT": (10, 1), "NH": (11, 1), "WA": (1, 2), "ID": (2, 2), "MT": (3, 2), "ND": (4, 2), "MN": (5, 2), "IL": (6, 2), "MI": (7, 2), "NY": (9, 2), "MA": (10, 2),
        "OR": (1, 3), "NV": (2, 3), "WY": (3, 3), "SD": (4, 3), "IA": (5, 3), "IN": (6, 3), "OH": (7, 3), "PA": (8, 3), "NJ": (9, 3), "CT": (10, 3), "RI": (11, 3), "CA": (1, 4), "UT": (2, 4), "CO": (3, 4),
        "NE": (4, 4), "MO": (5, 4), "KY": (6, 4), "WV": (7, 4), "VA": (8, 4), "MD": (9, 4), "DE": (10, 4), "AZ": (2, 5), "NM": (3, 5), "KS": (4, 5), "AR": (5, 5), "TN": (6, 5), "NC": (7, 5), "SC": (8, 5),
        "DC": (9, 5), "OK": (4, 6), "LA": (5, 6), "MS": (6, 6), "AL": (7, 6), "GA": (8, 6), "HI": (0, 7), "TX": (4, 7), "FL": (9, 7)}
def map_html(rel=""):
    tiles = []
    for ab, (x, y) in GRID.items():
        g = ab.lower(); pos = "grid-column:%d;grid-row:%d" % (x + 1, y + 1)
        if g in vaclass.STATE_NAME and classes_in(g):
            cl = classes_in(g)
            tiles.append('<a class="hv-t" style="%s" href="%s" title="%s: %s"><span>%s</span></a>' % (pos, state_url(g, rel), esc(state_name(g)), plural(len(cl), "license"), ab))
        else: tiles.append('<span class="hv-t off" style="%s" aria-hidden="true">%s</span>' % (pos, ab))
    return '<nav class="hv-map" aria-label="Pick your state">%s</nav>' % "".join(tiles)
def state_stats(g):
    cl = classes_in(g); ps = [p for c in cl for p in c["products"]]
    return cl, ps, (min(float(p["price"]) for p in ps) if ps else 0), (max(float(p["price"]) for p in ps) if ps else 0)
BEST = [("texas-journeyman-plumber", "complete-books-tabs-course"), ("florida-plumbing-contractor", "highlighted-tabbed"), ("arizona-plumbing-commercial-contractor-c-37", "ultimate-exam-room"),
        ("georgia-journeyman-plumber", "study-guide-course"), ("north-carolina-plumbing-class-ii-contractor", "online-course"), ("icc-journeyman-plumber-icc-g25-n", "highlighted-tabbed"),
        ("virginia-master-plumber", "live-training"), ("oklahoma-plumbing-and-natural-gas-contractor", "ultimate-rental")]
def home_main():
    lead = vacopy.HOME_LEAD.format(n=n_cls, lo=money(lowest))
    gopts = "".join('<option value="%s">%s</option>' % (g, esc(gn)) for g, gn, _ in vaclass.GROUPS if classes_in(g) and g not in NONSTATE)
    lopts = "".join('<option value="%s/" data-g="%s">%s</option>' % (c["slug"], c["group"], esc(c["name"])) for g, _, _ in vaclass.GROUPS if g not in NONSTATE for c in classes_in(g))
    finder = ('<form class="tx-finder hv-finder" action="search/" method="get" data-finder><label><span>Your state</span><select data-fg>%s</select></label>'
              '<label><span>Your license</span><select name="go" data-fl>%s</select></label><button class="btn btn-buy" type="submit">Show my prep</button></form>' % (gopts, lopts))
    n_states = len([g for g, _, _ in vaclass.GROUPS if g not in NONSTATE and classes_in(g)])
    h1_html = esc(vacopy.HOME_H1).replace("cold.", "<em>cold.</em>")
    hero = ('<section class="hero hv-hero pf-hero" aria-labelledby="h1"><canvas class="pf-water" aria-hidden="true"></canvas>'
            '<div class="wrap pf-grid"><div class="hv-hero-copy"><p class="hv-eyebrow">2026 plumber exam prep, state by state</p><h1 id="h1">%s</h1><p class="lead" id="lead">%s</p>'
            '<div class="gauge"><div class="g hot"><b>%s</b><span>prep from</span></div><div class="g"><b>%d</b><span>%s</span></div><div class="g"><b>%d</b><span>states and DC</span></div></div></div>'
            '<div class="pf-finder-box"><p class="pf-fh">Find your exam package</p><p class="pf-fs">Pick a state, then your license. We match the code your exam is written on.</p>%s</div></div></section>'
            % (h1_html, esc(lead), money(lowest), n_cls, esc(vacopy.LICENSES_COVERED), n_states - 1, finder))
    map_sec = ('<section id="map" class="hv-map-sec" aria-labelledby="h-map"><div class="wrap hv-map-grid"><div><h2 id="h-map">Where are you getting licensed?</h2>'
               '<p>Tap your state. Each state page names the board that licenses plumbers, explains how its exams work and lists every package for them. %d states and Washington DC are covered; grey states have no prep listed yet.</p>'
               '<p class="hv-legend"><span><i class="on"></i>Prep available</span><span><i></i>Not listed yet</span></p></div>%s</div></section>' % (n_states - 1, map_html()))
    tk = takeaways_html(["%d products across %d licenses in %d states and DC, from %s to %s." % (n_prod, n_cls, n_states - 1, money(lowest), money(max(float(p["price"]) for p in PRODUCTS)))]
                        + vacopy.HOME_TAKEAWAYS + ["Every Buy now button goes straight to secure checkout at our fulfillment center, %s." % FUL["name"]])
    by_path = {(p["cls"], p["slug"]): p for p in PRODUCTS}
    best = [by_path.get(k) for k in BEST]
    best_sec = ('<section id="best" class="center" aria-labelledby="h-best"><div class="wrap"><h2 id="h-best">What do plumbers buy most?</h2><p class="sub-h">A few of the most-ordered packages across the states, at the prices on the store today.</p><div class="singles">%s</div></div></section>'
                % "".join(card_html(p, "") for p in best if p))
    rows = []
    for g, gname, _ in vaclass.GROUPS:
        if g in NONSTATE or not classes_in(g): continue
        cl, ps, lo, hi = state_stats(g)
        pic = '<span class="hv-st-img hv-st-map"><img src="/shared/states/%s.svg" alt="Outline map of %s" width="76" height="76" loading="lazy" decoding="async"></span>' % (g, esc(gname))
        rows.append('<li><a class="va-lic hv-st" href="%s">%s<span class="hv-st-t"><b>%s</b><span class="va-n">%s &middot; %s</span><span class="va-p"><small>from</small> %s</span></span></a></li>' % (state_url(g), pic, esc(gname), plural(len(cl), "license"), plural(len(ps), "package"), money(lo)))
    states_sec = ('<section id="states" class="va-group" aria-labelledby="h-states"><div class="wrap"><h2 id="h-states">Which states do we cover?</h2><p class="sub-h">%d states and Washington DC. Each state page names the board that issues the license and lists every package for its exams.</p><ul class="va-lics hv-states">%s</ul></div></section>'
                  % (n_states - 1, "".join(rows)))
    natl = [c for g in NONSTATE[::-1] for c in classes_in(g)]
    natl_sec = ('<section id="national" class="va-group" aria-labelledby="h-national"><div class="wrap"><h2 id="h-national">What about ICC exams and code books?</h2>'
                '<p class="sub-h">Many cities and counties license plumbers with ICC national exams, and inspectors and plans examiners take ICC P1, P2 and P3. Code books and references are listed on their own.</p><ul class="va-lics">%s</ul></div></section>'
                % "".join('<li><a class="va-lic" href="%s/"><b>%s</b><span class="va-n">%s</span><span class="va-p"><small>from</small> %s</span></a></li>' % (c["slug"], esc(c["name"]), plural(len(c["products"]), "option"), money(c["lo"])) for c in natl))
    trs = []
    for g, gname, _ in vaclass.GROUPS:
        if g in NONSTATE or not classes_in(g): continue
        cl, ps, lo, hi = state_stats(g); st = vacopy.STATE[g]
        trs.append("<tr><td><a href=\"%s\">%s</a></td><td>%s</td><td>%s</td><td>%d</td><td>%s</td></tr>" % (state_url(g), esc(gname), esc(st["short"]), esc(st["provider"] or "See bulletin"), len(cl), money(lo)))
    table = ('<section id="boards" class="center" aria-labelledby="h-boards"><div class="wrap"><h2 id="h-boards">Who licenses plumbers in each state?</h2>'
             '<p class="sub-h">The licensing body and, where confirmed, the testing provider. Some states leave plumber licensing to cities.</p>'
             '<div class="compare"><table><thead><tr><th>State</th><th>Licensing body</th><th>Exams by</th><th>Licenses</th><th>Prep from</th></tr></thead><tbody>%s</tbody></table></div>'
             '<p class="va-note">Boards and providers checked November 19, 2026. Confirm with the board before you apply.</p></div></section>' % "".join(trs))
    types = {}
    for p in PRODUCTS: types.setdefault(p["type"], []).append(float(p["price"]))
    tname = dict((s_, n_) for s_, n_, _ in vaclass.TYPES)
    trows = "".join('<tr><td>%s</td><td>%s</td><td>%s</td><td>%d</td></tr>' % (esc(tname.get(t, t)), esc(vacopy.TYPE_BLURB.get(t, "")), (money(min(v)) if min(v) == max(v) else "%s to %s" % (money(min(v)), money(max(v)))), len(v))
                    for t, v in sorted(types.items(), key=lambda kv: vaclass.TYPE_RANK.get(kv[0], 99)) if not t.startswith("ca-") and t != "reference-book")
    types_tbl = ('<section id="compare" style="background:#fff" aria-labelledby="h-compare"><div class="wrap center"><h2 id="h-compare">Which kind of package should you choose?</h2>'
                 '<p class="sub-h">Most licenses offer the same building blocks. Prices vary by license because the reference lists differ.</p>'
                 '<div class="compare"><table><thead><tr><th>Package</th><th>What you get</th><th>Price range</th><th>Products</th></tr></thead><tbody>%s</tbody></table></div></div></section>' % trows)
    how = ('<section id="how" class="center" aria-labelledby="h-how"><div class="wrap"><h2 id="h-how">How does buying work?</h2><div class="big">'
           '<div><b>1</b><h3>Find your state and license</h3><p>Each state page names the licensing board, explains how its exams work and lists every license we have prep for.</p></div>'
           '<div><b>2</b><h3>Pick a package</h3><p>Start with the $59.99 study guide, add the online course, get the code books tabbed, or take The 1 Package with the paperwork and business setup done for you.</p></div>'
           '<div><b>3</b><h3>Check out in one click</h3><p>Buy now opens secure checkout at %s. Books ship free and online courses arrive by email, so you can start the same day.</p></div></div></div></section>' % esc(FUL["name"]))
    pairs = HOME_FAQ
    faq = '<section id="faq" aria-labelledby="h-faq"><div class="wrap center"><h2 id="h-faq">What do people ask before buying?</h2>%s</div></section>' % faq_html(pairs)
    latest = [q for q in blogkit.load_posts(os.path.join(ROOT, "content", "posts"), SITE or "") if q.get("kind", "blog") != "page"][:3]
    blog_sec = ""
    if latest:
        blog_sec = ('<section id="latest-posts" class="home-posts" aria-labelledby="h-latest"><div class="wrap"><h2 id="h-latest">What is new on the blog?</h2>'
                    '<p class="sub-h">Study plans and plumbing licensing news, each post checked against the board that sets the rule.</p><div class="hp-grid">%s</div>'
                    '<p class="hp-all"><a href="blog/">See every post</a></p></div></section>' % "".join(
                        '<a class="hp-card" href="blog/%s/">%s<span class="hp-body"><time datetime="%s">%s</time><b>%s</b><span>%s</span></span></a>' % (
                            q["slug"], ('<img src="%s" alt="%s" loading="lazy">' % (esc(q["image"]), esc(q["title"]))) if q.get("image") else "",
                            q["date"], nice_day(q["date"]), esc(q["title"]), esc(trim_desc(q["excerpt"], 150))) for q in latest))
    final = ('<section class="final" aria-labelledby="h-final"><div class="wrap"><h2 id="h-final">Your exam date is not moving. <em>Start today.</em></h2>'
             '<p>Pick your state above, choose how much help you want, and check out in one click. Books ship free from our fulfillment center, %s, and online courses arrive by email. Questions first? Call %s.</p>'
             '<a class="btn btn-buy" href="#states">Find my state</a></div></section>' % (esc(FUL["name"]), esc(CFG["phone"])))
    return hero + map_sec + tk + best_sec + states_sec + natl_sec + table + types_tbl + how + blog_sec + faq + sources_html("home", vacopy.MAIN_SOURCES) + final, lead
HOME_FAQ = [(q, a.replace("{ful}", FUL["name"])) for q, a in vacopy.HOME_FAQ]
home_main_html, home_lead = home_main()
u = render([], vacopy.HOME_TITLE, vacopy.HOME_DESC.format(n=n_cls, s=len([g for g, _, _ in vaclass.GROUPS if g not in NONSTATE and classes_in(g)]) - 1),
           home_main_html, CFG.get("logo"), [org_ld(), website_ld(), faq_ld(HOME_FAQ), crumbs_ld([("Home", "")])], route={"depth": 0, "home": True})
urls.append(u)

# ---------- license class pages + product pages ----------
def class_page(c):
    s, n, ps = c["slug"], c["name"], c["products"]
    lead = ("%s Here are %s, %s, each with one-click checkout." % (scope(c), plural(len(ps), "package"), span(c["lo"], c["hi"]))) if len(ps) > 1 else ("%s We carry one package for it, %s, with one-click checkout." % (scope(c), span(c["lo"], c["hi"])))
    if count_words(lead) < 40: lead += " Compare what each one includes, see how the exam works and find the answers to the questions people ask most."
    grp = c["group"]
    hero = ('<section class="hero hero--class" aria-labelledby="h1"><div class="wrap"><nav class="crumb" aria-label="Breadcrumb"><a href="../">All states</a><span>/</span><a href="%s">%s</a><span>/</span>%s</nav>'
            '<h1 id="h1">%s exam prep</h1><p class="lead" id="lead">%s</p><a class="btn btn-buy" href="#packs">See the %s</a></div></section>'
            % (state_url(grp, "../"), esc(state_name(grp)), esc(n), esc(("%s %s" % (state_name(grp), n)) if grp != "books" else n), esc(lead), "packages" if len(ps) > 1 else "package"))
    tk = takeaways_html(["%s for the %s exam, %s." % (plural(len(ps), "option"), n, span(c["lo"], c["hi"])),
                         facts_for(c)[0], facts_for(c)[1],
                         "Buy now goes straight to secure checkout; books ship from %s and online courses arrive by email." % FUL["name"]])
    intro = '<p class="sub-h">Buy now adds the item to your cart and opens secure checkout at %s. Details shows the full description first.</p>' % esc(FUL["name"])
    if len(ps) <= 10:
        packs = ('<section id="packs" class="center" aria-labelledby="h-packs"><div class="wrap"><h2 id="h-packs">%s %s</h2>%s<div class="singles">%s</div></div></section>'
                 % (len(ps), esc(n + (" packages" if len(ps) > 1 else " package")), intro, "".join(card_html(p, "../") for p in ps)))
    else:
        fam = collections.OrderedDict()
        for p in ps: fam.setdefault(FAMILY.get(p["type"], "Other options"), []).append(p)
        blocks = []
        for i, (fname, fps) in enumerate(fam.items()):
            for j in range(0, len(fps), 10):
                chunk = fps[j:j + 10]; label = fname if len(fps) <= 10 else "%s, part %d" % (fname, j // 12 + 1)
                blocks.append('<section %sclass="center" aria-labelledby="h-fam-%d-%d"><div class="wrap"><h2 id="h-fam-%d-%d">%s %s: %s</h2>%s<div class="singles">%s</div></div></section>'
                              % ('id="packs" ' if not blocks else "", i, j, i, j, esc(n), "options" if len(chunk) > 1 else "option", esc(label.lower()),
                                 intro if not blocks else '<p class="sub-h">%s of the %d %s options, from %s.</p>' % (plural(len(chunk), "product"), len(ps), esc(n), money(min(float(q["price"]) for q in chunk))), "".join(card_html(p, "../") for p in chunk)))
        packs = "".join(blocks)
    compact = len(ps) > 14
    rows = "".join('<tr><td><a href="%s/">%s</a>%s</td>%s<td>%s</td></tr>' % (p["slug"], esc(p["typeName"]), esc((" " + p["year"]) if compact and p["year"] else "") + esc(region_note(p)), "" if compact else "<td>%s</td>" % esc(vacopy.TYPE_BLURB.get(p["type"], "exam prep")), money(p["price"])) for p in ps)
    compare = ('<section id="compare" style="background:#fff" aria-labelledby="h-compare"><div class="wrap center"><h2 id="h-compare">How do the %s options compare?</h2>'
               '<p class="sub-h">Prices are the starting price for each option; some offer add-ons at checkout.</p><div class="compare"><table><thead><tr><th>Option</th>%s<th>Price</th></tr></thead><tbody>%s</tbody></table></div></div></section>' % (esc(n), "" if compact else "<th>What you get</th>", rows))
    facts = "".join("<li>%s</li>" % esc(f) for f in facts_for(c))
    how = ('<section id="exam" class="guide" aria-labelledby="h-exam"><div class="wrap"><h2 id="h-exam">How does the %s exam work?</h2><div class="guide-cols"><div><p>%s</p><ul class="va-facts">%s</ul></div>'
           '<div><h3 id="h-choose">Which %s option should I choose?</h3><p>%s</p></div></div></div></section>'
           % (esc(n), esc(vacopy.GROUP_HOW[grp].format(name=n)), facts, esc(n), esc(choose_text(c))))
    pairs = class_faq(c)
    faq = '<section id="faq" aria-labelledby="h-faq"><div class="wrap center"><h2 id="h-faq">%s exam questions</h2>%s</div></section>' % (esc(n), faq_html(pairs))
    sib = [x for x in classes_in(grp) if x["slug"] != s][:8]
    other_groups = [(g, gn) for g, gn, _ in vaclass.GROUPS if g != grp and classes_in(g) and g not in NONSTATE][:10]
    related = ('<section class="related-pages" aria-labelledby="h-related-pages"><div class="wrap"><h2 id="h-related-pages">Related pages</h2><div class="rp-cols">'
               '<div><h3>More in %s</h3><ul>%s</ul></div><div><h3>Other states</h3><ul>%s</ul></div><div><h3>Also on this site</h3><ul><li><a href="../faq/">Plumbing exam FAQ</a></li><li><a href="../blog/">Study tips and licensing news</a></li><li><a href="../#boards">Who licenses plumbers in each state</a></li></ul></div></div></div></section>'
               % (esc(state_name(grp)), "".join('<li><a href="../%s/">%s</a></li>' % (x["slug"], esc(x["name"])) for x in sib) or '<li><a href="%s">Every %s license</a></li>' % (state_url(grp, "../"), esc(state_name(grp))),
                  "".join('<li><a href="%s">%s</a></li>' % (state_url(g, "../"), esc(gn)) for g, gn in other_groups)))
    tabs = ('<nav class="tx-tabs" aria-label="On this page"><div class="wrap"><a href="#packs">Packages</a><a href="#compare">Compare</a><a href="#exam">How the exam works</a><a href="#faq">FAQ</a><a href="#h-sources">Sources</a></div></nav>')
    qf_rows = [("Price range", "%s to %s" % (money(c["lo"]), money(c["hi"])) if c["lo"] != c["hi"] else money(c["lo"])), ("Options", str(len(ps))),
               ("Licensed by", vacopy.ISSUER_SHORT[grp]), ("Book rule", vacopy.BOOK_SHORT[grp])]
    if vacopy.CLASS_FACTS.get(s): qf_rows.append(("The exam", vacopy.CLASS_FACTS[s][0]))
    qf = ('<aside class="tx-qf" aria-label="Quick facts"><p class="tx-qf-h">Quick facts</p><dl>%s</dl><a class="btn btn-buy" href="#packs">See the %s</a><p class="tx-qf-call">Not sure which one? Call <a href="tel:%s">%s</a></p></aside>'
          % ("".join("<div><dt>%s</dt><dd>%s</dd></div>" % (esc(a), esc(b)) for a, b in qf_rows), "packages" if len(ps) > 1 else "package", CFG["phoneTel"], esc(CFG["phone"])))
    main = hero + tabs + qf + tk + packs + compare + how + faq + related + sources_html(grp)
    sn = state_name(grp) if grp != "books" else ""
    abbr = grp.upper() if grp != "books" else ""
    title = fit_title("%s %s Exam Prep" % (sn, n), "%s %s Exam Prep" % (abbr, n), "%s %s Exam Prep" % (sn, n.split(" (")[0]), "%s %s Exam Prep" % (abbr, n.split(" (")[0]), "%s %s" % (abbr, n.split(" (")[0]))
    desc = ("%s exam prep for " + (state_name(grp) or "plumbing exams") + ": %s %s, including %s. One-click checkout.") % (n, plural(len(ps), "option"), span(c["lo"], c["hi"]), ", ".join(sorted({p["typeName"].lower() for p in ps})[:3]))
    lds = [{"@context": "https://schema.org", "@type": "CollectionPage", "name": "%s %s exam prep" % (sn, n), "url": absurl(s + "/"), "dateModified": TODAY, "publisher": publisher_ld(),
            "mainEntity": {"@type": "ItemList", "numberOfItems": len(ps), "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": absurl(p["path"]), "name": p["short"]} for i, p in enumerate(ps)]}},
           faq_ld(pairs), crumbs_ld([("All states", "")] + ([(sn, STATE_SLUG[grp] + "/")] if STATE_SLUG.get(grp) else []) + [(n, s + "/")])]
    sticky = '<div class="stickybar"><div><strong>%s</strong><small>%s from %s</small></div><a class="btn btn-buy" href="#packs">See options</a></div>' % (esc(n), plural(len(ps), "option"), money(c["lo"]))
    return render([s], title, desc, main, ps[-1]["image"], lds, page_type=None, route={"depth": 1, "cls": s}, sticky="", cta='<a class="btn btn-buy" href="#packs">See options</a>')

def first_sentence_fix(hx, subject):
    return re.sub(r"^(\s*(?:<p[^>]*>)?\s*)(This|These|It|They|That|Those|Such|Here)\b(\s+(?:\w+\s+){0,3}?(?:package|course|combo|bundle|set|guide|kit|book|books|product|option|training)\b)?",
                  lambda m: m.group(1) + "The " + subject, hx, count=1)

_BACKREF_WORD = re.compile(r"^(\s*)(This|These|That|Those|It|They|Such|Here|Below|Above)\b", re.I)
_SKIP_TAGS = {"h3", "h4", "summary", "th", "b", "strong", "a", "time", "small", "span", "s", "em"}
def _fix_start(chunk, subject):
    """A section may not open with a word that points back at another section (the AI-readiness rule). Find the first
    text the checker reads (outside headings and bold lead-ins) and name the thing instead."""
    stack = []
    for m in re.finditer(r"<(/?)([a-z0-9]+)[^>]*>|([^<]+)", chunk):
        if m.group(2):
            t = m.group(2).lower()
            if m.group(1):
                if t in stack: del stack[len(stack) - 1 - stack[::-1].index(t):]
            elif t not in ("br", "img", "hr"): stack.append(t)
            continue
        txt = m.group(3)
        if not txt.strip() or any(t in _SKIP_TAGS for t in stack): continue
        mm = _BACKREF_WORD.match(txt)
        if not mm: return chunk
        w = mm.group(2).lower()
        rep = ("The " + subject) if w == "it" else ("The materials" if w == "they" else ("Listed here" if w in ("below", "above", "here") else "The"))
        return chunk[:m.start(3)] + mm.group(1) + rep + txt[mm.end():] + chunk[m.end(3):]
    return chunk
def sectionize(hx, subject, first_title):
    """Turn a long Shopify description into page sections: every <h3> topic becomes its own H2 section, and anything
    still over about 350 words is split at a paragraph or list boundary, so no section passes the 400-word limit."""
    hx = re.sub(r"<(/?)h4>", r"<\1h3>", hx)  # description topics: h3 becomes the section H2; h4 steps up to h3
    parts = re.split(r"<h3>(.*?)</h3>", hx, flags=re.S)
    secs = [(first_title, parts[0])] + [(re.sub(r"<[^>]+>", "", parts[i]).strip().rstrip(":"), parts[i + 1]) for i in range(1, len(parts) - 1, 2)]
    out = []
    for title, body in secs:
        blocks = [m.group(0) for m in re.finditer(r"<(p|ul|ol|h4)\b[^>]*>.*?</\1>|[^<\s][^<]*", body, flags=re.S)]
        def _split_list(b):  # a very long list becomes several lists of whole items
            m = re.match(r"<(ul|ol)\b([^>]*)>(.*)</\1>$", b, flags=re.S)
            if not m or count_words(b) <= 340: return [b]
            items = re.findall(r"<li\b.*?</li>", m.group(3), flags=re.S)
            if not items: return [b]
            out_, cur_, n_ = [], [], 0
            for it in items:
                w_ = count_words(it)
                if cur_ and n_ + w_ > 300: out_.append(cur_); cur_, n_ = [], 0
                cur_.append(it); n_ += w_
            if cur_: out_.append(cur_)
            return ["<%s%s>%s</%s>" % (m.group(1), m.group(2), "".join(x), m.group(1)) for x in out_]
        blocks = [x for b in blocks for x in _split_list(b)]
        chunks, cur, n = [], [], 0
        for b in blocks:
            w = count_words(b)
            if cur and n + w > 340: chunks.append("".join(cur)); cur, n = [], 0
            cur.append(b); n += w
        if cur: chunks.append("".join(cur))
        chunks = [c_ for c_ in chunks if count_words(c_) > 0]
        if not chunks: continue
        if out and count_words(chunks[0]) < 40 and len(chunks) == 1 and count_words(out[-1][1]) + count_words(chunks[0]) <= 340:  # tiny topic: fold it into the previous section
            out[-1] = (out[-1][0], out[-1][1] + ("<h3>%s</h3>" % esc(title)) + chunks[0]); continue
        for k, ch in enumerate(chunks):
            out.append((title if k == 0 else "%s (continued)" % title, ch))
    out = [(t, _fix_start(b, subject)) for t, b in out]
    if not out: return hx
    html_ = out[0][1]
    for title, body in out[1:]:
        html_ += '</div><h2 class="desc-h">%s</h2><div class="desc">%s' % (esc(title) if "<" not in title else title, body)
    return html_

def product_page(c, p):
    parts = [c["slug"], p["slug"]]; rel = "../../"; path = "/".join(parts) + "/"
    full = FULL.get(p["id"], {"html": "", "images": [p["image"]]})
    hx = full.get("html") or ("<p>%s</p>" % esc(p.get("desc", "")))
    hx = re.sub(r"(?<![\d.])(?:\(?\d{3}\)?[\s.-]?)\d{3}[\s.-]\d{4}(?![\d.])", lambda m: m.group(0) if re.sub(r"\D", "", m.group(0))[-10:] == "8777759400" else CFG["phone"], hx)
    if FUL["name"] != BRAND: hx = re.sub(r"(?<![\w/.-])1 ?Exam ?Prep(?![\w.-])", BRAND, hx)
    if re.search(r"(\.\.\.|\u2026)\s*(</p>)?\s*$", hx):  # a truncated pull: end on the last full sentence
        hx = re.sub(r"(?s)^(.*[.!?])\s[^.!?]*(\.\.\.|\u2026)\s*(</p>)?\s*$", lambda m: m.group(1) + ("</p>" if m.group(3) else ""), hx)
    hx = first_sentence_fix(hx, p["short"])
    hx = sectionize(hx, p["short"], "About this %s package" % c["name"])
    imgs = [u for u in (full.get("images") or []) if u] or [p["image"]]
    v0 = p["variants"][0]; c0, n0 = float(v0.get("compareAt") or 0), float(v0["price"])
    compare_html = ('<s class="pc-was" id="pWas">%s</s><span class="pc-save" id="pSave">Save %d%%</span>' % (money(c0), round((c0 - n0) / c0 * 100))) if c0 > n0 else '<s class="pc-was" id="pWas" hidden></s><span class="pc-save" id="pSave" hidden></span>'
    real_variants = len(p["variants"]) > 1 or p["variants"][0]["title"] not in ("Default Title", "")
    variants_html = "".join('<label class="m-opt"><input type="radio" name="v" value="%s"%s><span>%s</span><b>%s%s</b></label>' % (v["id"], " checked" if i == 0 else "", esc(v["title"]), money(v["price"]),
                            ('<s>%s</s>' % money(v["compareAt"])) if v.get("compareAt") and float(v["compareAt"]) > float(v["price"]) else "") for i, v in enumerate(p["variants"])) if real_variants else ""
    thumbs = "".join('<button type="button" data-src="%s" class="%s" aria-label="Image %d"><img src="%s" alt="%s, image %d" loading="lazy"></button>' % (esc(u), "on" if i == 0 else "", i + 1, esc(u), esc(p["short"]), i + 1) for i, u in enumerate(imgs)) if len(imgs) > 1 else ""
    blurb = vacopy.TYPE_BLURB.get(p["type"], "exam prep")
    where = state_name(c["group"]) if c["group"] != "books" else "any state"
    sub_parts = ["The %s is %s for the %s exam (%s), at %s%s." % (p["short"], blurb, c["name"], where, money(n0), (", %d%% off the %s list price" % (round((c0 - n0) / c0 * 100), money(c0))) if c0 > n0 else ""),
                 "%s." % delivery(p), "Buy now goes straight to secure checkout at %s." % FUL["name"], "Call %s with questions first." % CFG["phone"],
                 "It is one of %s for this license." % plural(len(c["products"]), "option") if len(c["products"]) > 1 else "No other option is listed for this license yet."]
    sub = sub_parts[0]
    for extra_s in sub_parts[1:]:
        if count_words(sub + " " + extra_s) <= 56: sub += " " + extra_s
    if count_words(sub) > 56:  # very long product names: name the type instead of repeating the full title
        sub = "This %s is %s for the %s exam (%s), at %s. %s." % (p["typeName"], blurb, c["name"], where, money(n0), delivery(p))
        sub = "The " + sub[5:]
        for extra_s in sub_parts[2:]:
            if count_words(sub + " " + extra_s) <= 58: sub += " " + extra_s
    inc = ["%s: %s" % (p["typeName"], blurb), "Written for the %s exam%s" % (c["name"], region_note(p)), delivery(p)]
    if old_code(c, p): inc.append("Written to the %s code cycle. %s" % (p["year"], OLD_CODE_NOTE))
    if p.get("maxPrice") and float(p["maxPrice"]) > n0: inc.append("Options from %s to %s, chosen above before checkout" % (money(n0), money(p["maxPrice"])))
    included = '<ul class="included">%s</ul>' % "".join("<li>%s</li>" % esc(x) for x in inc)
    included += '<p class="included-sum">The %s costs %s%s and is written for the %s exam%s. %s, and Buy now takes you straight to checkout.</p>' % (
        esc(p["typeName"]), money(n0), (" to %s with the options above" % money(p["maxPrice"])) if p.get("maxPrice") and float(p["maxPrice"]) > n0 else "",
        esc(c["name"]), esc(region_note(p)), esc(delivery(p)))
    addons = [v["title"] for v in p["variants"][1:]]
    addons_html = ('<p class="addons"><b>Options at checkout:</b> %s. Pick one above and the price updates.</p>' % esc("; ".join([p["variants"][0]["title"]] + addons))) if addons else ""
    facts = "".join("<li>%s</li>" % esc(f) for f in facts_for(c))
    exam = '<h2 id="exam">How does the %s exam work?</h2><p>%s</p><ul class="va-facts">%s</ul>' % (esc(c["name"]), esc(vacopy.GROUP_HOW[c["group"]].format(name=c["name"])), facts)
    others = [q for q in c["products"] if q["id"] != p["id"]][:8]
    related = "".join('<a class="rel" href="../%s/"><img src="%s" alt="%s" loading="lazy"><span><b>%s</b><small>%s</small></span><span class="pc-now">%s</span></a>' % (
        q["slug"], esc(q["image"]), esc(q["short"]), esc(q["typeName"] + region_note(q)), esc(q["short"][:60] + ("…" if len(q["short"]) > 60 else "")), money(q["price"])) for q in others) or '<p>No other option is listed for this license yet.</p>'
    sib = [x for x in classes_in(c["group"]) if x["slug"] != c["slug"]][:5]
    more = '<div class="more-links"><h3>More %s licenses</h3><a href="%s">All %s licenses</a>%s<a href="%sfaq/">Plumbing exam FAQ</a><a href="%sblog/">Study tips</a></div>' % (esc(state_name(c["group"])), state_url(c["group"], rel), esc(state_name(c["group"])), "".join('<a href="%s%s/">%s</a>' % (rel, x["slug"], esc(x["name"])) for x in sib), rel, rel)
    pairs = [("How much is the %s?" % p["short"][:80], "%s%s. %s" % (money(n0), (" to %s depending on the option you pick" % money(p["maxPrice"])) if p.get("maxPrice") and float(p["maxPrice"]) > n0 else "", "The price at checkout is the one that applies, and it is shown before you pay.")),
             ("What is included?", "%s: %s. %s." % (p["typeName"], blurb, delivery(p))),
             ("Is the %s exam open book?" % c["name"], open_book(c)),
             ("Who issues the license or certification?", "It comes from %s. Buying study material does not register you or make you eligible to test." % who_issues(c)),
             ("Are these the real exam questions?", "No. Licensing exam questions are confidential. Courses and practice exams are original material written to the same subjects and format."),
             ("How fast can I start?", "Online courses and practice exams arrive by email after purchase. Books ship from our fulfillment center, %s; shipping options are shown at checkout." % FUL["name"])]
    if old_code(c, p): pairs.insert(2, ("Is the %s edition still right for my exam?" % p["year"], "Only if your bulletin still lists it. %s The %s edition suits exams that have not moved to the 2024 code yet." % (OLD_CODE_NOTE, p["year"])))
    if p["type"] in ("rental-package", "ultimate-rental"): pairs.append(("Do rental books have to go back?", "Yes. Rental books are returned after your exam, using the return instructions that come with the order. Buy the book package instead if you want to keep the references."))
    if p["type"] == "the-1-package": pairs.append(("What does The 1 Package cover beyond exam prep?", "It adds help with the state license application plus LLC or corporation setup, EIN filing and compliance guidance, so the paperwork moves while you study."))
    _sn, _ab = state_name(c["group"]), c["group"].upper()
    _cn, _cs = c["name"], c["name"].split(" (")[0]
    _code = re.search(r"\(((?:ICC )?[A-Z]{1,3}-?\d+[A-Z]?(?:-N)?|SP-PH|ICC [A-Z0-9-]+)\)", _cn)
    _t = p["typeName"].replace(" (all-inclusive)", "")
    _cands = ["%s %s %s" % (_sn, _cn, _t), "%s %s %s" % (_ab, _cn, _t), "%s %s %s" % (_sn, _cs, _t), "%s %s %s" % (_ab, _cs, _t)]
    if _code: _cands += ["%s %s %s" % (_sn, _code.group(1), _t), "%s %s %s" % (_ab, _code.group(1), _t)]
    _cands += ["%s %s" % (_ab, _t + " " + _cs)]
    if c["group"] == "books": _cands = [p["short"], p["short"][:60]]
    short_t = fit_title(*_cands)
    if p["year"] and p["year"] not in short_t and len(short_t) + 7 <= 60: short_t += " (%s)" % p["year"]
    desc = trim_desc("%s for the %s %s exam: %s. %s. One-click checkout." % (p["typeName"], state_name(c["group"]) if c["group"] not in NONSTATE else "plumbing", c["name"], blurb, money(n0)))
    if len(desc) < 70: desc = trim_desc(desc + " Fulfilled by %s; call %s with questions." % (FUL["name"], CFG["phone"]))
    full_text = html.unescape(re.sub(r"<[^>]+>", " ", hx))
    jsonld = schemakit.product_ld(p["short"], absurl(path), imgs, full_text if len(full_text) > 120 else (p.get("desc") or sub), p["id"],
                                  "%s exam prep" % c["name"], p["variants"], p.get("type", ""), brand=FUL["name"], fallback=sub)
    crumbs = [("All states", "")] + ([(state_name(c["group"]), STATE_SLUG[c["group"]] + "/")] if STATE_SLUG.get(c["group"]) else []) + [(c["name"], c["slug"] + "/"), (p["typeName"], path)]
    extra = head_extra(path, short_t, desc, imgs[0], rel, False, [crumbs_ld(crumbs), faq_ld(pairs)], page_type="WebPage", about="%s exam" % c["name"])
    pjson = json.dumps({"id": p["id"], "variants": p["variants"], "title": p["short"], "state": c["name"], "level": GROUP_NAME[c["group"]], "tierName": p["typeName"], "price": p["price"]})
    kicker = "%s · %s%s" % (c["name"], p["typeName"], region_note(p))
    out = (ptpl.replace("{{TITLE}}", esc(short_t)).replace("{{DESC}}", esc(desc))
           .replace("{{CANONICAL}}", ('<link rel="canonical" href="%s">\n' % absurl(path)) if SITE else "")
           .replace("{{OGIMAGE}}", '<meta property="og:image" content="%s">\n' % esc(imgs[0]))
           .replace("{{ASSETS_HEAD}}", assets_head(rel))
           .replace("{{ASSETS_PRODUCT}}", '<script src="%sshared/product.js"></script>' % rel)
           .replace("{{ASSETS_SEARCH}}", '<script src="%sshared/site-index.js" defer></script>\n<script src="%sshared/search.js" defer></script>\n<script src="%sshared/track.js" defer></script>' % (rel, rel, rel)).replace("{{HEAD_EXTRA}}", extra)
           .replace("{{NAV_TOOLS}}", nav_tools('<a class="btn btn-buy" href="%s" rel="noopener">Buy now</a>' % cart(v0["id"])))
           .replace("{{FOOTER}}", footer(rel)).replace("{{ROUTE}}", json.dumps({"depth": 2, "cls": c["slug"], "product": p["slug"]}))
           .replace("{{JSONLD}}", json.dumps(jsonld, ensure_ascii=False)).replace("{{P_JSON}}", pjson)
           .replace("{{HOME}}", rel).replace("{{CLASS}}", esc(c["name"])).replace("{{GROUP}}", c["group"]).replace("{{GROUP_NAME}}", esc(GROUP_NAME[c["group"]].split(":")[0]))
           .replace("{{TYPE_NAME}}", esc(p["typeName"])).replace("{{KICKER}}", esc(kicker)).replace("{{H1}}", esc(p["short"])).replace("{{SUB}}", esc(sub))
           .replace("{{IMAGE}}", esc(imgs[0])).replace("{{IMAGE_ALT}}", esc(p["short"])).replace("{{THUMBS}}", thumbs)
           .replace("{{PRICE}}", money(n0)).replace("{{COMPARE_HTML}}", compare_html).replace("{{VARIANTS_HTML}}", variants_html).replace("{{DELIVERY}}", esc(delivery(p)))
           .replace("{{BUY_URL}}", cart(v0["id"])).replace("{{MORE_LINKS_HTML}}", more)
           .replace("{{TAKEAWAYS_HTML}}", takeaways_html(["%s: %s%s." % (p["typeName"], money(n0), (", down from %s" % money(c0)) if c0 > n0 else ""), "For the %s exam%s; %s." % (c["name"], region_note(p), blurb),
                                                          (OLD_CODE_NOTE if old_code(c, p) else facts_for(c)[0]), "%s. Buying does not grant exam eligibility." % delivery(p)]))
           .replace("{{INCLUDED_HTML}}", included).replace("{{ADDONS_HTML}}", addons_html).replace("{{DESCRIPTION_HTML}}", hx).replace("{{EXAM_HTML}}", exam)
           .replace("{{RELATED_HTML}}", related).replace("{{FAQ_HTML}}", "".join('<details%s><summary>%s</summary><p>%s</p></details>' % (" open" if i == 0 else "", esc(q), esc(a)) for i, (q, a) in enumerate(pairs)))
           .replace("{{SOURCES_HTML}}", sources_html(c["group"]).replace('<section class="wrap sources"', '<section class="sources"')))
    d = os.path.join(ROOT, *parts); os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(anchor_ids(out))
    return absurl(path)

def state_page(g):
    gname = state_name(g); cl, ps, lo, hi = state_stats(g); st = vacopy.STATE[g]; sl = STATE_SLUG[g]
    names = [c["name"] for c in cl]
    lead = ("%s plumbing licenses come from %s. We carry prep for %s in %s, %s, with %s from %s to %s. Pick your license below to compare books, courses and complete packages."
            % (gname, st["board"], plural(len(cl), "license"), gname, (", ".join(names[:2]) + (" and more" if len(names) > 2 else "")) if len(names) > 1 else names[0], plural(len(ps), "package"), money(lo), money(hi)))
    if count_words(lead) > 54:
        lead = "%s plumbing licenses come from %s. We carry prep for %s in %s, with %s from %s to %s. Pick your license below to compare its packages." % (gname, st["board"], plural(len(cl), "license"), gname, plural(len(ps), "package"), money(lo), money(hi))
    if count_words(lead) > 54:
        lead = "%s plumbing licenses come from %s. We carry prep for %s here, with %s from %s to %s. Pick your license below." % (gname, st["board"], plural(len(cl), "license"), plural(len(ps), "package"), money(lo), money(hi))
    if count_words(lead) < 40: lead += " Each license page explains how that exam works and answers the questions people ask most."
    hero = ('<section class="hero hero--class hv-state-hero" aria-labelledby="h1"><div class="wrap"><nav class="crumb" aria-label="Breadcrumb"><a href="../">All states</a><span>/</span>%s</nav>'
            '<h1 id="h1">%s plumbing license exam prep</h1><p class="lead" id="lead">%s</p><a class="btn btn-buy" href="#licenses">See the %s licenses</a></div></section>' % (esc(gname), esc(gname), esc(lead), esc(gname)))
    qf_rows = [("Licensing body", st["board"][0].upper() + st["board"][1:]), ("Exams by", st["provider"] or "See your candidate bulletin"), ("Book rule", vacopy.BOOK_SHORT[g]),
               ("Licenses here", str(len(cl))), ("Packages", "%d, from %s" % (len(ps), money(lo)))]
    qf = ('<aside class="tx-qf hv-qf" aria-label="Quick facts"><p class="tx-qf-h">%s quick facts</p><dl>%s</dl>%s<a class="btn btn-buy" href="#licenses">See the licenses</a><p class="tx-qf-call">Not sure which license? Call <a href="tel:%s">%s</a></p></aside>'
          % (esc(gname), "".join("<div><dt>%s</dt><dd>%s</dd></div>" % (esc(a), esc(b)) for a, b in qf_rows), ('<p class="hv-qf-src"><a href="%s" rel="noopener" target="_blank">Official site</a></p>' % esc(st["url"])) if st["url"] else "", CFG["phoneTel"], esc(CFG["phone"])))
    tk = takeaways_html([st["facts"][0], "%s covering %s in %s, %s." % (plural(len(ps), "package"), plural(len(cl), "license"), gname, span(lo, hi))] + st["facts"][1:2]
                        + ["Buy now goes straight to secure checkout; books ship free from %s." % FUL["name"]])
    items = "".join('<li><a class="va-lic" href="../%s/"><b>%s</b><span class="va-n">%s</span><span class="va-p"><small>from</small> %s</span></a></li>' % (c["slug"], esc(c["name"]), plural(len(c["products"]), "option"), money(c["lo"])) for c in cl)
    lic = ('<section id="licenses" class="va-group" aria-labelledby="h-licenses"><div class="wrap"><h2 id="h-licenses">Which %s plumbing licenses do we cover?</h2><p class="sub-h">%s. Pick one to compare every package for that exam.</p><ul class="va-lics">%s</ul></div></section>'
           % (esc(gname), esc(plural(len(cl), "license") + " and " + plural(len(ps), "package")), items))
    def top(c):
        pr = sorted(c["products"], key=lambda p: vaclass.TYPE_RANK.get(p["type"], 0))
        return pr[-1]
    rows = "".join('<tr><td><a href="../%s/">%s</a></td><td>%d</td><td>%s</td><td>%s</td></tr>' % (c["slug"], esc(c["name"]), len(c["products"]), money(c["lo"]), esc("%s, %s" % (top(c)["typeName"].replace(" (all-inclusive)", ""), money(top(c)["price"])))) for c in cl)
    tbl = ('<section id="compare" style="background:#fff" aria-labelledby="h-compare"><div class="wrap center"><h2 id="h-compare">How do the %s licenses compare?</h2><p class="sub-h">Starting price and the most complete package for each license.</p>'
           '<div class="compare"><table><thead><tr><th>License</th><th>Options</th><th>From</th><th>Most complete</th></tr></thead><tbody>%s</tbody></table></div></div></section>' % (esc(gname), rows))
    facts = "".join("<li>%s</li>" % esc(f) for f in st["facts"])
    how = ('<section id="exam" class="guide" aria-labelledby="h-exam"><div class="wrap"><h2 id="h-exam">How does plumber licensing work in %s?</h2><div class="guide-cols"><div><p>%s</p><ul class="va-facts">%s</ul></div>'
           '<div><h3 id="h-books">Can you bring books into the %s exam?</h3><p>%s</p></div></div></div></section>'
           % (esc(gname), esc("%s licenses plumbers here. The board approves your application first; then you schedule the exam and bring only the references the candidate bulletin allows." % (st["board"][0].upper() + st["board"][1:])), facts, esc(gname), esc(vacopy.OPEN_BOOK[g])))
    pairs = [("Who issues plumbing licenses in %s?" % gname, "%s. Buying a package here does not register you or make you eligible; the licensing body approves you first, then the exam is scheduled." % (st["board"][0].upper() + st["board"][1:])),
             ("Is the %s plumbing exam open book?" % gname, vacopy.OPEN_BOOK[g]),
             ("How much does %s plumbing exam prep cost?" % gname, "Prep for the %s licenses here runs from %s to %s across %s. Online courses and practice questions are the lowest-cost start; highlighted and tabbed books, Ultimate packages and The 1 Package cost more and do more." % (gname, money(lo), money(hi), plural(len(ps), "package"))),
             ("Which %s license should I study for?" % gname, "The one your approval or application names. %s are listed here: %s." % (plural(len(cl), "license"), "; ".join(names[:8]) + ("; and more" if len(names) > 8 else ""))),
             ("Does the %s exam use the IPC or the UPC?" % gname, "Each package names its code in the title, the International Plumbing Code (IPC) or the Uniform Plumbing Code (UPC). Match it to the editions listed in your candidate bulletin."),
             ("Are these the real exam questions?", "No. Licensing exam questions are confidential. The courses and practice questions are original material written to the same subjects and format."),
             ("How do the books and courses arrive?", "Books ship free from our fulfillment center, %s, by USPS Media Mail. Online courses and practice questions arrive by email after purchase. Allow up to 15 business days for rental, Ultimate and 1 Package orders." % FUL["name"])]
    faq = '<section id="faq" aria-labelledby="h-faq"><div class="wrap center"><h2 id="h-faq">%s plumbing exam questions</h2>%s</div></section>' % (esc(gname), faq_html(pairs))
    others = [(x, xn) for x, xn, _ in vaclass.GROUPS if x not in (g,) + NONSTATE and classes_in(x)]
    i = [x for x, _ in others].index(sorted([x for x, _ in others] + [g], key=lambda k: state_name(k))[0]) if False else 0
    near = others[:12]
    related = ('<section class="related-pages" aria-labelledby="h-related-pages"><div class="wrap"><h2 id="h-related-pages">Related pages</h2><div class="rp-cols">'
               '<div><h3>Popular %s licenses</h3><ul>%s</ul></div><div><h3>Other states</h3><ul>%s</ul></div><div><h3>Also on this site</h3><ul><li><a href="../faq/">Plumbing exam FAQ</a></li><li><a href="../blog/">Study tips</a></li><li><a href="../plumbing-code-books/">Plumbing code books</a></li><li><a href="../#boards">Who licenses plumbers in each state</a></li></ul></div></div></div></section>'
               % (esc(gname), "".join('<li><a href="../%s/">%s</a></li>' % (c["slug"], esc(c["name"])) for c in sorted(cl, key=lambda c: -len(c["products"]))[:6]), "".join('<li><a href="%s">%s</a></li>' % (state_url(x, "../"), esc(xn)) for x, xn in near)))
    tabs = '<nav class="tx-tabs" aria-label="On this page"><div class="wrap"><a href="#licenses">Licenses</a><a href="#compare">Compare</a><a href="#exam">How licensing works</a><a href="#faq">FAQ</a><a href="#h-sources">Sources</a></div></nav>'
    main = hero + tabs + qf + tk + lic + tbl + how + faq + related + sources_html(g)
    title = fit_title("%s Plumbing License Exam Prep" % gname, "%s Plumber Exam Prep" % gname, "%s Plumbing License Prep" % gname, "%s Plumbing Exam Prep by License" % gname, "%s Plumber Exam Prep" % g.upper())
    desc = "%s plumbing license exam prep: %s and %s from %s, with books, highlighted and tabbed sets, online courses and one-click checkout." % (gname, plural(len(cl), "license"), plural(len(ps), "package"), money(lo))
    lds = [{"@context": "https://schema.org", "@type": "CollectionPage", "name": "%s plumbing license exam prep" % gname, "url": absurl(sl + "/"), "dateModified": TODAY, "publisher": publisher_ld(),
            "about": {"@type": "Thing", "name": "%s plumbing licensing" % gname},
            "mainEntity": {"@type": "ItemList", "numberOfItems": len(cl), "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": absurl(c["slug"] + "/"), "name": c["name"]} for i, c in enumerate(cl)]}},
           faq_ld(pairs), crumbs_ld([("All states", ""), (gname, sl + "/")])]
    img = next((p["image"] for p in ps if p.get("image")), CFG.get("logo"))
    return render([sl], title, desc, main, img, lds, page_type=None, route={"depth": 1, "state": g}, cta='<a class="btn btn-buy" href="#licenses">See licenses</a>')

for g, _, _ in vaclass.GROUPS:
    if STATE_SLUG.get(g) and classes_in(g):
        urls.append(state_page(g)); generated.append(STATE_SLUG[g])
for s in ORDER:
    if s not in CLASSES: continue
    c = CLASSES[s]
    urls.append(class_page(c)); generated.append(s)
    for p in c["products"]:
        urls.append(product_page(c, p)); generated.append(p["path"].rstrip("/"))
with open(manifest, "w") as f: f.write("\n".join(generated) + "\n")

# ---------- knowledge for the exam advisor (Max), only when aiFinderUrl is set ----------
if CFG.get("aiFinderUrl"):
    import maxkb
    _n_items, _n_pieces = maxkb.write(ROOT, PRODUCTS, CLASSES, ORDER, vacopy, vaclass, FULL,
                                      json.load(open(os.path.join(ROOT, "content", "faq-general.json"), encoding="utf-8")), old_code)
    print("Max knowledge: %d products, %d fact pieces" % (_n_items, _n_pieces))

# ---------- site index for search (independent of the catalog format) ----------
idx = {"classes": [{"n": c["name"], "u": c["slug"] + "/", "g": GROUP_NAME[c["group"]], "k": len(c["products"]), "lo": c["lo"]} for c in (CLASSES[s] for s in ORDER if s in CLASSES)],
       "products": [{"t": p["short"], "c": p["clsName"], "y": p["typeName"] + region_note(p), "p": float(p["price"]), "i": p["image"], "u": p["path"]} for p in PRODUCTS]}
open(os.path.join(ROOT, "shared", "site-index.js"), "w", encoding="utf-8").write("/* Generated by build.py for site search. */\nwindow.SITE_INDEX=%s;\n" % json.dumps(idx, separators=(",", ":"), ensure_ascii=False))

# ---------- /reviews/ : Google reviews + Shopper Approved (widgets injected by shared/va.js) ----------
sys.path.insert(0, os.path.join(ROOT, "tools")); import reviewskit as rk
_rc = rk.content(BRAND, "plumbing license exam", CFG["phone"], CFG["phoneTel"], CFG["email"], faq_url="../faq/", contact_url="tel:" + CFG["phoneTel"], home_url="../")
_rsecs = "".join('<section aria-labelledby="h-%s"><h2 id="h-%s">%s</h2>%s</section>' % (i, i, esc(h), b) for i, h, b in _rc["sections"])
_rsrc = ('<section class="sources" aria-labelledby="h-sources"><h2 id="h-sources">Sources</h2><ul>%s</ul><p class="upd">Reviews load live from Google and Shopper Approved; page updated <time datetime="%s">%s</time>.</p></section>'
         % ("".join('<li><a href="%s" rel="noopener" target="_blank">%s</a></li>' % (esc(u), esc(n)) for n, u in _rc["sources"]), TODAY, nice_day(TODAY)))
_rmain = ('<section class="hero hero--class" aria-labelledby="h1"><div class="wrap"><nav class="crumb" aria-label="Breadcrumb"><a href="../">Home</a><span>/</span>Reviews</nav>'
          '<h1 id="h1">%s</h1><p class="lead" id="lead">%s</p></div></section>'
          '<div class="wrap reviews-page">%s%s<section id="faq" aria-labelledby="h-rfaq"><h2 id="h-rfaq">What do people ask about our reviews?</h2>%s</section>%s</div>'
          % (esc(_rc["h1"]), esc(_rc["lead"]), takeaways_html(_rc["takeaways"]), _rsecs, faq_html(_rc["faq"]), _rsrc))
urls.append(render(["reviews"], fit_title(_rc["title"], "1 Exam Prep Customer Reviews and Ratings"), _rc["desc"], _rmain, CFG.get("logo"),
                   extra_ld=[crumbs_ld([("Home", ""), ("Reviews", "reviews/")]), faq_ld(_rc["faq"])]))

# ---------- 404 ----------
# GitHub Pages serves 404.html at whatever address was typed, so every link here is root-relative ("/faq/").
# An address that contains a real license or state (an old product link, say) still jumps to that page;
# anything else gets a real "not found" page with search, the finder and the main links.
def build_404():
    known = sorted(list(CLASSES) + [v for v in STATE_SLUG.values() if v])
    gopts = "".join('<option value="%s">%s</option>' % (g, esc(gn)) for g, gn, _ in vaclass.GROUPS if classes_in(g) and g not in NONSTATE)
    lopts = "".join('<option value="/%s/" data-g="%s">%s</option>' % (c["slug"], c["group"], esc(c["name"])) for g, _, _ in vaclass.GROUPS if g not in NONSTATE for c in classes_in(g))
    finder = ('<form class="tx-finder hv-finder" action="/search/" method="get" data-finder><label><span>Your state</span><select data-fg>%s</select></label>'
              '<label><span>Your license</span><select name="go" data-fl>%s</select></label><button class="btn btn-buy" type="submit">Show my prep</button></form>' % (gopts, lopts))
    pop = [CLASSES[k] for k in POPULAR if k in CLASSES]
    states = [(g, gn) for g, gn, _ in vaclass.GROUPS if g not in NONSTATE and classes_in(g)]
    main = ('<main id="main">'
            '<section class="hero hv-hero pf-hero pf-404" aria-labelledby="h1"><canvas class="pf-water" aria-hidden="true"></canvas>'
            '<div class="wrap pf-grid"><div class="hv-hero-copy"><p class="hv-eyebrow">Error 404 &middot; page not found</p>'
            '<h1 id="h1">This pipe leads <em>nowhere.</em></h1>'
            '<p class="lead">We could not find <code class="pf-404-path" id="nf-path">that page</code>. It may have moved when a product was renamed in the store, or the link has a typo. '
            'Search for your exam, or pick your state and license.</p>'
            '<form class="pf-404-search" action="/search/" method="get" role="search"><label for="nf-q" class="sr-only">Search the site</label>'
            '<input id="nf-q" name="q" type="search" placeholder="%s" autocomplete="off"><button class="btn btn-buy" type="submit">Search</button></form>'
            '<p class="pf-404-links"><a href="/">Home page</a><a href="/faq/">Plumbing exam FAQ</a><a href="/blog/">Blog</a><a href="tel:%s">Call %s</a></p></div>'
            '<div class="pf-finder-box"><p class="pf-fh">Find your exam package</p><p class="pf-fs">Pick a state, then your license, and go straight to its packages.</p>%s</div></div></section>'
            '<section class="va-group" aria-labelledby="h-pop"><div class="wrap"><h2 id="h-pop">Popular plumbing licenses</h2><ul class="va-lics">%s</ul></div></section>'
            '<section class="va-group" aria-labelledby="h-st"><div class="wrap"><h2 id="h-st">Browse by state</h2><ul class="pf-404-states">%s</ul></div></section>'
            '</main>') % (
        esc(vacopy.HOME_SEARCH_PLACEHOLDER), esc(CFG.get("phoneTel", "")), esc(CFG.get("phone", "")), finder,
        "".join('<li><a class="va-lic" href="/%s/"><b>%s %s</b><span class="va-n">%s</span><span class="va-p"><small>from</small> %s</span></a></li>'
                % (c["slug"], esc(state_name(c["group"]) or ""), esc(c["name"]), plural(len(c["products"]), "option"), money(c["lo"])) for c in pop),
        "".join('<li><a href="/%s/">%s</a></li>' % (STATE_SLUG.get(g) or classes_in(g)[0]["slug"], esc(gn)) for g, gn in states))
    redirect = ('<script>(function(){var S=%s;var p=location.pathname.split("/").filter(Boolean).map(function(x){return x.toLowerCase();});'
                'for(var k=0;k<p.length;k++){if(S.indexOf(p[k])>-1){location.replace("/"+p.slice(0,k+1).join("/")+"/");return;}}'
                'document.addEventListener("DOMContentLoaded",function(){var e=document.getElementById("nf-path");if(e)e.textContent=decodeURIComponent(location.pathname);});})();</script>'
                % json.dumps(known))
    title = "Page not found | %s" % BRAND
    desc = "The page you asked for is not on %s. Search the site or pick your state and license to find plumbing exam prep." % BRAND
    out = (tpl.replace("{{MAIN}}", main).replace("{{STICKY}}", "")
           .replace("{{ASSETS_HEAD}}", redirect + "\n" + assets_head("/"))
           .replace("{{ASSETS_SEARCH}}", '<script src="/shared/site-index.js" defer></script>\n<script src="/shared/search.js" defer></script>\n<script src="/shared/track.js" defer></script>\n<script src="/shared/va.js" defer></script>')
           .replace("{{HEAD_EXTRA}}", head_extra("404.html", title, desc, None, "/", True, (), "WebPage"))
           .replace("{{NAV_TOOLS}}", nav_tools('<a class="btn btn-buy" href="/#states">Find my license</a>'))
           .replace("{{FOOTER}}", footer("/")).replace("{{TITLE}}", esc(title)).replace("{{DESC}}", esc(trim_desc(desc)))
           .replace("{{CANONICAL}}", "").replace("{{OGIMAGE}}", "")
           .replace("{{REL}}", "/").replace("{{HOME}}", "/").replace("{{ROUTE}}", json.dumps({"depth": 0, "notFound": True})))
    out = re.sub(r'<meta property="og:url"[^>]*>\s*', "", out)
    open(os.path.join(ROOT, "404.html"), "w", encoding="utf-8").write(anchor_ids(out))
build_404()

# ---------- /search/ ----------
sp_main = ('<section class="wrap search-page"><h1 id="h1">Search</h1><form id="searchPage" class="srch-form" role="search"><input class="srch-q" name="q" type="search" placeholder="License, package or product" aria-label="Search" autocomplete="off"><button class="btn btn-buy" type="submit">Search</button></form><div id="searchOut"></div></section>')
render(["search"], "Search | " + BRAND, "Search %s exam prep by license, package type or product name." % BRAND, sp_main, CFG.get("logo"), route={"depth": 1, "search": True})
p_ = os.path.join(ROOT, "search", "index.html"); s_ = open(p_, encoding="utf-8").read().replace('content="index, follow, max-image-preview:large"', 'content="noindex, nofollow"')
s_ = re.sub(r'<link rel="alternate" type="text/markdown"[^>]*>\n', "", s_); s_ = re.sub(r'<script type="application/ld\+json">\{"@context": "https://schema.org", "@type": "WebPage".*?</script>\n', "", s_, flags=re.S)
open(p_, "w", encoding="utf-8").write(s_)

# ---------- /admin/ ----------
atpl = open(os.path.join(ROOT, "store", "admin.html"), encoding="utf-8").read()
admin_cfg = {"gtagId": CFG.get("gtagId", ""), "ga4PropertyId": CFG.get("ga4PropertyId", ""), "googleOAuthClientId": CFG.get("googleOAuthClientId", ""), "repo": CFG.get("repo", ""), "siteUrl": SITE or ""}
os.makedirs(os.path.join(ROOT, "admin"), exist_ok=True)
open(os.path.join(ROOT, "admin", "index.html"), "w", encoding="utf-8").write(brand_tokens(atpl.replace("{{ADMIN_JSON}}", json.dumps(admin_cfg))))

# ---------- blog ----------
ALL_POSTS = blogkit.load_posts(os.path.join(ROOT, "content", "posts"), SITE or "")
POSTS = [q for q in ALL_POSTS if q.get("kind", "blog") != "page"]
PAGES = [q for q in ALL_POSTS if q.get("kind", "blog") == "page"]
btpl = open(os.path.join(ROOT, "store", "blog-post.html"), encoding="utf-8").read()
bitpl = open(os.path.join(ROOT, "store", "blog-index.html"), encoding="utf-8").read()
BLOG_FAQ = [(q, a.replace("{ful}", FUL["name"])) for q, a in vacopy.BLOG_FAQ]
def nice_date(d): return nice_day(d)
def post_card(q, rel):
    img = ('<img src="%s" alt="%s" loading="lazy">' % (esc(q["image"]), esc(q["title"]))) if q["image"] else ('<div class="noimg">%s</div>' % esc(q["title"][:48]))
    return ('<a class="card" href="%sblog/%s/" data-track="blog_card">%s<div class="card-body"><p class="post-meta"><time datetime="%s">%s</time><span>%d min read</span></p><h2>%s</h2><p>%s</p></div></a>'
            % (rel, q["slug"], img, q["date"], nice_date(q["date"]), max(1, round(q["words"] / 220)), esc(q["title"]), esc(q["excerpt"])))
def blog_common(out, rel, path, title, desc, image, lds, route, noindex=False, page_type="WebPage"):
    desc = trim_desc(desc)
    return (out.replace("{{TITLE}}", esc(title)).replace("{{DESC}}", esc(desc)).replace("{{BRAND}}", esc(BRAND))
            .replace("{{CANONICAL}}", ('<link rel="canonical" href="%s">\n' % absurl(path)) if SITE else "")
            .replace("{{OGIMAGE}}", ('<meta property="og:image" content="%s">\n' % esc(image)) if image else "")
            .replace("{{HEAD_EXTRA}}", head_extra(path, title, desc, image, rel, noindex, lds, page_type))
            .replace("{{ASSETS_HEAD}}", assets_head(rel))
            .replace("{{ASSETS_SEARCH}}", '<script src="%sshared/site-index.js" defer></script>\n<script src="%sshared/search.js" defer></script>\n<script src="%sshared/track.js" defer></script>' % (rel, rel, rel))
            .replace("{{NAV_TOOLS}}", nav_tools('<a class="btn btn-buy" href="%s#states">Find my license</a>' % rel)).replace("{{FOOTER}}", footer(rel))
            .replace("{{ROUTE}}", json.dumps(route)).replace("{{REL}}", rel).replace("{{HOME}}", rel))
blog_dir = os.path.join(ROOT, "blog"); shutil.rmtree(blog_dir, ignore_errors=True); os.makedirs(blog_dir, exist_ok=True)
all_tags = sorted({t for q in POSTS for t in q["tags"]}, key=str.lower)
def blog_index(dest_parts, posts, tag=None):
    rel = "../" * len(dest_parts); path = "/".join(dest_parts) + "/"
    title = ("Posts tagged %s | %s" % (tag, BRAND)) if tag else "Plumbing License Exam Blog: Study Tips and State Rules"
    desc = ("Posts tagged %s from the %s blog." % (tag, BRAND)) if tag else "Study plans, state plumbing licensing rules and exam strategy for plumber and plumbing contractor exams, from %s." % BRAND
    h1 = ("Posts tagged “%s”" % tag) if tag else "The plumbing license exam blog"
    lead = ("%d post%s." % (len(posts), "" if len(posts) == 1 else "s")) if tag else (vacopy.BLOG_LEAD)
    feat, rest = (posts[0], posts[1:]) if posts and not tag else (None, posts)
    feat_html = ""
    if feat:
        fimg = ('<img src="%s" alt="%s">' % (esc(feat["image"]), esc(feat["title"]))) if feat["image"] else ""
        feat_html = ('<a class="feature%s" href="%sblog/%s/" data-track="blog_featured">%s<div><span class="pc-tier">Latest</span><h2>%s</h2><p>%s</p><p class="post-meta"><time datetime="%s">%s</time><span>%d min read</span></p></div></a>'
                     % ("" if fimg else " noimg", rel, feat["slug"], fimg, esc(feat["title"]), esc(feat["excerpt"]), feat["date"], nice_date(feat["date"]), max(1, round(feat["words"] / 220))))
    tagf = ('<nav class="tagbar" aria-label="Topics"><a class="tag" href="%sblog/"%s>All</a>%s</nav>' % (rel, "" if tag else ' aria-current="page"', "".join('<a class="tag" href="%sblog/tag/%s/"%s>%s</a>' % (rel, blogkit.slugify(t), ' aria-current="page"' if tag == t else "", esc(t)) for t in all_tags))) if all_tags else ""
    cards = "".join(post_card(q, rel) for q in rest)
    empty = '' if posts else '<p class="empty">No posts yet. The first one is on its way.</p>'
    lds = [crumbs_ld([("Home", ""), ("Blog", "blog/")] + ([(tag, path)] if tag else [])),
           {"@context": "https://schema.org", "@type": "Blog" if not tag else "CollectionPage", "name": h1, "url": absurl(path), "publisher": publisher_ld(), "dateModified": TODAY,
            "blogPost" if not tag else "hasPart": [{"@type": "BlogPosting", "headline": q["title"], "url": absurl("blog/%s/" % q["slug"]), "datePublished": q["date"]} for q in posts[:20]]}]
    if not tag:
        lds.append(faq_ld(BLOG_FAQ))
        lds.append({"@context": "https://schema.org", "@type": "Article", "headline": h1, "url": absurl(path), "mainEntityOfPage": absurl(path),
                    "author": {"@type": "Organization", "name": BRAND, "url": SITE or STORE}, "publisher": publisher_ld(),
                    "datePublished": LAUNCH, "dateModified": TODAY, "inLanguage": "en-US"})
    out = blog_common(bitpl, rel, path, title, desc, (feat or {}).get("image") or CFG.get("logo"), lds, {"depth": len(dest_parts), "blog": True}, noindex=bool(tag), page_type=None)
    out = out.replace("{{YEAR}}", TODAY[:4])
    intro = "" if tag else ('<div class="blog-intro"><p>Most people who fail a licensing exam do not fail on knowledge. They run out of time in the references, misread an exception, or bring the wrong edition. New posts land here first and in the <a href="%sblog/feed.xml">RSS feed</a>. When a post is about one license, it links straight to that license page so you can act on it.</p></div>' % rel)
    btk = takeaways_html(["%d post%s so far%s, written for plumber, plumbing contractor and inspector candidates." % (len(posts), "" if len(posts) == 1 else "s", (" tagged %s" % tag) if tag else ""),
                          "Topics: %s." % ", ".join(all_tags[:8]) if all_tags else "Topics cover study strategy, using the code book and state plumbing licensing rules.",
                          "Exam prep for %d plumbing licenses in %d states and DC, with every rule linked to the board that sets it." % (n_cls, len([g for g, _, _ in vaclass.GROUPS if g not in NONSTATE and classes_in(g)]) - 1),
                          "New posts appear in the RSS feed at /blog/feed.xml the moment they are published."])
    out = out.replace("{{BLOG_FAQ_HTML}}", "".join('<details%s><summary>%s</summary><p>%s</p></details>' % (" open" if i == 0 else "", esc(q), esc(a)) for i, (q, a) in enumerate(BLOG_FAQ)))
    out = out.replace("{{TAKEAWAYS_HTML}}", btk).replace("{{INTRO_HTML}}", intro).replace("{{H1}}", esc(h1)).replace("{{LEAD}}", esc(lead)).replace("{{TAG_FILTER}}", tagf).replace("{{FEATURED_HTML}}", feat_html).replace("{{CARDS_HTML}}", cards).replace("{{EMPTY_HTML}}", empty)
    if not tag: out = out.replace("</main>", sources_html("home", vacopy.MAIN_SOURCES).replace('<section class="wrap sources"', '<section class="sources"') + "\n</main>", 1)
    d = os.path.join(ROOT, *dest_parts); os.makedirs(d, exist_ok=True); open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(anchor_ids(out))
    if SITE and not tag: urls.append(absurl(path))
blog_index(["blog"], POSTS)
for t in all_tags: blog_index(["blog", "tag", blogkit.slugify(t)], [q for q in POSTS if t in q["tags"]], t)
from urllib.parse import quote
pages_dir = os.path.join(ROOT, "pages"); shutil.rmtree(pages_dir, ignore_errors=True)
def license_for(q):
    v = (q.get("state") or "").strip().lower()
    return next((c for c in CLASSES.values() if v and (v == c["slug"] or v == c["name"].lower())), None)
for q in POSTS + PAGES:
    is_page = q.get("kind") == "page"
    parts = ["pages" if is_page else "blog", q["slug"]]; rel = "../../"; path = "%s/%s/" % (parts[0], q["slug"]); url = absurl(path)
    lic = license_for(q)
    if lic:
        cta_url = "%s%s/" % (rel, lic["slug"]); cta_kicker = lic["name"]; cta_title = "Ready to study for the %s exam?" % lic["name"]
        cta_text = "%s from %s, with one-click checkout." % (plural(len(lic["products"]), "option"), money(lic["lo"])); cta_label = "See %s options" % lic["name"].split(" (")[0]
        more_link = '<a href="%s">%s</a>' % (cta_url, esc(lic["name"]))
    else:
        cta_url = rel + "#states"; cta_kicker = "Ready to study?"; cta_title = "Find your state and license, then choose a package."; cta_text = "Exam prep for %d plumbing licenses in %d states and DC." % (n_cls, len([g for g, _, _ in vaclass.GROUPS if g not in NONSTATE and classes_in(g)]) - 1); cta_label = "Find my license"; more_link = ""
    related = [r for r in POSTS if r["slug"] != q["slug"] and (set(r["tags"]) & set(q["tags"]))][:3] or [r for r in POSTS if r["slug"] != q["slug"]][:3]
    rel_html = ('<section class="related-posts" aria-labelledby="h-more"><h2 id="h-more">Keep reading</h2><div class="post-grid">%s</div></section>' % "".join(post_card(r, rel) for r in related)) if related else ""
    tags_html = ('<nav class="tagbar" aria-label="Topics">%s</nav>' % "".join('<a class="tag" href="%sblog/tag/%s/">%s</a>' % (rel, blogkit.slugify(t), esc(t)) for t in q["tags"])) if q["tags"] else ""
    hero = ('<figure class="hero"><img src="%s" alt="%s" fetchpriority="high"></figure>' % (esc(q["image"]), esc(q["title"]))) if q["image"] and ('src="%s"' % q["image"]) not in q["html"] else ""
    lds = [crumbs_ld([("Home", ""), ("Blog", "blog/"), (q["title"], path)]),
           {"@context": "https://schema.org", "@type": "BlogPosting", "headline": q["title"][:110], "description": q["excerpt"], "image": [q["image"]] if q["image"] else None, "datePublished": q["date"], "dateModified": q["updated"],
            "author": {"@type": "Organization" if not q["author"] or q["author"] == BRAND else "Person", "name": q["author"] or BRAND}, "publisher": publisher_ld(),
            "mainEntityOfPage": url, "url": url, "wordCount": q["words"], "keywords": ", ".join(q["tags"]) or None, "articleSection": "Plumbing License Exam Prep", "inLanguage": "en-US"}]
    lds[1] = {k: v for k, v in lds[1].items() if v}
    # FAQ schema from the post's own questions, unless the post already carries its own FAQPage markup
    if q.get("faq") and '"FAQPage"' not in q["html"]: lds.append(faq_ld(q["faq"]))
    ptitle = q.get("meta_title") or (q["title"] if len(q["title"]) + len(BRAND) + 3 > 60 else "%s | %s" % (q["title"], BRAND))
    pdesc = q.get("meta_description") or q["excerpt"]
    if is_page: lds[0] = crumbs_ld([("Home", ""), (q["title"], path)]); lds[1]["@type"] = "Article"
    out = blog_common(btpl, rel, path, ptitle, pdesc, q["image"] or CFG.get("logo"), lds, {"depth": 2, "blog": True, "post": q["slug"]}, page_type=None)
    if is_page: out = out.replace('<a href="{{REL}}blog/">Blog</a><span>/</span>', "").replace('<div class="post-meta">', '<div class="post-meta" hidden>')
    out = (out.replace("{{H1}}", esc(q["title"])).replace("{{TITLE_SHORT}}", esc(q["title"][:60] + ("…" if len(q["title"]) > 60 else ""))).replace("{{EXCERPT}}", esc(q["excerpt"]))
           .replace("{{DATE}}", q["date"]).replace("{{UPDATED}}", q["updated"]).replace("{{DATE_NICE}}", nice_date(q["date"])).replace("{{AUTHOR_HTML}}", ('<span>%s</span>' % esc(q["author"])) if q["author"] else "")
           .replace("{{READ_MIN}}", str(max(1, round(q["words"] / 220)))).replace("{{TAGS_HTML}}", tags_html).replace("{{HERO_HTML}}", hero).replace("{{TAKEAWAYS_HTML}}", takeaways_html(q.get("takeaways") or [])).replace("{{BODY_HTML}}", q["html"])
           .replace("{{URL_ENC}}", quote(url, safe="")).replace("{{TITLE_ENC}}", quote(q["title"], safe="")).replace("{{MORE_LINK}}", more_link)
           .replace("{{CTA_KICKER}}", esc(cta_kicker)).replace("{{CTA_TITLE}}", esc(cta_title)).replace("{{CTA_TEXT}}", esc(cta_text)).replace("{{CTA_URL}}", cta_url).replace("{{CTA_LABEL}}", esc(cta_label))
           .replace("{{RELATED_HTML}}", rel_html))
    d = os.path.join(ROOT, *parts); os.makedirs(d, exist_ok=True); open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(anchor_ids(out))
    if SITE: urls.append(url)
rpath = os.path.join(ROOT, "content", "redirects.json")
if os.path.exists(rpath):
    try: RED = json.load(open(rpath, encoding="utf-8"))
    except Exception: RED = {}
    for old, new in RED.items():
        old = old.strip("/"); new = new.strip("/")
        if not old or old == new or os.path.exists(os.path.join(ROOT, *old.split("/"), "index.html")): continue
        target = absurl(new + "/")
        os.makedirs(os.path.join(ROOT, *old.split("/")), exist_ok=True)
        open(os.path.join(ROOT, *old.split("/"), "index.html"), "w", encoding="utf-8").write('<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Moved</title><meta name="robots" content="noindex"><link rel="canonical" href="%s"><meta http-equiv="refresh" content="0; url=%s"><script>location.replace(%s)</script></head><body><p>This page has moved to <a href="%s">%s</a>.</p></body></html>' % (esc(target), esc(target), json.dumps(target), esc(target), esc(target)))
feed_items = "".join("<item><title>%s</title><link>%s</link><guid isPermaLink=\"true\">%s</guid><pubDate>%s</pubDate><description>%s</description></item>\n" % (
    esc(q["title"]), absurl("blog/%s/" % q["slug"]), absurl("blog/%s/" % q["slug"]), datetime.datetime.fromisoformat(q["date"][:10]).strftime("%a, %d %b %Y 09:00:00 -0500"), esc(q["excerpt"])) for q in POSTS[:30])
open(os.path.join(blog_dir, "feed.xml"), "w", encoding="utf-8").write('<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel><title>%s Blog</title><link>%s</link><description>Plumbing license exam study tips and state licensing news.</description><language>en-us</language>\n%s</channel></rss>\n' % (esc(BRAND), absurl("blog/"), feed_items))
open(os.path.join(blog_dir, "posts.json"), "w", encoding="utf-8").write(json.dumps([{k: q[k] for k in ("slug", "title", "date", "updated", "excerpt", "image", "tags", "state", "level", "author", "words")} for q in POSTS], ensure_ascii=False))

# ---------- /faq/ ----------
ftpl = open(os.path.join(ROOT, "store", "faq.html"), encoding="utf-8").read()
GEN_FAQ = json.load(open(os.path.join(ROOT, "content", "faq-general.json"), encoding="utf-8"))["categories"]
shutil.rmtree(os.path.join(ROOT, "faq"), ignore_errors=True)
gen_pairs = [(q, a.replace("1 Exam Prep", FUL["name"])) for cg in GEN_FAQ for q, a in cg["items"]]
sections = [(cg["slug"], cg["name"], len(cg["items"]), faq_html([(q, a.replace("1 Exam Prep", FUL["name"])) for q, a in cg["items"]])) for cg in GEN_FAQ]
lic_list = "".join('<li><a href="../%s/#faq">%s</a></li>' % (c["slug"], esc(c["name"])) for c in (CLASSES[s] for s in ORDER if s in CLASSES))
sections.append(("licenses", "Where are the questions for my state?", len([g for g, _, _ in vaclass.GROUPS if STATE_SLUG.get(g) and classes_in(g)]), '<p class="faq-count">Every state page and license page ends with its own questions: the price range, open-book rules and who issues the license. Pick your state below.</p><ul class="faq-states">%s</ul>' % "".join('<li><a href="../%s/#faq">%s</a></li>' % (STATE_SLUG[g], esc(n)) for g, n, _ in vaclass.GROUPS if STATE_SLUG.get(g) and classes_in(g))))
jump = "".join('<a class="tag" href="#%s">%s <small>%d</small></a>' % (sid, esc(name), n) for sid, name, n, _ in sections)
secs = "".join('<section class="faq-sec" aria-labelledby="%s"><h2 id="%s">%s</h2>%s</section>' % (sid, sid, esc(name), body) for sid, name, n, body in sections)
flead = vacopy.GENERAL_FAQ_LEAD.format(n=len(gen_pairs), k=n_cls)
ftitle = fit_title("Plumbing License Exam FAQ: %d Answers" % len(gen_pairs))
fdesc = trim_desc(flead)
lds = [crumbs_ld([("Home", ""), ("FAQ", "faq/")]), faq_ld(gen_pairs[:80])]
fout = (ftpl.replace("{{TITLE}}", esc(ftitle)).replace("{{DESC}}", esc(fdesc)).replace("{{BRAND}}", esc(BRAND))
        .replace("{{CANONICAL}}", ('<link rel="canonical" href="%s">\n' % absurl("faq/")) if SITE else "").replace("{{OGIMAGE}}", ('<meta property="og:image" content="%s">\n' % esc(CFG.get("logo"))) if CFG.get("logo") else "")
        .replace("{{HEAD_EXTRA}}", head_extra("faq/", ftitle, fdesc, CFG.get("logo"), "../", False, lds))
        .replace("{{ASSETS_HEAD}}", assets_head("../"))
        .replace("{{ASSETS_SEARCH}}", '<script src="../shared/site-index.js" defer></script>\n<script src="../shared/search.js" defer></script>\n<script src="../shared/track.js" defer></script>')
        .replace("{{NAV_TOOLS}}", nav_tools('<a class="btn btn-buy" href="../#states">Find my license</a>')).replace("{{FOOTER}}", footer("../"))
        .replace("{{ROUTE}}", json.dumps({"depth": 1, "faq": True})).replace("{{REL}}", "../").replace("{{HOME}}", "../")
        .replace("{{CRUMB_HTML}}", '<a href="../">Home</a><span>/</span>FAQ').replace("{{H1}}", "Plumbing license exam FAQ").replace("{{LEAD}}", esc(flead))
        .replace("{{TAKEAWAYS_HTML}}", takeaways_html(["%d questions answered here, plus 7 more on each of the %d license pages." % (len(gen_pairs), n_cls),
] + vacopy.FAQ_TAKEAWAYS))
        .replace("{{JUMP_HTML}}", jump).replace("{{SECTIONS_HTML}}", secs)
        .replace("{{CTA_KICKER}}", "Ready to study?").replace("{{CTA_TITLE}}", "Find your license, then choose a package.").replace("{{CTA_TEXT}}", esc("Exam prep for %d plumbing licenses, from %s. Buy buttons go straight to checkout." % (n_cls, money(lowest))))
        .replace("{{CTA_URL}}", "../#states").replace("{{CTA_LABEL}}", "Find my license")
        .replace("{{RELATED_HTML}}", sources_html("home", vacopy.MAIN_SOURCES).replace('<section class="wrap sources"', '<section class="sources"')).replace("{{MORE_LINK}}", ""))
os.makedirs(os.path.join(ROOT, "faq"), exist_ok=True); open(os.path.join(ROOT, "faq", "index.html"), "w", encoding="utf-8").write(anchor_ids(fout))
urls.append(absurl("faq/"))

# ---------- icons + manifest (text logo until brand/logo-source.png is added and tools/make_logo.py is run) ----------
fav = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="14" fill="#1b1f3b"/><path d="M12 33 32 15l20 18h-6v16H18V33z" fill="#ff5a1f"/><rect x="28" y="37" width="8" height="12" fill="#1b1f3b"/></svg>'
if not HAS_PNG_ICONS:
    open(os.path.join(ROOT, "shared", "favicon.svg"), "w").write(fav)
    try:
        from PIL import Image, ImageDraw, ImageFont
        def font(sz):
            for f in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"):
                if os.path.exists(f): return ImageFont.truetype(f, sz)
            return ImageFont.load_default()
        house = lambda sc, ox, oy: [(ox + x * sc, oy + y * sc) for x, y in [(12, 33), (32, 15), (52, 33), (46, 33), (46, 49), (18, 49), (18, 33)]]
        im = Image.new("RGBA", (180, 180), (27, 31, 59, 255)); dr = ImageDraw.Draw(im); dr.polygon(house(2.6, 7, 7), fill=(255, 90, 31, 255)); im.save(os.path.join(ROOT, "shared", "apple-touch-icon.png"))
        lg = Image.new("RGB", (1200, 630), (27, 31, 59)); d = ImageDraw.Draw(lg); d.polygon(house(4.2, 70, 140), fill=(255, 90, 31))
        lines, cur = [], ""
        for w in BRAND.split():
            t = (cur + " " + w).strip()
            if d.textlength(t, font=font(74)) > 800: lines.append(cur); cur = w
            else: cur = t
        lines.append(cur); y = 300 - 44 * len(lines)
        for ln in lines: d.text((340, y), ln, font=font(74), fill="white"); y += 88
        tl, tcur, tlines = CFG.get("tagline", "").split(), "", []
        for w in tl:
            t = (tcur + " " + w).strip()
            if d.textlength(t, font=font(30)) > 800: tlines.append(tcur); tcur = w
            else: tcur = t
        tlines.append(tcur)
        for ln in tlines[:2]: d.text((340, y + 10), ln, font=font(30), fill=(255, 176, 143)); y += 40
        d.text((340, 560), "Fulfilled by %s" % FUL["name"], font=font(24), fill=(170, 175, 205))
        lg.save(os.path.join(ROOT, "shared", "logo.png"), optimize=True)
    except Exception as e: print("logo images skipped:", e)
open(os.path.join(ROOT, "manifest.webmanifest"), "w").write(json.dumps({"name": BRAND, "short_name": "Plumbing Exam", "start_url": "./", "display": "browser", "background_color": "#ffffff", "theme_color": "#020c1b",
    "icons": ([{"src": "shared/logo-mark.png", "sizes": "512x512", "type": "image/png"}] if HAS_PNG_ICONS else []) + [{"src": "shared/apple-touch-icon.png", "sizes": "180x180", "type": "image/png"}] + ([] if HAS_PNG_ICONS else [{"src": "shared/favicon.svg", "sizes": "any", "type": "image/svg+xml"}])}, indent=1))



# ---------- robots.txt, llms.txt, agents.md ----------
bots = ["GPTBot", "ChatGPT-User", "OAI-SearchBot", "ClaudeBot", "Claude-User", "anthropic-ai", "PerplexityBot", "Google-Extended", "Applebot-Extended", "Bingbot", "CCBot", "Amazonbot", "meta-externalagent"]
rb = ("# robots.txt for %s (%s)\n# Search engines and AI assistants are both welcome. Internal search, raw data and the admin page are held back.\n\n" % (BRAND, (SITE or "/").rstrip("/"))
      + "User-agent: *\nAllow: /\nDisallow: /search/\nDisallow: /designs/\nDisallow: /store/\nDisallow: /admin/\nDisallow: /*?q=\n\n# Named so the allow is explicit for AI crawlers.\n" + "".join("User-agent: %s\nAllow: /\n\n" % b for b in bots))
if SITE: rb += "Sitemap: %ssitemap.xml\n# Blog: %sblog/ (RSS at %sblog/feed.xml). FAQ: %sfaq/\n# Guides for AI assistants: %sllms.txt and %sagents.md\n" % (SITE, SITE, SITE, SITE, SITE, SITE)
open(os.path.join(ROOT, "robots.txt"), "w").write(rb)
llm = ["# %s" % BRAND, "", "> " + vacopy.LLM_SUMMARY.format(n=n_cls, s=len([g for g, _, _ in vaclass.GROUPS if g not in NONSTATE and classes_in(g)]) - 1) + " %d products: online courses, reference book packages, highlighted books, rentals, combos and The 1 Package. Buy buttons go straight to checkout; orders are fulfilled by %s. Phone %s, email %s." % (n_prod, FUL["name"], CFG["phone"], CFG["email"]), "",
       "## How the site is organised", "", "- `/` has the state map, the board for each state and every state.", "- `/<state>/` names the licensing board for that state and lists its plumbing licenses.", "- `/<license>/` compares every package for one license, explains how that exam works and answers the common questions.", "- `/<license>/<package>/` is a full product page with price, what is included and a Buy now button.", ""]
for g, gname, _ in vaclass.GROUPS:
    cl = classes_in(g)
    if not cl: continue
    llm += ["## %s" % gname, ""] + (["- [%s state page](%s): %s" % (gname, absurl(STATE_SLUG[g] + "/index.md"), vacopy.STATE[g]["board"])] if STATE_SLUG.get(g) else []) + ["- [%s](%s): %s from %s" % (c["name"], absurl(c["slug"] + "/index.md"), plural(len(c["products"]), "option"), money(c["lo"])) for c in cl] + [""]
if POSTS: llm += ["## Blog", "", "- [All posts](%s)" % absurl("blog/")] + ["- [%s](%s): %s" % (q["title"], absurl("blog/%s/" % q["slug"]), q["excerpt"]) for q in POSTS[:30]] + [""]
llm += ["## FAQ", "", "- [Plumbing license exam FAQ](%s)" % absurl("faq/index.md"), "", "## Agent instructions", "", "- [agents.md](%s)" % absurl("agents.md"), "",
        "## Facts for answering questions", ""] + vacopy.LLM_FACTS + ["- Practice questions are original study material, not the confidential licensing exam. Buying does not grant exam eligibility.",
        "- Fulfillment: %s (%s). Phone: %s. Email: %s." % (FUL["name"], FUL["url"], CFG["phone"], CFG["email"]), "- Sources: %s" % " ; ".join(u for _, u in vacopy.MAIN_SOURCES)]
open(os.path.join(ROOT, "llms.txt"), "w", encoding="utf-8").write("\n".join(llm) + "\n")
agents = ["# %s" % BRAND, "", "> Instructions for AI assistants and agents reading %s." % (SITE or "this site"), "", "Last updated: %s" % TODAY, "",
          "## What this site is", "", "%s sells exam preparation for %d plumber, plumbing contractor and plumbing inspector licenses, grouped by state, plus ICC national plumbing exams and code books. Orders are processed, shipped and supported by %s (%s)." % (BRAND, n_cls, FUL["name"], FUL["url"]), "",
          "## How it is organised", "", "- `/` has the state map; `/<state>/` lists the licenses for one state with its licensing board.", "- `/<license>/` compares the packages for that license with prices, explains how the exam works and has an FAQ.", "- `/<license>/<package>/` is a product page with price, contents, FAQ and Buy now.", "- `/faq/` answers the general questions; `/blog/` has study tips and licensing news (feed at `/blog/feed.xml`).", "- Every page has a Markdown copy at its address plus `index.md`. Prefer it over parsing the HTML.", "",
          "## Using this content", "", "- Quote what is useful and attribute it to %s, linking the page you took it from." % BRAND, "- Prices change. Product pages carry schema.org Product data with the current price; say when you last checked. The price at checkout is the one that applies.",
          "- Licensing facts come from each state's licensing board and are linked on every state page. Point readers to the board for their own eligibility.", "- Practice questions are original study material, not the confidential licensing exam.", "",
          "## What this site cannot answer", "", "- Anything about a specific customer, order or account.", "- Exam dates, a person's eligibility or application status. Those belong to the board and the testing provider.", "- Anything not written on a page.", "",
          "## Contact", "", "- Phone: %s" % CFG["phone"], "- Email: %s" % CFG["email"], "- Fulfillment center: %s (%s)" % (FUL["name"], FUL["url"]), "",
          "## Crawling", "", "- Rules: %srobots.txt (all major search and AI crawlers are allowed)" % (SITE or "/"), "- Shortlist: %sllms.txt" % (SITE or "/"), "- Every page: %ssitemap.xml" % (SITE or "/"), ""]
open(os.path.join(ROOT, "agents.md"), "w", encoding="utf-8").write("\n".join(agents))

if SITE:
    import mdkit
    n_md = mdkit.write_all(ROOT, SITE, BRAND, TODAY, "Publisher: %s. Orders are fulfilled by %s (%s). Phone %s, email %s.  \nPrices change; the product page and checkout show the current price." % (BRAND, FUL["name"], FUL["url"], CFG["phone"], CFG["email"]))
    print("Markdown copies for AI assistants: %d" % n_md)
    urls = [u for u in urls if u]
    body = "".join("  <url><loc>%s</loc><lastmod>%s</lastmod><changefreq>weekly</changefreq><priority>%s</priority></url>\n" % (esc(u), TODAY, "1.0" if u == SITE else ("0.8" if u.count("/") - SITE.count("/") == 1 else "0.6")) for u in urls)
    open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8").write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + body + "</urlset>\n")

print("Built home + %d license pages + %d product pages + %d blog posts + /faq/ /search/ robots.txt llms.txt agents.md%s" % (len(CLASSES), len(PRODUCTS), len(POSTS), (" sitemap.xml (%d URLs)" % len(urls)) if SITE else ""))
if UNCLASSIFIED: print("Unclassified (listed under Other, add a rule in tools/vaclass.py):", "; ".join(UNCLASSIFIED))

# ---------- site dashboard tracker, just before </body> on every page (not /admin/) ----------
if CFG.get("dashboardUrl") and CFG.get("siteKey"):
    _tag = '<script src="%s/t.js" data-site="%s" defer></script>' % (html.escape(CFG["dashboardUrl"].rstrip("/")), html.escape(CFG["siteKey"]))
    _added = 0
    for _d, _subs, _files in os.walk(ROOT):
        _subs[:] = [x for x in _subs if not x.startswith(".") and x not in ("store", "tools", "node_modules", "brand", "admin", "content", "worker")]
        for _f in _files:
            if not _f.endswith(".html"): continue
            _p = os.path.join(_d, _f); _t = open(_p, encoding="utf-8").read()
            if "/t.js\" data-site=" in _t or "</body>" not in _t: continue
            _i = _t.rindex("</body>"); open(_p, "w", encoding="utf-8").write(_t[:_i] + _tag + "\n" + _t[_i:]); _added += 1
    print("Dashboard tracker added to %d pages" % _added)
