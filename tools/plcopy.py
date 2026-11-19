"""Copy for passyourplumbingexam.com: who licenses plumbers in each state and what the packages are.

build.py imports this as vacopy. Groups are states (codes from plclass.STATES) plus "icc" (ICC national exams) and
"books" (code books and references). Board names are the state agencies that license plumbers or plumbing contractors;
anything not confirmed is written as "check your candidate bulletin" rather than guessed. Checked 2026-11-19.

Things that came from the product titles rather than a board page (re-check when the store changes):
  - The 2026 journeyman study guides name their code: "Based on 2024 IPC" or "Based on 2024 UPC".
  - Exam vendors named in titles: Prov (Alabama, Florida counties, Tennessee), PSI (Maryland), ICC (city and inspector exams).
Things carried over from the other Pass Your sites (checked there):
  - Texas plumbing licenses come from the Texas State Board of Plumbing Examiners; exams by Pearson VUE (texas-site.md, Oct 28, 2026).
  - Nevada C-1 contractors are licensed by the Nevada State Contractors Board; journeyman cards are local (nevada-site.md, Nov 10, 2026).
"""

ICC_SRC = ("International Code Council: certification exams", "https://www.iccsafe.org/professional-development/certification/")
IPC_SRC = ("International Code Council: International Plumbing Code", "https://codes.iccsafe.org/")
UPC_SRC = ("IAPMO: Uniform Plumbing Code", "https://www.iapmo.org/")

def S(board, short, url, provider="", book="", facts=()):
    return dict(board=board, short=short, url=url, provider=provider, book=book, facts=list(facts))

