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

def make_buyee_deep_link(target_url, buyee_base_url=""):
    """IndoleadsアフィリエイトベースURLの ?url= に目的URLをエンコードして結合"""
    if buyee_base_url:
        encoded_target = urllib.parse.quote(target_url, safe="")
        return f"{buyee_base_url}?url={encoded_target}"
    return target_url

def make_surugaya_url(keyword_jp, buyee_base_url=""):
    """① 駿河屋（Buyee公式統合ショップ・アフィリエイトディープリンク）"""
    target_url = f"https://buyee.jp/surugaya/search?search_word={urllib.parse.quote(keyword_jp)}"
    return make_buyee_deep_link(target_url, buyee_base_url)

def make_mercari_url(keyword_jp, buyee_base_url=""):
    """② メルカリJP（Buyee公式連携・アフィリエイトディープリンク）"""
    target_url = f"https://buyee.jp/mercari/search?keyword={urllib.parse.quote(keyword_jp)}&status=on_sale"
    return make_buyee_deep_link(target_url, buyee_base_url)

def make_hardoff_url(keyword_jp):
    """③ ハードオフ（オフモール直接検索URL）"""
    return f"https://netmall.hardoff.co.jp/search/?q={urllib.parse.quote(keyword_jp)}"

def make_buyee_url(keyword_jp, buyee_base_url=""):
    """後方互換用エイリアス"""
    return make_mercari_url(keyword_jp, buyee_base_url)

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
GSC_META_TAG = '<meta name="google-site-verification" content="OMWM3rRBhDwVELwVX8JjeAHf3pCAWcCKjEzAu4Ese8w" />'

def ensure_gsc_verification():
    """Google Search Consoleの所有権確認用HTMLファイルおよびテンプレート/index.html内のmetaタグを自動維持・出力"""
    with open(GSC_VERIFICATION_FILE, "w", encoding="utf-8") as f:
        f.write(GSC_VERIFICATION_CONTENT)
    target_files = [
        "index.html",
        os.path.join("templates", "index_template.html"),
        os.path.join("templates", "article_template.html"),
    ]
    for path in target_files:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                html_text = f.read()
            if 'content="OMWM3rRBhDwVELwVX8JjeAHf3pCAWcCKjEzAu4Ese8w"' not in html_text:
                html_text = html_text.replace("<head>", f"<head>\n    {GSC_META_TAG}", 1)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(html_text)

def generate_robots_txt():
    """検索エンジンクローラー向けの robots.txt を生成"""
    robots_content = f"""User-agent: *
Allow: /

Sitemap: {SITE_URL}/sitemap.xml
"""
    with open("robots.txt", "w", encoding="utf-8") as f:
        f.write(robots_content)
    print("robots.txt を生成しました")

