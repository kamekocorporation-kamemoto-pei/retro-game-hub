import os
import subprocess
import urllib.parse
from datetime import datetime

# リポジトリ設定
REPO_URL = "https://github.com/kamekocorporation-kamemoto-pei/retro-game-hub.git"
BRANCH = "main"

def make_buyee_url(keyword_jp):
    encoded = urllib.parse.quote(keyword_jp)
    return f"https://buyee.jp/mercari/search?keyword={encoded}"

# 記事データの定義（ここに追加するだけで第2弾・第3弾も自動量産可能）
ARTICLES = [
    {
        "slug": "gba-sp-buying-guide",
        "title": "The Ultimate Guide to Buying a Japanese Game Boy Advance SP: Exclusive Colors, 'Junk' Goldmines, and How to Import",
        "description": "Learn why modders and collectors import the Game Boy Advance SP from Japan, how to decode Japanese condition ranks, and find cheap IPS mod bases on Mercari via Buyee.",
        "links": [
            {"label": 'Search "Junk" GBA SP for Modding on Buyee', "query": "ゲームボーイアドバンスSP 本体 ジャンク"},
            {"label": "Search CIB (Complete in Box) GBA SP on Buyee", "query": "ゲームボーイアドバンスSP 箱 完品"},
            {"label": "Search Famicom Color GBA SP on Buyee", "query": "ゲームボーイアドバンスSP ファミコンカラー"},
            {"label": "Search Tested Working GBA SP on Buyee", "query": "ゲームボーイアドバンスSP 本体 動作確認済 -ジャンク"}
        ]
    }
]

def generate_markdown(article):
    date_str = datetime.now().strftime("%Y-%m-%d")
    cta_md = "\n".join([f'- **[{link["label"]}]({make_buyee_url(link["query"])})**' for link in article["links"]])
    
    return f"""---
title: "{article['title']}"
description: "{article['description']}"
date: "{date_str}"
---

# {article['title']}

**Good news first: The Game Boy Advance SP is 100% region-free.** A Japanese console will play your North American and European cartridges right out of the box without any hardware modifications.

## 1. Why Buy a GBA SP from Japan?
* **JDM Exclusive Colors:** Japan received stunning exclusive variants like Pearl Blue, Famicom 20th Anniversary Edition, and Pokemon Center limited editions (Torchic Orange, Venusaur Green, Charizard Red).
* **Pristine Collector Condition:** Japanese gamers are famous for keeping original cardboard boxes and manuals in near-mint condition, making CIB (Complete in Box) hunting far easier than in Western markets.
* **Ultra-Light International Shipping:** Weighing only 142g, the GBA SP qualifies for inexpensive Small Packet international shipping.

## 2. The Japanese "Junk" Secret (A Modder's Goldmine)
On Western marketplaces like eBay, "For Parts / Not Working" usually means a dead motherboard or severe water damage. On Japanese marketplaces like Mercari and Yahoo! Auctions, **"Junk" (ジャンク)** often just means:
* The seller lost the charger and couldn't test it.
* The original rechargeable battery is dry (an easy $10 replacement).
* The outer shell has scratches or the screen has a burned polarizer—which doesn't matter at all if you are installing a modern IPS V5 backlight kit and a custom shell.

## 3. Japanese Condition Translation Guide
* **新品・未使用 (Brand New / Unused):** Unopened or unplayed collector grade.
* **目立った傷や汚れなし (Near Mint / Excellent):** Very clean shell and screen with minimal wear.
* **やや傷や汚れあり (Good / Lightly Played):** Normal surface scratches on the clamshell; works fine.
* **全体的に状態が悪い / ジャンク (Junk / For Parts):** Ideal low-cost donor motherboard for IPS screen modding.
* **箱説あり / 完品 (CIB):** Includes original box and manual.
* **本体のみ (Console Only):** Loose console without box.

## 4. Market Price Arbitrage: US vs. Japan
* **Modding Base ("Junk" Unit):** $65–$85 on eBay vs. **¥4,000–¥6,000 ($26–$40)** in Japan.
* **Complete in Box (Standard Color):** $150+ on eBay vs. **¥11,000–¥15,000 ($72–$98)** in Japan.

## 5. Find Live Listings on Japanese Marketplaces (via Buyee)
Click the pre-configured Japanese search queries below to browse live Mercari inventory directly through Buyee:

{cta_md}
"""