LOCAL = "Plumbing is licensed locally here, so the city or county where you work sets the exam."
STATE = {
    "al": S("the Alabama Plumbers and Gas Fitters Examining Board", "AL Plumbers and Gas Fitters Board", "https://pgfb.alabama.gov/", "Prov", "",
            ["The Alabama Plumbers and Gas Fitters Examining Board certifies journeyman and master plumbers statewide.",
             "Prov gives several of the Alabama plumber exams, and Alabama also has a plumbing business and law exam."]),
    "ak": S("the Alaska Department of Labor and Workforce Development, Mechanical Inspection", "Alaska Mechanical Inspection", "https://labor.alaska.gov/", "", "",
            ["Alaska issues plumber certificates of fitness through its Department of Labor and Workforce Development.",
             "The 2026 Alaska journeyman packages are built on the 2024 Uniform Plumbing Code."]),
    "az": S("the Arizona Registrar of Contractors (ROC)", "Arizona ROC", "https://roc.az.gov/", "", "some",
            ["The Arizona Registrar of Contractors licenses plumbing contractors in commercial (C-37), dual (CR-37) and residential (R-37R) classes, plus solar plumbing classes.",
             "Arizona has no statewide journeyman plumber license; cities that license journeymen set their own exams.",
             "Exam-room book packages hold only the references the testing center lets you bring in."]),
    "ar": S("the Arkansas Department of Health, Plumbing and Natural Gas Section", "AR Dept. of Health", "https://www.healthy.arkansas.gov/", "", "",
            ["Arkansas licenses plumbers through the Department of Health, Plumbing and Natural Gas Section.",
             "The 2026 Arkansas journeyman packages are built on the 2024 International Plumbing Code."]),
    "ca": S("the Contractors State License Board (CSLB)", "CSLB", "https://www.cslb.ca.gov/", "", "",
            ["The CSLB licenses C-36 plumbing contractors; applicants take the Law and Business exam as well as the trade exam.",
             "California has no statewide journeyman plumber license, so the journeyman packages suit local and union exams built on the UPC."]),
    "co": S("the Colorado State Plumbing Board (Division of Professions and Occupations)", "CO State Plumbing Board", "https://dpo.colorado.gov/Plumbing", "", "",
            ["The Colorado State Plumbing Board licenses residential, journeyman and master plumbers statewide.",
             "Some cities, such as Commerce City, also license plumbers with ICC exams."]),
    "ct": S("the Connecticut Department of Consumer Protection, Occupational and Professional Licensing", "CT DCP", "https://portal.ct.gov/dcp", "", "",
            ["Connecticut licenses plumbing contractors and journeypersons through the Department of Consumer Protection.",
             "The 2026 Connecticut journeyman packages are built on the 2024 International Plumbing Code."]),
    "de": S("the Delaware Board of Plumbing, Heating, Ventilation, Air Conditioning and Refrigeration Examiners", "DE PHVACR Board",
            "https://dpr.delaware.gov/boards/plumbers/", "", "",
            ["Delaware licenses master and journeyman plumbers through one board that also covers HVACR.",
             "The 2026 Delaware journeyman packages are built on the 2024 International Plumbing Code."]),
    "dc": S("the DC Department of Licensing and Consumer Protection (DLCP)", "DC DLCP", "https://dlcp.dc.gov/", "", "",
            ["Washington DC licenses journeyman and master plumbers, with separate licenses that add gas fitting.",
             "Book packages come plain or highlighted and tabbed for the DC exams."]),
    "fl": S("the Florida Construction Industry Licensing Board (CILB)", "Florida CILB", "https://www2.myfloridalicense.com/construction-industry/", "Pearson VUE", "open",
            ["The Florida Construction Industry Licensing Board certifies plumbing contractors statewide; Pearson VUE gives the state trade exam.",
             "Florida journeyman and master plumber cards are issued by counties, which use Prov or GITS exams.",
             "Florida also certifies plumbing inspectors and plans examiners using ICC exams (1P, 2P and 3P)."]),
    "ga": S("the Georgia State Construction Industry Licensing Board, Division of Master Plumbers and Journeyman Plumbers", "GA Plumbers Division",
            "https://sos.ga.gov/state-construction-industry-licensing-board", "", "",
            ["Georgia licenses master plumbers in Class I (Restricted) and Class II (Unrestricted), plus journeyman plumbers.",
             "Georgia candidates also study the NASCLA business and law guide written for the Georgia board."]),
    "hi": S("the Hawaii Board of Electricity and Plumbing (DCCA)", "HI DCCA", "https://cca.hawaii.gov/pvl/", "", "",
            ["Hawaii licenses journeyman and master plumbers through the Board of Electricity and Plumbing; C-37 plumbing contractors go through the Contractors License Board.",
             "The 2026 Hawaii journeyman packages are built on the 2024 Uniform Plumbing Code."]),
    "id": S("the Idaho Division of Occupational and Professional Licenses (DOPL), Plumbing Board", "Idaho DOPL", "https://dopl.idaho.gov/", "", "",
            ["Idaho licenses journeyman, contractor and specialty plumbers through the Plumbing Board at DOPL.",
             "Specialty licenses cover narrower work, such as appliance or water pump installation, with their own exams."]),
    "il": S("the Illinois Department of Public Health (IDPH)", "Illinois IDPH", "https://dph.illinois.gov/", "", "",
            ["The Illinois Department of Public Health licenses plumbers statewide; Chicago licenses its own.",
             "The 2026 Illinois journeyman packages are built on the 2024 International Plumbing Code."]),
    "in": S("the Indiana Plumbing Commission (Professional Licensing Agency)", "Indiana Plumbing Commission", "https://www.in.gov/pla/", "", "",
            ["The Indiana Plumbing Commission licenses journeyman plumbers and plumbing contractors.",
             "The 2026 Indiana journeyman packages are built on the 2024 International Plumbing Code."]),
    "ia": S("the Iowa Plumbing and Mechanical Systems Board", "Iowa PMSB", "https://dial.iowa.gov/", "", "",
            ["The Iowa Plumbing and Mechanical Systems Board licenses journeyman and master plumbers, including licenses that add gas.",
             "The 2026 Iowa journeyman packages are built on the 2024 Uniform Plumbing Code."]),
    "ks": S("the city or county where you work", "Local license", "", "ICC", "",
            ["Kansas has no statewide plumber license; cities and counties license plumbers and many use ICC exams.",
             "Kansas prep comes in two exam versions, ICC 557/560 and KGF/KGR, so check which one your city uses before you order."]),
    "la": S("the State Plumbing Board of Louisiana", "LA State Plumbing Board", "https://spbla.com/", "", "",
            ["The State Plumbing Board of Louisiana licenses journeyman and master plumbers.",
             "Louisiana master plumber candidates study the NASCLA business and law guide written for the board."]),
    "ma": S("the Massachusetts Board of State Examiners of Plumbers and Gas Fitters", "MA Plumbing Board", "https://www.mass.gov/orgs/board-of-state-examiners-of-plumbers-and-gas-fitters", "", "",
            ["Massachusetts licenses journeyman and master plumbers; each exam has a written part and a practical part.",
             "The book packages here cover the written Part 1 exams."]),
    "md": S("the Maryland State Board of Plumbing (Maryland Department of Labor)", "MD Board of Plumbing", "https://www.labor.maryland.gov/", "PSI", "",
            ["The Maryland State Board of Plumbing licenses journeyman and master plumbers and gas fitters.",
             "PSI gives the Maryland plumbing and gas fitting exams, with content outlines for each."]),
    "mi": S("the Michigan State Plumbing Board (LARA, Bureau of Construction Codes)", "Michigan LARA", "https://www.michigan.gov/lara", "", "",
            ["Michigan licenses plumbers through the State Plumbing Board in the Bureau of Construction Codes.",
             "The 2026 Michigan journeyman packages are built on the 2024 International Plumbing Code."]),
    "mn": S("the Minnesota Department of Labor and Industry (DLI)", "Minnesota DLI", "https://www.dli.mn.gov/", "", "",
            ["The Minnesota Department of Labor and Industry licenses journeyworker and master plumbers.",
             "Minneapolis and St. Paul have their own licenses for gas work and plumbing contractors."]),
    "ms": S("the Mississippi State Board of Contractors", "MS Board of Contractors", "https://www.msboc.us/", "", "",
            ["The Mississippi State Board of Contractors licenses plumbing contractors, with a separate residential class.",
             LOCAL]),
    "mo": S("the city or county where you work", "Local license", "", "ICC", "",
            ["Missouri has no statewide plumber license; cities such as Springfield and Kansas City license plumbers.",
             "Springfield and Kansas City use ICC exams written for their codes."]),
    "mt": S("the Montana State Board of Plumbers", "MT Board of Plumbers", "https://dli.mt.gov/", "", "",
            ["The Montana State Board of Plumbers licenses journeyman and master plumbers.",
             "The 2026 Montana journeyman packages are built on the 2024 Uniform Plumbing Code."]),
    "ne": S("the city where you work", "Local license", "", "", "",
            ["Nebraska has no statewide plumber license; cities such as Omaha and Lincoln license plumbers.",
             "The 2026 Nebraska journeyman packages are built on the 2024 International Plumbing Code."]),
    "nv": S("the Nevada State Contractors Board (NSCB)", "Nevada NSCB", "https://www.nscb.nv.gov/", "PSI", "some",
            ["The Nevada State Contractors Board licenses C-1 plumbing and heating contractors; every applicant also takes the business and law exam.",
             "Nevada journeyman plumber cards are local; Reno and Clark County set their own exams."]),
    "nh": S("the New Hampshire Mechanical Licensing Board (OPLC)", "NH Mechanical Licensing Board", "https://www.oplc.nh.gov/", "", "",
            ["New Hampshire licenses journeyman and master plumbers through the Mechanical Licensing Board.",
             "The 2026 New Hampshire journeyman packages are built on the 2024 International Plumbing Code."]),
    "nm": S("the New Mexico Construction Industries Division (Regulation and Licensing Department)", "NM CID", "https://www.rld.nm.gov/", "PSI", "",
            ["The New Mexico Construction Industries Division licenses MM-1 plumbing contractors and certifies journeyman plumbers.",
             "New Mexico also certifies plumbing inspectors, with their own exam."]),
    "ny": S("the city where you work", "Local license", "https://www.nyc.gov/site/buildings/", "", "",
            ["New York has no statewide plumber license; New York City and other cities license master plumbers.",
             "Check your city's exam rules before you order."]),
    "nc": S("the North Carolina State Board of Examiners of Plumbing, Heating and Fire Sprinkler Contractors", "NC Plumbing Board", "https://nclicensing.org/", "", "",
            ["North Carolina licenses plumbing contractors in Class I and Class II, plus plumbing technicians and restricted limited and special restricted classes.",
             "Each North Carolina class has its own exam, and the SP-PH exam has exam-room book packages."]),
    "oh": S("the Ohio Construction Industry Licensing Board (OCILB)", "Ohio OCILB", "https://com.ohio.gov/", "", "",
            ["The Ohio Construction Industry Licensing Board licenses plumbing contractors; journeyman plumbers are licensed by some cities.",
             "Plumbing plans examiners in Ohio and Cleveland use the ICC P3 exam."]),
    "ok": S("the Oklahoma Construction Industries Board (CIB)", "Oklahoma CIB", "https://oklahoma.gov/cib.html", "PSI", "",
            ["The Oklahoma Construction Industries Board licenses plumbing and natural gas contractors and journeymen, including residential classes.",
             "PSI gives the Oklahoma plumbing exams, and contractors also take a plumbing business and law exam."]),
    "or": S("the Oregon Building Codes Division (BCD)", "Oregon BCD", "https://www.oregon.gov/bcd/", "", "",
            ["The Oregon Building Codes Division licenses journeyman plumbers.",
             "The 2026 Oregon journeyman packages are built on the 2024 Uniform Plumbing Code."]),
    "pa": S("the city where you work", "Local license", "", "ICC", "",
            ["Pennsylvania has no statewide plumber license; cities such as Reading license plumbers with ICC exams.",
             "The 2026 Pennsylvania journeyman packages are built on the 2024 International Plumbing Code."]),
    "ri": S("the Rhode Island Department of Labor and Training, Professional Regulation", "RI DLT", "https://dlt.ri.gov/", "", "",
            ["Rhode Island licenses journeyman and master plumbers through the Department of Labor and Training.",
             "The 2026 Rhode Island journeyman packages are built on the 2024 International Plumbing Code."]),
    "sc": S("the South Carolina Contractor's Licensing Board and Residential Builders Commission (LLR)", "SC LLR", "https://llr.sc.gov/", "", "",
            ["South Carolina licenses commercial plumbing contractors through the Contractor's Licensing Board and residential plumbers through the Residential Builders Commission.",
             "Both boards sit within the Department of Labor, Licensing and Regulation."]),
    "sd": S("the South Dakota State Plumbing Commission", "SD Plumbing Commission", "https://dlr.sd.gov/", "", "",
            ["The South Dakota State Plumbing Commission licenses journeyman and master plumbers.",
             "The 2026 South Dakota journeyman packages are built on the 2024 Uniform Plumbing Code."]),
    "tn": S("the Tennessee Board for Licensing Contractors", "TN Board for Licensing Contractors", "https://www.tn.gov/commerce/regboards/contractors.html", "Prov", "",
            ["The Tennessee Board for Licensing Contractors licenses CMC-A mechanical plumbing contractors and limited licensed plumbers (LLP).",
             "Prov gives the Tennessee contractor exams; journeyman plumbers are licensed by some cities."]),
    "tx": S("the Texas State Board of Plumbing Examiners (TSBPE)", "TSBPE", "https://tsbpe.texas.gov/", "Pearson VUE", "",
            ["Texas plumbing licenses come from the Texas State Board of Plumbing Examiners; Pearson VUE gives the written exams.",
             "Texas licenses tradesman limited, journeyman and master plumbers, plus plumbing inspectors."]),
    "ut": S("the Utah Division of Professional Licensing (DOPL)", "Utah DOPL", "https://dopl.utah.gov/", "", "",
            ["Utah DOPL licenses journeyman, residential journeyman and master plumbers, and master plumbers take a law and rule exam.",
             "Utah apprentices can test out of training levels 1A to 2B with their own exams."]),
    "vt": S("the Vermont Division of Fire Safety", "VT Fire Safety", "https://firesafety.vermont.gov/", "", "",
            ["Vermont licenses journeyman and master plumbers through the Division of Fire Safety.",
             "The 2026 Vermont journeyman packages are built on the 2024 International Plumbing Code."]),
    "va": S("the Virginia Board for Contractors (DPOR)", "Virginia DPOR", "https://www.dpor.virginia.gov/", "PSI", "",
            ["Virginia licenses journeyman, master and residential plumbing tradesmen through DPOR; PSI gives the exams.",
             "Virginia also certifies plumbing inspectors and plans examiners using ICC P1, P2 and P3 exams."]),
    "wa": S("the Washington Department of Labor and Industries (L&I)", "Washington L&I", "https://lni.wa.gov/", "", "",
            ["Washington L&I certifies journeyman and specialty plumbers, such as domestic pump and irrigation plumbers.",
             "The 2026 Washington journeyman packages are built on the 2024 Uniform Plumbing Code."]),
    "wv": S("the West Virginia State Fire Marshal", "WV State Fire Marshal", "https://firemarshal.wv.gov/", "", "",
            ["The West Virginia State Fire Marshal licenses plumbers; plumbing contractors also hold a West Virginia contractor license.",
             "West Virginia also certifies plumbing inspectors and plans examiners using ICC P1, P2 and P3 exams."]),
    "wi": S("the Wisconsin Department of Safety and Professional Services (DSPS)", "Wisconsin DSPS", "https://dsps.wi.gov/", "", "",
            ["Wisconsin DSPS licenses journeyman and master plumbers.",
             "The 2026 Wisconsin journeyman packages are built on the 2024 Uniform Plumbing Code."]),
    "wy": S("the city where you work", "Local license", "", "ICC", "",
            ["Wyoming has no statewide plumber license; cities such as Casper license plumbers with ICC exams.",
             "Check with your city for the exam it uses before you order."]),
    "icc": S("the International Code Council (ICC), for the city or state that accepts the exam", "ICC", "https://www.iccsafe.org/", "Pearson VUE", "open",
             ["ICC national standard plumber exams (G24, G25, G27, G28 and the F series) are used by many cities and counties that license plumbers.",
              "ICC inspector and plans examiner certifications (P1, P2, P3) are open book on the code editions listed in the exam bulletin."]),
    "books": S("the board for the license you are testing for", "Depends on the license", "", "", "",
               ["These code books and references show up on many plumbing exam reference lists.",
                "Check the candidate bulletin for your exam to see which editions it allows."]),
}
def _src(g):
    s = STATE[g]; out = []
    if s["url"]: out.append(((s["short"] if s["short"] != "Local license" else "Licensing office") + " (official site)", s["url"]))
    if g in ("icc", "ks", "mo", "pa", "wy"): out.append(ICC_SRC)
    out.append(IPC_SRC if g not in ("ak", "az", "ca", "hi", "ia", "mt", "nm", "or", "sd", "wa", "wi") else UPC_SRC)
    return out
