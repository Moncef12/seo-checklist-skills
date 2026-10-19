"""
schema_rules.py - JSON-LD checks for checklist item T13 (add schema, test in Rich Results).

Valid JSON isn't enough: Google only shows a rich result when the properties it requires for
that type are present. This module walks every JSON-LD block (including @graph and nested
objects), applies the rules below and returns seo_check-style findings.

The rules follow Google Search Central's structured data documentation for each feature:
"required" properties block the rich result when missing (WARN); "recommended" ones only
weaken it (INFO). It is a fast first pass, not a replacement for the Rich Results Test.

Standard library only. This file is maintained in shared/ and copied into skills by `make sync`.
"""
import json
import re

ARTICLE = {"recommended": ["headline", "image", "datePublished", "author"]}
RULES = {
    "Article": ARTICLE, "NewsArticle": ARTICLE, "BlogPosting": ARTICLE, "TechArticle": ARTICLE,
    "Product": {"required": ["name"], "one_of": [["offers", "review", "aggregateRating"]],
                "recommended": ["image", "description", "brand"]},
    "Offer": {"one_of": [["price", "priceSpecification"]], "recommended": ["priceCurrency", "availability"]},
    "AggregateOffer": {"required": ["lowPrice", "priceCurrency"]},
    "AggregateRating": {"required": ["ratingValue"], "one_of": [["ratingCount", "reviewCount"]]},
    "Review": {"required": ["author"], "recommended": ["reviewRating"]},
    "BreadcrumbList": {"required": ["itemListElement"]},
    "FAQPage": {"required": ["mainEntity"]},
    "Question": {"required": ["name", "acceptedAnswer"]},
    "Organization": {"recommended": ["name", "url", "logo"]},
    "LocalBusiness": {"required": ["name", "address"], "recommended": ["telephone", "openingHoursSpecification",
                                                                        "url", "geo"]},
    "Event": {"required": ["name", "startDate", "location"], "recommended": ["endDate", "image", "offers"]},
    "VideoObject": {"required": ["name", "thumbnailUrl", "uploadDate"],
                    "recommended": ["description", "duration", "contentUrl"]},
    "Recipe": {"required": ["name", "image"], "recommended": ["recipeIngredient", "recipeInstructions"]},
    "JobPosting": {"required": ["title", "description", "datePosted", "hiringOrganization"]},
    "SoftwareApplication": {"required": ["name", "offers"], "one_of": [["aggregateRating", "review"]]},
    "Course": {"required": ["name", "description"], "recommended": ["provider"]},
    "Person": {"recommended": ["name"]},
}
for _t in ("MobileApplication", "WebApplication", "VideoGame"):
    RULES[_t] = RULES["SoftwareApplication"]
LOCAL_SUBTYPES = {
    "Restaurant", "Store", "Dentist", "MedicalBusiness", "MedicalClinic", "Physician", "AutoRepair",
    "AutomotiveBusiness", "ProfessionalService", "HomeAndConstructionBusiness", "LegalService", "Attorney",
    "FinancialService", "RealEstateAgent", "HealthAndBeautyBusiness", "BeautySalon", "HairSalon", "DaySpa",
    "FoodEstablishment", "CafeOrCoffeeShop", "Bakery", "BarOrPub", "LodgingBusiness", "Hotel",
    "SportsActivityLocation", "ExerciseGym", "EntertainmentBusiness", "ChildCare", "Plumber", "Electrician",
    "HVACBusiness", "Locksmith", "RoofingContractor", "GeneralContractor", "MovingCompany", "TravelAgency",
}
DATE_PROPS = ("datePublished", "dateModified", "uploadDate", "startDate", "endDate", "datePosted", "validThrough")
URL_PROPS = ("url", "logo", "image", "thumbnailUrl", "contentUrl", "item")
_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}([T ]\d{2}:\d{2}(:\d{2}(\.\d+)?)?(Z|[+-]\d{2}:?\d{2})?)?$")


def _types(node):
    t = node.get("@type")
    return [str(x).split("/")[-1] for x in (t if isinstance(t, list) else [t]) if x]


def _present(v):
    if v is None:
        return False
    if isinstance(v, str):
        return bool(v.strip())
    if isinstance(v, (list, dict)):
        return bool(v)
    return True


def _rule_for(t):
    if t in RULES:
        return t, RULES[t]
    if t in LOCAL_SUBTYPES or (t.endswith("Business") and t != "OnlineBusiness"):
        return "LocalBusiness", RULES["LocalBusiness"]
    return t, None


def iter_nodes(data, top=True):
    """Yield (node, is_top_level) for every dict with an @type, descending into @graph and values."""
    if isinstance(data, list):
        for x in data:
            yield from iter_nodes(x, top)
    elif isinstance(data, dict):
        if _types(data):
            yield data, top
        for k, v in data.items():
            if k == "@graph":
                yield from iter_nodes(v, True)
            elif isinstance(v, (dict, list)):
                yield from iter_nodes(v, False)