CATEGORY_DECODER_ROWS = {
    "Handhelds": [
        ("Safe", "🟢 Safe", "画面ヤケ / 黄ばみ", "Screen Yellowing", "Mild age-related color shift on DS/GBA screens. 100% playable and authentic."),
        ("Modder", "🟡 Modder Only", "外装傷み / 塗装ハゲ", "Shell Wear / Paint Peeling", "Great budget donor for IPS screen or reshell modding (authentic OEM motherboard inside)."),
        ("Trap", "🔴 Fatal Trap", "ビネガーシンドローム", "Vinegar Syndrome", "Degraded polarizer film causing dark blotches and sour odor. Requires screen replacement."),
        ("Trap", "🔴 Fatal Trap", "ヒンジ割れ / 充電ランプ一瞬点灯", "Cracked Hinge / Flash Charge Light", "Broken shell hinge or blown motherboard fuse (F1/F2)."),
        ("Trap", "🔴 Fatal Trap", "液漏れ / 水没反応", "Battery Corrosion / Water Damage", "Alkaline battery acid or liquid has corroded the PCB traces. Avoid."),
    ],
    "Consoles": [
        ("Safe", "🟢 Safe", "本体ヤケ / 変色", "ABS Plastic Yellowing", "Cosmetic yellowing common on white/grey Japanese consoles. Does not affect internal hardware reliability."),
        ("Modder", "🟡 Modder Only", "時計電池切れ", "Dead Clock Battery", "Requires a simple CR2032 coin battery swap (e.g., Sega Saturn back slot)."),
        ("Trap", "🔴 Fatal Trap", "通電のみ確認", "Power Light Only", "<strong>FATAL RED FLAG.</strong> The power LED turns on, but there is NO video/audio output (dead capacitors or GPU/PPU failure)."),
        ("Trap", "🔴 Fatal Trap", "ディスク読み込まず / 音楽CD画面", "Disc Read Error", "Failing optical laser pickup on CD/GD-ROM consoles."),
        ("Trap", "🔴 Fatal Trap", "ターミネータパック欠品", "Missing Jumper Pak", "For N64, the console will not output video without the front memory pak installed."),
    ],
    "Collector Games": [
        ("Safe", "🟢 Safe", "帯なし / ハガキなし", "Missing Obi Spine Card", "For CD games (Saturn/PS1/DC), missing the paper spine strip. 100% authentic disc at a lower price."),
        ("Modder", "🟡 Modder Only", "バックアップ電池切れ", "Dry Save/Clock Battery", "Common on GBA Pokemon or SFC RPGs. Confirms an authentic board; easily fixed by soldering a tabbed coin battery."),
        ("Trap", "🔴 Fatal Trap", "海外製 / 並行輸入品", "Overseas / Parallel Import", "<strong>100% COUNTERFEIT EUPHEMISM.</strong> When Japanese Mercari sellers list GBA/SFC cartridges (like Mother 3 or Pokemon) as &quot;Overseas version&quot;, it is guaranteed to be a cheap bootleg repro."),
        ("Trap", "🔴 Fatal Trap", "リング割れ / 深いキズ", "Center Ring Crack / Deep Scratches", "Structural crack in the disc hub or data-layer damage."),
    ],
    "Controllers & Gear": [
        ("Safe", "🟢 Safe", "軽度のスレ / ヤケ", "Minor Scuffs / Yellowing", "Normal cosmetic wear on authentic OEM plastic."),
        ("Trap", "🔴 Fatal Trap", "ドリフト / 入力暴走", "Stick Drift / Phantom Inputs", "Worn analog stick potentiometer requiring part replacement."),
        ("Trap", "🔴 Fatal Trap", "本体のみ・スタートアップディスク欠品", "Unit Only / Missing Startup Disc", "For Game Boy Player, the bottom attachment cannot boot on unmodded consoles without the Startup Disc."),
        ("Trap", "🔴 Fatal Trap", "社外品 / 互換品", "Third-Party / Generic Clone", "Unlicensed aftermarket replica lacking official Nintendo/Sega/Sony logos."),
    ],
}

UNIVERSAL_DECODER_ROWS = [
    ("Safe", "🟢 Safe", "動作確認済", "Tested & Working", "Safe to buy. Seller confirmed normal boot and operation."),
    ("Safe", "🟢 Safe", "箱説なし", "Loose / No Box or Manual", "Working authentic item missing collector packaging. Best value for players."),
    ("Trap", "🔴 Fatal Trap", "動作未確認", "Untested", "<strong>TRAP ON FLEA MARKETS.</strong> On Mercari JP, private sellers often use &quot;Untested&quot; to hide known dead units while avoiding returns."),
    ("Trap", "🔴 Fatal Trap", "現状品 / 部品取り", "As-Is / For Parts", "Confirmed broken unit sold strictly for spare parts."),
]