SOURCES = {g: _src(g) for g in STATE}
MAIN_SOURCES = [IPC_SRC, UPC_SRC, ICC_SRC]

SCOPE = {}
CLASS_FACTS = {}
OFFICIAL_SCOPE = "{name} exam prep."

def _how(g):
    s = STATE[g]
    p = (" %s gives the exam." % s["provider"]) if s["provider"] else ""
    return "The {name} license comes from " + s["board"] + "." + p + " The board approves your application first; then you schedule the exam and bring only the references the candidate bulletin allows."
GROUP_HOW = {g: _how(g) for g in STATE}
GROUP_FACTS = {g: STATE[g]["facts"] for g in STATE}
def _open(g):
    b = STATE[g]["book"]
    if b == "open": return "Yes, for most exams here. The trade exam allows the references listed in the candidate bulletin, so highlighted and tabbed books save the most time."
    if b == "some": return "Several exams here let you bring approved books, which is why exam-room book packages are offered. Your candidate bulletin lists the books allowed for your exam."
    return "It depends on the exam. Many plumbing trade exams allow the code book, but some are closed book. Your candidate bulletin lists the references allowed; if books are allowed, highlighted and tabbed sets save the most time."
OPEN_BOOK = {g: _open(g) for g in STATE}
WHO_ISSUES = {g: STATE[g]["board"] for g in STATE}
ISSUER_SHORT = {g: STATE[g]["short"] + ((", exams by %s" % STATE[g]["provider"]) if STATE[g]["provider"] else "") for g in STATE}
BOOK_SHORT = {g: {"open": "Open book", "some": "Approved books for several exams"}.get(STATE[g]["book"], "See the candidate bulletin") for g in STATE}
GROUP_FAQ = {g: [("Does the {name} exam use the IPC or the UPC?", "Each package names its code in the title. The 2026 journeyman study guides say \"Based on 2024 IPC\" or \"Based on 2024 UPC\"; book packages list the exact editions. Match it to the editions in your candidate bulletin."),
                 ("How long does the {name} prep take to arrive?", "Online courses and practice questions arrive by email after purchase. Book packages ship free by USPS Media Mail; allow up to 15 business days for rental, Ultimate and 1 Package orders.")] for g in STATE}