def generate_html(article):
    buttons_html = "\n".join([
        f'<a class="cta-btn" href="{make_buyee_url(link["query"])}" target="_blank" rel="noopener">{link["label"]} &rarr;</a>'
        for link in article["links"]
    ])
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{article['title']}</title>
    <meta name="description" content="{article['description']}">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; line-height: 1.7; color: #1f2937; max-width: 820px; margin: 0 auto; padding: 24px; background: #f9fafb; }}
        .card {{ background: #ffffff; padding: 36px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.06); }}
        h1 {{ font-size: 1.9rem; color: #111827; margin-top: 0; }}
        h2 {{ font-size: 1.35rem; color: #1e40af; border-bottom: 2px solid #e5e7eb; padding-bottom: 8px; margin-top: 32px; }}
        .badge {{ display: inline-block; background: #dbeafe; color: #1e40af; font-weight: 700; padding: 4px 12px; border-radius: 999px; font-size: 0.85rem; margin-bottom: 12px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 16px 0; }}
        th, td {{ border: 1px solid #e5e7eb; padding: 10px 12px; text-align: left; }}
        th {{ background: #f3f4f6; }}
        .cta-box {{ background: #eff6ff; border: 2px solid #bfdbfe; border-radius: 10px; padding: 24px; margin-top: 32px; }}
        .cta-btn {{ display: block; background: #2563eb; color: #ffffff; text-decoration: none; font-weight: 700; padding: 14px 20px; border-radius: 8px; margin: 12px 0; text-align: center; transition: background 0.2s; }}
        .cta-btn:hover {{ background: #1d4ed8; }}
    </style>
</head>
<body>
    <div class="card">
        <span class="badge">JDM Retro Gaming Guide</span>
        <h1>{article['title']}</h1>
        <p><strong>Region-Free Guarantee:</strong> The Game Boy Advance SP has no region lock. A Japanese GBA SP plays US and PAL cartridges natively without any modifications.</p>

        <h2>1. Why Import a GBA SP from Japan?</h2>
        <ul>
            <li><strong>JDM Exclusive Colors:</strong> Pearl Blue, Famicom 20th Anniversary, and Pokemon Center limited editions that were never sold in the West.</li>
            <li><strong>Superior Collector Condition:</strong> Japanese collectors preserve boxes and manuals meticulously, making CIB hunting far more rewarding.</li>
            <li><strong>Low Shipping Weight:</strong> At just 142g, international shipping via Small Packet stays very affordable, especially when consolidating multiple items.</li>
        </ul>

        <h2>2. The Japanese "Junk" Secret for IPS Modders</h2>
        <p>While "For Parts" on Western sites usually means fatal board damage, <strong>"Junk" (ジャンク)</strong> in Japan frequently means the seller simply lost the charger, the battery is old, or the shell is scratched—making them inexpensive, working motherboard donors for IPS LCD and USBC upgrades.</p>

        <h2>3. Condition Rank Translation Table</h2>
        <table>
            <tr><th>Japanese Term</th><th>English Meaning</th><th>Best For</th></tr>
            <tr><td>新品・未使用</td><td>Brand New / Unused</td><td>High-end collectors</td></tr>
            <tr><td>目立った傷や汚れなし</td><td>Near Mint / Excellent</td><td>Clean stock play</td></tr>
            <tr><td>やや傷や汚れあり</td><td>Good / Lightly Played</td><td>Everyday gaming</td></tr>
            <tr><td>ジャンク / 状態が悪い</td><td>Junk / Untested</td><td>IPS screen & shell modders</td></tr>
            <tr><td>箱説あり / 完品</td><td>Complete in Box (CIB)</td><td>Display & collection</td></tr>
        </table>

        <h2>4. Price Comparison: eBay vs. Japan</h2>
        <ul>
            <li><strong>Modding Base ("Junk" Console):</strong> $65–$85 on eBay vs. <strong>¥4,000–¥6,000 ($26–$40)</strong> in Japan.</li>
            <li><strong>CIB Standard Edition:</strong> $150+ on eBay vs. <strong>¥11,000–¥15,000 ($72–$98)</strong> in Japan.</li>
        </ul>

        <div class="cta-box">
            <h2 style="margin-top:0; border:none;">5. Browse Live Japanese Inventory via Buyee</h2>
            <p>Use our pre-translated Japanese search links below to see live Mercari listings right now:</p>
            {buttons_html}
        </div>
    </div>
</body>
</html>
"""

def run_git_commands():
    commands = [
        ["git", "add", "."],
        ["git", "commit", "-m", "Auto-publish GBA SP buying guide"],
        ["git", "push", "origin", BRANCH]
    ]
    for cmd in commands:
        subprocess.run(cmd, check=False)

def main():
    os.makedirs("content", exist_ok=True)
    for article in ARTICLES:
        md_path = os.path.join("content", f"{article['slug']}.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(generate_markdown(article))
            
        # トップページ（index.html）および個別ページとして出力
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(generate_html(article))
        with open(f"{article['slug']}.html", "w", encoding="utf-8") as f:
            f.write(generate_html(article))

    print("記事ファイル（Markdown / HTML）の生成が完了しました。")
    run_git_commands()
    print("GitHubへのアップロードが完了しました。")

if __name__ == "__main__":
    main()
