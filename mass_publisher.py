import os
import io
import re
import csv
import json
import shutil
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from PIL import Image, ImageDraw, ImageFont, ImageOps

REPO_URL = "https://github.com/kamekocorporation-kamemoto-pei/retro-game-hub.git"
BRANCH = "main"
CONFIG_FILE = "affiliate_config.txt"
SITE_URL = "https://kamekocorporation-kamemoto-pei.github.io/retro-game-hub"

# アフィリエイト定数設定
BUYEE_PREFIX = "https://io20.info/6aea82bc10193?url="
FROMJAPAN_AFF_URL = "https://affili.fromjapan.co.jp/gateway/A26382"
AMAZON_US_TAG = "kameko0613-20"
AMAZON_JP_TAG = "kameko084-22"
ZENMARKET_AFF_CODE = ""  # 審査通過後に "?aff=XXXX" 等を設定すれば全ページ自動反映

CACHE_PRODUCT_IMAGES_DIR = Path("marketing_tools") / "product_images"
WEB_PRODUCT_IMAGES_DIR = Path("images") / "products"

HTTP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,ja;q=0.8",
}

CURATED_IMAGE_QUERIES = {
    "gba-sp-buying-guide": ("Game Boy Advance SP", "ゲームボーイアドバンスSP 本体 箱 純正"),
    "nintendo-ds-lite-guide": ("Nintendo DS Lite", "ニンテンドーDS Lite 本体 箱 美品"),
    "gamecube-controller-white-guide": ("Nintendo GameCube controller", "ゲームキューブ コントローラー ホワイト 純正"),
    "pokemon-gba-cib-guide": ("Pokémon Emerald", "ポケットモンスター エメラルド 箱 カセット"),
    "game-boy-player-startup-disc-guide": ("Game Boy Player", "ゲームボーイプレーヤー スタートアップディスク"),
    "ps-vita-2000-japan-colors": ("PlayStation Vita", "PS Vita PCH-2000 ネオンオレンジ 本体"),
    "game-boy-micro-jdm-guide": ("Game Boy Micro", "ゲームボーイミクロ ファミコンバージョン 本体"),
    "sega-saturn-white-import-guide": ("Sega Saturn", "セガサターン シロ HST-3220 本体 箱"),
    "nintendo-64-clear-colors-guide": ("Nintendo 64", "NINTENDO64 クリアブルー 本体"),
    "ascii-keyboard-controller-gc": ("Nintendo GameCube accessories", "ゲームキューブ キーボードコントローラー 箱 本体"),
    "mother-3-gba-authentic-guide": ("Mother 3", "MOTHER3 ゲームボーイアドバンス 箱説 完品"),
    "ikaruga-dreamcast-gamecube-guide": ("Ikaruga", "斑鳩 ドリームキャスト ソフト 帯"),
    "castlevania-symphony-of-the-night-jp": ("Castlevania: Symphony of the Night", "悪魔城ドラキュラX 月下の夜想曲 PS1 帯"),
    "neo-geo-pocket-color-slim-guide": ("Neo Geo Pocket Color", "ネオジオポケットカラー New 本体 箱"),
    "chrono-trigger-sfc-cib-guide": ("Chrono Trigger", "クロノトリガー スーパーファミコン 箱 カセット"),
}

def _search_yahoo_jp_images(query: str) -> list:
    urls = []
    try:
        url = "https://search.yahoo.co.jp/image/search?p=" + urllib.parse.quote(query)
        req = urllib.request.Request(url, headers=HTTP_HEADERS)
        raw_html = urllib.request.urlopen(req, timeout=10).read().decode("utf-8", errors="ignore")
        orig_urls = re.findall(r'"original"\s*:\s*\{"url"\s*:\s*"(https?://[^"]+)"', raw_html)
        thumb_urls = re.findall(r'"thumbnail"\s*:\s*\{"url"\s*:\s*"(https?://[^"]+)"', raw_html)
        for u in orig_urls + thumb_urls:
            u_clean = u.replace("\\/", "/")
            if u_clean not in urls:
                urls.append(u_clean)
    except Exception:
        pass
    return urls

def _search_bing_images(query: str) -> list:
    urls = []
    try:
        url = "https://www.bing.com/images/search?q=" + urllib.parse.quote(query) + "&FORM=HDRSC2"
        req = urllib.request.Request(url, headers=HTTP_HEADERS)
        raw_html = urllib.request.urlopen(req, timeout=10).read().decode("utf-8", errors="ignore")
        murls = re.findall(r'murl&quot;:&quot;(https?://[^&]+?)&quot;', raw_html)
        for u in murls:
            if any(bad in u.lower() for bad in ("free-aigames", "monjeux", "poki.com", "crazygames")):
                continue
            if u not in urls:
                urls.append(u)
    except Exception:
        pass
    return urls

