import os
import csv
import subprocess
import urllib.parse
from datetime import datetime

REPO_URL = "https://github.com/kamekocorporation-kamemoto-pei/retro-game-hub.git"
BRANCH = "main"
CONFIG_FILE = "affiliate_config.txt"
SITE_URL = "https://kamekocorporation-kamemoto-pei.github.io/retro-game-hub"

def get_affiliate_config():
    """ローカル設定ファイルからストアIDとBuyeeアフィリエイトURLを安全に読み込む"""
    config = {
        "AMAZON_TAG": "YOUR_STORE_ID_HERE",
        "BUYEE_BASE_URL": ""
    }
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            f.write("AMAZON_TAG=YOUR_STORE_ID_HERE\nBUYEE_BASE_URL=\n")
        return config
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                config[k.strip()] = v.strip()
            elif config["AMAZON_TAG"] == "YOUR_STORE_ID_HERE":
                config["AMAZON_TAG"] = line
    return config

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

def make_buyee_url(keyword_jp, buyee_base_url=""):
    target_url = f"https://buyee.jp/mercari/search?keyword={urllib.parse.quote(keyword_jp)}&status=on_sale"
    if buyee_base_url:
        encoded_target = urllib.parse.quote(target_url, safe="")
        return f"{buyee_base_url}?url={encoded_target}"
    return target_url

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

GSC_VERIFICATION_FILE = "googlef37282339517c341.html"
GSC_VERIFICATION_CONTENT = "google-site-verification: googlef37282339517c341.html"

def ensure_gsc_verification():
    """Google Search Consoleの所有権確認用HTMLファイルを自動維持・出力"""
    with open(GSC_VERIFICATION_FILE, "w", encoding="utf-8") as f:
        f.write(GSC_VERIFICATION_CONTENT)

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

    config = get_affiliate_config()
    amazon_tag = config.get("AMAZON_TAG", "YOUR_STORE_ID_HERE")
    buyee_base_url = config.get("BUYEE_BASE_URL", "")
    print(f"適用中のAmazonトラッキングID: {amazon_tag}")
    print(f"適用中のBuyeeトラッキングベースURL: {'有効 (' + buyee_base_url + ')' if buyee_base_url else '未設定'}")

    with open(article_tpl_path, "r", encoding="utf-8") as f:
        article_template = f.read()
    with open(index_tpl_path, "r", encoding="utf-8") as f:
        index_template = f.read()
    with open(csv_path, "r", encoding="utf-8") as f:
        articles = list(csv.DictReader(f))

    current_date = datetime.now().strftime("%Y-%m-%d")

    # 同カテゴリの関連記事を抽出するためのマップ
    category_map = {}
    for a in articles:
        category_map.setdefault(a["category"], []).append(a)

    list_items_html = ""
    for i, row in enumerate(articles):
        canonical_url = f"{SITE_URL}/{row['slug']}.html"

        # 関連記事の選定（偏りが出ないようローテーション）
        same_cat = [a for a in category_map.get(row["category"], []) if a["slug"] != row["slug"]]
        num_same = len(same_cat)
        if num_same <= 4:
            selected_related = same_cat
        else:
            start_idx = i % num_same
            selected_related = [same_cat[(start_idx + offset) % num_same] for offset in range(4)]

        related_cards = []
        for rel in selected_related:
            snippet = rel["why_japan"].strip()
            if len(snippet) > 105:
                snippet = snippet[:102].rstrip() + "..."
            card = f"""                <div class="related-card">
                    <span class="badge">{rel['category']}</span>
                    <h3><a href="{rel['slug']}.html">{rel['title']}</a></h3>
                    <p>{snippet}</p>
                    <a class="read-more" href="{rel['slug']}.html">Read Guide &rarr;</a>
                </div>"""
            related_cards.append(card)
        related_guides_html = "\n".join(related_cards)

        html_out = article_template.format(
            title=row["title"],
            category=row["category"],
            region_info=row["region_info"],
            why_japan=row["why_japan"],
            anti_bootleg=row["anti_bootleg"],
            buyer_tips=row["buyer_tips"],
            jp_keyword_main=row["jp_keyword_main"],
            jp_keyword_sub=row["jp_keyword_sub"],
            buyee_url_main=make_buyee_url(row["jp_keyword_main"], buyee_base_url),
            buyee_url_sub=make_buyee_url(row["jp_keyword_sub"], buyee_base_url),
            ad_1_label=row["ad_1_label"], ad_1_url=make_amazon_url(row["ad_1_query"], amazon_tag),
            ad_2_label=row["ad_2_label"], ad_2_url=make_amazon_url(row["ad_2_query"], amazon_tag),
            ad_3_label=row["ad_3_label"], ad_3_url=make_amazon_url(row["ad_3_query"], amazon_tag),
            site_url=SITE_URL,
            canonical_url=canonical_url,
            current_date=current_date,
            related_guides_html=related_guides_html
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

    # sitemap.xml, robots.txt, Google Search Console確認ファイルの自動生成
    generate_sitemap(articles, current_date)
    generate_robots_txt()
    ensure_gsc_verification()

def run_git_commands():
    commands = [
        ["git", "add", "-A"],
        ["git", "commit", "-m", "Add related guides section, curator message, and compliant disclosures"],
        ["git", "push", "origin", BRANCH]
    ]
    for cmd in commands:
        subprocess.run(cmd, check=False)

if __name__ == "__main__":
    ensure_gitignore()
    build_site()
    run_git_commands()
    print("サイト再生成およびGitHubへの反映が完了しました！")