def _render_decoder_rows(rows):
    out = []
    for level, badge_text, jp_term, en_term, desc in rows:
        if level == "Safe":
            pill_cls = "risk-safe"
        elif level == "Modder":
            pill_cls = "risk-mod"
        else:
            pill_cls = "risk-trap"
        out.append(
            f"""                <tr>
                    <td style="width: 130px;"><span class="risk-pill {pill_cls}">{badge_text}</span></td>
                    <td style="width: 220px;"><span class="jp-term">{jp_term}</span><span class="en-term">{en_term}</span></td>
                    <td>{desc}</td>
                </tr>"""
        )
    return "\n".join(out)

def build_junk_decoder_html(category):
    """カテゴリ別のJDM Condition & 'JUNK' Decoder HTMLセクションを動的生成"""
    universal_rows_html = _render_decoder_rows(UNIVERSAL_DECODER_ROWS)
    cat_rows = CATEGORY_DECODER_ROWS.get(category, CATEGORY_DECODER_ROWS["Consoles"])
    cat_rows_html = _render_decoder_rows(cat_rows)

    return f"""        <div class="decoder-section">
            <h2>2. JDM Condition &amp; &quot;JUNK&quot; Decoder ({category} Edition)</h2>
            <div class="safety-rule-box">
                <strong>⚠️ Curator Safety Rule:</strong> On Japanese flea markets (Mercari JP / Yahoo Auctions), proxy services NEVER refund items labeled as <strong>ジャンク (Junk)</strong> or <strong>動作未確認 (Untested)</strong>. Unless you are an experienced modder, always filter for <strong>動作確認済 (Tested &amp; Working)</strong> or buy from staff-inspected stores like Suruga-ya.
            </div>

            <h3 class="decoder-subhead">📋 Part A: Universal JDM Condition Terms (All Categories)</h3>
            <table>
                <tr>
                    <th>Risk Level</th>
                    <th>Japanese Term (Kanji)</th>
                    <th>Real-World Meaning for Overseas Buyers</th>
                </tr>
{universal_rows_html}
            </table>

            <h3 class="decoder-subhead">🔍 Part B: Specialized Decoder for {category}</h3>
            <table>
                <tr>
                    <th>Risk Level</th>
                    <th>{category} Listing Term</th>
                    <th>Hardware Reality &amp; Buyer Verdict</th>
                </tr>
{cat_rows_html}
            </table>
        </div>"""

