import os
import csv
import subprocess
import urllib.parse
from datetime import datetime

REPO_URL = "https://github.com/kamekocorporation-kamemoto-pei/retro-game-hub.git"
BRANCH = "main"
CONFIG_FILE = "affiliate_config.txt"
SITE_URL = "https://kamekocorporation-kamemoto-pei.github.io/retro-game-hub"

def get_amazon_tag():
    """ローカル設定ファイルからストアIDを安全に読み込む"""
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            f.write("YOUR_STORE_ID_HERE")
        return "YOUR_STORE_ID_HERE"
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        tag = f.read().strip()
        return tag if tag else "YOUR_STORE_ID_HERE"

def ensure_gitignore():
    """ストアID設定ファイルがGitHubに公開されないよう保護する"""
    gitignore_path = ".gitignore"
    ignore_entry = f"\n{CONFIG_FILE}\n"
    if os.path.exists(gitignore_path):
        with open(gitignore_path, "r", encoding="utf-8") as f:
            content = f.read()
        if CONFIG_FILE not in content:
            with open(gitignore_path, "a", encoding="utf-8") as f:
                f.write(ignore_entry)
    else:
        with open(gitignore_path, "w", encoding="utf-8") as f:
            f.write(f"{CONFIG_FILE}\n")

def make_buyee_url(keyword_jp):
    return f"https://buyee.jp/mercari/search?keyword={urllib.parse.quote(keyword_jp)}"

def make_amazon_url(query_en, amazon_tag):
    base_url = f"https://www.amazon.co.jp/s?k={urllib.parse.quote(query_en)}"
    if amazon_tag and amazon_tag != "YOUR_STORE_ID_HERE":
        return f"{base_url}&tag={urllib.parse.quote(amazon_tag)}"
    return base_url

def generate_sitemap(articles, current_date):
    """Google検索インデックス用の sitemap.xml を標準規格で生成"""
    urls_xml = f"""  <url>
    <loc>{SITE_URL}/</loc>
    <lastmod>{current_date}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>\n"""
    
    for row in articles:
        urls_xml += f"""  <url>
    <loc>{SITE_URL}/{row['slug']}.html</loc>
    <lastmod>{current_date}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>\n"""

    sitemap_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{urls_xml.rstrip()}
</urlset>
"""
    with open("sitemap.xml", "w", encoding="utf-8") as f:
        f.write(sitemap_content)
    print(f"sitemap.xml を生成しました（合計 {len(articles) + 1} URL）")

def generate_robots_txt():
    """検索エンジンクローラー向けの robots.txt を生成"""
    robots_content = f"""User-agent: *
Allow: /

Sitemap: {SITE_URL}/sitemap.xml
"""
    with open("robots.txt", "w", encoding="utf-8") as f:
        f.write(robots_content)
    print("robots.txt を生成しました")

def build_site():
    csv_path = os.path.join("data", "retro_games.csv")
    article_tpl_path = os.path.join("templates", "article_template.html")
    index_tpl_path = os.path.join("templates", "index_template.html")

    if not os.path.exists(csv_path):
        print("エラー: data/retro_games.csv が見つかりません。")
        return

    amazon_tag = get_amazon_tag()
    print(f"適用中のAmazonトラッキングID: {amazon_tag}")

    with open(article_tpl_path, "r", encoding="utf-8") as f:
        article_template = f.read()
    with open(index_tpl_path, "r", encoding="utf-8") as f:
        index_template = f.read()
    with open(csv_path, "r", encoding="utf-8") as f:
        articles = list(csv.DictReader(f))

    current_date = datetime.now().strftime("%Y-%m-%d")

    list_items_html = ""
    for row in articles:
        canonical_url = f"{SITE_URL}/{row['slug']}.html"
        html_out = article_template.format(
            title=row["title"],
            category=row["category"],
            region_info=row["region_info"],
            why_japan=row["why_japan"],
            anti_bootleg=row["anti_bootleg"],
            buyer_tips=row["buyer_tips"],
            jp_keyword_main=row["jp_keyword_main"],
            jp_keyword_sub=row["jp_keyword_sub"],
            buyee_url_main=make_buyee_url(row["jp_keyword_main"]),
            buyee_url_sub=make_buyee_url(row["jp_keyword_sub"]),
            ad_1_label=row["ad_1_label"], ad_1_url=make_amazon_url(row["ad_1_query"], amazon_tag),
            ad_2_label=row["ad_2_label"], ad_2_url=make_amazon_url(row["ad_2_query"], amazon_tag),
            ad_3_label=row["ad_3_label"], ad_3_url=make_amazon_url(row["ad_3_query"], amazon_tag),
            site_url=SITE_URL,
            canonical_url=canonical_url,
            current_date=current_date
        )
        with open(f"{row['slug']}.html", "w", encoding="utf-8") as out_f:
            out_f.write(html_out)

        list_items_html += f"""
        <div class="article-card" data-category="{row['category']}">
            <span class="badge">{row['category']}</span>
            <span class="auth-tag">🛡️ Anti-Bootleg Verified</span>
            <h2><a href="{row['slug']}.html">{row['title']}</a></h2>
            <p>{row['why_japan']}</p>
            <a class="read-more" href="{row['slug']}.html">Read Authenticity Guide & Browse Live Listings &rarr;</a>
        </div>
        """

    with open("index.html", "w", encoding="utf-8") as out_idx:
        out_idx.write(index_template.format(
            list_items=list_items_html,
            site_url=SITE_URL,
            current_date=current_date
        ))

    # sitemap.xml と robots.txt の自動生成
    generate_sitemap(articles, current_date)
    generate_robots_txt()

def run_git_commands():
    commands = [
        ["git", "add", "."],
        ["git", "commit", "-m", "Implement technical SEO: dynamic meta tags, canonical URLs, OGP, JSON-LD structured data, sitemap.xml, and robots.txt"],
        ["git", "push", "origin", BRANCH]
    ]
    for cmd in commands:
        subprocess.run(cmd, check=False)

if __name__ == "__main__":
    ensure_gitignore()
    build_site()
    run_git_commands()
    print("サイト再生成およびGitHubへの反映が完了しました！")
