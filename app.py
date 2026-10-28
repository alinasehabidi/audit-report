"""
Springfield Properties – Website & AI Search Audit
A guided presentation for management, prepared by Ali Naseh (audit date: 28 October 2026).

Story: what I checked → what I found → why it matters → how I'd fix it → what else I can do.
All findings live in /data so they can be edited without touching this code.
Nothing is estimated: metrics that need company access are shown as unavailable.
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

st.set_page_config(page_title="Springfield Properties · Website & AI Search Audit", page_icon="🏢",
                   layout="wide", initial_sidebar_state="collapsed")

DATA = Path(__file__).parent / "data"
SITE = "https://springfieldproperties.ae"

# Palette taken from Springfield's navy-and-white logo and site.
NAVY = "#0B1F3A"
NAVY_2 = "#16325C"
INK = "#13233F"
MUTED = "#5E6B80"
LINE = "#E3E7EE"
BG = "#F6F7F9"
WHITE = "#FFFFFF"
ACCENT = "#2E5C9E"
GOOD = "#2F855A"
PRIORITY_COLORS = {"Critical": "#B42318", "High": "#C4661F", "Medium": "#B08900", "Low": "#4A6FA5"}
PRIORITY_ORDER = ["Critical", "High", "Medium", "Low"]
STATUS_OPTIONS = ["Open", "In progress", "Fixed", "Won't fix"]
OWNER_LABEL = {"Independent": "I can do this", "Developer": "Needs a developer", "Company access": "Needs your access or sign-off"}


@st.cache_data
def load_json(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


@st.cache_data
def load_csv(name):
    return pd.read_csv(DATA / name)


findings_raw = load_json("findings.json")
roadmap = load_json("roadmap.json")
kpis = load_json("kpis.json")
growth = load_json("growth_services.json")
errors_df = load_csv("website_errors.csv")
brand_df = load_csv("brand_variants.csv")
placeholder_df = load_csv("placeholder_titles.csv")
cutoff_df = load_csv("cutoff_descriptions.csv")
FBY = {f["id"]: f for f in findings_raw}

if "status" not in st.session_state:
    st.session_state.status = {f["id"]: f.get("status", "Open") for f in findings_raw}


def findings_df():
    df = pd.DataFrame(findings_raw)
    df["status"] = df["id"].map(st.session_state.status)
    df["priority"] = pd.Categorical(df["priority"], PRIORITY_ORDER, ordered=True)
    df["urls_text"] = df["urls"].apply(lambda u: "\n".join(u))
    df["first_url"] = df["urls"].apply(lambda u: u[0] if u else "")
    return df.sort_values(["priority", "id"]).reset_index(drop=True)


df_all = findings_df()

# ─────────────────────────── Style ───────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Cormorant+Garamond:wght@600;700&display=swap');
html, body, .stApp, [class*="css"] {{ font-family: 'Inter', sans-serif; }}
.stApp {{ background: {BG}; color: {INK}; }}
.block-container {{ padding-top: 1.2rem; padding-bottom: 3rem; max-width: 1240px; }}
h1, h2, h3, h4 {{ color: {NAVY}; }}
a {{ color: {ACCENT} !important; }}
header[data-testid="stHeader"] {{ background: transparent; }}

.hero {{ background: linear-gradient(120deg, {NAVY} 0%, {NAVY_2} 70%, #24477C 100%); color: {WHITE};
        border-radius: 20px; padding: 40px 44px; margin-bottom: 22px; position: relative; overflow: hidden; }}
.hero:before {{ content: ""; position: absolute; inset: auto -80px -120px auto; width: 420px; height: 420px; border-radius: 50%;
               border: 1px solid rgba(255,255,255,.12); }}
.hero:after {{ content: ""; position: absolute; inset: auto 40px -160px auto; width: 300px; height: 300px; border-radius: 50%;
              border: 1px solid rgba(255,255,255,.08); }}
.brand {{ font-weight: 700; letter-spacing: .22em; font-size: 12px; text-transform: uppercase; opacity: .85; }}
.hero h1 {{ font-family: 'Cormorant Garamond', serif; font-size: 46px; line-height: 1.08; color: {WHITE}; margin: 10px 0 12px; max-width: 900px; }}
.hero p {{ font-size: 17px; line-height: 1.55; color: rgba(255,255,255,.86); max-width: 820px; margin: 0; }}
.hero .by {{ margin-top: 18px; font-size: 13px; color: rgba(255,255,255,.7); }}

.kpi {{ background: {WHITE}; border: 1px solid {LINE}; border-radius: 16px; padding: 20px 22px; height: 100%; }}
.kpi .n {{ font-family: 'Cormorant Garamond', serif; font-size: 44px; font-weight: 700; color: {NAVY}; line-height: 1; }}
.kpi .l {{ font-size: 14.5px; color: {INK}; margin-top: 8px; font-weight: 600; }}
.kpi .s {{ font-size: 13px; color: {MUTED}; margin-top: 4px; }}

.step {{ background: {WHITE}; border: 1px solid {LINE}; border-radius: 16px; padding: 20px; height: 100%; }}
.step .num {{ width: 30px; height: 30px; border-radius: 50%; background: {NAVY}; color: {WHITE}; display: flex; align-items: center;
             justify-content: center; font-weight: 700; font-size: 14px; margin-bottom: 10px; }}
.step h4 {{ margin: 0 0 6px; font-size: 17px; }}
.step p {{ margin: 0; color: {MUTED}; font-size: 14px; line-height: 1.5; }}
.step .go {{ margin-top: 10px; font-size: 13px; color: {ACCENT}; font-weight: 600; }}

.issue {{ background: {WHITE}; border: 1px solid {LINE}; border-left: 5px solid var(--c); border-radius: 14px; padding: 20px 22px; margin-bottom: 14px; }}
.issue h3 {{ margin: 6px 0 8px; font-size: 20px; }}
.issue .row {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 18px; margin-top: 10px; }}
.issue .k {{ font-size: 12px; text-transform: uppercase; letter-spacing: .08em; color: {MUTED}; font-weight: 600; }}
.issue .v {{ font-size: 14.5px; color: {INK}; margin-top: 3px; line-height: 1.5; }}
.example {{ background: {BG}; border: 1px dashed #C9D1DD; border-radius: 10px; padding: 10px 14px; font-family: ui-monospace, Menlo, monospace;
           font-size: 13px; color: {INK}; margin-top: 8px; }}
.pill {{ display: inline-block; padding: 3px 11px; border-radius: 999px; font-size: 12px; font-weight: 600; margin-right: 6px; }}
.tag {{ display: inline-block; padding: 3px 10px; border-radius: 999px; font-size: 12px; margin-right: 6px; background: #EEF2F8; color: {NAVY_2}; }}

.section {{ font-family: 'Cormorant Garamond', serif; font-size: 32px; color: {NAVY}; font-weight: 700; margin: 6px 0 4px; }}
.lead {{ font-size: 16.5px; color: {INK}; line-height: 1.6; max-width: 900px; margin-bottom: 18px; }}
.note {{ background: #EEF3FA; border-left: 4px solid {NAVY}; border-radius: 8px; padding: 12px 16px; font-size: 14.5px; color: {INK}; }}
.warn {{ background: #FFF6E8; border-left: 4px solid #C4661F; border-radius: 8px; padding: 12px 16px; font-size: 14.5px; color: {INK}; }}
.good {{ background: #EDF7F1; border-left: 4px solid {GOOD}; border-radius: 8px; padding: 12px 16px; font-size: 14.5px; color: {INK}; }}

.phase {{ background: {WHITE}; border: 1px solid {LINE}; border-radius: 16px; padding: 20px; height: 100%; border-top: 5px solid {NAVY}; }}
.phase .when {{ font-size: 12px; text-transform: uppercase; letter-spacing: .1em; color: {MUTED}; font-weight: 700; }}
.phase h4 {{ margin: 6px 0 8px; font-size: 18px; }}
.phase ul {{ padding-left: 18px; margin: 0; color: {INK}; font-size: 14px; }}
.phase .out {{ margin-top: 12px; font-size: 13.5px; color: {GOOD}; font-weight: 600; }}

.svc {{ background: {WHITE}; border: 1px solid {LINE}; border-radius: 16px; padding: 20px; height: 100%; }}
.svc h4 {{ margin: 6px 0 6px; font-size: 17px; }}
.svc p {{ margin: 0 0 8px; color: {INK}; font-size: 14px; line-height: 1.5; }}
.svc .why {{ color: {MUTED}; }}
.svc .meta {{ font-size: 12.5px; color: {MUTED}; border-top: 1px solid {LINE}; padding-top: 8px; margin-top: 6px; }}
.ev-Proven {{ background: #E3F2E9; color: {GOOD}; }}
.ev-Emerging {{ background: #FFF1DD; color: #A35A12; }}

.glossary {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }}
.gl {{ background: {WHITE}; border: 1px solid {LINE}; border-radius: 14px; padding: 16px 18px; }}
.gl b {{ color: {NAVY}; font-size: 15px; }}
.gl div {{ color: {MUTED}; font-size: 14px; margin-top: 4px; line-height: 1.45; }}

.stTabs [role="tablist"] {{ gap: 6px; border-bottom: 1px solid {LINE}; flex-wrap: wrap; }}
.stTabs [role="tab"] {{ color: {MUTED}; padding: 10px 16px; border-radius: 10px 10px 0 0; font-weight: 500; }}
.stTabs [aria-selected="true"] {{ color: {NAVY} !important; background: {WHITE}; border-bottom: 3px solid {NAVY} !important; font-weight: 700; }}
[data-testid="stExpander"] {{ background: {WHITE}; border: 1px solid {LINE}; border-radius: 12px; }}
div[data-testid="stDownloadButton"] button {{ background: {NAVY}; color: {WHITE}; border: none; }}
div[data-testid="stDownloadButton"] button:hover {{ background: {NAVY_2}; color: {WHITE}; }}

@media (max-width: 900px) {{
  .hero {{ padding: 28px 22px; }} .hero h1 {{ font-size: 32px; }}
  .issue .row, .glossary {{ grid-template-columns: 1fr; }}
}}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────── Helpers ───────────────────────────
def pill(priority):
    c = PRIORITY_COLORS.get(priority, MUTED)
    return f'<span class="pill" style="background:{c}1A;color:{c}">{priority}</span>'


def kpi_row(items):
    cols = st.columns(len(items))
    for col, (n, label, sub) in zip(cols, items):
        col.markdown(f'<div class="kpi"><div class="n">{n}</div><div class="l">{label}</div><div class="s">{sub}</div></div>',
                     unsafe_allow_html=True)


def section(title, lead=""):
    st.markdown(f'<div class="section">{title}</div>', unsafe_allow_html=True)
    if lead:
        st.markdown(f'<div class="lead">{lead}</div>', unsafe_allow_html=True)


def style_fig(fig, height=320):
    fig.update_layout(template="plotly_white", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(family="Inter, sans-serif", color=INK, size=13), height=height,
                      margin=dict(l=10, r=10, t=60, b=10), title=dict(x=0, y=0.97, yanchor="top", font=dict(size=15, color=NAVY)),
                      legend=dict(orientation="h", yanchor="bottom", y=1.0, x=0, title_text=""))
    fig.update_xaxes(gridcolor=LINE, zerolinecolor=LINE)
    fig.update_yaxes(gridcolor=LINE, zerolinecolor=LINE)
    return fig


def short(url):
    return url.replace(SITE, "") or "/"


def to_excel(frames):
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        for name, d in frames.items():
            d.to_excel(xw, sheet_name=name[:31], index=False)
    return buf.getvalue()


def export_frame(df):
    cols = ["id", "title", "type", "category", "priority", "status", "owner", "phase", "affected", "urls_text", "evidence",
            "impact", "solution", "dependencies", "effort", "role", "success_metric", "validation"]
    out = df[cols].copy()
    out["priority"] = out["priority"].astype(str)
    out["owner"] = out["owner"].map(OWNER_LABEL)
    return out.rename(columns={"urls_text": "urls"})


def proof(ids):
    """Expandable technical proof for the team."""
    with st.expander("See the proof and affected pages"):
        for fid in ids:
            f = FBY[fid]
            st.markdown(f"**{fid} · {f['title']}**")
            st.markdown(f["evidence"])
            if f["urls"]:
                st.markdown("\n".join(f"- [{short(u)}]({u})" for u in f["urls"][:10]))
            st.caption(f"How we'll know it's fixed: {f['success_metric']} · Check: {f['validation']}")


# ─────────────────────────── Hero ───────────────────────────
st.markdown(f"""
<div class="hero">
  <div class="brand">Springfield Properties · Website & AI Search Audit</div>
  <h1>Your website is strong. A few fixable errors are costing you trust and visibility.</h1>
  <p>I checked all 748 pages of springfieldproperties.ae. Here is what buyers, Google and AI assistants like ChatGPT see today,
  what I would fix first, and how I would get Springfield named more often when people ask for a Dubai agency.</p>
  <div class="by">Prepared by Ali Naseh · Marketing Technology & AI Specialist candidate · Audit date 28 October 2026</div>
