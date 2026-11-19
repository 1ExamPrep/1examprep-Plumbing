"""Sort the plumbing catalog into states, licenses and package types.

build.py imports this (as vaclass, so the shared code reads the same as the Texas, Virginia and HVAC repos). Everything
is worked out from the product title, so the catalog can come from tools/pull_storefront.py, the dashboard sync or
tools/sync_shopify.py.

How a title becomes a license: the package wording is cut off the end ("Exam Book Package", "- Online Exam Prep",
"Ultimate Exam Prep Rental Package"...), the state is found, and what is left is the license name. ALIASES merges
spellings of the same license. A new product with a new license gets its own page on the next build without any
code change; check the "licenses" list printed by: python3 tools/plclass.py tools/catalog-titles.txt
"""
import re

STATE = "State"

STATES = [("al", "Alabama"), ("ak", "Alaska"), ("az", "Arizona"), ("ar", "Arkansas"), ("ca", "California"), ("co", "Colorado"),
          ("ct", "Connecticut"), ("de", "Delaware"), ("dc", "Washington DC"), ("fl", "Florida"), ("ga", "Georgia"), ("hi", "Hawaii"),
          ("id", "Idaho"), ("il", "Illinois"), ("in", "Indiana"), ("ia", "Iowa"), ("ks", "Kansas"), ("ky", "Kentucky"), ("la", "Louisiana"),
          ("me", "Maine"), ("md", "Maryland"), ("ma", "Massachusetts"), ("mi", "Michigan"), ("mn", "Minnesota"), ("ms", "Mississippi"),
          ("mo", "Missouri"), ("mt", "Montana"), ("ne", "Nebraska"), ("nv", "Nevada"), ("nh", "New Hampshire"), ("nj", "New Jersey"),
          ("nm", "New Mexico"), ("ny", "New York"), ("nc", "North Carolina"), ("nd", "North Dakota"), ("oh", "Ohio"), ("ok", "Oklahoma"),
          ("or", "Oregon"), ("pa", "Pennsylvania"), ("ri", "Rhode Island"), ("sc", "South Carolina"), ("sd", "South Dakota"),
          ("tn", "Tennessee"), ("tx", "Texas"), ("ut", "Utah"), ("vt", "Vermont"), ("va", "Virginia"), ("wa", "Washington"),
          ("wv", "West Virginia"), ("wi", "Wisconsin"), ("wy", "Wyoming")]
STATE_NAME = dict(STATES)
_BY_NAME = sorted(((n, k) for k, n in STATES), key=lambda x: -len(x[0]))
EXTRA_GROUPS = [("icc", "ICC national plumbing exams", ""), ("books", "Plumbing code books and references", "")]
GROUPS = [(k, n, "") for k, n in STATES] + EXTRA_GROUPS

# package types: (slug, name, regex on the title). The first match wins, so specific wording comes first.
_MATCH = [
    ("the-1-package", "The 1 Package (all-inclusive)", r"^The 1 Package"),
    ("complete-books-tabs-course", "Complete Books, Tabs and Course", r"Complete Books, Tabs & Course"),
    ("study-guide-course", "Study Guide and Online Course", r"Study Guide & Online Course"),
    ("study-guide", "Exam Prep Study Guide", r"Exam Prep Study Guide|Journeyman Plumber Exam Study Guide"),
    ("ultimate-exam-room", "Ultimate Exam-Room Package", r"Ultimate Books Exam Room Approved"),
    ("rental-exam-room", "Exam-Room Books and Course Rental", r"Rental - Exam Room Approved"),
    ("exam-room-highlighted", "Highlighted and Tabbed Exam-Room Books", r"Highlighted & Tabbed Books Allowed into Exam"),
    ("exam-room-books", "Books Allowed into the Exam", r"Books Allowed into Exam"),
    ("ultimate-2021", "Ultimate Exam Prep Package (2021 IPC)", r"Ultimate Exam Prep Package \[2021"),
    ("exam-prep-2021", "Exam Prep Package (2021 IPC)", r"Exam Prep Package \[2021"),
    ("ultimate-rental", "Ultimate Exam Prep Package", r"Ultimate (Exam Prep )?(Rental|Package)"),
    ("refresher-class", "Books Refresher Class", r"Refresher Class"),
    ("live-training", "Live Virtual Training", r"Live Virtual"),
    ("rental-package", "Books and Courses Rental", r"Rental"),
    ("online-practice-exams", "Online Practice Questions", r"Practice Questions"),
    ("intro-course", "Introduction Course", r"^Introduction to Becoming"),
    ("flash-combo", "Flash Card Combo", r"Flash Card Combo"),
    ("flash-cards", "Flash Cards", r"Flash Card"),
    ("tabs-highlights", "Pre-Printed Tabs and Highlights", r"Pre-Printed Tabs and Highlights"),
    ("tabs", "Pre-Printed Tabs", r"Pre-?\s?Printed( Tabs)?|PrePrinted"),
    ("highlighted-tabbed", "Highlighted and Tabbed Books", r"Highlighted"),
    ("content-outline", "Exam Content Outline Books", r"Content Outline"),
    ("tutoring", "Private Tutoring", r"Tutoring"),
    ("online-course", "Online Exam Prep Course", r"Online|Course|^GITS|Prep Package"),
    ("book-package", "Complete Book Package", r"Book (Package|Set)|Book package|Books Package"),
]
TYPES = [(s, n, (lambda rx: (lambda t, ty: re.search(rx, t, re.I) is not None))(rx)) for s, n, rx in _MATCH] + [("reference-book", "Reference Book", lambda t, ty: True)]
_RANK_ORDER = ["tabs", "tabs-highlights", "content-outline", "flash-cards", "flash-combo", "online-practice-exams", "study-guide", "intro-course", "online-course",
               "study-guide-course", "live-training", "refresher-class", "exam-room-books", "exam-room-highlighted", "book-package", "reference-book",
               "highlighted-tabbed", "exam-prep-2021", "complete-books-tabs-course", "rental-exam-room", "rental-package", "tutoring", "ultimate-2021",
               "ultimate-exam-room", "ultimate-rental", "the-1-package"]
