"""
Springfield Properties – SEO, AEO & GEO Audit Dashboard
Prepared by Ali Naseh · Audit date: 28 October 2026

All findings come from the audit report and the website errors spreadsheet,
stored in /data so they can be edited without touching this code.
Nothing here is estimated: metrics that need company access are shown as unavailable.
"""
from __future__ import annotations

import io
import json
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ─────────────────────────────── Setup ───────────────────────────────
st.set_page_config(
    page_title="Springfield Properties · Search Audit",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

DATA = Path(__file__).parent / "data"
SITE = "https://springfieldproperties.ae"

NAVY = "#0A1428"
PANEL = "#101D36"
PANEL_2 = "#15264A"
LINE = "#22355C"
TEXT = "#F4F7FB"
MUTED = "#9AA8C3"
NEON = "#39FF88"
PRIORITY_COLORS = {"Critical": "#FF5C7A", "High": "#FFAE42", "Medium": "#F2D35B", "Low": "#5CC8FF"}
PRIORITY_ORDER = ["Critical", "High", "Medium", "Low"]
STATUS_OPTIONS = ["Open", "In progress", "Fixed", "Won't fix"]
OWNER_LABEL = {
    "Independent": "I can implement",
    "Developer": "Needs developer support",
    "Company access": "Needs company access / sign-off",
}


@st.cache_data
def load_json(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


@st.cache_data
def load_csv(name: str) -> pd.DataFrame:
    return pd.read_csv(DATA / name)


findings_raw = load_json("findings.json")
roadmap = load_json("roadmap.json")
kpis = load_json("kpis.json")
errors_df = load_csv("website_errors.csv")
brand_df = load_csv("brand_variants.csv")
placeholder_df = load_csv("placeholder_titles.csv")
cutoff_df = load_csv("cutoff_descriptions.csv")

# Session state keeps status edits while the app is open (export to save them).
if "status" not in st.session_state:
    st.session_state.status = {f["id"]: f.get("status", "Open") for f in findings_raw}


def findings_df() -> pd.DataFrame:
    df = pd.DataFrame(findings_raw)
    df["status"] = df["id"].map(st.session_state.status)
    df["priority"] = pd.Categorical(df["priority"], PRIORITY_ORDER, ordered=True)
    df["urls_text"] = df["urls"].apply(lambda u: "\n".join(u))
    df["first_url"] = df["urls"].apply(lambda u: u[0] if u else "")
    return df.sort_values(["priority", "id"]).reset_index(drop=True)


# ─────────────────────────────── Styling ───────────────────────────────
st.markdown(
    f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:wght@600&display=swap');
html, body, [class*="css"], .stApp {{ font-family: 'Inter', sans-serif; }}
.stApp {{ background: radial-gradient(1200px 600px at 85% -10%, rgba(57,255,136,0.07), transparent 60%), {NAVY}; color: {TEXT}; }}
.block-container {{ padding-top: 1.6rem; padding-bottom: 3rem; max-width: 1400px; }}
h1, h2, h3, h4 {{ color: {TEXT}; letter-spacing: -0.01em; }}
p, li, label, .stMarkdown {{ color: {TEXT}; }}
a {{ color: {NEON} !important; text-decoration: none; }}
a:hover {{ text-decoration: underline; }}

.hero {{ border: 1px solid {LINE}; border-radius: 18px; padding: 28px 32px; margin-bottom: 18px;
         background: linear-gradient(135deg, {PANEL_2} 0%, {PANEL} 55%, {NAVY} 100%); position: relative; overflow: hidden; }}
.hero:after {{ content: ""; position: absolute; right: -60px; top: -60px; width: 260px; height: 260px; border-radius: 50%;
              background: radial-gradient(circle, rgba(57,255,136,0.18), transparent 70%); }}
.hero .eyebrow {{ color: {NEON}; font-size: 12px; font-weight: 600; letter-spacing: .16em; text-transform: uppercase; }}
.hero h1 {{ font-family: 'Playfair Display', serif; font-size: 38px; margin: 6px 0 6px; line-height: 1.15; }}
.hero p {{ color: {MUTED}; margin: 0; font-size: 15px; max-width: 900px; }}
.chips {{ margin-top: 14px; display: flex; flex-wrap: wrap; gap: 8px; }}
.chip {{ border: 1px solid {LINE}; background: rgba(255,255,255,0.03); color: {TEXT}; border-radius: 999px; padding: 4px 12px; font-size: 12.5px; }}
.chip b {{ color: {NEON}; font-weight: 600; }}

.card {{ background: {PANEL}; border: 1px solid {LINE}; border-radius: 14px; padding: 16px 18px; height: 100%; }}
.card .label {{ color: {MUTED}; font-size: 12.5px; text-transform: uppercase; letter-spacing: .08em; }}
.card .value {{ font-size: 32px; font-weight: 700; color: {TEXT}; margin-top: 2px; line-height: 1.1; }}
.card .sub {{ color: {MUTED}; font-size: 12.5px; margin-top: 4px; }}
.card.accent {{ border-color: rgba(57,255,136,0.55); box-shadow: 0 0 0 1px rgba(57,255,136,0.15) inset; }}
.card.accent .value {{ color: {NEON}; }}

.badge {{ display: inline-block; padding: 2px 10px; border-radius: 999px; font-size: 11.5px; font-weight: 600; margin-right: 6px; }}
.tag {{ display: inline-block; padding: 2px 9px; border-radius: 6px; font-size: 11.5px; margin-right: 6px; border: 1px solid {LINE}; color: {MUTED}; }}
.state-measured {{ background: rgba(57,255,136,0.12); color: {NEON}; border: 1px solid rgba(57,255,136,0.4); }}
.state-external {{ background: rgba(92,200,255,0.12); color: #5CC8FF; border: 1px solid rgba(92,200,255,0.4); }}
.state-unavailable {{ background: rgba(154,168,195,0.12); color: {MUTED}; border: 1px dashed {MUTED}; }}
.state-illustrative {{ background: rgba(255,174,66,0.12); color: #FFAE42; border: 1px solid rgba(255,174,66,0.45); }}

.section-title {{ font-size: 20px; font-weight: 600; margin: 8px 0 2px; }}
.section-sub {{ color: {MUTED}; font-size: 14px; margin-bottom: 12px; }}
.note {{ border-left: 3px solid {NEON}; background: rgba(57,255,136,0.05); padding: 10px 14px; border-radius: 6px; color: {TEXT}; font-size: 14px; }}
.warn {{ border-left: 3px solid #FFAE42; background: rgba(255,174,66,0.06); padding: 10px 14px; border-radius: 6px; font-size: 14px; }}

.lane {{ display: grid; grid-template-columns: 150px repeat(4, minmax(0,1fr)); gap: 8px; margin-bottom: 8px; }}
.lane .lname {{ background: {PANEL_2}; border: 1px solid {LINE}; border-radius: 10px; padding: 10px; font-weight: 600; font-size: 13.5px; display:flex; align-items:center; }}
.lane .cell {{ background: {PANEL}; border: 1px solid {LINE}; border-radius: 10px; padding: 10px; font-size: 13px; color: {MUTED}; }}
.lane .cell.on {{ border-color: {NEON}; color: {TEXT}; background: rgba(57,255,136,0.07); }}
.lane.head .cell {{ background: transparent; border: none; font-weight: 600; color: {TEXT}; text-align: center; }}
.lane.head .cell.on {{ color: {NEON}; }}
.lane.head .lname {{ background: transparent; border: none; }}

.owner-col {{ background: {PANEL}; border: 1px solid {LINE}; border-radius: 14px; padding: 14px 16px; }}
.owner-col h4 {{ margin: 0 0 4px; font-size: 16px; }}
.owner-item {{ border-top: 1px solid {LINE}; padding: 8px 0; font-size: 13.5px; }}
.owner-item .meta {{ color: {MUTED}; font-size: 12px; }}

.stTabs [role="tablist"] {{ gap: 4px; border-bottom: 1px solid {LINE}; flex-wrap: wrap; }}
.stTabs [role="tab"] {{ background: transparent; color: {MUTED}; border-radius: 8px 8px 0 0; padding: 8px 14px; }}
.stTabs [aria-selected="true"] {{ color: {TEXT} !important; background: {PANEL}; border-bottom: 2px solid {NEON} !important; }}
[data-testid="stExpander"] {{ background: {PANEL}; border: 1px solid {LINE}; border-radius: 12px; }}
[data-testid="stExpander"] summary p {{ font-weight: 500; }}
[data-testid="stMetricValue"] {{ color: {TEXT}; }}
div[data-testid="stDownloadButton"] button, div.stButton button {{ border: 1px solid {NEON}; color: {NEON}; background: transparent; }}
div[data-testid="stDownloadButton"] button:hover {{ background: rgba(57,255,136,0.1); color: {NEON}; }}

@media (max-width: 900px) {{
  .hero h1 {{ font-size: 28px; }}
  .lane {{ grid-template-columns: 1fr; }}
  .lane.head {{ display: none; }}
}}
</style>
""",
    unsafe_allow_html=True,
)


# ─────────────────────────────── Helpers ───────────────────────────────
def badge(priority: str) -> str:
    c = PRIORITY_COLORS.get(priority, MUTED)
    return f'<span class="badge" style="background:{c}22;color:{c};border:1px solid {c}66">{priority}</span>'


def card(label: str, value, sub: str = "", accent: bool = False) -> str:
    cls = "card accent" if accent else "card"
    return f'<div class="{cls}"><div class="label">{label}</div><div class="value">{value}</div><div class="sub">{sub}</div></div>'


def cards(items: list[tuple]):
    cols = st.columns(len(items))
    for col, it in zip(cols, items):
        col.markdown(card(*it), unsafe_allow_html=True)


def style_fig(fig: go.Figure, height: int = 320) -> go.Figure:
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color=TEXT, size=13),
        margin=dict(l=10, r=10, t=78, b=10),
        height=height,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, bgcolor="rgba(0,0,0,0)", title_text=""),
        title_font=dict(size=15),
        title=dict(x=0, y=0.98, yanchor="top"),
    )
    fig.update_xaxes(gridcolor=LINE, zerolinecolor=LINE)
    fig.update_yaxes(gridcolor=LINE, zerolinecolor=LINE)
    return fig


def section(title: str, sub: str = ""):
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)
    if sub:
        st.markdown(f'<div class="section-sub">{sub}</div>', unsafe_allow_html=True)


def short(url: str) -> str:
    return url.replace(SITE, "") or "/"


def finding_card(f: dict, expanded: bool = False):
    status = st.session_state.status.get(f["id"], "Open")
    pcol = {"Critical": "red", "High": "orange", "Medium": "yellow", "Low": "blue"}[f["priority"]]
    scol = {"Open": "gray", "In progress": "orange", "Fixed": "green", "Won't fix": "gray"}.get(status, "gray")
    label = f":{pcol}-badge[{f['priority']}] **{f['id']}** · {f['title']} :{scol}-badge[{status}]"
    with st.expander(label, expanded=expanded):
        st.markdown(
            badge(f["priority"])
            + f'<span class="tag">{f["category"]}</span><span class="tag">{f["type"]}</span>'
            + f'<span class="tag">{OWNER_LABEL[f["owner"]]}</span><span class="tag">Phase: {f["phase"]}</span>',
            unsafe_allow_html=True,
        )
        c1, c2 = st.columns([1.15, 1])
        with c1:
            st.markdown("**Evidence**")
            st.markdown(f["evidence"])
            st.markdown("**Business impact**")
            st.markdown(f["impact"])
            if f["urls"]:
                st.markdown(f"**Affected** · {f['affected']}")
                st.markdown("\n".join(f"- [{short(u)}]({u})" for u in f["urls"][:10]))
            else:
                st.markdown(f"**Affected** · {f['affected']}")
        with c2:
            st.markdown("**Recommended fix**")
            st.markdown(f["solution"])
            st.markdown("**Implementation steps**")
            st.markdown("\n".join(f"{i}. {s}" for i, s in enumerate(f["steps"], 1)))
            st.markdown(
                f"**Effort** {f['effort']} · **Role** {f['role']}  \n"
                f"**Dependencies** {f['dependencies']}  \n"
                f"**Success metric** {f['success_metric']}  \n"
                f"**Validation** {f['validation']}"
            )


def to_excel(frames: dict[str, pd.DataFrame]) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        for name, d in frames.items():
            d.to_excel(xw, sheet_name=name[:31], index=False)
    return buf.getvalue()


def export_frame(df: pd.DataFrame) -> pd.DataFrame:
    cols = ["id", "title", "type", "category", "priority", "status", "owner", "phase", "affected", "urls_text",
            "evidence", "impact", "solution", "dependencies", "effort", "role", "success_metric", "validation"]
    out = df[cols].copy()
    out["priority"] = out["priority"].astype(str)
    out["owner"] = out["owner"].map(OWNER_LABEL)
    return out.rename(columns={"urls_text": "urls"})


df_all = findings_df()

# ─────────────────────────────── Sidebar ───────────────────────────────
with st.sidebar:
    st.markdown("### About this audit")
    st.markdown(
        f"**Site:** [springfieldproperties.ae]({SITE})  \n**Audit date:** 28 October 2026  \n**Prepared by:** Ali Naseh"
    )
    st.markdown("### Method")
    st.markdown(
        "- All 748 sitemap URLs fetched and checked\n"
        "- Titles, descriptions and text extracted; dictionary spell-check + manual review\n"
        "- Pattern search for company names, ORN, phones, emails, years, visa figures\n"
        "- One page per template reviewed in depth\n"
        "- Visa and fee claims checked against current sources"
    )
    st.markdown("### Limitations")
    st.markdown(
        "- **Core Web Vitals:** not measured (PageSpeed API unreachable from the audit environment)\n"
        "- **Indexing, clicks, AI Overview traffic:** need Search Console\n"
        "- **Conversion events:** need GA4 / GTM\n"
        "- **Lead quality:** needs CRM\n"
        "- **Listing/project schema, 404s, broken links:** need Rich Results Test / full crawler"
    )
    st.caption("Status changes are kept while this session is open. Use the export buttons to save them.")

# ─────────────────────────────── Hero ───────────────────────────────
n_verified = int((df_all["type"] == "Verified problem").sum())
n_opp = int((df_all["type"] == "Opportunity").sum())
n_access = int((df_all["type"] == "Needs access").sum())
st.markdown(
    f"""
<div class="hero">
  <div class="eyebrow">SEO · AEO · GEO Audit &nbsp;|&nbsp; 28 October 2026</div>
  <h1>Springfield Properties: search & AI visibility audit</h1>
  <p>A strong technical base and genuinely useful content, held back by outdated legal facts, template errors and an
  inconsistent brand name. Most problems sit in a few templates and data fields, so a small number of fixes clears hundreds of pages.</p>
  <div class="chips">
    <span class="chip"><b>748</b> URLs audited</span>
    <span class="chip"><b>{n_verified}</b> verified problems</span>
    <span class="chip"><b>{n_opp}</b> opportunities</span>
    <span class="chip"><b>{n_access}</b> items need company access</span>
    <span class="chip"><b>{len(errors_df)}</b> page-level errors logged</span>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

tabs = st.tabs(
    ["Overview", "SEO", "AEO", "GEO", "Issue tracker", "Roadmap", "Brand audit", "KPIs", "Implementation", "Evidence explorer"]
)

# ═══════════════════════════════ OVERVIEW ═══════════════════════════════
with tabs[0]:
    cards([
        ("Critical issues", int((df_all["priority"] == "Critical").sum()), "Fix in the first 48 hours", True),
        ("High priority", int((df_all["priority"] == "High").sum()), "Days 3–14"),
        ("Pages with brand variants", 281, "of 748 crawled"),
        ("Placeholder page titles", 28, "visible in Google results"),
        ("Outdated visa minimum", "9 pages", "+ 3 outdated visa guides"),
    ])
    st.write("")
    c1, c2 = st.columns([1, 1.25])
    with c1:
        pc = df_all.groupby("priority", observed=False).size().reset_index(name="count")
        fig = px.pie(pc, names="priority", values="count", hole=0.62, color="priority", color_discrete_map=PRIORITY_COLORS,
                     category_orders={"priority": PRIORITY_ORDER}, title="All register items by priority")
        fig.update_traces(textinfo="value", textfont_size=14, sort=False)
        st.plotly_chart(style_fig(fig), width="stretch")
    with c2:
        cc = df_all.groupby(["category", "type"]).size().reset_index(name="count")
        fig = px.bar(cc, y="category", x="count", color="type", orientation="h", title="Register items by category and type",
                     color_discrete_map={"Verified problem": "#FF5C7A", "Opportunity": NEON, "Needs access": "#5CC8FF"})
        fig.update_layout(yaxis_title=None, xaxis_title="Items", yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(style_fig(fig), width="stretch")

    section("What is working (verified)")
    w1, w2 = st.columns(2)
    w1.markdown(
        "- All crawlers, AI crawlers included, can reach the site; robots.txt lists the sitemap\n"
        "- Sitemap covers 748 URLs: listings, 189 projects, 23 area guides, 92 blog posts, 53 developers, 23 reports\n"
        "- Canonical tags on every template checked; www and missing trailing slash redirect correctly"
    )
    w2.markdown(
        "- Homepage has RealEstateAgent structured data; blog posts have Article + BreadcrumbList\n"
        "- Area guides answer buyer questions honestly; project pages have FAQs (Parkwood: 12)\n"
        "- Springfield publishes its own quarterly transaction data"
    )

    section("The five problems that matter most")
    top5 = pd.DataFrame([
        ["1", "Outdated visa rules (AED 750,000 minimum, AED 10M Golden Visa, 'mortgaged doesn't qualify')", "9 pages + 3 guides", "Misleads buyers; contradicts Springfield's own Q2 2026 report"],
        ["2", "Wrong RERA licence number (ORN 1192 instead of 11929)", "3 listings", "Regulatory accuracy"],
        ["3", "Unfilled %currentyear% / %sitename% in page titles", "28 pages", "Visible in Google on high-value pages"],
        ["4", "Company name written 15+ ways", "281 pages", "Weakens brand and entity recognition"],
        ["5", "Listing template faults: cut descriptions, generic share image, empty alt text, no project/area links", "All listings (249 cut descriptions)", "Lower click-through, weaker internal linking"],
    ], columns=["#", "Problem", "Scale", "Why it matters"])
    st.dataframe(top5, hide_index=True, width="stretch")

    section("Recommendation")
    st.markdown(
        '<div class="note">Fix accuracy and templates in the first 48 hours, then spend weeks 2–4 turning Springfield\'s own data '
        "and expert agents into sourced, dated content, and measure from day one. Targets are set only after a 28-day baseline.</div>",
        unsafe_allow_html=True,
    )
    with st.expander("Audit coverage and limitations"):
        cov = pd.DataFrame([
            ["Crawlability", "robots.txt, sitemap.xml, redirect tests, llms.txt request", "Site-wide", "Verified"],
            ["Titles, descriptions, text", "All sitemap URLs fetched; titles, meta descriptions, main text extracted", "748 pages", "Verified"],
            ["Spelling", "Dictionary check + manual review", "748 pages", "Verified"],
            ["Facts & consistency", "Pattern search: names, ORN, phones, emails, years, visa figures, fees", "748 pages", "Verified"],
            ["Structured data", "JSON-LD types from raw HTML", "Home, area guide, blog, terms", "Partly verified"],
            ["Templates", "In-depth review of one page per template", "7 templates", "Verified"],
            ["Core Web Vitals", "PageSpeed Insights", "—", "Needs access / not run"],
            ["Indexing, traffic, leads", "Search Console, GA4, CRM", "—", "Needs access"],
        ], columns=["Check", "How", "Coverage", "Status"])
        st.dataframe(cov, hide_index=True, width="stretch")


# ═══════════════════════════════ CATEGORY TABS ═══════════════════════════════
def category_tab(cats: list[str], intro: str):
    sub = df_all[df_all["category"].isin(cats)]
    cards([(p, int((sub["priority"] == p).sum()), "items") for p in PRIORITY_ORDER])
    st.write("")
    st.markdown(f'<div class="section-sub">{intro}</div>', unsafe_allow_html=True)
    t = st.segmented_control("Show", ["All", "Verified problem", "Opportunity", "Needs access"], default="All",
                             key=f"seg_{'_'.join(cats)}")
    show = sub if t in (None, "All") else sub[sub["type"] == t]
    for _, row in show.iterrows():
        finding_card(findings_by_id[row["id"]])


findings_by_id = {f["id"]: f for f in findings_raw}

with tabs[1]:
    section("SEO findings and recommendations",
            "Crawl and index foundations are sound; losses come from templates that generate titles, descriptions, images and links.")
    with st.expander("Crawlability & indexability (verified)", expanded=False):
        st.dataframe(pd.DataFrame([
            ["robots.txt", "User-agent: *, Allow: /, Disallow: /api/, Disallow: /_next/image, sitemap declared", "Good, one risk"],
            ["AI crawlers", "No rules for OAI-SearchBot, GPTBot, PerplexityBot, Google-Extended → all allowed", "Good"],
            ["Sitemap", "One flat file, 748 URLs", "Good; split by type"],
            ["Canonicals", "Present and self-referencing on every template checked", "Good"],
            ["Redirects", "www. and missing trailing slash redirect to canonical URL", "Good"],
            ["404 handling", "Not testable from audit environment", "Needs access"],
        ], columns=["Item", "Observation", "Status"]), hide_index=True, width="stretch")
        st.markdown('<div class="warn"><b>Risk:</b> every site photo loads through <code>/_next/image/?url=…</code>, which robots.txt blocks. '
                    "This may stop Google fetching listing images. Validate with Search Console URL Inspection (finding A08).</div>",
                    unsafe_allow_html=True)
    with st.expander("Listing title pattern: before → after"):
        st.dataframe(pd.DataFrame([
            ["Title tag", "Modern 2BR Living | Parkwood Dubai Hills Estate, Dubai Hills Estate, Dubai", "2 Bed Apartment for Sale in Parkwood, Dubai Hills Estate | Springfield"],
            ["H1", "Modern 2BR Living | Parkwood Dubai Hills Estate", "2 Bed Apartment in Parkwood, Dubai Hills Estate"],
            ["Subtitle", "—", "Modern 2BR Living (agent tagline)"],
            ["Meta description", "…cut mid-word", "AED 3,131,733 · 1,075 sq ft · 2 bed · off-plan. A modern 2-bedroom in Parkwood by Emaar…"],
        ], columns=["Element", "Today (SP-S-6777)", "Proposed pattern"]), hide_index=True, width="stretch")
    with st.expander("Structured data by template"):
        st.dataframe(pd.DataFrame([
            ["Homepage", "RealEstateAgent, PostalAddress, City", "Add both offices, telephone, sameAs, founding date, RERA ORN"],
            ["Blog post", "Article, BreadcrumbList", "Named author (Person), dateModified"],
            ["Area guide", "BreadcrumbList only", "Place; Article if authored and dated"],
            ["Listing, project", "Not verified", "Rich Results Test; RealEstateListing / Offer matching visible price"],
        ], columns=["Template", "JSON-LD found", "Recommendation"]), hide_index=True, width="stretch")
        st.caption("Google shows no rich result for listings and stopped showing FAQ rich results in May 2026. "
                   "Structured data states facts clearly; it does not by itself produce rich results or AI citations.")
    category_tab(["SEO", "Local SEO", "Analytics", "Conversion"],
                 "Includes local SEO, analytics and conversion-tracking items.")

with tabs[2]:
    section("AEO findings and recommendations",
            "Project FAQs and area guides have the right shape; several answers are wrong or contradictory, and the strongest guides lack numbers, dates and named authors.")
    with st.expander("Accuracy: answers that are wrong or out of date", expanded=True):
        st.dataframe(pd.DataFrame([
            ["2-year property visa", "AED 750,000 minimum", "Removed for sole owners (Apr 2026); joint owners AED 400,000 each", "9 pages"],
            ["Investor visa types", "'Three-Year' AED 750k; 'Five-Year' AED 5M", "Visa is 2 years; see above", "1 guide"],
            ["Golden Visa threshold", "AED 10M, 40% real estate, no loans", "AED 2M in property; mortgaged/off-plan can qualify", "1 guide"],
            ["Golden Visa with mortgage", "'Must be fully paid' / 'significant portion paid'", "No minimum paid-down since Jan 2024; bank NOC", "2 pages"],
            ["Golden Visa processing", "'7–10 business days' and '2 to 4 weeks'", "One figure, checked with DLD", "1 guide"],
            ["DLD 4% fee payer", "Stated 3 different ways on one page", "One consistent statement", "1 guide"],
            ["Years in business", "'Over 13 years'", "Since 2008 (18 years)", "About page"],
        ], columns=["Topic", "What the site says", "Current position", "Pages"]), hide_index=True, width="stretch")
        st.markdown('<div class="warn">Confirm every regulated figure with DLD / GDRFA before publishing. Sources: Khaleej Times (29 Apr 2026), '
                    "Property Finder Golden Visa guide, Springfield's own Q2 2026 report.</div>", unsafe_allow_html=True)
    with st.expander("Sample: answer-first Golden Visa guide"):
        st.markdown(
            "**Title tag:** Dubai Golden Visa Through Property (2026): AED 2M Rules, Costs | Springfield  \n"
            "**H1:** How to Get a Dubai Golden Visa Through Property  \n"
            "**Opening answer:** *You can apply for a 10-year UAE Golden Visa if you own Dubai property worth at least AED 2 million, "
            "including mortgaged and off-plan property registered with the Dubai Land Department. Joint owners each need a share worth AED 2 million.*  \n"
            "**Below the answer:** Last verified: [date] by [named consultant, RERA BRN] · Sources: DLD, GDRFA  \n"
            "**H2s:** Who qualifies · Mortgaged and off-plan · Documents · Costs (table) · Processing time · Family sponsorship · The 2-year visa alternative · FAQs"
        )
    with st.expander("Sample: key-figures block for each area guide"):
        st.dataframe(pd.DataFrame([
            ["Average sale price", "AED per sq ft, apartments and villas, quarter stated", "Springfield quarterly report / DLD"],
            ["Typical annual rent", "AED by bedroom count", "Springfield listings / DLD rental index"],
            ["Gross yield", "% with date", "Calculated from rows above"],
            ["Service charges", "AED per sq ft range", "DLD Mollak service charge index"],
            ["Metro", "Yes / no, nearest station", "RTA"],
            ["Last updated", "Date + analyst name", "—"],
        ], columns=["Metric", "Format", "Source"]), hide_index=True, width="stretch")
    category_tab(["AEO"], "Answer quality, accuracy and structure.")

with tabs[3]:
    section("GEO findings and recommendations",
            "AI assistants can crawl the site; they lack a consistent, credible picture of the company and enough sourced, current data to quote.")
    g1, g2 = st.columns([1, 1.2])
    with g1:
        st.dataframe(pd.DataFrame([
            ["Crawlable, indexable, text content, schema matching visible content", "Established (Google docs)"],
            ["Allow OAI-SearchBot and Bingbot", "Established (OpenAI docs)"],
            ["Consistent business facts across site and profiles", "Established for local SEO"],
            ["Original, dated data with named experts", "Established principle; citations not guaranteed"],
            ["Third-party mentions in lists, press, directories", "Emerging"],
            ["Wikidata entry", "Emerging"],
            ["llms.txt", "Not supported ('purely speculative', Google, June 2026)"],
        ], columns=["Recommendation", "Evidence base"]), hide_index=True, width="stretch")
    with g2:
        ag = kpis["ai_grader"]
        ov = pd.DataFrame({"Engine": list(ag["overall"].keys()), "Score": list(ag["overall"].values())})
        fig = px.bar(ov, x="Engine", y="Score", text="Score", title="Third-party AI search grader · overall score (0–100)",
                     color_discrete_sequence=[NEON])
        fig.update_traces(textposition="outside", marker_line_width=0)
        fig.update_yaxes(range=[0, 100])
        st.plotly_chart(style_fig(fig, 300), width="stretch")
        st.markdown('<span class="badge state-external">EXTERNAL TOOL · MEASURED 28 OCT 2026</span>'
                    '<span style="color:#9AA8C3;font-size:12.5px">One tool\'s scoring, not an official metric. Share of voice 1/10 on all three.</span>',
                    unsafe_allow_html=True)
    category_tab(["GEO"], "Entity consistency, credibility, original data and third-party presence.")

# ═══════════════════════════════ ISSUE TRACKER ═══════════════════════════════
with tabs[4]:
    section("Priority issue tracker", "Change status in the table; counts and progress update instantly. Export to keep your changes.")
    f1, f2, f3 = st.columns([1.4, 1.2, 1])
    pr = f1.pills("Priority", PRIORITY_ORDER, selection_mode="multi", default=PRIORITY_ORDER, key="tr_pr")
    ty = f2.pills("Type", ["Verified problem", "Opportunity", "Needs access"], selection_mode="multi",
                  default=["Verified problem", "Opportunity", "Needs access"], key="tr_ty")
    stf = f3.multiselect("Status", STATUS_OPTIONS, default=STATUS_OPTIONS, key="tr_st")
    view = df_all[df_all["priority"].isin(pr or []) & df_all["type"].isin(ty or []) & df_all["status"].isin(stf)]

    done = int((df_all["status"] == "Fixed").sum())
    cards([
        ("Open", int((df_all["status"] == "Open").sum()), "all items"),
        ("In progress", int((df_all["status"] == "In progress").sum()), "all items"),
        ("Fixed", done, "all items", True),
        ("Shown", len(view), "after filters"),
    ])
    st.progress(done / len(df_all), text=f"{done} of {len(df_all)} register items fixed")

    edit = view[["id", "title", "priority", "category", "type", "effort", "owner", "phase", "status", "first_url"]].copy()
    edit["priority"] = edit["priority"].astype(str)
    edit["owner"] = edit["owner"].map(OWNER_LABEL)
    edited = st.data_editor(
        edit,
        hide_index=True,
        width="stretch",
        height=min(42 + 35 * len(edit), 640),
        disabled=["id", "title", "priority", "category", "type", "effort", "owner", "phase", "first_url"],
        column_config={
            "id": st.column_config.TextColumn("ID", width="small"),
            "title": st.column_config.TextColumn("Finding", width="large"),
            "priority": st.column_config.TextColumn("Priority", width="small"),
            "status": st.column_config.SelectboxColumn("Status", options=STATUS_OPTIONS, required=True, width="small"),
            "category": "Category",
            "type": "Type",
            "effort": "Effort",
            "owner": "Who",
            "phase": "Phase",
            "first_url": st.column_config.LinkColumn("Example URL", display_text=r"https://springfieldproperties\.ae(.*)"),
        },
        key="tracker_editor",
    )
    changed = False
    for _, r in edited.iterrows():
        if st.session_state.status.get(r["id"]) != r["status"]:
            st.session_state.status[r["id"]] = r["status"]
            changed = True
    if changed:
        # Reset the editor so row-index edits never re-apply to a re-filtered table.
        del st.session_state["tracker_editor"]
        st.rerun()

    c1, c2 = st.columns([1.3, 1])
    with c1:
        m = df_all.groupby(["priority", "status"], observed=False).size().reset_index(name="count")
        fig = px.bar(m, x="priority", y="count", color="status", title="Status by priority",
                     category_orders={"priority": PRIORITY_ORDER, "status": STATUS_OPTIONS},
                     color_discrete_map={"Open": "#FF5C7A", "In progress": "#FFAE42", "Fixed": NEON, "Won't fix": MUTED})
        fig.update_layout(xaxis_title=None, yaxis_title="Items")
        st.plotly_chart(style_fig(fig, 300), width="stretch")
    with c2:
        st.markdown("**Export**")
        exp = export_frame(df_all[df_all["id"].isin(view["id"])])
        st.download_button("Download filtered tracker (CSV)", exp.to_csv(index=False).encode("utf-8"),
                           "springfield_issue_tracker.csv", "text/csv", width="stretch")
        st.download_button("Download filtered tracker (Excel)", to_excel({"Tracker": exp}),
                           "springfield_issue_tracker.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", width="stretch")

# ═══════════════════════════════ ROADMAP ═══════════════════════════════
with tabs[5]:
    section("Implementation roadmap", "Critical fixes land in 48 hours; growth work runs to day 90. Pick a phase to see what happens, who does it and how it is measured.")
    phases = roadmap["phases"]
    labels = [p["label"] for p in phases]
    r1, r2 = st.columns([2.2, 1])
    sel_label = r1.segmented_control("Phase", labels, default=labels[0], key="phase_sel") or labels[0]
    start = r2.date_input("Plan start date", value=date.today(), key="plan_start")
    sel = next(p for p in phases if p["label"] == sel_label)
    idx = labels.index(sel_label)

    # Workstream grid
    head = '<div class="lane head"><div class="lname"></div>' + "".join(
        f'<div class="cell{" on" if i == idx else ""}">{l}</div>' for i, l in enumerate(labels)) + "</div>"
    rows = ""
    for ws, items in roadmap["workstreams"].items():
        rows += f'<div class="lane"><div class="lname">{ws}</div>' + "".join(
            f'<div class="cell{" on" if i == idx else ""}">{it}</div>' for i, it in enumerate(items)) + "</div>"
    st.markdown(head + rows, unsafe_allow_html=True)

    # Gantt
    gantt = []
    for p in phases:
        for ws, items in roadmap["workstreams"].items():
            i = labels.index(p["label"])
            gantt.append(dict(Workstream=ws, Phase=p["label"], Task=items[i],
                              Start=start + timedelta(days=p["start_day"]), Finish=start + timedelta(days=max(p["end_day"], p["start_day"] + 1))))
    gdf = pd.DataFrame(gantt)
    gdf["Selected"] = gdf["Phase"].eq(sel_label).map({True: "Selected phase", False: "Other phases"})
    fig = px.timeline(gdf, x_start="Start", x_end="Finish", y="Workstream", color="Selected", hover_data=["Phase", "Task"],
                      color_discrete_map={"Selected phase": NEON, "Other phases": "#2B4170"}, title="90-day timeline")
    fig.update_yaxes(autorange="reversed", title=None)
    fig.update_traces(marker_line_color=NAVY, marker_line_width=2)
    st.plotly_chart(style_fig(fig, 300), width="stretch")

    d1, d2, d3 = st.columns(3)
    with d1:
        st.markdown(f"#### {sel['label']}")
        st.markdown("**Deliverables**\n" + "\n".join(f"- {d}" for d in sel["deliverables"]))
        st.markdown(f"**Effort:** {sel['effort']}")
    with d2:
        st.markdown("#### Who")
        st.markdown("**I can do independently**\n" + "\n".join(f"- {d}" for d in sel["independent"]))
        st.markdown("**Needs company access or developer**\n" + "\n".join(f"- {d}" for d in sel["needs_access"]))
    with d3:
        st.markdown("#### Outcome")
        st.markdown(f'<div class="note">{sel["outcome"]}</div>', unsafe_allow_html=True)
        st.markdown("**KPIs**\n" + "\n".join(f"- {k}" for k in sel["kpis"]))
        st.markdown("**Risks**\n" + "\n".join(f"- {k}" for k in sel["risks"]))

    st.markdown(f"**Register items scheduled in this phase**")
    ph = df_all[df_all["phase"] == sel["key"]][["id", "title", "priority", "effort", "owner", "status"]].copy()
    ph["priority"] = ph["priority"].astype(str)
    ph["owner"] = ph["owner"].map(OWNER_LABEL)
    st.dataframe(ph, hide_index=True, width="stretch")

# ═══════════════════════════════ BRAND AUDIT ═══════════════════════════════
with tabs[6]:
    section("Brand consistency audit",
            "Site-controlled elements say 'Springfield Properties'; agent-written listing copy carries 15+ versions. Fix at the data source, not page by page.")
    long = brand_df.assign(variant=brand_df["variants"].str.split("; ")).explode("variant")
    long["variant"] = long["variant"].str.strip()

    def family(v: str) -> str:
        u = v.upper()
        if u.startswith("SPRING FIELD PROPERTIES"):
            return "Spring Field Properties (+ suffixes)"
        if u.startswith("SPRING FIELD REAL ESTATE"):
            return "Spring Field Real Estate"
        if u.startswith("SPRINGFIELD REAL ESTATE"):
            return "Springfield Real Estate"
        if u.startswith("SPRINGFIELD PROPERTIES"):
            return "SPRINGFIELD PROPERTIES legal forms"
        return "Other"

    long["family"] = long["variant"].apply(family)
    n_var = long["variant"].nunique()
    cards([
        ("Pages affected", len(brand_df), "of 748 crawled", True),
        ("Distinct name strings", n_var, "exact spellings found"),
        ("Listings among them", int(brand_df["url"].str.contains("/for-(?:sale|rent)/").sum()), "plus the privacy policy"),
        ("Approved public name", "1", "Springfield Properties"),
    ])
    st.write("")
    b1, b2 = st.columns([1.4, 1])
    with b1:
        vc = long.groupby("variant")["url"].nunique().reset_index(name="pages").sort_values("pages")
        fig = px.bar(vc, x="pages", y="variant", orientation="h", text="pages", title="Pages containing each name variant",
                     color_discrete_sequence=["#FF5C7A"])
        fig.update_layout(yaxis_title=None, xaxis_title="Pages", xaxis_range=[0, vc["pages"].max() * 1.15])
        fig.update_traces(textposition="outside", cliponaxis=False)
        st.plotly_chart(style_fig(fig, 540), width="stretch")
    with b2:
        fc = long.groupby("family")["url"].nunique().reset_index(name="pages")
        fig = px.pie(fc, names="family", values="pages", hole=0.6, title="Variant families (pages)",
                     color_discrete_sequence=["#FF5C7A", "#FFAE42", "#F2D35B", "#5CC8FF", MUTED])
        st.plotly_chart(style_fig(fig, 360), width="stretch")
        st.markdown("**Mixed on one page:** listing SP-S-6777 shows *Spring Field Real Estate SOC*, *Springfield Real Estate*, "
                    "*SPRING FIELD REAL ESTATE* and *Springfield Properties* together.")

    section("Proposed standardisation")
    st.dataframe(pd.DataFrame([
        ["Spring Field Properties / Spring Field Properties LLC SOC", "Springfield Properties", "Listing opening line"],
        ["Spring Field Real Estate / Springfield Real Estate", "Springfield Properties", "Description body"],
        ["SPRING FIELD PROPERTIES LLC SOC / SPRING FIELD REAL ESTATE / SPRINGFIELD PROPERTIES L.L.C.S.O.C …", "[Verified legal name] · RERA ORN 11929 · Permit [auto]", "Locked licence line"],
        ["Spring Field Properties (privacy policy)", "Springfield Properties", "Privacy policy"],
    ], columns=["Found today", "Use instead", "Where"]), hide_index=True, width="stretch")
    st.markdown('<div class="warn"><b>Do not change legal or licensing text until verified.</b> The site shows both '
                '"Springfield Properties L.L.C S.O.C" and "SPRING FIELD PROPERTIES L.L.C S.O.C"; Property Finder lists "Springfield Real Estate". '
                "Check the trade licence and the DLD broker register first.</div>", unsafe_allow_html=True)

    s1, s2 = st.columns(2)
    with s1:
        section("Where the text comes from")
        st.dataframe(pd.DataFrame([
            ["Visible page text", "Rendered page", "Variants in description, highlights, sign-off"],
            ["HTML metadata", "View source: title, meta description, og:", "Variants reach meta descriptions cut from the description"],
            ["Structured data", "JSON-LD; Rich Results Test", "Homepage standard; listings not verified"],
            ["Listing feed / CRM", "Compare with Property Finder; CRM record", "Hypothesis: listing photos on a listing-tool S3 bucket, agent photos from Property Finder"],
            ["CMS", "Is the listing editable in CMS or feed-only?", "Needs access"],
        ], columns=["Layer", "How to check", "What it showed"]), hide_index=True, width="stretch")
    with s2:
        section("Scalable correction")
        st.markdown(
            "1. **Confirm the legal name** (trade licence, DLD broker register)\n"
            "2. **Fix at source:** one locked licence field in the CRM; description template opening with 'Springfield Properties'\n"
            "3. **Website render rule:** replace known variants in listing text; licence line from site settings\n"
            "4. **Bulk clean** the CRM export, then re-sync\n"
            "5. **Weekly automated check** for non-approved variants and any ORN other than 11929"
        )

    section("Affected pages")
    q = st.text_input("Search URL or variant", key="brand_q", placeholder="e.g. dubai-hills, Spring Field Real Estate")
    fams = st.multiselect("Variant family", sorted(long["family"].unique()), key="brand_fam")
    bview = brand_df.copy()
    if q:
        bview = bview[bview["url"].str.contains(q, case=False) | bview["variants"].str.contains(q, case=False)]
    if fams:
        keep = long[long["family"].isin(fams)]["url"].unique()
        bview = bview[bview["url"].isin(keep)]
    st.dataframe(bview[["url", "variants", "use_instead"]], hide_index=True, width="stretch", height=360,
                 column_config={"url": st.column_config.LinkColumn("Page", display_text=r"https://springfieldproperties\.ae(.*)", width="large"),
                                "variants": st.column_config.TextColumn("Variants found", width="large"),
                                "use_instead": "Use instead"})
    st.download_button("Download brand variants (CSV)", bview.to_csv(index=False).encode("utf-8"), "brand_variants_filtered.csv", "text/csv")

# ═══════════════════════════════ KPIs ═══════════════════════════════
with tabs[7]:
    section("KPI dashboard", "Every number is labelled by where it comes from. Nothing is estimated.")
    st.markdown(
        '<span class="badge state-measured">MEASURED · AUDIT CRAWL</span>'
        '<span class="badge state-external">MEASURED · EXTERNAL TOOL</span>'
        '<span class="badge state-unavailable">UNAVAILABLE · NEEDS ACCESS</span>'
        '<span class="badge state-illustrative">ILLUSTRATIVE · NOT SPRINGFIELD DATA</span>',
        unsafe_allow_html=True,
    )
    st.write("")
    k1, k2 = st.columns([1.1, 1])
    with k1:
        st.markdown("#### Technical & content health")
        st.markdown('<span class="badge state-measured">MEASURED · AUDIT CRAWL 28 OCT 2026</span>', unsafe_allow_html=True)
        mh = pd.DataFrame(kpis["measured_site_health"])
        fig = px.bar(mh.iloc[1:].sort_values("value"), x="value", y="metric", orientation="h", text="value",
                     color_discrete_sequence=["#FFAE42"], title="Issues found (lower is better)")
        fig.update_layout(yaxis_title=None, xaxis_title="Pages", xaxis_range=[0, mh["value"].iloc[1:].max() * 1.18])
        fig.update_traces(textposition="outside", cliponaxis=False)
        st.plotly_chart(style_fig(fig, 360), width="stretch")
    with k2:
        st.markdown("#### Audit coverage")
        st.markdown('<span class="badge state-measured">MEASURED · SITEMAP</span>', unsafe_allow_html=True)
        sm = pd.DataFrame({"type": list(kpis["sitemap_mix"].keys()), "urls": list(kpis["sitemap_mix"].values())})
        fig = px.treemap(sm, path=["type"], values="urls", title="748 sitemap URLs by page type",
                         color_discrete_sequence=["#1E3A6B", "#22477F", "#2A5694", "#3264A8", "#3A73BD", "#4382D1", "#4C91E5", "#5CC8FF", "#39FF88"])
        fig.update_traces(texttemplate="%{label}<br>%{value}", marker_line_color=NAVY)
        st.plotly_chart(style_fig(fig, 360), width="stretch")

    st.markdown("#### AI citations & visibility")
    st.markdown(f'<span class="badge state-external">MEASURED · EXTERNAL TOOL</span><span style="color:{MUTED};font-size:12.5px">{kpis["ai_grader"]["source"]}</span>',
                unsafe_allow_html=True)
    comp = pd.DataFrame(kpis["ai_grader"]["components"])
    long_c = comp.melt(id_vars=["component", "max"], var_name="engine", value_name="score")
    long_c["pct"] = (long_c["score"] / long_c["max"] * 100).round(0)
    long_c["label"] = long_c["score"].astype(str) + "/" + long_c["max"].astype(str)
    fig = px.bar(long_c, x="component", y="pct", color="engine", barmode="group", text="label",
                 title="Component scores (% of maximum)", color_discrete_map={"ChatGPT": "#FF5C7A", "Perplexity": "#FFAE42", "Gemini": NEON})
    fig.update_layout(yaxis_title="% of max", xaxis_title=None, yaxis_range=[0, 105])
    fig.update_traces(textposition="outside", textfont_size=11)
    st.plotly_chart(style_fig(fig, 340), width="stretch")
    st.caption("Reading: when AI assistants mention Springfield, sentiment is reasonable; they rarely mention it (share of voice 1/10 everywhere).")

    st.markdown("#### Organic visibility, AI referrals and qualified leads")
    st.markdown('<span class="badge state-unavailable">UNAVAILABLE · NEEDS ACCESS</span>', unsafe_allow_html=True)
    ua = pd.DataFrame(kpis["unavailable"])
    st.dataframe(ua.rename(columns={"area": "KPI area", "metric": "Metric", "needs": "Source needed", "status": "Status"}),
                 hide_index=True, width="stretch")
    st.markdown(f'<div class="note"><b>Target-setting:</b> {kpis["target_method"]}</div>', unsafe_allow_html=True)

    st.write("")
    if st.toggle("Show illustrative dashboard layout (sample data, not Springfield's)", key="illus"):
        st.markdown('<span class="badge state-illustrative">ILLUSTRATIVE SAMPLE · NOT SPRINGFIELD DATA</span>'
                    '<span style="color:#9AA8C3;font-size:12.5px">Shows how the live dashboard will look once Search Console, GA4 and CRM are connected.</span>',
                    unsafe_allow_html=True)
        weeks = pd.date_range(start=date.today() - timedelta(weeks=11), periods=12, freq="W")
        demo = pd.DataFrame({"Week": weeks,
                             "Organic clicks (sample)": [100, 104, 99, 108, 112, 110, 118, 121, 125, 123, 130, 134],
                             "Qualified enquiries (sample)": [10, 11, 10, 12, 12, 11, 13, 13, 14, 14, 15, 15]})
        fig = go.Figure()
        fig.add_scatter(x=demo["Week"], y=demo["Organic clicks (sample)"], name="Organic clicks (sample)", line=dict(color="#FFAE42", dash="dot"))
        fig.add_scatter(x=demo["Week"], y=demo["Qualified enquiries (sample)"], name="Qualified enquiries (sample)", yaxis="y2",
                        line=dict(color="#5CC8FF", dash="dot"))
        fig.update_layout(title="ILLUSTRATIVE ONLY · index values, not real data", yaxis=dict(title="Clicks (index)"),
                          yaxis2=dict(title="Enquiries (index)", overlaying="y", side="right", showgrid=False))
        fig.add_annotation(text="SAMPLE DATA", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False,
                           font=dict(size=48, color="rgba(255,174,66,0.18)"))
        st.plotly_chart(style_fig(fig, 320), width="stretch")

# ═══════════════════════════════ IMPLEMENTATION ═══════════════════════════════
with tabs[8]:
    section("Implementation plan", "What I can implement myself, what needs developer support, and what needs company access or sign-off.")
    oc = df_all.groupby(["owner", "priority"], observed=False).size().reset_index(name="count")
    oc["owner"] = oc["owner"].map(OWNER_LABEL)
    fig = px.bar(oc, x="count", y="owner", color="priority", orientation="h", category_orders={"priority": PRIORITY_ORDER},
                 color_discrete_map=PRIORITY_COLORS, title="Register items by who delivers them")
    fig.update_layout(yaxis_title=None, xaxis_title="Items")
    st.plotly_chart(style_fig(fig, 260), width="stretch")

    cols = st.columns(3)
    for col, key in zip(cols, ["Independent", "Developer", "Company access"]):
        items = df_all[df_all["owner"] == key]
        html = f'<div class="owner-col"><h4>{OWNER_LABEL[key]}</h4><div class="sub" style="color:{MUTED};font-size:12.5px">{len(items)} items</div>'
        for _, r in items.iterrows():
            html += (f'<div class="owner-item">{badge(str(r["priority"]))}<b>{r["id"]}</b> {r["title"]}'
                     f'<div class="meta">{r["effort"]} · {r["phase"]} · {r["dependencies"]}</div></div>')
        html += "</div>"
        col.markdown(html, unsafe_allow_html=True)

    st.write("")
    i1, i2 = st.columns([1.2, 1])
    with i1:
        section("Resources for 90 days")
        st.dataframe(pd.DataFrame([
            ["Marketing Technology & AI Specialist", "Full time", "Full time", "Audit, specs, content, schema, profiles, tracking, reporting"],
            ["Web developer", "7–8 days", "3–4 days", "Templates, render rule, schema, landing pages, hreflang"],
            ["Content writer / editor", "5 days", "~2 days/week", "Guides, area figures, Arabic coordination"],
            ["Listings / CRM admin", "1–2 days", "~2 hours/week", "ORN, licence field, bulk clean, handover status"],
            ["Market analyst", "3 days", "~2 days/month", "Monthly and quarterly reports"],
            ["Compliance / legal", "2–3 hours", "1 hour/quarter", "Visa and fee wording, legal name"],
            ["Translator", "—", "5 days", "Arabic versions"],
        ], columns=["Resource", "Days 1–30", "Days 31–90", "Used for"]), hide_index=True, width="stretch")
    with i2:
        section("Access needed on day 1")
        for a in ["CMS editor", "Google Search Console", "GA4 + Google Tag Manager", "Bing Webmaster Tools",
                  "Google Business Profile (both offices)", "CRM / listing tool export", "Property Finder & Bayut agency accounts",
                  "Social profile admins"]:
            st.checkbox(a, key=f"acc_{a}")
        st.caption("Tick items as access is granted (kept for this session).")

    section("How I can contribute")
    st.dataframe(pd.DataFrame([
        ["Template fixes, landing pages, schema", "HTML, CSS, JavaScript, PHP, REST APIs; spec and implement or review with the developer", "WordPress Developer, Avadh Institute (2019–2021)"],
        ["Springfield data → reports and area figures", "Python and API data work for real estate", "Desert Fox, Dubai (2026–present): market-insight web app for The Valley by Emaar with Python and the DXB Interact API"],
        ["Proving which pages produce qualified leads", "CRO, A/B testing, attribution, dashboards", "Growth Analyst, Paytm Payments Bank (2021–2026): CRO lifted final signup conversion by 10%"],
        ["Brand-name and ORN fix at scale", "Data workflows: export, clean, validate, re-sync, weekly checks", "REST API and third-party data integrations"],
        ["Accurate guides, faster", "AI-assisted research and drafting with human fact-check and named expert review", "Prompt frameworks that cut content production time ~70% (Promptify.ig)"],
        ["Property content", "Property video, photography, reels", "Desert Fox, Dubai"],
    ], columns=["Need from this audit", "What I bring", "Evidence"]), hide_index=True, width="stretch")
    st.markdown('<div class="note"><b>Responsible AI:</b> AI drafts and monitors; people decide. Every regulated fact is checked against DLD or GDRFA '
                "and signed off before publishing. AI-visibility results are reported as test samples, not guaranteed rankings.</div>",
                unsafe_allow_html=True)

# ═══════════════════════════════ EVIDENCE EXPLORER ═══════════════════════════════
with tabs[9]:
    section("Evidence explorer", "Search and filter every finding and every page-level error. Export exactly what you see.")
    dataset = st.segmented_control("Dataset", ["Findings register", "Page-level website errors", "Placeholder titles", "Cut-off descriptions"],
                                   default="Findings register", key="ex_ds") or "Findings register"

    if dataset == "Findings register":
        e1, e2, e3, e4 = st.columns([1.6, 1, 1, 1])
        q = e1.text_input("Search text", key="ex_q", placeholder="e.g. visa, ORN, alt text, Parkwood")
        cats = e2.multiselect("Category", sorted(df_all["category"].unique()), key="ex_cat")
        prs = e3.multiselect("Priority", PRIORITY_ORDER, key="ex_pr")
        sts = e4.multiselect("Status", STATUS_OPTIONS, key="ex_st")
        e5, e6 = st.columns([1.6, 2])
        urlq = e5.text_input("URL contains", key="ex_url", placeholder="e.g. /projects/, sp-s-6777")
        tys = e6.pills("Type", ["Verified problem", "Opportunity", "Needs access"], selection_mode="multi", key="ex_ty")
        v = df_all.copy()
        if q:
            blob = (v["title"] + " " + v["evidence"] + " " + v["solution"] + " " + v["affected"] + " " + v["impact"]).str.lower()
            v = v[blob.str.contains(q.lower(), regex=False)]
        if cats:
            v = v[v["category"].isin(cats)]
        if prs:
            v = v[v["priority"].isin(prs)]
        if sts:
            v = v[v["status"].isin(sts)]
        if urlq:
            v = v[v["urls_text"].str.contains(urlq, case=False, regex=False) | v["affected"].str.contains(urlq, case=False, regex=False)]
        if tys:
            v = v[v["type"].isin(tys)]
        st.markdown(f"**{len(v)}** of {len(df_all)} findings")
        tbl = v[["id", "title", "category", "priority", "status", "type", "affected", "first_url"]].copy()
        tbl["priority"] = tbl["priority"].astype(str)
        st.dataframe(tbl, hide_index=True, width="stretch",
                     column_config={"first_url": st.column_config.LinkColumn("Example URL", display_text=r"https://springfieldproperties\.ae(.*)"),
                                    "title": st.column_config.TextColumn("Finding", width="large"),
                                    "id": "ID", "category": "Category", "priority": "Priority", "status": "Status",
                                    "type": "Type", "affected": "Affected"})
        x1, x2 = st.columns(2)
        exp = export_frame(v)
        x1.download_button("Export filtered findings (CSV)", exp.to_csv(index=False).encode("utf-8"), "springfield_findings_filtered.csv", "text/csv",
                           width="stretch")
        x2.download_button("Export filtered findings (Excel)", to_excel({"Findings": exp}), "springfield_findings_filtered.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", width="stretch")
        st.markdown("**Details**")
        for _, r in v.iterrows():
            finding_card(findings_by_id[r["id"]])

    elif dataset == "Page-level website errors":
        e = errors_df.copy()
        e1, e2, e3 = st.columns([1.6, 1, 1])
        q = e1.text_input("Search text or URL", key="er_q", placeholder="e.g. Flexiable, 750,000, /blog/")
        cats = e2.multiselect("Category", sorted(e["category"].unique()), key="er_cat")
        sev = e3.multiselect("Severity", ["High", "Medium", "Low"], key="er_sev")
        if q:
            blob = (e["page"].astype(str) + " " + e["text_found"].astype(str) + " " + e["correction"].astype(str)).str.lower()
            e = e[blob.str.contains(q.lower(), regex=False)]
        if cats:
            e = e[e["category"].isin(cats)]
        if sev:
            e = e[e["severity"].isin(sev)]
        st.markdown(f"**{len(e)}** of {len(errors_df)} page-level errors (from Springfield_Website_Errors_Audit.xlsx)")
        sc = errors_df.groupby(["category", "severity"]).size().reset_index(name="count")
        fig = px.bar(sc, x="category", y="count", color="severity", title="Page-level errors by category",
                     color_discrete_map={"High": "#FFAE42", "Medium": "#F2D35B", "Low": "#5CC8FF"},
                     category_orders={"severity": ["High", "Medium", "Low"]})
        fig.update_layout(xaxis_title=None, yaxis_title="Rows")
        st.plotly_chart(style_fig(fig, 260), width="stretch")
        e_show = e[["category", "severity", "page", "where", "text_found", "correction", "source"]]
        st.dataframe(e_show, hide_index=True, width="stretch", height=460,
                     column_config={"page": st.column_config.LinkColumn("Page", display_text=r"https://springfieldproperties\.ae(.*)"),
                                    "text_found": st.column_config.TextColumn("Text found on site", width="large"),
                                    "correction": st.column_config.TextColumn("Suggested correction", width="large")})
        x1, x2 = st.columns(2)
        x1.download_button("Export filtered errors (CSV)", e_show.to_csv(index=False).encode("utf-8"), "springfield_errors_filtered.csv", "text/csv",
                           width="stretch")
        x2.download_button("Export all audit data (Excel)",
                           to_excel({"Findings": export_frame(df_all), "Website errors": errors_df, "Brand variants": brand_df,
                                     "Placeholder titles": placeholder_df, "Cut-off descriptions": cutoff_df}),
                           "springfield_audit_all_data.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           width="stretch")

    elif dataset == "Placeholder titles":
        st.markdown(f"**{len(placeholder_df)}** pages with an unfilled placeholder in the title tag (finding F04)")
        ptype = placeholder_df["url"].str.extract(r"springfieldproperties\.ae/([^/]+)/")[0].fillna("other")
        fig = px.histogram(ptype.to_frame("section"), x="section", title="By site section", color_discrete_sequence=["#FFAE42"])
        fig.update_layout(xaxis_title=None, yaxis_title="Pages")
        st.plotly_chart(style_fig(fig, 240), width="stretch")
        st.dataframe(placeholder_df[["url", "problem", "fix"]], hide_index=True, width="stretch",
                     column_config={"url": st.column_config.LinkColumn("Page", display_text=r"https://springfieldproperties\.ae(.*)")})
        st.download_button("Export (CSV)", placeholder_df.to_csv(index=False).encode("utf-8"), "placeholder_titles.csv", "text/csv")

    else:
        st.markdown(f"**{len(cutoff_df)}** examples shown · **249** listing meta descriptions end mid-word site-wide (finding F07). "
                    "One template fix corrects all of them.")
        st.dataframe(cutoff_df[["url", "cut_word", "description_end"]], hide_index=True, width="stretch",
                     column_config={"url": st.column_config.LinkColumn("Listing", display_text=r"https://springfieldproperties\.ae(.*)"),
                                    "cut_word": "Cut-off word", "description_end": st.column_config.TextColumn("End of meta description", width="large")})
        st.download_button("Export (CSV)", cutoff_df.to_csv(index=False).encode("utf-8"), "cutoff_descriptions.csv", "text/csv")

st.markdown(
    f'<div style="color:{MUTED};font-size:12px;margin-top:28px;border-top:1px solid {LINE};padding-top:12px">'
    "Springfield Properties SEO, AEO & GEO audit · Live site audited 28 October 2026 · Prepared by Ali Naseh. "
    "No traffic, rankings, search volumes or AI citation counts are estimated; unavailable metrics are labelled as such.</div>",
    unsafe_allow_html=True,
)