</div>
""", unsafe_allow_html=True)

tabs = st.tabs(["1 · Overview", "2 · What I found", "3 · AI search check", "4 · My 90-day plan", "5 · What else I can do",
                "6 · Details for the team"])

# ═══════════════════════════ 1. OVERVIEW ═══════════════════════════
with tabs[0]:
    kpi_row([
        ("748", "pages checked", "Every page in the website's sitemap"),
        ("7", "problems that matter", "Out of 41 items logged for the team"),
        ("48 h", "to fix the most serious", "Mostly content edits, no rebuild"),
        ("1 in 10", "AI share of voice", "How often AI assistants name Springfield (one external tool)"),
    ])
    st.write("")
    section("Search has changed: three places buyers now find you",
            "Buyers no longer just scroll Google. They read Google's instant answers and ask AI assistants. Each needs the website to be accurate and consistent.")
    st.markdown("""
<div class="glossary">
  <div class="gl"><b>SEO · Google search</b><div>Showing up when someone searches "2 bed apartment Dubai Hills for sale".</div></div>
  <div class="gl"><b>AEO · Instant answers</b><div>Being the answer Google, Siri or Alexa reads out for "How much do I need for a Golden Visa?".</div></div>
  <div class="gl"><b>GEO · AI assistants</b><div>Being named when someone asks ChatGPT or Gemini "Which agency should I use in Dubai?".</div></div>