def _is_fallback_card(img_path: Path) -> bool:
    if not img_path.exists():
        return True
    if img_path.stat().st_size < 3500:
        return True
    try:
        with Image.open(img_path) as im:
            if im.size in ((720, 540), (840, 630)):
                rgb = im.convert("RGB")
                px1 = rgb.getpixel((5, 5))
                px2 = rgb.getpixel((100, 100))
                if (abs(px1[0] - 15) <= 6 and abs(px1[1] - 23) <= 6 and abs(px1[2] - 42) <= 6 and
                    abs(px2[0] - 15) <= 6 and abs(px2[1] - 23) <= 6 and abs(px2[2] - 42) <= 6):
                    return True
    except Exception:
        return True
    return False

def _search_wikipedia_image(wiki_title: str) -> list:
    urls = []
    if not wiki_title:
        return urls
    try:
        api = (
            "https://en.wikipedia.org/w/api.php?action=query"
            f"&titles={urllib.parse.quote(wiki_title)}"
            "&prop=pageimages&piprop=original|thumbnail&pithumbsize=1000&format=json&redirects=1"
        )
        req = urllib.request.Request(
            api,
            headers={"User-Agent": "JDMRetroHubCurator/1.0 (https://github.com/kamekocorporation-kamemoto-pei)"}
        )
        data = json.loads(urllib.request.urlopen(req, timeout=8).read().decode("utf-8", errors="ignore"))
        pages = data.get("query", {}).get("pages", {})
        for p in pages.values():
            orig = p.get("original", {}).get("source")
            thumb = p.get("thumbnail", {}).get("source")
            if orig and not orig.lower().endswith(".svg"):
                urls.append(orig)
            if thumb:
                urls.append(thumb)
    except Exception:
        pass
    return urls

def _save_web_optimized(im: Image.Image, dest_path: Path):
    web_im = ImageOps.contain(im.convert("RGB"), (840, 840), Image.Resampling.LANCZOS)
    web_im.save(dest_path, "JPEG", quality=88, optimize=True)

def _sync_single_product_image(row: dict) -> tuple:
    slug = row["slug"].strip()
    cached_jpg = CACHE_PRODUCT_IMAGES_DIR / f"{slug}.jpg"
    web_jpg = WEB_PRODUCT_IMAGES_DIR / f"{slug}.jpg"

    # 1. If web image already exists and is a real photo (not fallback), keep it
    if not _is_fallback_card(web_jpg):
        if _is_fallback_card(cached_jpg):
            shutil.copy2(web_jpg, cached_jpg)
        return (slug, "existing")

    # 2. If cached image exists and is a real photo, copy/optimize to images/products/
    if not _is_fallback_card(cached_jpg):
        try:
            im = Image.open(cached_jpg).convert("RGB")
            _save_web_optimized(im, web_jpg)
            return (slug, "copied_from_cache")
        except Exception:
            pass

    # 3. Fetch automatically using Yahoo JP + Bing + Wikipedia
    title_clean = re.sub(r"\s*\([^)]*\)", "", row.get("title", slug)).strip()
    jp_kw = row.get("jp_keyword_main", "").strip()
    jp_sub = row.get("jp_keyword_sub", "").strip()
    if slug in CURATED_IMAGE_QUERIES:
        wiki_title, search_q = CURATED_IMAGE_QUERIES[slug]
    else:
        wiki_title = title_clean
        search_q = f"{jp_kw} 本体 箱" if jp_kw else f"{title_clean} Japanese retro game"

    cand_urls = _search_yahoo_jp_images(search_q)
    if not cand_urls and jp_kw:
        cand_urls += _search_bing_images(jp_kw)
    if jp_kw and jp_kw != search_q:
        cand_urls += _search_yahoo_jp_images(jp_kw)
    cand_urls += _search_bing_images(f"{jp_kw} レトロゲーム" if jp_kw else f"{title_clean} Japan")
    cand_urls += _search_wikipedia_image(wiki_title)

    for min_w, min_h in [(420, 320), (220, 180)]:
        for u in cand_urls[:18]:
            try:
                req = urllib.request.Request(u, headers=HTTP_HEADERS)
                raw_bytes = urllib.request.urlopen(req, timeout=8).read()
                im = Image.open(io.BytesIO(raw_bytes))
                if im.width < min_w or im.height < min_h:
                    continue
                if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
                    rgba = im.convert("RGBA")
                    bg = Image.new("RGB", rgba.size, (255, 255, 255))
                    bg.paste(rgba, mask=rgba.split()[3])
                    im = bg
                else:
                    im = im.convert("RGB")
                im.save(cached_jpg, "JPEG", quality=92)
                _save_web_optimized(im, web_jpg)
                return (slug, "fetched")
            except Exception:
                continue

    # 4. Clean stylized OEM reference card fallback if network image unavailable
    fallback = Image.new("RGB", (720, 540), (15, 23, 42))
    draw = ImageDraw.Draw(fallback)
    draw.rounded_rectangle([24, 24, 696, 516], radius=20, outline=(56, 189, 248), width=4)
    try:
        font_lg = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 30)
        font_sm = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 20)
    except Exception:
        font_lg = ImageFont.load_default()
        font_sm = font_lg
    draw.text((360, 235), title_clean[:38], font=font_lg, fill=(248, 250, 252), anchor="mm")
    draw.text((360, 295), "JDM Authentic Hardware / CIB Reference", font=font_sm, fill=(148, 163, 184), anchor="mm")
    fallback.save(cached_jpg, "JPEG", quality=90)
    _save_web_optimized(fallback, web_jpg)
    return (slug, "fallback")

