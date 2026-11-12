# Daily Market Brief Automation

An automated tool that curates, summarizes, and publishes daily market-moving news using RSS, Google Gemini AI, and GitHub Actions.

## Step-by-Step Setup Guide

### 1. Local Environment & VS Code
1. Open this folder in VS Code.
2. Open the VS Code terminal (`Ctrl + ~` or `Terminal -> New Terminal`).
3. Create a Python virtual environment:
   `python -m venv venv`
4. Activate the virtual environment:
   - **Windows:** `venv\Scripts\activate`
   - **Mac/Linux:** `source venv/bin/activate`
5. Install requirements:
   `pip install -r requirements.txt`

### 2. Getting Free API Keys
1. **Google Gemini:** Go to [Google AI Studio](https://aistudio.google.com/), sign in, and click "Get API Key". 
2. **Unsplash:** Go to [Unsplash Developers](https://unsplash.com/developers), register an app, and copy the "Access Key".
3. Rename `.env.example` to `.env` and paste your keys inside. 

### 3. Running Locally
- **Test run (no files created):** `python main.py --dry-run`
- **Full build:** `python main.py`
- **Preview site:** The HTML files will be in the `site/` folder. Right-click `site/index.html` in VS Code and select "Open in Default Browser".

### 4. Publishing on GitHub Pages
1. Push this code to a new public GitHub repository.
2. Go to your repository **Settings** -> **Secrets and variables** -> **Actions** -> **New repository secret**.
3. Add three secrets: `GEMINI_API_KEY`, `UNSPLASH_API_KEY`, and `PEXELS_API_KEY` with your respective keys.
4. Go to the **Actions** tab and click "Run workflow" on the *Daily News Generator*. Wait for it to finish.
5. Go to **Settings** -> **Pages**. Under "Source", select `Deploy from a branch`. Under branch, select `gh-pages` and `/ (root)`. Save.
6. Your live site will appear at `https://[your-username].github.io/[repo-name]/`.

### 5. Managing Free Tiers
- **Gemini (Free Tier):** Allows 15 requests per minute. Since our script bundles everything into *one* request a day, you will never hit this limit.
- **Unsplash (Demo Tier):** Allows 50 image requests per hour. We make ~5-8 requests a day. You are well within limits. 
- **If you hit limits:** The script handles errors gracefully. Gemini will retry 3 times. Unsplash will fall back to Pexels, and if that fails, it will use a static placeholder image so your site never breaks.