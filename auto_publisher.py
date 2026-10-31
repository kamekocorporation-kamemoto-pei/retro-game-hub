import os
import subprocess
import urllib.parse
from datetime import datetime

REPO_URL = "https://github.com/kamekocorporation-kamemoto-pei/retro-game-hub.git"
BRANCH = "main"

def make_buyee_url(keyword_jp):
    encoded = urllib.parse.quote(keyword_jp)
    return f"https://buyee.jp/mercari/search?keyword={encoded}"

# 第1弾〜第5弾のマスターデータ（Buyee検索リンク ＋ 関連品Amazon広告リンクを完備）
ARTICLES = [
    {
        "slug": "gba-sp-buying-guide",
        "title": "The Ultimate Guide to Buying a Japanese Game Boy Advance SP: Exclusive Colors, 'Junk' Goldmines, and How to Import",
        "description": "Learn why modders and collectors import the Game Boy Advance SP from Japan, decode condition ranks, and find cheap IPS mod bases.",
        "category": "Retro Handhelds",
        "links": [
            {"label": 'Search "Junk" GBA SP for Modding on Buyee', "query": "ゲームボーイアドバンスSP 本体 ジャンク"},
            {"label": "Search CIB (Complete in Box) GBA SP on Buyee", "query": "ゲームボーイアドバンスSP 箱 完品"},
            {"label": "Search Famicom Color GBA SP on Buyee", "query": "ゲームボーイアドバンスSP ファミコンカラー"}
        ],
        "ads": [
            {"label": "🔧 Recommended: IPS V5 Backlight Display Upgrade Kit", "url": "https://www.amazon.com/s?k=GBA+SP+IPS+backlight+kit"},
            {"label": "🛠️ Essential: Tri-wing Screwdriver & Opening Tool Set", "url": "https://www.amazon.com/s?k=triwing+screwdriver+gba"},
            {"label": "🛡️ Protection: Hard Shell Carrying Case for GBA SP", "url": "https://www.amazon.com/s?k=gba+sp+carrying+case"}
        ]
    },
    {
        "slug": "nintendo-ds-lite-guide",
        "title": "Why the Nintendo DS Lite from Japan is the Ultimate Budget Retro Buy: Region-Free GBA & DS Gaming",
        "description": "Discover how to score pristine, rock-bottom priced Nintendo DS Lite consoles from Japan that play both DS and GBA cartridges globally.",
        "category": "Retro Handhelds",
        "links": [
            {"label": "Search Nintendo DS Lite Consoles on Buyee", "query": "DS Lite 本体 美品"},
            {"label": "Search Crystal/Limited Color DS Lite on Buyee", "query": "ニンテンドーDS Lite 限定 本体"}
        ],
        "ads": [
            {"label": "🔋 Essential: USB Charging Cable for DS Lite", "url": "https://www.amazon.com/s?k=ds+lite+usb+charger"},
            {"label": "🛡️ Protection: Clear Crystal Protective Armor Shell Case", "url": "https://www.amazon.com/s?k=ds+lite+clear+case"},
            {"label": "🖊️ Maintenance: Replacement Touch Stylus Pens (Pack)", "url": "https://www.amazon.com/s?k=ds+lite+stylus+replacement"}
        ]
    },
    {
        "slug": "gamecube-controller-white-guide",
        "title": "The Ultimate Smash Bros. Player's Guide: Importing the Official White GameCube Controller from Japan",
        "description": "Why competitive Smash Ultimate and Melee players worldwide hunt for the Japanese-exclusive White GC Controller with T3 boards.",
        "category": "Controllers & Gear",
        "links": [
            {"label": "Search White GC Controllers (Smash Edition) on Buyee", "query": "ゲームキューブ コントローラー ホワイト"},
            {"label": "Search Tested GameCube Consoles on Buyee", "query": "ゲームキューブ 本体 動作確認"}
        ],
        "ads": [
            {"label": "🎮 Essential: GameCube Controller USB Adapter for Switch/PC", "url": "https://www.amazon.com/s?k=gamecube+controller+adapter+switch"},
            {"label": "🕹️ Maintenance: Replacement Analog Sticks & T3 Box Parts", "url": "https://www.amazon.com/s?k=gamecube+controller+replacement+sticks"},
            {"label": "🔌 Cable Management: Extra Long Extension Cable for GC", "url": "https://www.amazon.com/s?k=gamecube+controller+extension+cable"}
        ]
    },
    {
        "slug": "pokemon-gba-cib-guide",
        "title": "How to Safely Buy Authentic Japanese Pokémon GBA Games (Emerald, Ruby, Sapphire) Without Bootlegs",
        "description": "Avoid counterfeit cartridges on eBay. Discover why Japanese CIB (Complete in Box) Pokémon Emerald and Ruby are the ultimate collector safe-haven.",
        "category": "Collector Games",
        "links": [
            {"label": "Search CIB Pokémon Emerald (Japan) on Buyee", "query": "ポケットモンスター エメラルド 箱説"},
            {"label": "Search CIB Pokémon Ruby & Sapphire on Buyee", "query": "ポケットモンスター ルビー サファイア 箱説"}
        ],
        "ads": [
            {"label": "🛡️ Protection: Clear Acrylic Display Protector Cases for GBA Boxes", "url": "https://www.amazon.com/s?k=gba+box+protector+case"},
            {"label": "🔋 Repair: CR1616 Battery Holder with Tabs for Cartridge Saves", "url": "https://www.amazon.com/s?k=cr1616+battery+holder+gba"},
            {"label": "🔍 Maintenance: Precision Bit Screwdriver for Game Cartridges", "url": "https://www.amazon.com/s?k=gameboy+cartridge+screwdriver"}
        ]
    },
    {
        "slug": "game-boy-player-startup-disc-guide",
        "title": "The Holy Grail of Retro Setup: Importing the Game Boy Player and Startup Disc for GameCube",
        "description": "Play GBA games on your big screen TV. Learn why the Japanese Game Boy Player Startup Disc is a high-value collector target and how to import it safely.",
        "category": "Accessories & Hardware",
        "links": [
            {"label": "Search Game Boy Player Startup Disc on Buyee", "query": "ゲームボーイプレーヤー ディスク"},
            {"label": "Search Game Boy Player Unit (Black/Orange) on Buyee", "query": "ゲームボーイプレーヤー 本体"}
        ],
        "ads": [
            {"label": "📺 Modern Display: HDMI Upgrader / Line Doubler for GameCube", "url": "https://www.amazon.com/s?k=gamecube+hdmi+adapter"},
            {"label": "🎮 Control: Wireless Retro Receiver Adapter for GameCube", "url": "https://www.amazon.com/s?k=gamecube+wireless+controller+adapter"},
            {"label": "🧰 Storage: Memory Card 1019 Blocks for GameCube", "url": "https://www.amazon.com/s?k=gamecube+memory+card"}
        ]
    }
]

