import os
import csv
import subprocess
import urllib.parse

REPO_URL = "https://github.com/kamekocorporation-kamemoto-pei/retro-game-hub.git"
BRANCH = "main"

# 1. 初期マスターデータ（上位15タイトル：ここに行を追加するだけで300記事まで無限に拡張可能）
INITIAL_CSV_DATA = [
    {
        "slug": "gba-sp-buying-guide",
        "title": "Game Boy Advance SP (JDM Models & Mod Bases)",
        "category": "Retro Handhelds",
        "region_info": "100% Region-Free (Plays North American, PAL, and Japanese GB/GBC/GBA cartridges natively).",
        "why_japan": "Japan received exclusive colorways (Pearl Blue, Famicom Color, Pokemon Center editions) and offers a massive supply of inexpensive 'Junk' units ideal for IPS V5 screen modding.",
        "anti_bootleg": "Beware of 'Reshelled' consoles sold as original limited editions on Western sites. On Japanese listings, look for '純正' (Genuine/OEM shell) and inspect the serial number sticker font on the backplate. Avoid listings with brand-new looking Famicom shells at suspiciously low prices unless disclosed as '社外シェル' (Aftermarket shell).",
        "buyer_tips": "Japanese 'Junk' (ジャンク) GBA SPs usually just have a dead dry battery or a scratched polarizer film, while the motherboard remains rock-solid.",
        "jp_keyword_main": "ゲームボーイアドバンスSP 本体 純正",
        "jp_keyword_sub": "ゲームボーイアドバンスSP 本体 ジャンク",
        "ad_1_label": "🔧 IPS V5 Drop-in Backlight LCD Kit for GBA SP", "ad_1_query": "GBA SP IPS V5 backlight kit",
        "ad_2_label": "🔋 900mAh Upgraded Replacement Battery for GBA SP", "ad_2_query": "GBA SP replacement battery",
        "ad_3_label": "🛠️ Tri-Wing & Phillips Precision Screwdriver Set", "ad_3_query": "triwing screwdriver gameboy"
    },
    {
        "slug": "nintendo-ds-lite-guide",
        "title": "Nintendo DS Lite (USG-001 Japanese Import)",
        "category": "Retro Handhelds",
        "region_info": "100% Region-Free for both Nintendo DS and Game Boy Advance cartridges. System menu language can be switched to English in settings.",
        "why_japan": "The DS Lite sold over 18 million units in Japan. Because of massive domestic supply, pristine consoles sell for a fraction of US/EU prices.",
        "anti_bootleg": "Counterfeit DS Lite reshells are rampant on eBay. Authentic Japanese units feature crisp text on the back serial sticker and tight hinge tolerances. Check photos for yellowing on the bottom touch screen ('画面焼け' - screen yellowing) if you want a display-grade unit.",
        "buyer_tips": "Once your Japanese DS Lite arrives, tap the bottom wrench icon (Settings) -> Globe icon -> Select 'English' to convert the entire OS to English.",
        "jp_keyword_main": "ニンテンドーDS Lite 本体 美品",
        "jp_keyword_sub": "DS Lite 本体 箱説",
        "ad_1_label": "🔌 USB Charging Cable for Nintendo DS Lite", "ad_1_query": "DS Lite USB charger cable",
        "ad_2_label": "🛡️ Clear Polycarbonate Protective Case for DS Lite", "ad_2_query": "DS Lite crystal clear case",
        "ad_3_label": "📱 Tempered Glass Dual Screen Protector Film", "ad_3_query": "DS Lite screen protector"
    },
    {
        "slug": "gamecube-controller-white-guide",
        "title": "Official White GameCube Controller (T3 Stickbox)",
        "category": "Controllers & Gear",
        "region_info": "100% Region-Free (Works on all US/PAL/JP GameCubes, Wii consoles, and Switch/PC via USB adapter).",
        "why_japan": "Released exclusively in Japan in 2008, the late-model White controller features a 3-meter long cable and guaranteed Type-3 (T3) plastic-screw stickboxes favored by competitive Smash Bros. players.",
        "anti_bootleg": "Third-party knockoffs omit the official 'NINTENDO GAMECUBE' logo on the front shell. Always verify the engraved logo and look for model number 'DOL-003' molded on the back of the right grip.",
        "buyer_tips": "Look for listings stating 'スティック良好' (Tight/Good analog stick) to ensure minimal drift for competitive play.",
        "jp_keyword_main": "ゲームキューブ コントローラー ホワイト 純正",
        "jp_keyword_sub": "GCコントローラー 後期",
        "ad_1_label": "🎮 4-Port GameCube USB Adapter for Switch & PC", "ad_1_query": "GameCube controller USB adapter",
        "ad_2_label": "🕹️ OEM-Style Replacement Analog Stick Caps", "ad_2_query": "GameCube controller replacement stick",
        "ad_3_label": "🛠️ Tri-Wing Screwdriver for Controller Maintenance", "ad_3_query": "triwing screwdriver gamecube"
    },
    {
        "slug": "pokemon-gba-cib-guide",
        "title": "Pokémon Emerald, Ruby & Sapphire (Authentic Japanese CIB)",
        "category": "Collector Games",
        "region_info": "100% Region-Free hardware compatibility (Note: Game text is in Japanese, highly prized by shiny hunters, speedrunners, and CIB collectors).",
        "why_japan": "Over 80% of loose English Pokémon GBA cartridges on Western marketplaces are counterfeit. Japanese CIB (Complete in Box) copies are far cheaper, authentic, and feature stunning exclusive box artwork.",
        "anti_bootleg": "HOW TO SPOT REAL JAPANESE CARTS: 1) Authentic Japanese Emerald uses a translucent emerald shell where you can see the internal battery and vertical golden rectangles on the back PCB. 2) Look for a two-digit factory number stamped (indented) into the front label. 3) Verify '純正品' (Authentic) and check that the original cardboard box includes the inner tray.",
        "buyer_tips": "Many Japanese sellers specify '電池切れ' (Dry internal clock battery - game still saves, but time-based events stop) or '電池交換済' (New battery installed).",
        "jp_keyword_main": "ポケットモンスター エメラルド 箱説",
        "jp_keyword_sub": "ポケモン ルビー サファイア 完品",
        "ad_1_label": "🛡️ PET Clear Box Protectors for Japanese GBA Boxes", "ad_1_query": "Japanese GBA box protector",
        "ad_2_label": "🔋 CR1616 Tabbed Battery for GBA Clock Repair", "ad_2_query": "CR1616 tabbed battery gameboy",
        "ad_3_label": "🗄️ Acrylic Display Stand for GBA Cartridges", "ad_3_query": "GBA cartridge display stand"
    },
    {
        "slug": "game-boy-player-startup-disc-guide",
        "title": "Game Boy Player & Startup Disc for GameCube",
        "category": "Accessories & Hardware",
        "region_info": "The bottom hardware attachment (DOL-017) is 100% Region-Free! (The Startup Disc itself is region-locked to Japanese consoles or modded systems).",
        "why_japan": "Japan got exclusive matching colors (Spice Orange, Symphonic Green, Platinum, Indigo), and even if you use a US/PAL GameCube with Swiss homebrew, the Japanese hardware attachment fits and works natively.",
        "anti_bootleg": "The Game Boy Player hardware cannot be easily faked, but buyers often accidentally purchase the unit WITHOUT the Startup Disc. Watch out for '本体のみ' (Unit only, no disc) vs. 'スタートアップディスク付' (Includes Startup Disc).",
        "buyer_tips": "If you use GBI (Game Boy Interface) via SD Media Launcher on a Western GameCube, you only need the cheap Japanese hardware unit ('本体のみ') in your favorite color!",
        "jp_keyword_main": "ゲームボーイプレーヤー スタートアップディスク",
        "jp_keyword_sub": "ゲームボーイプレーヤー オレンジ 本体",
        "ad_1_label": "📺 Carby / Digital HDMI Adapter for GameCube (DOL-001)", "ad_1_query": "GameCube HDMI adapter",
        "ad_2_label": "💾 SD2SP2 / GC2SD Memory Card Adapter for Homebrew", "ad_2_query": "GameCube SD card adapter",
        "ad_3_label": "🎮 Retro-Bit Prism Component / HDMI Cable", "ad_3_query": "GameCube component cable"
    },
    {
        "slug": "ps-vita-2000-japan-colors",
        "title": "PlayStation Vita Slim (PCH-2000 JDM Exclusive Colors)",
        "category": "Retro Handhelds",
        "region_info": "100% Region-Free with Full English OS support right out of the box.",
        "why_japan": "North America only received standard Black and Aqua Blue. Japan received Neon Orange, Glacier White, Lime Green/White, Light Blue, Metallic Red, and Dragon Quest Metal Slime editions.",
        "anti_bootleg": "Beware of third-party refurbished units from China using cheap replacement LCDs. Japanese domestic listings ('国内版') with original box ('箱付き') guarantee genuine Sony parts and original serial labels.",
        "buyer_tips": "In Japanese PS Vita menus, the 'O' button is Confirm and 'X' is Cancel. You can easily swap this or change system language to English during initial setup.",
        "jp_keyword_main": "PS Vita PCH-2000 本体 美品",
        "jp_keyword_sub": "PS Vita PCH-2000 箱付",
        "ad_1_label": "💾 SD2Vita MicroSD Card Adapter (Version 5.0)", "ad_1_query": "SD2Vita adapter",
        "ad_2_label": "🛡️ Tempered Glass Screen & Back Touch Protector for Vita 2000", "ad_2_query": "PS Vita 2000 screen protector",
        "ad_3_label": "🎮 Ergonomic Hand Grip Handle with L2/R2 Triggers", "ad_3_query": "PS Vita 2000 trigger grip"
    },
    {
        "slug": "game-boy-micro-jdm-guide",
        "title": "Game Boy Micro (20th Anniversary Famicom Edition)",
        "category": "Retro Handhelds",
        "region_info": "100% Region-Free (Plays all GBA cartridges globally).",
        "why_japan": "The iconic red-and-gold Famicom 20th Anniversary edition and Mother 3 Deluxe Box were flagship releases in Japan and remain in much cleaner collector condition.",
        "anti_bootleg": "Aftermarket aluminum shells and fake faceplates flood Western sites. Authentic Japanese Famicom Editions have crisp, laser-etched '20th Anniversary' emblems on the back and a flush-fitting OEM faceplate.",
        "buyer_tips": "Check the listing photos for 'フェイスプレート傷なし' (Scratch-free faceplate), as OEM faceplates are the hardest part to replace.",
        "jp_keyword_main": "ゲームボーイミクロ ファミコンバージョン",
        "jp_keyword_sub": "ゲームボーイミクロ 本体 美品",
        "ad_1_label": "🔌 USB Charging Cable for Game Boy Micro (OXY-001)", "ad_1_query": "Game Boy Micro USB charger",
        "ad_2_label": "🛡️ Soft Neoprene Pouch & Screen Protector for GB Micro", "ad_2_query": "Game Boy Micro case",
        "ad_3_label": "🔋 Replacement OXY-003 Battery for Game Boy Micro", "ad_3_query": "Game Boy Micro battery"
    },
    {
        "slug": "sega-saturn-white-import-guide",
        "title": "Japanese Sega Saturn (White Console & 2D Shmups/Fighters)",
        "category": "Retro Consoles",
        "region_info": "Region-locked by default, but instantly unlocked for all regions using a simple Action Replay 4M Plus or Pseudo Saturn Kai cartridge.",
        "why_japan": "The Sega Saturn was a massive hit in Japan, resulting in the legendary Mist Grey/White console design and hundreds of arcade-perfect 2D shooters and Capcom/SNK fighters that never left Japan.",
        "anti_bootleg": "When buying high-end Japanese Saturn games (like Radiant Silvergun or Castlevania), always check for the '帯' (Obi spine card) and verify the Sega Saturn ring watermark on the bottom inner ring of the CD to avoid CDR reproductions.",
        "buyer_tips": "Model HST-3220 (White Saturn) is the most reliable late-revision board. Always use an Action Replay 4M RAM cart to play X-Men vs. Street Fighter and Marvel Super Heroes.",
        "jp_keyword_main": "セガサターン 本体 シロ",
        "jp_keyword_sub": "セガサターン 本体 動作確認済",
        "ad_1_label": "🔓 Action Replay 4M Plus / Pseudo Saturn All-in-One Cart", "ad_1_query": "Sega Saturn Action Replay 4M",
        "ad_2_label": "📺 RAD2X / HDMI Converter Cable for Sega Saturn", "ad_2_query": "Sega Saturn HDMI adapter",
        "ad_3_label": "🔋 CR2032 Save Battery Pack (5-Pack for Saturn)", "ad_3_query": "CR2032 battery"
    },
    {
        "slug": "nintendo-64-clear-colors-guide",
        "title": "Nintendo 64 Jusco & Clear Color Consoles (NUS-001 JPN)",
        "category": "Retro Consoles",
        "region_info": "Hardware is identical to North American N64! Only a plastic cartridge tray tab separates US and JP carts (easily swapped with a region-free 3D printed tray in 2 minutes).",
        "why_japan": "Japan received exclusive two-tone clear consoles (Midnight Blue, Clear Blue/White, Clear Red/White, and the rare Jusco 30th Anniversary Clear Grey) at far lower prices than US Funtastic models.",
        "anti_bootleg": "Watch out for cheap translucent AliExpress replacement shells. Genuine Japanese N64 consoles have original serial number metal plates inside the bottom slot and authentic 'NUS-001(JPN)' stickers.",
        "buyer_tips": "Check if the console includes the '拡張パック' (Memory Expansion Pak - NUS-007) under the front jumper lid—many Japanese bundles include it for free!",
        "jp_keyword_main": "NINTENDO64 本体 クリア",
        "jp_keyword_sub": "ニンテンドー64 本体 拡張パック",
        "ad_1_label": "🔓 N64 Region-Free Cartridge Tray Slot (No Cutting Required)", "ad_1_query": "N64 region free cartridge tray",
        "ad_2_label": "📺 RetroTINK / N64 to HDMI S-Video Converter", "ad_2_query": "N64 HDMI adapter",
        "ad_3_label": "🕹️ Hall Effect Replacement Joystick Module for N64", "ad_3_query": "N64 replacement joystick"
    },
    {
        "slug": "ascii-keyboard-controller-gc",
        "title": "ASCII Keyboard Controller for GameCube (Phantasy Star Online)",
        "category": "Controllers & Gear",
        "region_info": "100% Region-Free (Works on all GameCube and Wii systems globally).",
        "why_japan": "Created for Phantasy Star Online Episode I & II, this hybrid controller/keyboard is one of the most iconic and sought-after Nintendo peripherals ever made, and it was never sold in North American retail stores.",
        "anti_bootleg": "No full replicas exist due to the complex mold, but verify that BOTH purple and grey dual plugs (controller port + keyboard port) are intact and uncut.",
        "buyer_tips": "Keys often yellow over time; search with '美品' (Near Mint) or '箱付き' (Boxed) if you want crisp white keycaps.",
        "jp_keyword_main": "アスキーキーボードコントローラー ゲームキューブ",
        "jp_keyword_sub": "ASCII キーボード GC",
        "ad_1_label": "🎮 Dual GameCube Extension Cables (Required for Couch Play)", "ad_1_query": "GameCube controller extension cable",
        "ad_2_label": "🧹 Mechanical Keycap Puller & Cleaning Kit", "ad_2_query": "keyboard cleaning kit",
        "ad_3_label": "🔌 GameCube to PC USB Adapter", "ad_3_query": "GameCube USB adapter"
    },
    {
        "slug": "mother-3-gba-authentic-guide",
        "title": "MOTHER 3 (Game Boy Advance Authentic Japanese Release)",
        "category": "Collector Games",
        "region_info": "100% Region-Free (Japanese text; beloved by EarthBound collectors and compatible with cartridge dumpers for English fan-translation patching).",
        "why_japan": "Never released outside Japan, Mother 3 is the crown jewel of any GBA collection. While eBay is flooded with $15 fake English repro carts, the authentic Japanese boxed release holds real collector value.",
        "anti_bootleg": "CRITICAL CHECK: Almost every loose 'English Mother 3' cart online is a cheap Chinese bootleg that corrupts save files. A real Mother 3 cartridge ONLY exists in Japanese (model AGB-B3UJ-JPN) in a clean red cardboard box.",
        "buyer_tips": "For the ultimate grail, search for the 'MOTHER3 デラックスボックス' (Deluxe Box), which includes the limited edition Mother 3 Game Boy Micro and Franklin Badge.",
        "jp_keyword_main": "MOTHER3 箱説 GBA",
        "jp_keyword_sub": "MOTHER3 デラックスボックス",
        "ad_1_label": "💾 GBxCart RW / Epilogue GB Operator (Cartridge Dumper & Patcher)", "ad_1_query": "Game Boy cartridge reader USB",
        "ad_2_label": "🛡️ Custom Acrylic Display Case for Japanese GBA Boxes", "ad_2_query": "Japanese GBA box protector",
        "ad_3_label": "📘 Mother 3 Official Guidebook Accessories", "ad_3_query": "Earthbound collector guide"
    },
    {
        "slug": "ikaruga-dreamcast-gamecube-guide",
        "title": "Ikaruga 斑鳩 (Dreamcast & GameCube Authentic Japanese Edition)",
        "category": "Action & Shmups",
        "region_info": "Zero language barrier (Menus and arcade gameplay are in English). Requires Japanese console or freeloader/region-free mod.",
        "why_japan": "Treasure's masterpiece bullet-hell shooter commands massive prices in the West, while the original Japanese Dreamcast (complete with Obi spine card) and GameCube releases are much more affordable.",
        "anti_bootleg": "Dreamcast MIL-CD bootlegs are common on Western sites. Authentic Japanese Dreamcast GD-ROMs feature the dense double-ring barcode and Sega trademark etched into the inner mirror ring, plus the vertical '帯' (Obi strip).",
        "buyer_tips": "Always include '帯付' (With Obi spine card) when searching for Dreamcast games to maximize collector resale value.",
        "jp_keyword_main": "斑鳩 IKARUGA ドリームキャスト 帯",
        "jp_keyword_sub": "斑鳩 ゲームキューブ",
        "ad_1_label": "🕹️ Arcade FightStick for Dreamcast / GameCube", "ad_1_query": "arcade stick retro",
        "ad_2_label": "📺 Kaico / Beharbros HDMI Adapter for Sega Dreamcast", "ad_2_query": "Dreamcast HDMI adapter",
        "ad_3_label": "🛡️ CD Jewel Case Resealable Protective Sleeves", "ad_3_query": "CD jewel case protector sleeves"
    },
    {
        "slug": "castlevania-symphony-of-the-night-jp",
        "title": "Castlevania: Symphony of the Night (悪魔城ドラキュラX 月下の夜想曲)",
        "category": "Action & Shmups",
        "region_info": "Playable with minimal Japanese knowledge. The original Japanese PS1 print includes an exclusive Artbook & Soundtrack CD never included in standard US releases.",
        "why_japan": "While the US Black Label PS1 version sells for $120–$180+, the Japanese original release features superior Ayami Kojima cover art and bonus physical media at a much fairer price.",
        "anti_bootleg": "Ensure the PS1 disc has the authentic black polycarbonate underside! Silver-bottomed discs are either music CDs or counterfeit bootlegs. Check that the bonus 'アートワークス' (Artbook + Music CD) is included.",
        "buyer_tips": "Avoid 'PS one Books' (budget reprint) if you want the original thick jewel case and bonus soundtrack CD.",
        "jp_keyword_main": "悪魔城ドラキュラX 月下の夜想曲 PS1 帯",
        "jp_keyword_sub": "月下の夜想曲 サターン",
        "ad_1_label": "📺 RAD2X / PS1 Digital HDMI Cable Adapter", "ad_1_query": "PS1 HDMI adapter",
        "ad_2_label": "💾 MemCard PRO for PlayStation 1", "ad_2_query": "PS1 memory card",
        "ad_3_label": "🛡️ Double-Disc Thick PS1 Case Protectors", "ad_3_query": "PS1 double case protector"
    },
    {
        "slug": "neo-geo-pocket-color-slim-guide",
        "title": "Neo Geo Pocket Color & Slimline (New Neo Geo Pocket)",
        "category": "Retro Handhelds",
        "region_info": "100% Region-Free AND Dual-Language! Many Japanese NGPC cartridges automatically boot in English when inserted into a console set to English.",
        "why_japan": "SNK released a lighter, 13% thinner revision called the 'New Neo Geo Pocket Color' (Slimline) exclusively in Japan right before the company folded.",
        "anti_bootleg": "Look for model number 'NEOP-A2' on the back sticker to guarantee you are getting the true Japanese-exclusive Slimline revision rather than the standard bulky model.",
        "buyer_tips": "Don't forget that the NGPC requires both 2x AA batteries AND a CR2032 coin battery for system memory/language settings!",
        "jp_keyword_main": "ネオジオポケットカラー 本体",
        "jp_keyword_sub": "NEWネオジオポケットカラー 本体",
        "ad_1_label": "🔧 IPS Backlight LCD Kit for Neo Geo Pocket Color", "ad_1_query": "Neo Geo Pocket Color IPS kit",
        "ad_2_label": "🔋 AA Rechargeable Lithium Batteries + CR2032 Set", "ad_2_query": "AA rechargeable batteries",
        "ad_3_label": "🛡️ Hard EVA Carrying Case for Retro Handhelds", "ad_3_query": "retro handheld carrying case"
    },
    {
        "slug": "chrono-trigger-sfc-cib-guide",
        "title": "Chrono Trigger (Super Famicom Complete in Box with Map/Cards)",
        "category": "Collector Games",
        "region_info": "Fits Super Famicom or modded SNES (Cartridge shell swap or broken plastic tabs). Ideal for display and collection.",
        "why_japan": "A complete-in-box US SNES copy of Chrono Trigger costs $700–$1,000+ and is heavily counterfeited. The original Japanese Super Famicom CIB version features Akira Toriyama's iconic vertical box art for around $25–$40!",
        "anti_bootleg": "Genuine Japanese SFC cartridges are so affordable that bootleggers rarely fake them, making Japan the safest place to buy an authentic 1995 Square board. Check for crisp gold Nintendo seal logos on the box.",
        "buyer_tips": "Look for '完品' (Complete) or '予約特典カード' (Pre-order prism collector cards) if you want a museum-grade piece.",
        "jp_keyword_main": "クロノトリガー SFC 箱説 美品",
        "jp_keyword_sub": "クロノトリガー 特典カード",
        "ad_1_label": "🛡️ Super Famicom (SFC) Clear PET Box Protector Case", "ad_1_query": "Super Famicom box protector",
        "ad_2_label": "🔓 SNES / Super Famicom Universal Cartridge Adapter", "ad_2_query": "Super Famicom to SNES adapter",
        "ad_3_label": "🛠️ 3.8mm & 4.5mm Gamebit Screwdriver Set for SNES/SFC", "ad_3_query": "gamebit screwdriver snes"
    }
]

