# ⭐ GithubStar

> Auto-updated daily leaderboard of the most starred GitHub projects.  
> Zero backend. Free forever. Emails delivered every morning.

**Live site:** [githubstar.vercel.app](https://githubstar.vercel.app)

---

## ✨ How it works

```
GitHub Actions (daily cron)
  └─► fetch_repos.py
        ├─► GitHub Search API  →  data/repos.json
        ├─► git commit + push
        └─► Gmail SMTP         →  📧 email digest to subscribers

Vercel detects push → auto-deploys index.html in ~30 seconds
```

---

## 🚀 Deploy in 5 minutes

### 1 · Fork & clone

```bash
git clone https://github.com/YOUR_USERNAME/githubstar
cd githubstar
```

### 2 · Deploy to Vercel (free)

1. Go to [vercel.com](https://vercel.com) → **New Project**
2. Import your forked GitHub repo
3. Framework: **Other** (it's a static site)
4. Click **Deploy** → done! Your site is live.

Vercel auto-deploys every time you push to `main`.

### 3 · Get a GitHub Personal Access Token

1. Go to [github.com/settings/tokens](https://github.com/settings/tokens)
2. **Generate new token (classic)**
3. Scope: ✅ `public_repo` (read-only is fine)
4. Copy the token

### 4 · Set up Gmail App Password (for email)

1. Enable 2FA on your Google account
2. Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
3. Create an app password for "Mail"
4. Copy the 16-character password

### 5 · Add GitHub Actions secrets

In your repo: **Settings → Secrets and variables → Actions → New repository secret**

| Secret name         | Value                              |
|---------------------|------------------------------------|
| `GH_PAT`            | Your GitHub personal access token  |
| `EMAIL_SENDER`      | your@gmail.com                     |
| `EMAIL_APP_PASSWORD`| Your Gmail app password            |
| `SUBSCRIBERS`       | email1@x.com,email2@x.com          |

### 6 · Test it manually

Go to **Actions → 🌟 Daily GitHub Stars Update → Run workflow**

That's it! The workflow will:
- Fetch top 30 repos
- Update `data/repos.json`
- Commit & push (triggers Vercel redeploy)
- Send email digest to subscribers

---

## ⚙️ Configuration

Edit `scripts/fetch_repos.py` to customize:

```python
TOP_N = 30           # How many repos to show
# Email shows top 10; site shows all TOP_N
```

The cron schedule is in `.github/workflows/daily-update.yml`:
```yaml
- cron: "0 8 * * *"   # Every day at 8:00 AM UTC
```

Change to any time you like: [crontab.guru](https://crontab.guru)

---

## 🗂 Project structure

```
githubstar/
├── index.html                          # Frontend (reads data/repos.json)
├── data/
│   └── repos.json                      # Auto-generated daily ← DO NOT edit
├── scripts/
│   └── fetch_repos.py                  # Fetcher + email sender
├── .github/
│   └── workflows/
│       └── daily-update.yml            # GitHub Actions cron job
├── vercel.json                         # Vercel routing config
└── README.md
```

---

## 📧 Email preview

Every morning subscribers get a digest with the top 10 repos, star counts, descriptions, and a link to the full site.

---

## 🛠 Local development

```bash
# Fetch data locally (needs GITHUB_TOKEN env var)
export GITHUB_TOKEN=ghp_xxxx
python scripts/fetch_repos.py

# Serve locally
python -m http.server 3000
# Open http://localhost:3000
```

---

## 📄 License

MIT — fork it, remix it, star it. ⭐