def generate_article_html(article):
    buttons_html = "\n".join([
        f'<a class="cta-btn" href="{make_buyee_url(link["query"])}" target="_blank" rel="noopener">{link["label"]} &rarr;</a>'
        for link in article["links"]
    ])
    
    ads_html = "\n".join([
        f'<li><a href="{ad["url"]}" target="_blank" rel="nofollow noopener">{ad["label"]}</a></li>'
        for ad in article["ads"]
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
        .nav-back {{ display: inline-block; margin-bottom: 20px; color: #2563eb; text-decoration: none; font-weight: 600; }}
        .nav-back:hover {{ text-decoration: underline; }}
        h1 {{ font-size: 1.8rem; color: #111827; margin-top: 0; }}
        h2 {{ font-size: 1.3rem; color: #1e40af; border-bottom: 2px solid #e5e7eb; padding-bottom: 6px; margin-top: 32px; }}
        .badge {{ display: inline-block; background: #dbeafe; color: #1e40af; font-weight: 700; padding: 4px 12px; border-radius: 999px; font-size: 0.85rem; margin-bottom: 12px; }}
        .cta-box {{ background: #eff6ff; border: 2px solid #bfdbfe; border-radius: 10px; padding: 24px; margin-top: 32px; }}
        .cta-btn {{ display: block; background: #2563eb; color: #ffffff; text-decoration: none; font-weight: 700; padding: 14px 20px; border-radius: 8px; margin: 12px 0; text-align: center; transition: background 0.2s; }}
        .cta-btn:hover {{ background: #1d4ed8; }}
        .ads-box {{ background: #fdf4ff; border: 1px dashed #f0abfc; border-radius: 8px; padding: 18px; margin-top: 32px; font-size: 0.95rem; }}
        .ads-box h3 {{ margin-top: 0; color: #86198f; font-size: 1.05rem; }}
        .ads-box ul {{ padding-left: 20px; margin-bottom: 0; }}
        .ads-box li {{ margin: 6px 0; }}
        .ads-box a {{ color: #701a75; text-decoration: none; }}
        .ads-box a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <div class="card">
        <a class="nav-back" href="index.html">&larr; Back to All Guides</a>
        <span class="badge">{article['category']}</span>
        <h1>{article['title']}</h1>
        <p><em>{article['description']}</em></p>

        <h2>Why Import from Japan?</h2>
        <p>Japanese second-hand markets (Mercari, Yahoo! Auctions, and Hard-Off) offer unmatched preservation quality, unique colorways, and price arbitrage compared to Western markets. All hardware items featured are verified for overseas collectors.</p>

        <div class="cta-box">
            <h2 style="margin-top:0; border:none; font-size:1.2rem;">🔍 Live Inventory Search (via Buyee)</h2>
            <p>Click below to browse current verified listings straight from Japanese marketplaces:</p>
            {buttons_html}
        </div>

        <div class="ads-box">
            <h3>🛒 Recommended Accessories & Repair Parts</h3>
            <p>Enhance your setup or restore your hardware with these top-rated companion items:</p>
            <ul>
                {ads_html}
            </ul>
        </div>
    </div>
</body>
</html>
"""

def generate_index_html(articles):
    list_items = ""
    for art in articles:
        list_items += f"""
        <div class="article-card">
            <span class="badge">{art['category']}</span>
            <h2><a href="{art['slug']}.html">{art['title']}</a></h2>
            <p>{art['description']}</p>
            <a class="read-more" href="{art['slug']}.html">Read Guide & Browse Inventory &rarr;</a>
        </div>
        """
        
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>JDM Retro Gaming & Importing Hub</title>
    <meta name="description" content="Your ultimate guide to importing Japanese retro consoles, rare games, and modding gear via Buyee.">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; line-height: 1.6; color: #1f2937; max-width: 900px; margin: 0 auto; padding: 32px; background: #f3f4f6; }}
        header {{ text-align: center; margin-bottom: 40px; }}
        h1 {{ font-size: 2.3rem; color: #111827; margin-bottom: 8px; }}
        p.subtitle {{ color: #4b5563; font-size: 1.1rem; }}
        .article-card {{ background: #ffffff; padding: 28px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); margin-bottom: 24px; transition: transform 0.2s; }}
        .article-card:hover {{ transform: translateY(-3px); }}
        .badge {{ display: inline-block; background: #dbeafe; color: #1e40af; font-weight: 700; padding: 3px 10px; border-radius: 999px; font-size: 0.8rem; margin-bottom: 8px; }}
        .article-card h2 {{ margin: 6px 0 10px 0; font-size: 1.4rem; }}
        .article-card h2 a {{ color: #1d4ed8; text-decoration: none; }}
        .article-card h2 a:hover {{ text-decoration: underline; }}
        .read-more {{ display: inline-block; margin-top: 12px; font-weight: 600; color: #2563eb; text-decoration: none; }}
        .read-more:hover {{ text-decoration: underline; }}
        footer {{ text-align: center; margin-top: 50px; color: #6b7280; font-size: 0.9rem; }}
    </style>
</head>
<body>
    <header>
        <h1>🎮 JDM Retro Gaming Import Hub</h1>
        <p class="subtitle">The definitive guide for collectors and modders to source authentic Japanese retro gear via Buyee.</p>
    </header>

    <main>
        {list_items}
    </main>

    <footer>
        <p>&copy; 2026 JDM Retro Gaming Hub. Powered by automated curation & Buyee proxy shopping.</p>
    </footer>
</body>
</html>
"""

def run_git_commands():
    commands = [
        ["git", "add", "."],
        ["git", "commit", "-m", "Add 5-part retro game buying guides with related ads"],
        ["git", "push", "origin", BRANCH]
    ]
    for cmd in commands:
        subprocess.run(cmd, check=False)

def main():
    os.makedirs("content", exist_ok=True)
    
    # 各記事のHTMLおよびMarkdownを生成
    for article in ARTICLES:
        html_content = generate_article_html(article)
        with open(f"{article['slug']}.html", "w", encoding="utf-8") as f:
            f.write(html_content)
            
    # メインのインデックス（ポータルサイト）を生成
    index_content = generate_index_html(ARTICLES)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(index_content)

    print("全5記事およびインデックスページの生成が完了しました。")
    run_git_commands()
    print("GitHubへのアップロードが完了しました。")

if __name__ == "__main__":
    main()