TYPE_RANK = {s: i for i, s in enumerate(_RANK_ORDER)}

SKIP = re.compile(r"Free Demo|Personal AI Tutor", re.I)  # $0 demos are not listed

# Wording that ends the license name in a title
_CUT = re.compile(r"(\s+-\s+|\s+Exam\b|\s+Examination\b|;|\s+Books?\b|\s+Book Package|\s+Highlighted\b|\s+Ultimate\b|\s+Online\b|\s+Pre-?\s?Printed|"
                  r"\s+Study\b|\s+Flash\b|\s+Live Virtual|\s+Complete\b|\s+\+\s+Business|\s+Trade$|,?\s+Licensing\b)", re.I)
def norm(x):
    """Lowercase, no spaces around hyphens or inside brackets' dashes, single spaces: the form ALIASES keys are compared in."""
    x = re.sub(r"\s*-\s*", "-", x.lower().replace("&amp;", "&"))
    x = re.sub(r"\(\s*", "(", re.sub(r"\s*\)", ")", x))
    return re.sub(r"\s+", " ", x).strip(" -")
# Licenses spelled more than one way: lowercase key after normalising -> canonical name
ALIASES = {
    "plumbing, class i contractor": "Plumbing Class I Contractor",
    "plumbing, class ii contractor": "Plumbing Class II Contractor",
    "plumbing technician contractor": "Plumbing Technician",
    "master plumber class i (restricted) contractor": "Master Plumber Class I (Restricted)",
    "master plumber i (restricted) contractor": "Master Plumber Class I (Restricted)",
    "master plumber class ii (unrestricted) contractor": "Master Plumber Class II (Unrestricted)",
    "master plumber ii (unrestricted) contractor": "Master Plumber Class II (Unrestricted)",
    "commercial plumber": "Commercial Plumber Contractor", "commercial plumbing contractor": "Commercial Plumber Contractor",
    "residential plumber": "Residential Plumber Contractor",
    "journeyman plumber contractor": "Journeyman Plumber",
    "journeyworker plumber": "Journeyman Plumber",
    "plumbing residential/commercial contractor (cr-37)": "Plumbing Residential / Commercial Contractor (CR-37)",
    "plumbing, including solar residential/commercial contractor (cr-77)": "Plumbing, Including Solar Residential / Commercial Contractor (CR-77)",
    "solar plumbing, liquid systems only residential/commercial contractor (cr-78)": "Solar Plumbing, Liquid Systems Only Residential / Commercial Contractor (CR-78)",
    "plumbing, including solar residential contractor": "Plumbing, Including Solar Residential Contractor (R-37)",
    "plumbing residential contractor (r-37r)": "Plumbing, Residential Contractor (R-37R)",
    "plumbing contractor (mm-1)": "Plumbing Contractor MM-1",
    "plumbing inspector contractor": "Plumbing Inspector",
    "plumbing business and law contractor": "Plumbing Business and Law",
    "cmc-a mechanical plumbing contractor": "CMC-A Mechanical Plumbing",
    "cmc-a - mechanical plumbing (prov)": "CMC-A Mechanical Plumbing",
    "llp - limited licensed plumber (prov)": "Limited Licensed Plumber Contractor",
    "limited licensed plumber contractor (prov)": "Limited Licensed Plumber Contractor",
    "residential plumbing and natural gas journeyman contractor": "Residential Plumbing and Natural Gas Journeyman",
    "master plumber / master gasfitter contractor": "Master Plumber / Master Gasfitter Contractor",
    "master plumber-gas fitter content outline contractor (psi)": "Master Plumber / Master Gasfitter Contractor",
    "journey plumber-gas fitter content outline (psi)": "Plumber Gas Fitter Journeyman",
    "master plumber with gas (icc - 557 - ks)": "Master Plumber with Gas Contractor (ICC 557)",
    "master plumber with gas contractor (icc - 557 - ks)": "Master Plumber with Gas Contractor (ICC 557)",
    "master plumber with gas (icc - kgf)": "Master Plumber with Gas Contractor (ICC KGF)",
    "master plumber with gas contractor (icc - kgf)": "Master Plumber with Gas Contractor (ICC KGF)",
    "journeyman plumber with gas (icc - 560 - ks)": "Journeyman Plumber with Gas (ICC 560)",
    "journeyman plumber with gas (icc - kgr)": "Journeyman Plumber with Gas (ICC KGR)",
    "springfield journeyman plumber (icc - w25_mo_s)": "Springfield Journeyman Plumber (ICC W25)",
    "(springfield) icc journeyman plumber": "Springfield Journeyman Plumber (ICC W25)",
    "springfield master plumber contractor (icc - w24_mo_s)": "Springfield Master Plumber (ICC W24)",
    "(springfield) icc) master plumber": "Springfield Master Plumber (ICC W24)",
    "kansas city journeyman plumber with gas contractor (icc - 675_mo_kc)": "Kansas City Journeyman Plumber with Gas (ICC 675)",
    "commerce city master plumber with gas (icc - g27-n)": "Commerce City Master Plumber with Gas (ICC G27-N)",
    "minneapolis journeyman plumber with gas (icc - 498 - mn - mi)": "Minneapolis Journeyman Plumber with Gas (ICC 498)",
    "minneapolis master plumber with gas (icc - 497 - mn - mi)": "Minneapolis Master Plumber with Gas (ICC 497)",
    "reading journeyman plumber (icc - g25-n)": "Reading Journeyman Plumber (ICC G25-N)",
    "reading master plumber (icc - g24-n)": "Reading Master Plumber (ICC G24-N)",
    "reading national standard master plumber (icc - f24-n)": "Reading National Standard Master Plumber (ICC F24-N)",
    "casper journeyman plumber with gas (icc - g28-n)": "Casper Journeyman Plumber with Gas (ICC G28-N)",
    "cleveland plumbing plans examiner (icc - p3)": "Cleveland Plumbing Plans Examiner (ICC P3)",
    "plumbing plans examiner (icc - p3)": "Plumbing Plans Examiner (ICC P3)", "plumbing plans examiner (icc 3p)": "Plumbing Plans Examiner (ICC P3)",
    "commercial plumbing inspector (icc - p2)": "Commercial Plumbing Inspector (ICC P2)", "commercial plumbing inspector (icc 2p)": "Commercial Plumbing Inspector (ICC P2)",
    "commercial plumbing inspector (icc - 2p)": "Commercial Plumbing Inspector (ICC P2)", "2p commercial plumbing inspector": "Commercial Plumbing Inspector (ICC P2)",
    "residential plumbing inspector (icc - p1)": "Residential Plumbing Inspector (ICC P1)", "residential plumbing inspector (icc 1p)": "Residential Plumbing Inspector (ICC P1)",
    "residential plumbing inspector (icc - 1p)": "Residential Plumbing Inspector (ICC P1)", "1p residential plumbing inspector": "Residential Plumbing Inspector (ICC P1)",
    "plumbing plans examiner (icc - 3p)": "Plumbing Plans Examiner (ICC P3)",
    "icc commercial plumbing inspector i3": "Commercial Plumbing Inspector (ICC I3)", "icc residential plumbing inspector j3": "Residential Plumbing Inspector (ICC J3)",
    "chicago plumber (journeyman)": "Chicago Journeyman Plumber",
    "gits journeyman plumber": "Journeyman Plumber (County, GITS PBE1B)", "gits master plumber": "Master Plumber (County, GITS PAE1B)",
    "prov journeyman plumber (county": "Journeyman Plumber (County, Prov)", "prov journeyman plumber (county -)": "Journeyman Plumber (County, Prov)",
    "prov master plumber (county -)": "Master Plumber (County, Prov)", "prov master plumber with gas": "Master Plumber with Gas (County, Prov)",
    "prov plumbing maintenance (county -)": "Plumbing Maintenance (County, Prov)",
    "prov journeyman plumber": "Journeyman Plumber", "prov master plumber": "Master Plumber",
    "master plumber & natural gas nascla contractor's guide to business, law and project management": "Master Plumber and Natural Gas",
    "master plumber & natural gas nascla": "Master Plumber and Natural Gas",
    "plumbing and heating contractor (c-1)": "Plumbing and Heating Contractor (C-1)",
    "journeyman plumber part 1 (written)": "Journeyman Plumber Part 1 (Written)",
    "master plumber part 1 (written)": "Master Plumber Part 1 (Written)",
    "plumbing (c-36) contractor licensing": "Plumbing Contractor (C-36)",
    "plumbing contractor trade": "Plumbing Contractor", "plumbing contractor + business & finance": "Plumbing Contractor",
    "introduction to becoming a plumbing contractor": "Plumbing Contractor",
    "the 2025 journeyman plumber": "Journeyman Plumber",
    "master plumber contractor": "Master Plumber",
    "cmc-a": "CMC-A Mechanical Plumbing", "llp": "Limited Licensed Plumber Contractor",
    "cmc-a mechanical plumbing (prov)": "CMC-A Mechanical Plumbing", "llp limited licensed plumber (prov)": "Limited Licensed Plumber Contractor",
    "prov journeyman plumber (county)": "Journeyman Plumber (County, Prov)", "prov master plumber (county)": "Master Plumber (County, Prov)",
    "prov plumbing maintenance (county)": "Plumbing Maintenance (County, Prov)",
}
ALIASES = {norm(k): v for k, v in ALIASES.items()}
# ICC national exams: code -> name (titles say G25N, G25-N, F24N...)
ICC = [("G28", "Journeyman Plumber with Gas (ICC G28-N)"), ("G27", "Master Plumber with Gas (ICC G27-N)"), ("G25", "Journeyman Plumber (ICC G25-N)"),
       ("G24", "Master Plumber (ICC G24-N)"), ("F28", "National Standard Journeyman Plumber with Gas (ICC F28-N)"), ("F27", "National Standard Master Plumber with Gas (ICC F27-N)"),
       ("F25", "National Standard Journeyman Plumber (ICC F25-N)"), ("F24", "National Standard Master Plumber (ICC F24-N)")]