</div>""", unsafe_allow_html=True)
    st.write("")
    section("The story in four steps")
    s = st.columns(4)
    steps = [
        ("What I found", "Outdated visa rules, a wrong licence number, broken Google titles and the company name written 15+ ways.", "Tab 2"),
        ("How AI sees you", "AI assistants speak well of Springfield but rarely mention it: 1 in 10 on share of voice.", "Tab 3"),
        ("How I'd fix it", "Serious errors in 48 hours, templates in 2 weeks, content and authority over 90 days.", "Tab 4"),
        ("What else I can do", "Press features, rankings, Wikipedia readiness, reviews, video and community answers.", "Tab 5"),
    ]
    for i, (col, (t, p, go_)) in enumerate(zip(s, steps), 1):
        col.markdown(f'<div class="step"><div class="num">{i}</div><h4>{t}</h4><p>{p}</p><div class="go">See {go_} →</div></div>',
                     unsafe_allow_html=True)
    st.write("")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="good"><b>What is already working</b><br>'
                    "• Google and AI tools can read the whole site<br>"
                    "• Clear, honest area guides and project FAQs<br>"
                    "• Springfield publishes its own market data, which most agencies don't<br>"
                    "• 18 years of history, RERA licensed, awards from major developers</div>", unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="warn"><b>What is holding it back</b><br>'
                    "• Some pages give buyers outdated visa rules<br>"
                    "• Errors visible in Google results and on listings<br>"
                    "• The company name is inconsistent across the web<br>"
                    "• Market reports stopped after May 2026</div>", unsafe_allow_html=True)
    st.write("")
    st.markdown('<div class="note"><b>My recommendation:</b> fix accuracy first (48 hours), then the listing templates (2 weeks), '
                "then turn Springfield's own data and expert agents into content other sites and AI tools quote (90 days). "
                "Measure from day one and set targets only after a 4-week baseline.</div>", unsafe_allow_html=True)

# ═══════════════════════════ 2. WHAT I FOUND ═══════════════════════════
ISSUES = [
    dict(p="Critical", t="Some pages give buyers outdated visa rules",
         ex="“Purchases starting from AED 750,000 can qualify for an investor visa” — on 9 pages",
         what="The AED 750,000 minimum for the 2-year property visa was removed in April 2026. Springfield's own Q2 2026 report says so. Older guides also describe rules that no longer apply, such as an AED 10 million Golden Visa threshold.",
         risk="Buyers make decisions on wrong information; it undermines trust in Springfield's expertise.",
         fix="One verified visa answer used on every page, checked with DLD. About 1–2 days.", ids=["F01", "F02"]),
    dict(p="Critical", t="Wrong licence number on 3 listings",
         ex="“RERA ORN: 1192” instead of 11929",
         what="A missing digit in the RERA licence number on three listings.",
         risk="Regulatory accuracy on a licence number.", fix="Correct 3 listings today; lock the licence line so agents can't retype it. 30 minutes.",
         ids=["F03"]),
    dict(p="High", t="Broken page titles showing in Google",
         ex="“Off Plan Properties Dubai %currentyear% | New Launches & Prices”",
         what="28 pages, including the main off-plan page and 12 developer pages, show unfinished code in the title buyers see on Google.",
         risk="Looks careless on the pages that matter most for new launches.", fix="One template fix by a developer. Half a day.", ids=["F04"]),
    dict(p="High", t="The company name is written 15+ different ways",
         ex="“Spring Field Properties LLC SOC” · “Springfield Real Estate” · “SPRING FIELD REAL ESTATE”",
         what="281 pages (mostly listings) use a different name from the website's “Springfield Properties”. One listing shows four versions.",
         risk="Google and AI tools are less sure these all mean one company, so Springfield is named less often.",
         fix="Confirm the legal name, then fix it once at the source (CRM) and on the website. 2–3 days.", ids=["F05"]),
    dict(p="High", t="Listing pages lose clicks before buyers arrive",
         ex="Title today: “Modern 2BR Living | Parkwood Dubai Hills Estate, Dubai Hills Estate, Dubai”",
         what="Listing titles repeat the location, 249 descriptions are cut mid-word, shared links show no property photo, images have no descriptions, and listings don't link to the project or area guide.",
         risk="Fewer clicks from Google and WhatsApp shares; weaker pages for “2 bed in Parkwood” searches.",
         fix="Redesign the listing template once: “2 Bed Apartment for Sale in Parkwood, Dubai Hills Estate”. 3–4 developer days.",
         ids=["F07", "F08", "F11", "F12", "F13"]),
    dict(p="High", t="Market reports stopped after May 2026",
         ex="Newest monthly report: May 2026 · no Q3 2026 report",
         what="Springfield's own transaction data is its most quotable asset, but publishing has paused and report pages have no date or named analyst.",
         risk="Journalists and AI tools quote whoever publishes current data.", fix="Publish the missing reports with a date and named analyst; keep a monthly rhythm.",
         ids=["F10"]),
    dict(p="High", t="Contact details disagree between pages",
         ex="Privacy policy: info@springfield-re.com, +971 4 4542588 · Contact page: info@springfieldproperties.ae, +971 50 631 9606",
         what="The privacy policy lists a different email domain, two other phone numbers and different office numbers.",
         risk="Conflicting business details confuse Google, AI tools and clients.", fix="Update after confirming which are current. 1 hour.", ids=["F06"]),
]

with tabs[1]:
    section("What I found",
            "Seven problems matter most. Each one is real, shown with an example from the live site, and has a clear fix. "
            "The full list of 41 items is in tab 6 for the marketing team.")
    for it in ISSUES:
        c = PRIORITY_COLORS[it["p"]]
        st.markdown(f"""
