# Springfield Properties – Website & AI Search Audit

A guided Streamlit presentation for management, built from the audit of https://springfieldproperties.ae/ (live site audited 28 October 2026).
Prepared by Ali Naseh.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Community Cloud

1. Create a GitHub repository and upload everything in this folder (keep the `data/` and `.streamlit/` folders).
2. Go to https://share.streamlit.io → **Create app** → pick the repository, branch `main`, main file `app.py`.
3. Click **Deploy**. No secrets are needed.

## Project structure

```
app.py                     Presentation (6 tabs: Overview, What I found, AI search check, 90-day plan, What else I can do, Details for the team)
requirements.txt           Python packages
.streamlit/config.toml     Navy-and-white theme based on Springfield's logo
data/findings.json         Findings register: 23 verified problems, 10 opportunities, 8 needs-access items
data/growth_services.json  'What else I can do' activities (edit to add or remove services)
data/roadmap.json          Phases (48 h, 14, 30, 90 days) and workstreams
data/kpis.json             Measured crawl metrics, third-party AI grader scores, unavailable metrics
data/website_errors.csv    74 page-level errors (from Springfield_Website_Errors_Audit.xlsx)
data/brand_variants.csv    281 pages with non-standard company names
data/placeholder_titles.csv  28 pages with %currentyear% / %sitename% in titles
data/cutoff_descriptions.csv 44 examples of listing descriptions cut mid-word
```

## Editing the data

- **Add or change a finding:** edit `data/findings.json`. Each finding has `id`, `type` (Verified problem / Opportunity / Needs access),
  `category`, `title`, `affected`, `urls`, `evidence`, `impact`, `solution`, `steps`, `dependencies`, `priority`
  (Critical / High / Medium / Low), `effort`, `role`, `owner` (Independent / Developer / Company access), `phase`
  (48 hours / 14 days / 30 days / 90 days), `success_metric`, `validation`, `status`.
- **Add real KPI data later:** add Search Console, GA4 or CRM figures to `data/kpis.json` and move the metric out of `unavailable`.
- Status changes made in the app last for the browser session only; use the export buttons to save them, then paste the
  statuses back into `findings.json` if you want them to persist.

## Data integrity

- No traffic, rankings, search volumes, Core Web Vitals or AI citation counts are estimated.
- AI visibility scores come from one third-party grader run on 28 Oct 2026 and are labelled as such.
