"""Canonical renderer capabilities shared by validation and rendering."""


LAYOUT_FAMILIES = {
    "matrix": {
        "academic-method-framework",
        "proposal-matrix-route",
        "cn-research-method-matrix",
        "cn-paper-framework-canvas",
    },
    "system": {
        "software-system-route",
        "engineering-architecture-route",
        "engineering-architecture",
        "cn-wide-project-map",
    },
    "campaign": {"campaign-strategy-map"},
    "mainline": {
        "cn-ppt-mainline-route",
        "ppt-mainline-route",
        "research-ppt-mainline",
    },
    "a4-stage": {"cn-a4-stage-route", "a4-stage-route"},
    "vertical": {
        "vertical-research-route",
        "proposal-phase-axis",
        "cn-proposal-poster-route",
        "cn-grant-application-route",
        "cn-monochrome-linework-route",
    },
    "horizontal": {
        "horizontal-stages",
        "campaign-funnel",
        "creative-production-pipeline",
        "layered-architecture",
        "timeline-swimlane",
        "wide-collaboration-map",
    },
}

SUPPORTED_LAYOUTS = frozenset(
    layout for layouts in LAYOUT_FAMILIES.values() for layout in layouts
)

SUPPORTED_STYLES = frozenset(
    {
        "academic-blue",
        "accessible-high-contrast",
        "advertising-clean-campaign",
        "blue-green-research",
        "cn-blue-green-proposal",
        "cn-defense-poster",
        "cn-polished-pastel-academic",
        "cn-reviewer-linework",
        "cn-soft-grant-report",
        "dark-technical",
        "defense-color",
        "editorial-clarity",
        "evidence-infographic",
        "grant-linework",
        "mechanism-snapshot",
        "minimal-gray",
        "monochrome-paper",
        "nature-editorial",
        "premium-scientific",
        "proposal-pastel-route",
        "research-ppt-blue",
        "schematic-precision",
        "soft-pastel",
        "wide-collaboration-map",
    }
)

STYLE_ALIASES = {
    "advertising-clean-campaign": "advertising-clean-campaign",
    "cn-grant-pastel": "cn-soft-grant-report",
    "cn-linework": "cn-reviewer-linework",
    "cn-thesis-pastel": "cn-polished-pastel-academic",
    "formal-research-ppt": "research-ppt-blue",
    "high-contrast-accessible": "accessible-high-contrast",
    "nature-style-editorial": "nature-editorial",
    "premium-scientific": "premium-scientific",
    "presentation-clean": "defense-color",
}


def canonical_style_name(name):
    return STYLE_ALIASES.get(name, name)


def layout_family(name):
    for family, layouts in LAYOUT_FAMILIES.items():
        if name in layouts:
            return family
    return None