def sync_and_fetch_product_images(articles: list):
    """全150品目の商品画像を marketing_tools/product_images/ と images/products/ に同期・自動補完"""
    CACHE_PRODUCT_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    WEB_PRODUCT_IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    stats = {"existing": 0, "copied_from_cache": 0, "fetched": 0, "fallback": 0}
    print(f"商品画像の同期・補完を開始します（全 {len(articles)} 品目）...")
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(_sync_single_product_image, row): row["slug"] for row in articles}
        for idx, fut in enumerate(as_completed(futures), 1):
            slug, status = fut.result()
            stats[status] = stats.get(status, 0) + 1
            if idx % 25 == 0 or idx == len(articles):
                print(f"  進捗: {idx}/{len(articles)} 完了 (キャッシュ複製:{stats['copied_from_cache']}, 新規取得:{stats['fetched']}, 既存:{stats['existing']})")
    print(f"商品画像の準備完了: {stats}")

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
    """ストアID設定ファイルがGitHubに公開されないよう保護しつつ、公開用のimages/products/は追跡許可する"""
    gitignore_path = ".gitignore"
    required_entries = [
        CONFIG_FILE,
        "!images/",
        "!images/**",
        "!images/products/",
        "!images/products/*.jpg",
        "!images/products/*.png",
    ]
    if os.path.exists(gitignore_path):
        with open(gitignore_path, "r", encoding="utf-8") as f:
            content = f.read()
        to_append = [e for e in required_entries if e not in content]
        if to_append:
            with open(gitignore_path, "a", encoding="utf-8") as f:
                f.write("\n" + "\n".join(to_append) + "\n")
    else:
        with open(gitignore_path, "w", encoding="utf-8") as f:
            f.write("\n".join(required_entries) + "\n")

def make_buyee_deep_link(target_url, buyee_base_url=""):
    """IndoleadsアフィリエイトベースURLの ?url= に目的URLをエンコードして結合"""
    encoded_target = urllib.parse.quote(target_url, safe="")
    prefix = BUYEE_PREFIX
    if buyee_base_url:
        prefix = buyee_base_url if buyee_base_url.endswith("?url=") else f"{buyee_base_url}?url="
    if prefix:
        return f"{prefix}{encoded_target}"
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

def make_fromjapan_url(keyword_jp=""):
    """④ FromJapan / One Map（複数まとめ買い・横断検索用アフィリエイトリンク）"""
    return FROMJAPAN_AFF_URL

def make_zenmarket_url(keyword_jp):
    """⑤ ZenMarket（ZENMARKET_AFF_CODE設定時に全ページへアフィリエイトコードを自動付与）"""
    base = f"https://zenmarket.jp/en/mercari.aspx?q={urllib.parse.quote(keyword_jp)}"
    if ZENMARKET_AFF_CODE:
        code = ZENMARKET_AFF_CODE.strip()
        if code.startswith("?"):
            return f"{base}&{code[1:]}"
        elif code.startswith("&"):
            return f"{base}{code}"
        else:
            return f"{base}&aff={urllib.parse.quote(code)}"
    return base

def make_buyee_url(keyword_jp, buyee_base_url=""):
    """後方互換用エイリアス"""
    return make_mercari_url(keyword_jp, buyee_base_url)