ICC_INSP = [(r"\bP1\b", "Residential Plumbing Inspector (ICC P1)"), (r"\bP2\b", "Commercial Plumbing Inspector (ICC P2)"), (r"\bP3\b", "Plumbing Plans Examiner (ICC P3)")]
OTHER = ("plumbing-code-books", "Plumbing Code Books and References", "books")
STATE_CODE = {
    # which code each state's 2026 journeyman packages are written on, from the product titles ("Based on 2024 IPC|UPC")
}

def slugify(s): return re.sub(r"[^a-z0-9]+", "-", s.lower().replace("&", "and")).strip("-")
def region(title): return STATE

def find_state(t):
    if re.search(r"District of Columbia|Washington DC|Washington, DC", t): return "dc"
    for n, k in _BY_NAME:
        if re.search(r"\b%s\b" % re.escape(n), t):
            if n == "Kansas" and re.search(r"Kansas City", t) and "Missouri" in t: continue
            if n == "Virginia" and "West Virginia" in t: continue
            if n == "Washington" and re.search(r"Washington DC", t): continue
            return k
    return None

def license_of(t):
    """(group, license name) for a title, or None for references and code books."""
    g = find_state(t)
    s = re.sub(r"^20\d\d\s+", "", t.strip())
    s = re.sub(r"^The 1 Package:\s*All-Inclusive\s+", "", s)
    s = re.sub(r"^Introduction to Becoming an?\s+", "", s)
    s = s.replace("&amp;", "&")
    if g:
        name = STATE_NAME[g]
        s = re.sub(r"^(District of Columbia|Washington DC)\s+", "", s) if g == "dc" else s.replace(name, "", 1)
    s = re.sub(r"\s+", " ", s).strip(" -:")
    s = re.sub(r"\(([^)]*)\)", lambda m: "(" + re.sub(r"\s*-\s*", "-", m.group(1)).strip("- ") + ")", s)
    s = re.sub(r"^(CMC-A|LLP)\s+-\s+", r"\1 ", s)
    if g == "fl" and re.search(r"Building Code", s): return None
    if not g:
        if re.search(r"^ICC\b|\bICC\b", s):
            for rx, n in ICC_INSP:
                if re.search(rx, s): return ("icc", n)
            m = re.search(r"\b([FG]2[4578])", s)
            if m: return ("icc", dict(ICC)[m.group(1)])
        if re.search(r"Journeyman Plumber Exam Study Guide", t): return ("icc", "Journeyman Plumber (any state, 2024 UPC)")
        return None
    m = _CUT.search(" " + s)
    lic = (" " + s)[:m.start()].strip(" -:,") if m else s
    lic = re.sub(r"\s+", " ", lic).strip()
    lic = ALIASES.get(norm(lic), lic)
    if g == "ga" and re.search(r"NASCLA", t): lic = "Master Plumber (business and law guide)" if "Master" in t else "Business and Law (NASCLA)"
    if g == "la" and re.search(r"NASCLA", t): lic = "Master Plumber and Natural Gas"
    if lic.lower() in ("", "the 1 package"): return None
    return (g, lic)

