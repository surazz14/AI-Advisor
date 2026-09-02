"""Official source document → citation title + main URL.

Keep this as the single place to add or fix citation links.
Keys must match `source_document` values stored in Supabase / CSVs.
"""

from __future__ import annotations

SOURCE_CITATIONS: dict[str, dict[str, str]] = {
    "R-Codes-Vol1-2026": {
        "title": "Residential Design Codes Volume 1",
        "url": "https://www.wa.gov.au/government/document-collections/residential-design-codes",
    },
    "LPS5": {
        "title": "Local Planning Scheme No. 5 (Shire of Plantagenet)",
        "url": "https://www.plantagenet.wa.gov.au/develop-build/town-planning/framework.aspx",
    },
    "LPP3": {
        "title": "Local Planning Policy No. 3 – Outbuildings & Shipping Containers",
        "url": "https://www.plantagenet.wa.gov.au/documents/1135/local-planning-policy-3-outbuildings-and-shipping-containers",
    },
    "LPP5": {
        "title": "Local Planning Policy No. 5 – Exemptions from Development Approval",
        "url": "https://www.plantagenet.wa.gov.au/documents/1060/local-planning-policy-5-exemptions-from-development-approval",
    },
    "TPS3-POL20": {
        "title": "TPS Policy No. 20 – Porongurup Rural Village",
        "url": "https://www.plantagenet.wa.gov.au/develop-build/town-planning/framework.aspx",
    },
    "POL5-RELOC": {
        "title": "Local policy – Relocated / transportable dwellings",
        "url": "https://www.plantagenet.wa.gov.au/develop-build/town-planning/framework.aspx",
    },
    "LPP-Fencing": {
        "title": "Local fencing guidance (Shire of Plantagenet)",
        "url": "https://www.plantagenet.wa.gov.au/develop-build/building/building-approvals.aspx",
    },
    "mixed-fencing": {
        "title": "Fencing rules (WA / Plantagenet)",
        "url": "https://www.plantagenet.wa.gov.au/develop-build/building/building-approvals.aspx",
    },
    "Dividing Fences Act 1961": {
        "title": "Dividing Fences Act 1961 (WA)",
        "url": "https://www.legislation.wa.gov.au/legislation/statutes.nsf/main_mrtitle_302_homepage.html",
    },
    "Building Regulations 2012 (WA)": {
        "title": "Building Regulations 2012 (WA) — pool barriers",
        "url": "https://www.wa.gov.au/organisation/department-of-energy-mines-industry-regulation-and-safety/building-and-energy/swimming-pool-and-spa-safety",
    },
    "AS 1926.1-2012 (via Building Regulations 2012)": {
        "title": "AS 1926.1 — swimming pool safety barriers",
        "url": "https://www.wa.gov.au/organisation/department-of-energy-mines-industry-regulation-and-safety/building-and-energy/swimming-pool-and-spa-safety",
    },
    "Shire of Plantagenet (confirmed gap)": {
        "title": "Shire of Plantagenet — fencing (no standalone LPP)",
        "url": "https://ablis.business.gov.au/service/wa/permission-to-erect-or-alter-a-fence-private-property-shire-of-plantagenet/18422",
    },
    "Shire of Plantagenet (ABLIS registry)": {
        "title": "Shire of Plantagenet — fence / building process",
        "url": "https://ablis.business.gov.au/service/wa/permission-to-erect-or-alter-a-fence-private-property-shire-of-plantagenet/18422",
    },
    "WA Dept. of Consumer Protection": {
        "title": "WA Consumer Protection — dividing fences guidance",
        "url": "https://www.commerce.wa.gov.au/consumer-protection/dividing-fences",
    },
    "SPP3.7_Guidelines": {
        "title": "State Planning Policy 3.7 Bushfire & Planning for Bushfire Guidelines",
        "url": "https://www.planning.wa.gov.au/state-planning-policy-3.7-bushfire",
    },
    "Bushfire-Guidance": {
        "title": "Bushfire planning guidance (WA)",
        "url": "https://www.wa.gov.au/organisation/department-of-planning-lands-and-heritage/bushfire",
    },
    # Fallback labels for mixed uploads (current_policy_rules uses specific keys above)
    "mixed-current": {
        "title": "Shire of Plantagenet local planning policies",
        "url": "https://www.plantagenet.wa.gov.au/develop-build/town-planning/framework.aspx",
    },
}


def citation_for_source(source_document: str | None) -> dict[str, str]:
    """Return {title, url} for a source_document key."""
    key = (source_document or "").strip()
    if key in SOURCE_CITATIONS:
        return dict(SOURCE_CITATIONS[key])
    return {
        "title": key or "Planning policy",
        "url": "https://www.plantagenet.wa.gov.au/develop-build/town-planning/framework.aspx",
    }