def make_amazon_url(query_en, amazon_tag=AMAZON_US_TAG):
    """米国Amazon（Amazon.com）検索アフィリエイトリンク（メイン）"""
    base_url = f"https://www.amazon.com/s?k={urllib.parse.quote(query_en)}"
    tag = AMAZON_US_TAG if not amazon_tag or amazon_tag == "YOUR_STORE_ID_HERE" else amazon_tag
    return f"{base_url}&tag={urllib.parse.quote(tag)}"

def make_amazon_jp_url(query_en, amazon_jp_tag=AMAZON_JP_TAG):
    """日本Amazon（Amazon.co.jp）検索アフィリエイトリンク（サブ）"""
    base_url = f"https://www.amazon.co.jp/s?k={urllib.parse.quote(query_en)}"
    tag = amazon_jp_tag or AMAZON_JP_TAG
    return f"{base_url}&tag={urllib.parse.quote(tag)}"

def generate_sitemap(articles, current_date):
    """Google検索インデックス用の sitemap.xml および sitemap-main.xml を標準規格で生成（BOMなしUTF-8・クリーン出力）"""
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
</urlset>"""
    clean_sitemap = sitemap_content.strip() + "\n"
    for filename in ("sitemap.xml", "sitemap-main.xml"):
        with open(filename, "w", encoding="utf-8", newline="\n") as f:
            f.write(clean_sitemap)
    print(f"sitemap.xml および sitemap-main.xml を生成しました（合計 {len(articles) + 1} URL）")

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
Sitemap: {SITE_URL}/sitemap-main.xml
"""
    with open("robots.txt", "w", encoding="utf-8", newline="\n") as f:
        f.write(robots_content.strip() + "\n")
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

def build_smart_proxy_routing_html(keyword_jp=""):
    """購入リンク直前に配置する Smart Proxy Routing & True Cost Guide HTMLを生成"""
    fj_url = make_fromjapan_url(keyword_jp)
    zm_url = "https://zenmarket.jp/en/" if not ZENMARKET_AFF_CODE else make_zenmarket_url(keyword_jp)
    return f"""        <div class="proxy-routing-box">
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
                    <p style="margin-top:8px;"><a href="{fj_url}" target="_blank" rel="noopener sponsored" style="color:#60a5fa;font-weight:bold;">👉 Compare Multi-Store Hauls &amp; Compact Consolidation via FROM JAPAN (Official Partner) &rarr;</a> | <a href="{zm_url}" target="_blank" rel="noopener" style="color:#94a3b8;">ZenMarket</a></p>
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

    # 全150品目の商品画像を同期・自動取得して images/products/{slug}.jpg に配置
    sync_and_fetch_product_images(articles)

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
        smart_proxy_routing_html = build_smart_proxy_routing_html(row["jp_keyword_main"])

        html_out = article_template.format(
            slug=row["slug"],
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
            fromjapan_url_main=make_fromjapan_url(row["jp_keyword_main"]),
            zenmarket_url_main=make_zenmarket_url(row["jp_keyword_main"]),
            buyee_url_main=make_mercari_url(row["jp_keyword_main"], buyee_base_url),
            buyee_url_sub=make_mercari_url(row["jp_keyword_sub"], buyee_base_url),
            ad_1_label=row["ad_1_label"],
            ad_1_url=make_amazon_url(row["ad_1_query"], AMAZON_US_TAG),
            ad_1_jp_url=make_amazon_jp_url(row["ad_1_query"], AMAZON_JP_TAG),
            ad_2_label=row["ad_2_label"],
            ad_2_url=make_amazon_url(row["ad_2_query"], AMAZON_US_TAG),
            ad_2_jp_url=make_amazon_jp_url(row["ad_2_query"], AMAZON_JP_TAG),
            ad_3_label=row["ad_3_label"],
            ad_3_url=make_amazon_url(row["ad_3_query"], AMAZON_US_TAG),
            ad_3_jp_url=make_amazon_jp_url(row["ad_3_query"], AMAZON_JP_TAG),
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
            <a class="card-thumb-wrap" href="{row['slug']}.html">
                <img class="card-thumb-img" src="images/products/{row['slug']}.jpg" alt="Authentic Japanese {row['title']} CIB / Console" loading="lazy" onerror="this.parentElement.style.display='none';">
            </a>
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
            request_form_target=request_form_target,
            fromjapan_aff_url=FROMJAPAN_AFF_URL
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
        [git_exe, "add", "-A"],
        [git_exe, "commit", "-m", "Deploy TikTok crosslink banner, profile links, and TikTok SEO enhancements"],
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