TYPE_BLURB = {
    "study-guide": "the 2026 state study guide on your exam's code",
    "study-guide-course": "the 2026 study guide plus the online course",
    "complete-books-tabs-course": "code books with tabs placed, study guide and course",
    "exam-prep-2021": "the exam prep package written to the 2021 IPC",
    "ultimate-2021": "the Ultimate package written to the 2021 IPC",
    "tabs": "pre-printed tabs for the reference books",
    "tabs-highlights": "pre-printed tabs plus highlighting guides for the reference books",
    "content-outline": "the books listed in the exam content outline",
    "flash-cards": "study flash cards for quick review",
    "flash-combo": "flash cards for the trade exam and the business and finance exam",
    "online-practice-exams": "online practice questions with explanations",
    "intro-course": "an introduction to becoming a plumbing contractor",
    "online-course": "a self-study online course built around the exam",
    "live-training": "live virtual classes with an instructor plus the self-study course",
    "refresher-class": "a two-day class on using the books in the exam",
    "exam-room-books": "only the books the testing center lets you bring in",
    "exam-room-highlighted": "the exam-room books, already highlighted and tabbed",
    "book-package": "every reference book the exam is written to, new and unmarked",
    "reference-book": "a code book or reference used on plumbing licensing exams",
    "highlighted-tabbed": "the reference books already highlighted and tabbed",
    "rental-exam-room": "the exam-room books on rental plus the online course",
    "rental-package": "rental books plus the online course",
    "tutoring": "private one-on-one tutoring with a plumbing exam instructor",
    "ultimate-exam-room": "exam-room books, the course and application help",
    "ultimate-rental": "tabbed rental books, a year of the course and application help",
    "the-1-package": "the Ultimate package plus LLC setup, EIN filing and compliance help",
    "other": "exam prep",
}

