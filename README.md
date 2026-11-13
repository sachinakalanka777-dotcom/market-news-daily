# MarketPulse News – Daily US Market Briefing

Automated daily US stock-market news curation using public RSS feeds, Gemini AI, optional Groq backup, Unsplash images, and GitHub Actions. The workflow runs at 06:00 Sri Lanka time (00:30 UTC).

## What this version fixes/adds

- Fixes the previous `build_site()` bug: generated data is now passed into the builder instead of being discarded and replaced by an unrelated `data/daily_data.json` read.
- Gemini is the primary summarizer; Groq is an optional backup. If both are unavailable, the site still publishes publisher headlines/snippets and original links.
- Retries transient AI failures with short backoff; no 15-minute sleep that can exhaust the Actions job.
- Fetches multiple RSS sources independently, so one broken feed does not stop the build.
- Deduplicates canonical article URLs and filters market-relevant stories.
- AI output is mapped back to the original article ID. The AI cannot invent a source URL.
- Adds market-impact labels, categories, sector tags, archive pages, source health, generated time, and Unsplash attribution.

## 1. API keys you need

### Gemini (required)
1. Open https://aistudio.google.com/apikey
2. Sign in with your Google account.
3. Create an API key and copy it.
4. Do not paste it into source code or commit it to GitHub.

### Unsplash (optional, you already have this)
1. Open https://unsplash.com/developers and sign in.
2. Create a developer application.
3. Copy its **Access Key** (not the Secret Key).
4. Unsplash demo applications have request limits; this workflow requests one image per selected story. If the limit is reached, placeholder imagery is used. Follow Unsplash hotlinking and attribution requirements.

### Groq (optional backup – recommended)
1. Open https://console.groq.com/ and create/sign in to an account.
2. Open the API Keys page: https://console.groq.com/keys
3. Create a new key, copy it once, and store it securely.
4. Groq may ask you to verify your account or accept its terms. Availability, free usage and rate limits can change; check the console for the current limits.
5. Add it to GitHub as the secret `GROQ_API_KEY`. No Groq account/key is needed for the first deployment. Without it, the code falls back to publisher snippets if Gemini fails.

## 2. Add/update GitHub Actions secrets

Open your repository:
`Settings → Secrets and variables → Actions → Repository secrets`

Create or update:

| Secret name | Value | Required? |
|---|---|---|
| `GEMINI_API_KEY` | Your Google AI Studio API key | Yes |
| `UNSPLASH_API_KEY` | Your Unsplash Access Key | Optional (you already have it) |
| `GROQ_API_KEY` | Your Groq API key | Optional backup |

Never put API keys in `config.py`, HTML, JavaScript, or a public `.env` file. If a key was ever committed publicly, revoke it and create a new one.

## 3. Replace repository files

1. Download the updated project ZIP.
2. Extract it.
3. Open your existing GitHub repository `market-news-daily`.
4. Upload/replace the project files and folders from the extracted directory. Make sure the `.github/workflows/daily.yml` file is included. Do not upload your local `.env` file.
5. Commit the changes to the default branch (usually `main`).

## 4. GitHub Pages / custom domain

- Keep the current custom domain `marketpulsenews.online` in GitHub Pages settings.
- The workflow publishes the generated `site/` folder to the `gh-pages` branch and writes the CNAME file.
- If your repository currently uses a different Pages publishing method, check `Settings → Pages` and make sure it is compatible with deployment to `gh-pages`.
- Do not delete/change DNS records if the domain is already working.

## 5. Run a manual test

1. Open the repository **Actions** tab.
2. Select **MarketPulse Daily News**.
3. Click **Run workflow** → **Run workflow**.
4. Open the run and inspect each step. Green means successful; if it fails, expand the failed step and read its error.
5. When deploy succeeds, visit https://marketpulsenews.online/ and hard-refresh (`Ctrl + F5`).

## 6. Local test (optional)

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env  # Windows; then edit .env
# macOS/Linux: cp .env.example .env
python main.py --dry-run --skip-images
python main.py
```

## Important notes

- Scheduled GitHub Actions can start a few minutes later than the exact cron time because GitHub does not guarantee execution to the minute.
- The workflow cron is `30 0 * * *` = 06:00 Sri Lanka time. GitHub cron is UTC.
- RSS availability and publisher feed policies can change. A failed source is logged in the site health panel and does not stop other sources.
- News summaries and bullish/bearish/neutral labels are AI-assisted estimates, not predictions or financial advice. Always check original articles.
- This project uses RSS headlines and snippets. It does not scrape or republish full copyrighted articles.