<div class="issue" style="--c:{c}">
  {pill(it['p'])}
  <h3>{it['t']}</h3>
  <div class="example">{it['ex']}</div>
  <div class="row">
    <div><div class="k">What's happening</div><div class="v">{it['what']}</div></div>
    <div><div class="k">Why it matters</div><div class="v">{it['risk']}</div></div>
    <div><div class="k">The fix</div><div class="v">{it['fix']}</div></div>
  </div>
</div>""", unsafe_allow_html=True)
        proof(it["ids"])
        st.write("")

# ═══════════════════════════ 3. AI SEARCH CHECK ═══════════════════════════
with tabs[2]:
    section("How AI assistants see Springfield",
            "When people ask AI tools for a Dubai agency, Springfield is rarely named. When it is, what they say is positive. "
            "The opportunity is visibility, not reputation.")
    ag = kpis["ai_grader"]
    c1, c2 = st.columns([1.1, 1])
    with c1:
        ov = pd.DataFrame({"Assistant": list(ag["overall"].keys()), "Score": list(ag["overall"].values())})
        fig = px.bar(ov, x="Score", y="Assistant", orientation="h", text="Score", title="AI search score out of 100",
                     color_discrete_sequence=[NAVY])
        fig.update_traces(textposition="outside", cliponaxis=False)
        fig.update_layout(xaxis_range=[0, 100], yaxis_title=None, xaxis_title=None)
        st.plotly_chart(style_fig(fig, 260), width="stretch")
        comp = pd.DataFrame(ag["components"])
        comp["Average %"] = ((comp["ChatGPT"] + comp["Perplexity"] + comp["Gemini"]) / 3 / comp["max"] * 100).round(0)
        fig = px.bar(comp.sort_values("Average %"), x="Average %", y="component", orientation="h", text="Average %",
                     title="Where the score comes from (average of the three, % of maximum)",
                     color="Average %", color_continuous_scale=[[0, "#B42318"], [0.5, "#C4661F"], [1, GOOD]])
        fig.update_traces(texttemplate="%{text:.0f}%", textposition="outside", cliponaxis=False)
        fig.update_layout(coloraxis_showscale=False, yaxis_title=None, xaxis_title=None, xaxis_range=[0, 100])
        st.plotly_chart(style_fig(fig, 280), width="stretch")
    with c2:
        st.markdown('<div class="good"><b>Good news:</b> sentiment is the strongest score (50–83%). When AI tools describe Springfield, they describe it well.</div>',
                    unsafe_allow_html=True)
        st.write("")
        st.markdown('<div class="warn"><b>The gap:</b> share of voice is 1 out of 10 on all three assistants. Competitors are named instead.</div>',
                    unsafe_allow_html=True)
        st.write("")
        st.markdown("**Why this happens**")
        st.markdown(
            "1. **Mixed identity.** Springfield appears under several names, so AI tools are less sure it's one company.\n"
            "2. **Few mentions elsewhere.** AI answers lean on rankings, press and directories; Springfield is missing from the main agency lists.\n"
            "3. **Little fresh, quotable data.** Reports paused in May 2026, without dates or named experts."
        )
        st.markdown("**What moves it**")
        st.markdown("Fix the identity (tab 4) · get listed and featured elsewhere (tab 5) · publish dated data from named experts.")
        st.caption(f"Source: {ag['source']}. ChatGPT scores lowest; it relies heavily on Bing, so Bing Webmaster Tools is part of the plan.")

# ═══════════════════════════ 4. 90-DAY PLAN ═══════════════════════════
with tabs[3]:
    section("My 90-day plan", "Fix what is wrong first, then build what makes Springfield quoted. Each phase ends with something you can check.")
    phases = roadmap["phases"]
    plain = {
        "48 hours": ("Stop the damage", ["Correct visa pages and licence numbers", "Fix broken Google titles", "Align contact details", "Capture today's baseline"]),
        "14 days": ("Fix the templates", ["New listing titles and descriptions", "One company name everywhere", "Area guides get real numbers", "Track every call, form and WhatsApp"]),
        "30 days": ("Become the source", ["One trusted visa guide and cost guide", "Q3 market report with a named analyst", "Expert author profiles", "Wikidata and ranking submissions"]),
        "90 days": ("Grow and measure", ["Monthly data and PR", "Arabic versions of top guides", "New landing pages where demand exists", "Monthly results report"]),
    }
    cols = st.columns(4)
    for col, p in zip(cols, phases):
        h, items = plain[p["key"]]
        col.markdown(f'<div class="phase"><div class="when">{p["label"]}</div><h4>{h}</h4><ul>'
                     + "".join(f"<li>{x}</li>" for x in items) + f'</ul><div class="out">✓ {p["outcome"]}</div></div>',
                     unsafe_allow_html=True)
    st.write("")
    start = st.date_input("Plan start date", value=date.today(), key="plan_start")
    g = []
    for p in phases:
        h, _ = plain[p["key"]]
        g.append(dict(Phase=f"{p['label']}: {h}", Start=start + timedelta(days=p["start_day"]),
                      Finish=start + timedelta(days=max(p["end_day"], p["start_day"] + 1))))
    gdf = pd.DataFrame(g)
    fig = px.timeline(gdf, x_start="Start", x_end="Finish", y="Phase", title="Timeline", color_discrete_sequence=[NAVY])
    fig.update_yaxes(autorange="reversed", title=None)
    st.plotly_chart(style_fig(fig, 240), width="stretch")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Who does the work**")
        oc = df_all.groupby("owner").size().reset_index(name="items")
        oc["owner"] = oc["owner"].map(OWNER_LABEL)
        fig = px.pie(oc, names="owner", values="items", hole=0.6, color_discrete_sequence=[NAVY, ACCENT, "#9FB3D1"])
        fig.update_traces(textinfo="value")
        st.plotly_chart(style_fig(fig, 280), width="stretch")
        st.caption("Of 41 logged items: I can do 10 myself, 15 need developer time, 16 need your access or sign-off.")
    with c2:
        st.markdown("**What I need from Springfield on day 1**")
        st.markdown(
            "- Website editor access\n- Google Search Console and Google Analytics\n- CRM / listing tool export\n"
            "- Google Business Profiles (both offices)\n- Property Finder and Bayut agency accounts\n"
            "- About 10–12 developer days over 90 days\n- Quick sign-off from compliance on visa wording"
        )
        st.markdown('<div class="note">Targets are agreed after a 4-week baseline. I won\'t promise percentages before we have real numbers.</div>',
                    unsafe_allow_html=True)

# ═══════════════════════════ 5. WHAT ELSE I CAN DO ═══════════════════════════
with tabs[4]:
    section("What else I can do", growth["intro"])
    services = growth["services"]
    groups = list(dict.fromkeys(s["group"] for s in services))
    kpi_row([
        (str(len(services)), "growth activities", "Beyond fixing the website"),
        (str(sum(s["evidence"] == "Proven" for s in services)), "proven methods", "Established search and PR practice"),
        (str(sum(s["evidence"] == "Emerging" for s in services)), "emerging methods", "Seen in AI answers; no guarantees"),
        ("0", "shortcuts", "No bought links, fake reviews or hidden edits"),
    ])
    st.write("")
    pick = st.segmented_control("Show", ["All"] + groups, default="All", key="growth_group") or "All"
    show = services if pick == "All" else [s for s in services if s["group"] == pick]
    for i in range(0, len(show), 2):
        cols = st.columns(2)
        for col, s in zip(cols, show[i:i + 2]):
            note = f'<p style="color:#A35A12;font-size:13px"><b>Honest note:</b> {s["note"]}</p>' if s.get("note") else ""
            col.markdown(
                f'<div class="svc"><span class="pill ev-{s["evidence"]}">{s["evidence"]}</span><span class="tag">{s["aeo_geo"]}</span>'
                f'<span class="tag">{s["group"]}</span><h4>{s["title"]}</h4>'
                f'<p>{s["what"]}</p><p class="why"><b>Why it helps:</b> {s["why"]}</p>{note}'
                f'<div class="meta">Effort: {s["effort"]} · First impact: {s["impact_time"]}</div></div>',
                unsafe_allow_html=True)
            with col.expander("How I'd do it"):
                st.markdown("\n".join(f"{n}. {x}" for n, x in enumerate(s["how"], 1)))
        st.write("")
    c1, c2 = st.columns([1.2, 1])
    with c1:
        st.markdown('<div class="note"><b>Wikipedia, honestly:</b> a page can only be approved when independent publications have written '
                    "about Springfield in depth. Today the coverage is mostly interviews and market quotes. I can create the Wikidata entry now, "
                    "build the press coverage, and submit a properly disclosed draft when the sources exist. Typical path: 6–12 months.</div>",
                    unsafe_allow_html=True)
    with c2:
        st.markdown("**What I won't do**")
        st.markdown("\n".join(f"- {w}" for w in growth["wont_do"]))
    st.caption("Proven = long-established search and PR practice. Emerging = widely observed in AI answers, but no search engine publishes how much it counts.")

# ═══════════════════════════ 6. DETAILS FOR THE TEAM ═══════════════════════════
with tabs[5]:
    section("Details for the marketing team",
            "Everything behind the summary: all 41 logged items, page-by-page errors, the company-name data and the measurement plan. Filter and export as needed.")
    view = st.segmented_control("Open", ["Issue tracker", "All evidence", "Company name data", "Measurement plan"],
                                default="Issue tracker", key="detail_view") or "Issue tracker"

    if view == "Issue tracker":
        f1, f2, f3 = st.columns([1.3, 1.3, 1])
        pr = f1.pills("Priority", PRIORITY_ORDER, selection_mode="multi", default=PRIORITY_ORDER, key="tr_pr")
        ty = f2.pills("Type", ["Verified problem", "Opportunity", "Needs access"], selection_mode="multi",
                      default=["Verified problem", "Opportunity", "Needs access"], key="tr_ty")
        stf = f3.multiselect("Status", STATUS_OPTIONS, default=STATUS_OPTIONS, key="tr_st")
        v = df_all[df_all["priority"].isin(pr or []) & df_all["type"].isin(ty or []) & df_all["status"].isin(stf)]
        done = int((df_all["status"] == "Fixed").sum())
        st.progress(done / len(df_all), text=f"{done} of {len(df_all)} items fixed · {len(v)} shown")
        edit = v[["id", "title", "priority", "category", "type", "effort", "owner", "phase", "status", "first_url"]].copy()
        edit["priority"] = edit["priority"].astype(str)
        edit["owner"] = edit["owner"].map(OWNER_LABEL)
        edited = st.data_editor(
            edit, hide_index=True, width="stretch", height=min(42 + 35 * len(edit), 620),
            disabled=["id", "title", "priority", "category", "type", "effort", "owner", "phase", "first_url"],
            column_config={"id": "ID", "title": st.column_config.TextColumn("Item", width="large"), "priority": "Priority",
                           "category": "Area", "type": "Type", "effort": "Effort", "owner": "Who", "phase": "Phase",
                           "status": st.column_config.SelectboxColumn("Status", options=STATUS_OPTIONS, required=True),
                           "first_url": st.column_config.LinkColumn("Example page", display_text=r"https://springfieldproperties\.ae(.*)")},
            key="tracker_editor")
        changed = False
        for _, r in edited.iterrows():
            if st.session_state.status.get(r["id"]) != r["status"]:
                st.session_state.status[r["id"]] = r["status"]
                changed = True
        if changed:
            del st.session_state["tracker_editor"]
            st.rerun()
        x1, x2 = st.columns(2)
        exp = export_frame(df_all[df_all["id"].isin(v["id"])])
        x1.download_button("Export tracker (CSV)", exp.to_csv(index=False).encode("utf-8"), "springfield_tracker.csv", "text/csv", width="stretch")
        x2.download_button("Export tracker (Excel)", to_excel({"Tracker": exp}), "springfield_tracker.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", width="stretch")
        st.caption("Status changes last while this page is open; export to keep them.")

    elif view == "All evidence":
        ds = st.radio("Dataset", ["Findings (41)", f"Page-level errors ({len(errors_df)})", f"Broken titles ({len(placeholder_df)})",
                                  f"Cut-off descriptions ({len(cutoff_df)} examples)"], horizontal=True, key="ev_ds")
        if ds.startswith("Findings"):
            e1, e2, e3, e4 = st.columns([1.6, 1, 1, 1])
            q = e1.text_input("Search", key="ex_q", placeholder="e.g. visa, ORN, Parkwood")
            cats = e2.multiselect("Area", sorted(df_all["category"].unique()), key="ex_cat")
            prs = e3.multiselect("Priority", PRIORITY_ORDER, key="ex_pr")
            urlq = e4.text_input("URL contains", key="ex_url", placeholder="/projects/")
            v = df_all.copy()
            if q:
                blob = (v["title"] + " " + v["evidence"] + " " + v["solution"] + " " + v["affected"]).str.lower()
                v = v[blob.str.contains(q.lower(), regex=False)]
            if cats:
                v = v[v["category"].isin(cats)]
            if prs:
                v = v[v["priority"].isin(prs)]
            if urlq:
                v = v[v["urls_text"].str.contains(urlq, case=False, regex=False) | v["affected"].str.contains(urlq, case=False, regex=False)]
            st.markdown(f"**{len(v)}** of {len(df_all)} items")
            for _, r in v.iterrows():
                f = FBY[r["id"]]
                with st.expander(f"{f['id']} · {f['title']} · {f['priority']} · {st.session_state.status[f['id']]}"):
                    st.markdown(pill(f["priority"]) + f'<span class="tag">{f["category"]}</span><span class="tag">{f["type"]}</span>'
                                f'<span class="tag">{OWNER_LABEL[f["owner"]]}</span>', unsafe_allow_html=True)
                    a, b = st.columns(2)
                    a.markdown(f"**Evidence**  \n{f['evidence']}\n\n**Impact**  \n{f['impact']}")
                    if f["urls"]:
                        a.markdown("**Pages**\n" + "\n".join(f"- [{short(u)}]({u})" for u in f["urls"][:10]))
                    b.markdown(f"**Fix**  \n{f['solution']}\n\n**Steps**\n" + "\n".join(f"{n}. {s}" for n, s in enumerate(f["steps"], 1)))
                    b.markdown(f"**Effort** {f['effort']} · **Role** {f['role']}  \n**Needs** {f['dependencies']}  \n"
                               f"**Success** {f['success_metric']}  \n**Check** {f['validation']}")
            exp = export_frame(v)
            x1, x2 = st.columns(2)
            x1.download_button("Export filtered (CSV)", exp.to_csv(index=False).encode("utf-8"), "springfield_findings.csv", "text/csv", width="stretch")
            x2.download_button("Export all audit data (Excel)",
                               to_excel({"Findings": export_frame(df_all), "Website errors": errors_df, "Brand variants": brand_df,
                                         "Placeholder titles": placeholder_df, "Cut-off descriptions": cutoff_df}),
                               "springfield_audit_all_data.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", width="stretch")
        elif ds.startswith("Page-level"):
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
            show = e[["category", "severity", "page", "where", "text_found", "correction", "source"]]
            st.dataframe(show, hide_index=True, width="stretch", height=480,
                         column_config={"page": st.column_config.LinkColumn("Page", display_text=r"https://springfieldproperties\.ae(.*)"),
                                        "category": "Category", "severity": "Severity", "where": "Where", "source": "Source",
                                        "text_found": st.column_config.TextColumn("Text on site", width="large"),
                                        "correction": st.column_config.TextColumn("Correction", width="large")})
            st.download_button("Export (CSV)", show.to_csv(index=False).encode("utf-8"), "springfield_errors.csv", "text/csv")
        elif ds.startswith("Broken titles"):
            st.dataframe(placeholder_df[["url", "problem", "fix"]], hide_index=True, width="stretch",
                         column_config={"url": st.column_config.LinkColumn("Page", display_text=r"https://springfieldproperties\.ae(.*)"),
                                        "problem": "Problem", "fix": "Fix"})
        else:
            st.caption("249 listing descriptions end mid-word site-wide; one template fix corrects all of them.")
            st.dataframe(cutoff_df[["url", "cut_word", "description_end"]], hide_index=True, width="stretch",
                         column_config={"url": st.column_config.LinkColumn("Listing", display_text=r"https://springfieldproperties\.ae(.*)"),
                                        "cut_word": "Cut word", "description_end": st.column_config.TextColumn("End of description", width="large")})

    elif view == "Company name data":
        long = brand_df.assign(variant=brand_df["variants"].str.split("; ")).explode("variant")
        long["variant"] = long["variant"].str.strip()
        kpi_row([(str(len(brand_df)), "pages affected", "of 748 checked"), (str(long["variant"].nunique()), "different spellings", "exact versions found"),
                 ("1", "approved name", "Springfield Properties")])
        st.write("")
        vc = long.groupby("variant")["url"].nunique().reset_index(name="pages").sort_values("pages")
        fig = px.bar(vc, x="pages", y="variant", orientation="h", text="pages", title="Pages using each version of the name",
                     color_discrete_sequence=[NAVY])
        fig.update_traces(textposition="outside", cliponaxis=False)
        fig.update_layout(yaxis_title=None, xaxis_title=None, xaxis_range=[0, vc["pages"].max() * 1.15])
        st.plotly_chart(style_fig(fig, 540), width="stretch")
        st.markdown('<div class="warn"><b>Before changing legal text:</b> the site shows both "Springfield Properties L.L.C S.O.C" and '
                    '"SPRING FIELD PROPERTIES L.L.C S.O.C", and Property Finder lists "Springfield Real Estate". Confirm the legal name on the trade licence first.</div>',
                    unsafe_allow_html=True)
        q = st.text_input("Search page or name", key="brand_q")
        b = brand_df if not q else brand_df[brand_df["url"].str.contains(q, case=False) | brand_df["variants"].str.contains(q, case=False)]
        st.dataframe(b[["url", "variants"]], hide_index=True, width="stretch", height=360,
                     column_config={"url": st.column_config.LinkColumn("Page", display_text=r"https://springfieldproperties\.ae(.*)"),
                                    "variants": st.column_config.TextColumn("Versions found", width="large")})
        st.download_button("Export (CSV)", b.to_csv(index=False).encode("utf-8"), "brand_variants.csv", "text/csv")

    else:
        st.markdown("**Measured during the audit** (website crawl, 28 Oct 2026)")
        mh = pd.DataFrame(kpis["measured_site_health"])
        st.dataframe(mh.rename(columns={"metric": "Metric", "value": "Value", "source": "Source"}), hide_index=True, width="stretch")
        st.markdown("**Not available yet: needs Springfield's access**")
        st.dataframe(pd.DataFrame(kpis["unavailable"]).rename(columns={"area": "Area", "metric": "Metric", "needs": "Source", "status": "Status"}),
                     hide_index=True, width="stretch")
        st.markdown(f'<div class="note"><b>How targets will be set:</b> {kpis["target_method"]}</div>', unsafe_allow_html=True)
        st.markdown("**Monthly report will track:** Google clicks and impressions by page type · Bing and Copilot visibility · page speed · "
                    "calls, forms and WhatsApp enquiries by page · qualified leads from the CRM · AI share of voice on 30 fixed buyer questions.")
        st.caption("Audit limits: page speed (Core Web Vitals) not measured; indexing, traffic and leads need Search Console, GA4 and CRM; "
                   "listing and project structured data not verified.")

st.markdown(f'<div style="color:{MUTED};font-size:12.5px;margin-top:30px;border-top:1px solid {LINE};padding-top:12px">'
            "Springfield Properties website and AI search audit · Live site checked 28 October 2026 · Prepared by Ali Naseh. "
            "No traffic, rankings or AI citation counts are estimated; anything that needs company access is labelled as unavailable.</div>",
            unsafe_allow_html=True)