HOME_H1 = "Know the code cold. Pass your plumbing exam the first time."
HOME_TITLE = "Plumbing Exam Prep by State | Pass Your Plumbing Exam"
HOME_DESC = "Plumbing exam prep for {n} licenses in {s} states and DC: 2026 study guides on the 2024 IPC or UPC, tabbed code books, courses and ICC exam prep."
HOME_LEAD = ("Pass Your Plumbing Exam has prep for {n} plumber, plumbing contractor and inspector licenses. Pick your state to see who licenses plumbers and which code "
             "the exam uses, then compare study guides, tabbed code books and courses, from {lo} to The 1 Package, with one-click checkout.")
HOME_SEARCH_PLACEHOLDER = "Try Texas journeyman, Arizona C-37 or ICC G25"
LICENSES_COVERED = "plumbing licenses covered"
HOME_TAKEAWAYS = [
    "Every state exam is written on one plumbing code, the International Plumbing Code (IPC) or the Uniform Plumbing Code (UPC); each package names its code.",
    "The 2026 journeyman study guide is $59.99, the guide plus online course $119.99 and the complete books, tabs and course package $344.99 in each state.",
    "Some states, such as Kansas, Missouri, Pennsylvania and Wyoming, leave plumber licensing to cities, which often use ICC exams.",
]
HOME_FAQ = [
    ("Which plumbing license do I need?", "Your state and the work you do decide that. Most states license journeyman and master plumbers, and many also license plumbing contractors. Each state page names the board and lists every license we have prep for."),
    ("Does my plumbing exam use the IPC or the UPC?", "Your state or city adopts one of them. Every package on this site names its code in the title, such as \"Based on 2024 IPC\" or \"Based on 2024 UPC\", so match it to the editions in your candidate bulletin."),
    ("Is the plumbing exam open book?", "It depends on the exam. Florida contractor and ICC inspector exams allow the listed references, for example, while some journeyman exams are closed book. Your candidate bulletin lists what you can bring."),
    ("What is in the 2026 journeyman packages?", "The study guide is $59.99. The guide plus online course is $119.99. The complete package at $344.99 adds the code books with tabs already placed."),
    ("What do the Ultimate Package and The 1 Package include?", "The Ultimate Package bundles highlighted and tabbed rental books, a year of online course access and help with your license application. The 1 Package adds LLC or corporation setup, EIN filing and compliance guidance."),
    ("Are these the real exam questions?", "No. Licensing exam questions are confidential. The courses and practice questions are original material written to the same subjects and format, with explanations."),
    ("Does buying a package register me for the exam?", "No. Your state board or city approves your application first, then the testing provider schedules the exam. A package gets you ready for the test itself."),
    ("How do orders arrive?", "Books ship free from our fulfillment center, {ful}, by USPS Media Mail. Online courses and practice questions arrive by email after purchase. Allow up to 15 business days for rental, Ultimate and 1 Package orders."),
]
GENERAL_FAQ_LEAD = "Here are {n} answers about plumbing license exams: who licenses plumbers, the IPC and the UPC, open-book rules, ICC exams, package types, rentals, shipping and ordering. Each of the {k} license pages and every state page adds questions of its own, so check yours too."
FAQ_TAKEAWAYS = [
    "Each state, and in some places each city, sets its own plumbing exam; the state page tells you who issues your license.",
    "Every package names the plumbing code it is built on, the IPC or the UPC.",
    "Rental, Ultimate and 1 Package prices include a refundable book deposit.",
]
BLOG_FAQ = [
    ("How long should I study for a plumbing license exam?", "Most candidates plan six to eight weeks at about an hour a day: learning the code layout, practicing sizing and fixture unit questions, and taking timed practice exams."),
    ("Is the plumbing exam open book?", "Some are. Florida contractor and ICC inspector exams allow the listed references; some journeyman exams are closed book. Your candidate bulletin decides."),
    ("IPC or UPC?", "Your exam uses the code your state or city adopted. Every package here names its code."),
    ("Are the practice questions the real exam questions?", "No. Licensing exam questions are confidential. Our courses and practice questions are original material written to the same subjects."),
    ("Does buying a package register me for the exam?", "No. Your board approves you first, then the testing provider schedules the exam."),
    ("How do orders arrive?", "Books ship from our fulfillment center, {ful}; online courses arrive by email after purchase."),
]
FAQ_GROUP_INTRO = {}
LLM_SUMMARY = "Exam prep for {n} plumber, plumbing contractor and plumbing inspector licenses in {s} states and Washington DC, plus ICC national plumbing exams and plumbing code books."
LLM_FACTS = [
    "- Every state, and in some places each city, licenses plumbers separately; each state page names the board and the exam provider where known.",
    "- Each package names its plumbing code: the International Plumbing Code (IPC) or the Uniform Plumbing Code (UPC).",
    "- 2026 journeyman packages in each state: Study Guide $59.99, Study Guide & Online Course $119.99, Complete Books, Tabs & Course $344.99.",
    "- Kansas, Missouri, Nebraska, New York, Pennsylvania and Wyoming have no statewide plumber license; cities license plumbers, often with ICC exams.",
    "- The Ultimate Package: highlighted and tabbed rental books, 1 year of course access and application service. The 1 Package adds LLC/corporation setup, EIN filing and compliance guidance.",
    "- Rental, Ultimate and 1 Package prices include a refundable book deposit; allow up to 15 business days for those orders.",
]
BLOG_LEAD = "This blog has study plans, state licensing rules and exam strategy for plumbing license exams, written for people who work full days and study at night. Each post links to the state and license it covers, and every rule we quote links to the board that sets it."
PROMO = "Free shipping on every book package. Online courses start the day you buy."
COLLAGE = []
MAX_ALIASES = {}