def classify(title, ptype):
    li = license_of(title)
    if not li:
        cls = OTHER; grp = "books"
    else:
        grp, name = li
        prefix = STATE_NAME.get(grp, "icc")
        cls = ("%s-%s" % (slugify(prefix), slugify(name)), name, grp)
    typ = next(((s, n) for s, n, f in TYPES if f(title, ptype or "")), ("reference-book", "Reference Book"))
    if cls is OTHER and typ[0] not in ("tabs", "tutoring", "flash-cards"): typ = ("reference-book", "Reference Book")
    m = re.search(r"Based on (20\d\d) (IPC|UPC)|\[(20\d\d) (IPC|UPC)\]", title)
    code = (m.group(2) or m.group(4)) if m else ""
    year = (m.group(1) or m.group(3)) if m else ""
    return {"cls": cls[0], "clsName": cls[1], "group": cls[2], "type": typ[0], "typeName": typ[1], "rank": TYPE_RANK.get(typ[0], 99),
            "region": STATE, "year": year, "code": code}

def clean_title(t):
    t = t.replace("&amp;", "&")
    return re.sub(r"\s+", " ", t).strip()

def assign(products):
    """Give every product its license, package type and a short URL slug that is unique inside its license."""
    used, out = {}, []
    for p in sorted(products, key=lambda p: (p["title"], p["id"])):
        if SKIP.search(p["title"]) or float(p.get("price") or 0) <= 0: continue
        c = classify(p["title"], p.get("type", ""))
        base = c["type"] if c["cls"] != OTHER[0] else slugify(clean_title(p["title"]))[:60].rstrip("-")
        if c["type"] == "online-course" and re.search(r"Prov\b|\(Prov\)", p["title"]): base += "-prov"
        key = (c["cls"], base); n = used.get(key, 0) + 1; used[key] = n
        sl = base if n == 1 else "%s-%d" % (base, n)
        out.append(dict(p, **c, slug=sl, path="%s/%s/" % (c["cls"], sl), short=clean_title(p["title"])))
    return out

DISPLAY_ORDER = []
CLASSES = []  # filled by build.py from the catalog (license_of); kept for the shared code

if __name__ == "__main__":
    import sys, collections
    titles = [l for l in open(sys.argv[1]).read().splitlines() if l.strip()]
    ps = [{"id": str(i), "title": t, "price": "10", "variants": [{"id": "0", "price": "10"}]} for i, t in enumerate(titles)]
    got = assign(ps)
    by = collections.OrderedDict()
    for p in sorted(got, key=lambda p: (p["group"], p["clsName"])): by.setdefault((p["group"], p["clsName"]), []).append(p["typeName"])
    for (g, n), ts in by.items(): print("%-5s %-75s %2d  %s" % (g, n[:75], len(ts), ", ".join(sorted(set(ts)))[:120]))
    print("\nproducts %d, licenses %d, groups %d, skipped %d" % (len(got), len(by), len({g for g, _ in by}), len(ps) - len(got)))