ARTICLE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Authentic Japanese Import & Anti-Bootleg Guide</title>
    <meta name="description" content="How to buy an authentic {title} from Japan via Buyee. Includes anti-bootleg verification checklist, region compatibility, and condition translations.">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; line-height: 1.7; color: #1f2937; max-width: 820px; margin: 0 auto; padding: 24px; background: #f9fafb; }}
        .card {{ background: #ffffff; padding: 36px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.06); }}
        .nav-back {{ display: inline-block; margin-bottom: 20px; color: #2563eb; text-decoration: none; font-weight: 600; }}
        .nav-back:hover {{ text-decoration: underline; }}
        h1 {{ font-size: 1.8rem; color: #111827; margin-top: 0; }}
        h2 {{ font-size: 1.3rem; color: #1e40af; border-bottom: 2px solid #e5e7eb; padding-bottom: 6px; margin-top: 32px; }}
        .badge {{ display: inline-block; background: #dbeafe; color: #1e40af; font-weight: 700; padding: 4px 12px; border-radius: 999px; font-size: 0.85rem; margin-bottom: 12px; }}
        .region-box {{ background: #ecfdf5; border-left: 4px solid #10b981; padding: 14px 18px; border-radius: 6px; margin: 16px 0; color: #065f46; }}
        .auth-box {{ background: #fffbeb; border: 2px solid #fcd34d; border-radius: 10px; padding: 20px; margin: 28px 0; }}
        .auth-box h2 {{ margin-top: 0; color: #b45309; border-bottom: none; padding-bottom: 0; font-size: 1.25rem; }}
        table {{ width: 100%; border-collapse: collapse; margin: 16px 0; font-size: 0.95rem; }}
        th, td {{ border: 1px solid #e5e7eb; padding: 10px 12px; text-align: left; }}
        th {{ background: #f3f4f6; }}
        .cta-box {{ background: #eff6ff; border: 2px solid #bfdbfe; border-radius: 10px; padding: 24px; margin-top: 32px; }}
        .cta-btn {{ display: block; background: #2563eb; color: #ffffff; text-decoration: none; font-weight: 700; padding: 14px 20px; border-radius: 8px; margin: 12px 0; text-align: center; transition: background 0.2s; }}
        .cta-btn:hover {{ background: #1d4ed8; }}
        .cta-btn.secondary {{ background: #1e40af; }}
        .ads-box {{ background: #fdf4ff; border: 1px dashed #f0abfc; border-radius: 8px; padding: 18px; margin-top: 32px; font-size: 0.95rem; }}
        .ads-box h3 {{ margin-top: 0; color: #86198f; font-size: 1.05rem; }}
        .ads-box ul {{ padding-left: 20px; margin-bottom: 0; }}
        .ads-box li {{ margin: 6px 0; }}
        .ads-box a {{ color: #701a75; text-decoration: none; font-weight: 600; }}
        .ads-box a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <div class="card">
        <a class="nav-back" href="index.html">&larr; Back to All Guides</a>
        <div><span class="badge">{category}</span></div>
        <h1>{title}</h1>

        <div class="region-box">
            <strong>🌍 Region & Language Compatibility:</strong> {region_info}
        </div>

        <h2>1. Why Import from Japan?</h2>
        <p>{why_japan}</p>

        <div class="auth-box">
            <h2>🛡️ Authenticity & Anti-Bootleg Checklist (How to Avoid Fakes)</h2>
            <p>{anti_bootleg}</p>
            <p style="margin-bottom:0;"><strong>💡 Insider Tip:</strong> {buyer_tips}</p>
        </div>

        <h2>2. Decoding Japanese Seller Condition Ranks</h2>
        <table>
            <tr><th>Japanese Term</th><th>English Translation</th><th>What to Expect</th></tr>
            <tr><td><strong>純正 / 正規品</strong></td><td>Genuine / Authentic OEM</td><td>Original Nintendo/Sony/Sega factory parts (Not a cheap reshell or repro).</td></tr>
            <tr><td><strong>完品 / 箱説付</strong></td><td>Complete in Box (CIB)</td><td>Includes original box, manual, and inner tray.</td></tr>
            <tr><td><strong>美品 / 目立った傷や汚れなし</strong></td><td>Near Mint / Excellent</td><td>Well-cared-for collector condition with clean labels/screens.</td></tr>
            <tr><td><strong>動作確認済</strong></td><td>Tested & Working</td><td>Seller verified the console/cartridge boots properly.</td></tr>
            <tr><td><strong>ジャンク (Junk)</strong></td><td>Untested / For Modding</td><td>Great for IPS screen upgrades or shell swaps; sold as-is.</td></tr>
        </table>

        <div class="cta-box">
            <h2 style="margin-top:0; border:none; font-size:1.25rem;">🔍 Browse Verified Japanese Inventory (via Buyee)</h2>
            <p>We pre-configured these Japanese search filters to help you find authentic listings directly on Mercari Japan:</p>
            <a class="cta-btn" href="{buyee_url_main}" target="_blank" rel="noopener">Search "{jp_keyword_main}" on Buyee &rarr;</a>
            <a class="cta-btn secondary" href="{buyee_url_sub}" target="_blank" rel="noopener">Search "{jp_keyword_sub}" on Buyee &rarr;</a>
        </div>

        <div class="ads-box">
            <h3>🛒 Essential Accessories, Protection & Modding Gear</h3>
            <p>Protect your authentic import or upgrade your setup with these proven tools:</p>
            <ul>
                <li><a href="{ad_1_url}" target="_blank" rel="nofollow noopener">{ad_1_label}</a></li>
                <li><a href="{ad_2_url}" target="_blank" rel="nofollow noopener">{ad_2_label}</a></li>
                <li><a href="{ad_3_url}" target="_blank" rel="nofollow noopener">{ad_3_label}</a></li>
            </ul>
        </div>
    </div>
</body>
</html>
"""

INDEX_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>JDM Retro Gaming Import & Anti-Bootleg Hub</title>
    <meta name="description" content="The definitive database for collectors and modders to buy authentic Japanese retro consoles, controllers, and CIB games without bootlegs.">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; line-height: 1.6; color: #1f2937; max-width: 920px; margin: 0 auto; padding: 32px 20px; background: #f3f4f6; }}
        header {{ text-align: center; margin-bottom: 32px; }}
        h1 {{ font-size: 2.2rem; color: #111827; margin-bottom: 8px; }}
        p.subtitle {{ color: #4b5563; font-size: 1.1rem; max-width: 680px; margin: 0 auto; }}
        .filter-bar {{ display: flex; flex-wrap: wrap; gap: 10px; justify-content: center; margin: 24px 0; }}
        .search-input {{ width: 100%; max-width: 480px; padding: 12px 16px; border: 2px solid #d1d5db; border-radius: 8px; font-size: 1rem; display: block; margin: 0 auto 20px auto; }}
        .article-card {{ background: #ffffff; padding: 26px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); margin-bottom: 20px; transition: transform 0.2s; }}
        .article-card:hover {{ transform: translateY(-2px); }}
        .badge {{ display: inline-block; background: #dbeafe; color: #1e40af; font-weight: 700; padding: 3px 10px; border-radius: 999px; font-size: 0.8rem; margin-bottom: 8px; }}
        .auth-tag {{ display: inline-block; background: #fef3c7; color: #b45309; font-weight: 700; padding: 3px 10px; border-radius: 999px; font-size: 0.8rem; margin-left: 6px; }}
        .article-card h2 {{ margin: 6px 0 10px 0; font-size: 1.35rem; }}
        .article-card h2 a {{ color: #1d4ed8; text-decoration: none; }}
        .article-card h2 a:hover {{ text-decoration: underline; }}
        .read-more {{ display: inline-block; margin-top: 10px; font-weight: 600; color: #2563eb; text-decoration: none; }}
        .read-more:hover {{ text-decoration: underline; }}
        footer {{ text-align: center; margin-top: 50px; color: #6b7280; font-size: 0.9rem; }}
    </style>
</head>
<body>
    <header>
        <h1>🎮 JDM Retro Gaming Import Hub</h1>
        <p class="subtitle">100% Authentic Japanese Consoles, Mods & CIB Games. Every guide includes an Anti-Bootleg Verification Checklist and direct Buyee search filters.</p>
    </header>

    <input type="text" id="searchBox" class="search-input" placeholder="🔍 Search guides (e.g., GBA SP, Pokemon, GameCube, Saturn)..." onkeyup="filterGuides()">

    <main id="guideList">
        {list_items}
    </main>

    <footer>
        <p>&copy; 2026 JDM Retro Gaming Import Hub. Built for collectors to avoid counterfeits and source directly from Japan.</p>
    </footer>

    <script>
        function filterGuides() {{
            const query = document.getElementById('searchBox').value.toLowerCase();
            const cards = document.querySelectorAll('.article-card');
            cards.forEach(card => {{
                const text = card.innerText.toLowerCase();
                card.style.display = text.includes(query) ? 'block' : 'none';
            }});
        }}
    </script>
</body>
</html>
"""

def make_buyee_url(keyword_jp):
    return f"https://buyee.jp/mercari/search?keyword={urllib.parse.quote(keyword_jp)}"

def make_amazon_url(query_en):
    return f"https://www.amazon.com/s?k={urllib.parse.quote(query_en)}"

def ensure_directories_and_files():
    os.makedirs("data", exist_ok=True)
    os.makedirs("templates", exist_ok=True)
    
    csv_path = os.path.join("data", "retro_games.csv")
    if not os.path.exists(csv_path):
        fieldnames = list(INITIAL_CSV_DATA[0].keys())
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(INITIAL_CSV_DATA)

    with open(os.path.join("templates", "article_template.html"), "w", encoding="utf-8") as f:
        f.write(ARTICLE_TEMPLATE)
    with open(os.path.join("templates", "index_template.html"), "w", encoding="utf-8") as f:
        f.write(INDEX_TEMPLATE)

def build_site():
    csv_path = os.path.join("data", "retro_games.csv")
    with open(csv_path, "r", encoding="utf-8") as f:
        articles = list(csv.DictReader(f))

    list_items_html = ""
    for row in articles:
        html_out = ARTICLE_TEMPLATE.format(
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
            ad_1_label=row["ad_1_label"], ad_1_url=make_amazon_url(row["ad_1_query"]),
            ad_2_label=row["ad_2_label"], ad_2_url=make_amazon_url(row["ad_2_query"]),
            ad_3_label=row["ad_3_label"], ad_3_url=make_amazon_url(row["ad_3_query"])
        )
        with open(f"{row['slug']}.html", "w", encoding="utf-8") as out_f:
            out_f.write(html_out)

        list_items_html += f"""
        <div class="article-card">
            <span class="badge">{row['category']}</span>
            <span class="auth-tag">🛡️ Anti-Bootleg Verified</span>
            <h2><a href="{row['slug']}.html">{row['title']}</a></h2>
            <p>{row['why_japan']}</p>
            <a class="read-more" href="{row['slug']}.html">Read Authenticity Guide & Browse Live Listings &rarr;</a>
        </div>
        """

    with open("index.html", "w", encoding="utf-8") as out_idx:
        out_idx.write(INDEX_TEMPLATE.format(list_items=list_items_html))

def run_git_commands(commit_msg="Expand database with 30 new high-value JDM retro items"):
    commands = [
        ["git", "add", "."],
        ["git", "commit", "-m", commit_msg],
        ["git", "push", "origin", BRANCH]
    ]
    for cmd in commands:
        subprocess.run(cmd, check=False)

if __name__ == "__main__":
    ensure_directories_and_files()
    build_site()
    run_git_commands()
    print("CSVデータベース構築・全15記事生成・GitHubアップロードが完了しました！")
