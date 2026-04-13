#!/usr/bin/env python3
"""
GithubStar - Daily Top Starred Repos Fetcher + Email Notifier
Fetches top GitHub repos by stars (recently pushed, high star count)
and sends a daily email digest to subscribers.

Required environment variables (set as GitHub Actions secrets):
  - GITHUB_TOKEN        : GitHub personal access token (for higher rate limits)
  - EMAIL_SENDER        : Gmail address to send from
  - EMAIL_APP_PASSWORD  : Gmail App Password (not your main password)
  - SUBSCRIBERS         : Comma-separated list of recipient emails
"""

import os
import json
import smtplib
import datetime
import urllib.request
import urllib.parse
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# ─── Config ───────────────────────────────────────────────────────────────────

GITHUB_TOKEN     = os.environ.get("GITHUB_TOKEN", "")
EMAIL_SENDER     = os.environ.get("EMAIL_SENDER", "")
EMAIL_PASSWORD   = os.environ.get("EMAIL_APP_PASSWORD", "")
SUBSCRIBERS_RAW  = os.environ.get("SUBSCRIBERS", "")
SUBSCRIBERS      = [e.strip() for e in SUBSCRIBERS_RAW.split(",") if e.strip()]

OUTPUT_FILE      = os.path.join(os.path.dirname(__file__), "../data/repos.json")
TOP_N            = 30   # How many repos to track

LANG_COLORS = {
    "Python":     "#3572A5",
    "JavaScript": "#f1e05a",
    "TypeScript": "#3178c6",
    "Go":         "#00ADD8",
    "Rust":       "#dea584",
    "Java":       "#b07219",
    "C++":        "#f34b7d",
    "C":          "#555555",
    "Ruby":       "#701516",
    "Swift":      "#F05138",
    "Kotlin":     "#7F52FF",
    "Shell":      "#89e051",
    "Markdown":   "#083fa1",
    "HTML":       "#e34c26",
    "CSS":        "#563d7c",
    "Dockerfile": "#384d54",
    "Jupyter Notebook": "#DA5B0B",
}

# ─── GitHub API ───────────────────────────────────────────────────────────────

def gh_request(url):
    """Make an authenticated GitHub API request."""
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "GithubStar-Bot/1.0")
    if GITHUB_TOKEN:
        req.add_header("Authorization", f"Bearer {GITHUB_TOKEN}")
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())


def fetch_top_repos():
    """Fetch top starred repositories using GitHub Search API."""
    # Search for repos with 10k+ stars, pushed recently
    cutoff = (datetime.date.today() - datetime.timedelta(days=365)).isoformat()
    query  = urllib.parse.quote(f"stars:>10000 pushed:>{cutoff}")
    url    = f"https://api.github.com/search/repositories?q={query}&sort=stars&order=desc&per_page={TOP_N}"

    print(f"Fetching top repos from GitHub API...")
    data  = gh_request(url)
    items = data.get("items", [])

    repos = []
    for i, item in enumerate(items, 1):
        lang = item.get("language") or "Other"
        repos.append({
            "rank":        i,
            "name":        item["name"],
            "full_name":   item["full_name"],
            "description": (item.get("description") or "")[:200],
            "stars":       item["stargazers_count"],
            "forks":       item["forks_count"],
            "language":    lang,
            "lang_color":  LANG_COLORS.get(lang, "#8b949e"),
            "url":         item["html_url"],
            "owner":       item["owner"]["login"],
            "avatar":      item["owner"]["avatar_url"],
            "topics":      item.get("topics", [])[:5],
            "pushed_at":   item.get("pushed_at", ""),
            "created_at":  item.get("created_at", ""),
        })
        print(f"  #{i:2d} {item['full_name']} ⭐ {item['stargazers_count']:,}")

    return repos