def _label(node, t):
    name = node.get("name") or node.get("headline") or node.get("title")
    return f"{t} \"{str(name)[:40]}\"" if isinstance(name, str) and name.strip() else t


def _breadcrumb_items(node):
    items = node.get("itemListElement")
    items = items if isinstance(items, list) else [items] if isinstance(items, dict) else []
    problems = []
    for i, it in enumerate(items, 1):
        if not isinstance(it, dict):
            problems.append(f"item {i} is not an object")
            continue
        missing = [p for p in ("position", "name") if not _present(it.get(p))
                   and not (p == "name" and isinstance(it.get("item"), dict) and _present(it["item"].get("name")))]
        if i < len(items) and not _present(it.get("item")):
            missing.append("item (URL)")
        if missing:
            problems.append(f"item {i} is missing {', '.join(missing)}")
    return problems


def _faq_questions(node):
    qs = node.get("mainEntity")
    qs = qs if isinstance(qs, list) else [qs] if isinstance(qs, dict) else []
    bad = 0
    for q in qs:
        ans = q.get("acceptedAnswer") if isinstance(q, dict) else None
        ans = ans[0] if isinstance(ans, list) and ans else ans
        named = isinstance(q, dict) and _present(q.get("name"))
        if not (named and isinstance(ans, dict) and _present(ans.get("text"))):
            bad += 1
    return len(qs), bad


def check_node(node, top):
    """Findings for one typed node."""
    f = []
    for t in _types(node):
        rule_name, rule = _rule_for(t)
        label = _label(node, t)
        if t == "HowTo":
            f.append(("INFO", "schema-tip", "HowTo rich results were retired by Google in 2023 - the markup is "
                                        "harmless but no longer shows in results"))
        if t == "WebSite" and "potentialAction" in node:
            f.append(("INFO", "schema-tip", "WebSite SearchAction: Google retired the sitelinks search box in "
                                        "November 2024, so this markup is no longer used"))
        if not rule:
            continue
        nested_ok = {"Offer", "AggregateOffer", "AggregateRating", "Review", "Question", "Person", "Organization"}
        if not top and rule_name in nested_ok:
            # nested inside another item: judged as part of the parent, only obvious gaps matter
            rule = {k: v for k, v in rule.items() if k != "recommended"}
            if rule_name in ("Review", "Person", "Organization"):
                rule = {}
        missing = [p for p in rule.get("required", []) if not _present(node.get(p))]
        for group in rule.get("one_of", []):
            if not any(_present(node.get(p)) for p in group):
                missing.append(" or ".join(group))
        if missing:
            f.append(("WARN", "schema", f"{label} is missing required {', '.join(missing)} - not eligible for "
                                        "its rich result"))
        rec = [p for p in rule.get("recommended", []) if not _present(node.get(p))]
        if rec and top:
            f.append(("INFO", "schema-tip", f"{label} could add recommended {', '.join(rec)}"))
        if rule_name == "BreadcrumbList" and _present(node.get("itemListElement")):
            problems = _breadcrumb_items(node)
            if problems:
                f.append(("WARN", "schema", "BreadcrumbList " + "; ".join(problems[:4])))
        if rule_name == "FAQPage":
            n, bad = _faq_questions(node)
            if bad:
                f.append(("WARN", "schema", f"FAQPage: {bad}/{n} questions lack a name or acceptedAnswer.text"))
            f.append(("INFO", "schema-tip", "FAQ rich results only show for well-known government and health sites "
                                        "since August 2023. Keep the markup if it's accurate, but don't expect "
                                        "the dropdowns"))
    for p in DATE_PROPS:
        v = node.get(p)
        if isinstance(v, str) and v.strip() and not _ISO.match(v.strip()):
            f.append(("WARN", "schema", f"{_types(node)[0]}.{p} \"{v[:30]}\" is not an ISO 8601 date"))
    for p in URL_PROPS:
        v = node.get(p)
        if isinstance(v, str) and v.strip().startswith("/"):
            f.append(("INFO", "schema-tip", f"{_types(node)[0]}.{p} is a relative URL (\"{v[:40]}\") - "
                                        "use an absolute URL"))
    return f


def check_blocks(raw_blocks):
    """Findings for all JSON-LD blocks of a page (invalid JSON is reported by seo_check itself)."""
    f = []
    for raw in raw_blocks:
        try:
            data = json.loads(raw)
        except Exception:
            continue
        tops = data if isinstance(data, list) else [data]
        for obj in tops:
            if isinstance(obj, dict) and "schema.org" not in json.dumps(obj.get("@context", "")):
                f.append(("WARN", "schema", "JSON-LD block has no schema.org @context - Google ignores it"))
        for node, top in iter_nodes(data):
            f.extend(check_node(node, top))
    seen, out = set(), []
    for x in f:  # the same message from repeated nodes only once
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out