def build_smart_proxy_routing_html():
    """購入リンク直前に配置する Smart Proxy Routing & True Cost Guide HTMLを生成"""
    return """        <div class="proxy-routing-box">
            <div class="proxy-routing-header">
                <h2>✈️ Smart Proxy Routing &amp; True Cost Guide</h2>
                <p>How to avoid hidden shipping bloat and foreign exchange fees when importing from Japan:</p>
            </div>
            <div class="proxy-grid">
                <div class="proxy-tip-card">
                    <span class="proxy-tip-badge badge-single">🥇 Single Item &amp; High-Value</span>
                    <h4>1. Single Item &amp; High-Value Games &rarr; Suruga-ya (Staff-Inspected)</h4>
                    <p><strong>Why:</strong> Every item is tested and authenticated by store staff before shipping. Look for frequent &quot;Free Shipping / 0 Yen Commission&quot; campaigns on Buyee.</p>
                </div>
                <div class="proxy-tip-card">
                    <span class="proxy-tip-badge badge-consolidation">📦 Multi-Item Hauls</span>
                    <h4>2. Multi-Item Consolidation (Avoiding the &quot;Volumetric Air&quot; Shipping Trap)</h4>
                    <p><strong>Why:</strong> When combining multiple consoles or boxed games via proxy, standard consolidation often leaves inner seller boxes intact, causing DHL/FedEx <strong>volumetric weight (容積重量)</strong> to explode to $60–$100+. Always request downsizing or consider proxies known for compact repacking when building large hauls.</p>
                </div>
                <div class="proxy-tip-card">
                    <span class="proxy-tip-badge badge-fx">💴 Currency &amp; FX Tip</span>
                    <h4>3. Currency &amp; Fee Tip (Avoiding Hidden FX Markups)</h4>
                    <p><strong>Why:</strong> Proxy platforms often embed a 3%–6% exchange rate markup when charging in USD/EUR. Whenever possible, set your payment method (PayPal or zero-FX credit card) to bill directly in <strong>Japanese Yen (JPY)</strong> to save on every order.</p>
                </div>
            </div>
        </div>"""

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
    request_form_url = config.get("REQUEST_FORM_URL", "").strip()

    if request_form_url:
        request_form_target = 'target="_blank" rel="noopener"'
        print(f"適用中のGoogleフォームURL: {request_form_url}")
    else:
        request_form_url = "#request-guide"
        request_form_target = 'onclick="alert(\'Form URL not yet configured. Please set REQUEST_FORM_URL in affiliate_config.txt!\'); return false;"'
        print("適用中のGoogleフォームURL: 未設定（#request-guide にフォールバック）")

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

        junk_decoder_html = build_junk_decoder_html(row["category"])
        smart_proxy_routing_html = build_smart_proxy_routing_html()

        html_out = article_template.format(
            title=row["title"],
            category=row["category"],
            region_info=row["region_info"],
            why_japan=row["why_japan"],
            anti_bootleg=row["anti_bootleg"],
            buyer_tips=row["buyer_tips"],
            jp_keyword_main=row["jp_keyword_main"],
            jp_keyword_sub=row["jp_keyword_sub"],
            buyee_surugaya_url_main=make_surugaya_url(row["jp_keyword_main"], buyee_base_url),
            buyee_mercari_url_main=make_mercari_url(row["jp_keyword_main"], buyee_base_url),
            buyee_mercari_url_sub=make_mercari_url(row["jp_keyword_sub"], buyee_base_url),
            hardoff_url_main=make_hardoff_url(row["jp_keyword_main"]),
            buyee_url_main=make_mercari_url(row["jp_keyword_main"], buyee_base_url),
            buyee_url_sub=make_mercari_url(row["jp_keyword_sub"], buyee_base_url),
            ad_1_label=row["ad_1_label"], ad_1_url=make_amazon_url(row["ad_1_query"], amazon_tag),
            ad_2_label=row["ad_2_label"], ad_2_url=make_amazon_url(row["ad_2_query"], amazon_tag),
            ad_3_label=row["ad_3_label"], ad_3_url=make_amazon_url(row["ad_3_query"], amazon_tag),
            site_url=SITE_URL,
            canonical_url=canonical_url,
            current_date=current_date,
            related_guides_html=related_guides_html,
            request_form_url=request_form_url,
            request_form_target=request_form_target,
            junk_decoder_html=junk_decoder_html,
            smart_proxy_routing_html=smart_proxy_routing_html
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
            current_date=current_date,
            request_form_url=request_form_url,
            request_form_target=request_form_target
        ))

    print(f"全 {len(articles)} 記事ページ + index.html を再生成しました")

    # sitemap.xml, robots.txt, Google Search Console確認ファイルの自動生成
    generate_sitemap(articles, current_date)
    generate_robots_txt()
    ensure_gsc_verification()

def run_git_commands():
    git_exe = r"C:\Users\inomo\AppData\Local\Programs\MinGit\cmd\git.exe"
    if not os.path.exists(git_exe):
        git_exe = "git"
    commands = [
        [git_exe, "add", "."],
        [git_exe, "commit", "-m", "Add Google Search Console verification meta tag and persist in mass_publisher"],
        [git_exe, "push", "origin", BRANCH]
    ]
    for cmd in commands:
        subprocess.run(cmd, check=False)

if __name__ == "__main__":
    ensure_gitignore()
    ensure_gsc_verification()
    build_site()
    run_git_commands()
    print("サイト再生成およびGitHubへの反映が完了しました！")