def save_data(repos):
    """Write repos list to data/repos.json."""
    payload = {
        "updated_at": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "updated_date": datetime.date.today().strftime("%B %d, %Y"),
        "total":      len(repos),
        "repos":      repos,
    }
    os.makedirs(os.path.dirname(os.path.abspath(OUTPUT_FILE)), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Saved {len(repos)} repos to {OUTPUT_FILE}")


# ─── Email ────────────────────────────────────────────────────────────────────

def build_email_html(repos, date_str):
    """Build a styled HTML email digest."""
    rows = ""
    for r in repos[:10]:   # Top 10 in email
        topics = " ".join(f'<span style="background:#161b22;color:#58a6ff;padding:2px 8px;border-radius:12px;font-size:11px;margin-right:4px">{t}</span>' for t in r["topics"][:3])
        rows += f"""
        <tr>
          <td style="padding:16px 12px;border-bottom:1px solid #21262d;vertical-align:top;width:36px">
            <span style="color:#f0b429;font-size:18px;font-weight:800">#{r['rank']}</span>
          </td>
          <td style="padding:16px 12px;border-bottom:1px solid #21262d">
            <div style="margin-bottom:4px">
              <a href="{r['url']}" style="color:#58a6ff;font-weight:700;font-size:15px;text-decoration:none">{r['full_name']}</a>
            </div>
            <div style="color:#8b949e;font-size:13px;margin-bottom:8px">{r['description']}</div>
            <div>{topics}</div>
          </td>
          <td style="padding:16px 12px;border-bottom:1px solid #21262d;text-align:right;white-space:nowrap">
            <div style="color:#f0b429;font-weight:700">⭐ {r['stars']:,}</div>
            <div style="color:#8b949e;font-size:12px;margin-top:2px">{r['language']}</div>
          </td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#0d1117;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif">
  <div style="max-width:640px;margin:0 auto;padding:32px 16px">

    <!-- Header -->
    <div style="text-align:center;margin-bottom:32px">
      <div style="font-size:28px;font-weight:900;color:#f0b429;letter-spacing:-1px">★ GithubStar</div>
      <div style="color:#8b949e;font-size:14px;margin-top:4px">Daily Top Starred Projects · {date_str}</div>
    </div>

    <!-- Table -->
    <table width="100%" cellpadding="0" cellspacing="0"
           style="background:#161b22;border:1px solid #21262d;border-radius:12px;overflow:hidden">
      {rows}
    </table>

    <!-- CTA -->
    <div style="text-align:center;margin-top:24px">
      <a href="https://githubstar.vercel.app" 
         style="display:inline-block;background:#f0b429;color:#0d1117;font-weight:800;
                padding:12px 32px;border-radius:8px;text-decoration:none;font-size:14px">
        View All {len(repos)} Repos →
      </a>
    </div>

    <!-- Footer -->
    <div style="text-align:center;margin-top:24px;color:#484f58;font-size:12px">
      Auto-generated daily by GithubStar · 
      <a href="https://github.com" style="color:#484f58">Unsubscribe</a>
    </div>
  </div>
</body></html>"""


def send_email(repos):
    """Send daily digest email to all subscribers."""
    if not SUBSCRIBERS:
        print("⚠️  No subscribers configured — skipping email.")
        return
    if not EMAIL_SENDER or not EMAIL_PASSWORD:
        print("⚠️  Email credentials not set — skipping email.")
        return

    date_str = datetime.date.today().strftime("%B %d, %Y")
    subject  = f"★ GithubStar Daily Digest — {date_str}"
    html     = build_email_html(repos, date_str)

    print(f"\nSending email to {len(SUBSCRIBERS)} subscriber(s)...")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = f"GithubStar <{EMAIL_SENDER}>"
    msg["To"]      = ", ".join(SUBSCRIBERS)
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
        smtp.sendmail(EMAIL_SENDER, SUBSCRIBERS, msg.as_string())

    print(f"✅ Email sent to: {', '.join(SUBSCRIBERS)}")


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 50)
    print("  GithubStar — Daily Update")
    print(f"  {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 50 + "\n")

    repos = fetch_top_repos()
    save_data(repos)
    send_email(repos)

    print("\n🚀 Done!")
