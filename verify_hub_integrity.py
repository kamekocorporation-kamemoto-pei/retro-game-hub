# -*- coding: utf-8 -*-
"""
JDM Retro Gaming Hub - Factory Infrastructure Integrity Auditor
Verifies compliance across Web Media, Protected Constants, SEO Assets,
Video Rendering Queues, and SNS Automation.
"""

import os
import sys
import re
import json
from pathlib import Path

# Force UTF-8 stdout
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = Path(__file__).resolve().parent
MANIFEST_PATH = BASE_DIR / "organization_manifest.json"

class HubIntegrityAuditor:
    def __init__(self):
        self.results = []
        self.manifest = self._load_manifest()

    def _load_manifest(self):
        if not MANIFEST_PATH.exists():
            return None
        with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    def log(self, category: str, test_name: str, passed: bool, detail: str = ""):
        self.results.append({
            "category": category,
            "test": test_name,
            "status": "PASS" if passed else "FAIL",
            "detail": detail
        })

    def audit_manifest(self):
        cat = "01. Organization Manifest"
        if not self.manifest:
            self.log(cat, "organization_manifest.json exists", False, "File not found")
            return

        self.log(cat, "organization_manifest.json exists", True, f"Version {self.manifest.get('version')}")
        
        constants = self.manifest.get("protected_constants", {})
        expected_keys = [
            "ga4_measurement_id", "fromjapan_affiliate_id",
            "amazon_us_store_id", "amazon_jp_store_id"
        ]
        all_const = all(constants.get(k) for k in expected_keys)
        self.log(cat, "Protected constants defined", all_const, f"{len(constants)} constants registered")

        departments = self.manifest.get("departments", {})
        has_8_dept = len(departments) == 8
        self.log(cat, "8 Specialized Departments mapped", has_8_dept, f"{len(departments)}/8 departments found")

    def audit_web_media(self):
        cat = "02. Web Media & Protected Constants"
        constants = self.manifest.get("protected_constants", {}) if self.manifest else {}
        ga4_id = constants.get("ga4_measurement_id", "G-L84SX664FD")
        fj_id = constants.get("fromjapan_affiliate_id", "A26382")
        us_amz = constants.get("amazon_us_store_id", "kameko0613-20")
        jp_amz = constants.get("amazon_jp_store_id", "kameko084-22")
        tiktok_url = "https://www.tiktok.com/@jdm_retro_gaming_hub"

        # Check index.html
        idx_path = BASE_DIR / "index.html"
        if not idx_path.exists():
            self.log(cat, "index.html existence", False, "Missing index.html")
        else:
            idx_txt = idx_path.read_text(encoding="utf-8", errors="ignore")
            has_ga4 = ga4_id in idx_txt
            has_sameas = tiktok_url in idx_txt
            has_footer = "Follow @jdm_retro_gaming_hub on TikTok" in idx_txt or tiktok_url in idx_txt
            self.log(cat, "index.html GA4 tracking tag", has_ga4, f"ID: {ga4_id}")
            self.log(cat, "index.html JSON-LD sameAs TikTok", has_sameas, f"URL: {tiktok_url}")
            self.log(cat, "index.html TikTok footer link", has_footer, "Profile link present")

        # Check representative article HTML files
        sample_articles = [
            "001_gba-sp-buying-guide.html",
            "gba-sp-buying-guide.html",
            "super-famicom-1chip-guide.html",
            "sega-dreamcast-ntsc-j-guide.html"
        ]
        checked_article = None
        for sa in sample_articles:
            p = BASE_DIR / sa
            if p.exists():
                checked_article = p
                break

        if not checked_article:
            # Fallback to any article HTML
            for h in BASE_DIR.glob("*.html"):
                if h.name != "index.html":
                    checked_article = h
                    break

        if not checked_article:
            self.log(cat, "Article HTML files existence", False, "No article HTML found")
        else:
            art_txt = checked_article.read_text(encoding="utf-8", errors="ignore")
            self.log(cat, f"Article GA4 tag ({checked_article.name})", ga4_id in art_txt, f"ID: {ga4_id}")
            self.log(cat, f"Article FROM JAPAN affiliate ({checked_article.name})", fj_id in art_txt, f"ID: {fj_id}")
            self.log(cat, f"Article US Amazon affiliate ({checked_article.name})", us_amz in art_txt, f"Tag: {us_amz}")
            self.log(cat, f"Article JP Amazon affiliate ({checked_article.name})", jp_amz in art_txt, f"Tag: {jp_amz}")
            self.log(cat, f"Article TikTok crosslink banner ({checked_article.name})", "Watch 60-Second Visual Authenticity Check on TikTok" in art_txt, "Hero crosslink card verified")
            self.log(cat, f"Article JSON-LD sameAs ({checked_article.name})", tiktok_url in art_txt, "Structured data verified")

    def audit_seo_crawler_files(self):
        cat = "03. SEO Analytics & Crawler Files"
        target_files = ["sitemap.xml", "sitemap-main.xml", "robots.txt"]
        for fname in target_files:
            fpath = BASE_DIR / fname
            if not fpath.exists():
                self.log(cat, f"{fname} existence", False, "File missing")
                continue

            raw_bytes = fpath.read_bytes()
            has_bom = raw_bytes.startswith(b"\xef\xbb\xbf")
            is_valid_size = len(raw_bytes) > 20
            self.log(cat, f"{fname} clean BOM-free UTF-8", not has_bom and is_valid_size,
                     f"BOM: {'DETECTED (FAIL)' if has_bom else 'None (Clean)'}, Size: {len(raw_bytes)} bytes")

    def audit_video_queue(self):
        cat = "04. Video Production Queue (#009-#022)"
        drive_ready = Path(r"E:\JDM_Retro_Hub_Videos\03_Ready_to_Post")
        alt_ready = BASE_DIR / "marketing_tools" / "drive_staging" / "JDM_Retro_Hub_Videos" / "03_Ready_to_Post"
        target_dir = drive_ready if drive_ready.exists() else alt_ready

        if not target_dir.exists():
            self.log(cat, "03_Ready_to_Post directory existence", False, f"Not found at {target_dir}")
            return

        self.log(cat, "03_Ready_to_Post directory access", True, f"Located at: {target_dir}")

        missing_videos = []
        found_videos = []
        for i in range(9, 23):
            prefix = f"{i:03d}_"
            matches = list(target_dir.glob(f"{prefix}*.mp4"))
            if not matches:
                # also check recursive in case synced to subfolders
                matches = list(target_dir.parent.glob(f"**/{prefix}*.mp4"))
            
            if matches and matches[0].stat().st_size > 500000:
                found_videos.append((i, matches[0].name, matches[0].stat().st_size))
            else:
                missing_videos.append(f"#{i:03d}")

        all_present = len(missing_videos) == 0
        detail_msg = f"{len(found_videos)}/14 videos verified (>500KB)" if all_present else f"Missing: {', '.join(missing_videos)}"
        self.log(cat, "Posting Queue #009-#022 (11/14-11/27) completeness", all_present, detail_msg)

        # Also verify #023-#029 English + Multilingual (ES, FR, DE) MP4s
        drive_root = target_dir.parent
        missing_23_29 = []
        for i in range(23, 30):
            prefix = f"{i:03d}_"
            en_matches = list(drive_root.glob(f"{prefix}*.mp4")) or list(target_dir.glob(f"{prefix}*.mp4"))
            if not en_matches:
                missing_23_29.append(f"EN#{i:03d}")
            for lang in ["es", "fr", "de"]:
                m_matches = list((drive_root / "multilingual" / lang).glob(f"{prefix}*.mp4"))
                if not m_matches:
                    missing_23_29.append(f"{lang.upper()}#{i:03d}")
        all_23_29 = len(missing_23_29) == 0
        self.log(
            cat,
            "Batch #023-#029 4-Language MP4s (EN/ES/FR/DE)",
            all_23_29,
            "28/28 multilingual MP4s verified" if all_23_29 else f"Missing: {', '.join(missing_23_29[:6])}",
        )

    def audit_tiktok_seo_scripts(self):
        cat = "05. TikTok Scripts SEO Golden Template"
        scripts_path = BASE_DIR / "marketing_tools" / "tiktok_scripts_150.json"
        if not scripts_path.exists():
            self.log(cat, "tiktok_scripts_150.json existence", False, "File missing")
            return

        with open(scripts_path, "r", encoding="utf-8") as f:
            scripts = json.load(f)

        self.log(cat, "Master scripts count (全150品目)", len(scripts) == 150, f"Total items: {len(scripts)}")

        seo_target_items = [s for s in scripts if s.get("id", 0) >= 12]
        seo_passed = []
        seo_failed = []

        forbidden_words = [
            "check link in bio", "links in our bio", "direct", "inventory",
            "fake", "buy", "trap", "scam", "proxy"
        ]

        valid_pattern_prefixes = (
            "Authentic Japanese ",
            "How to Identify an Authentic ",
            "Complete JDM Collector's Guide: ",
        )

        for item in seo_target_items:
            iid = item.get("id")
            caption = item.get("caption", "")
            first_line = caption.split("\n")[0] if caption else ""

            # Check 1: Caption matches one of 4 valid safe collector patterns
            has_valid_header = (
                first_line.startswith(valid_pattern_prefixes) or
                ("Japanese Import & OEM Authenticity Guide" in first_line)
            )

            # Check 2: Zero forbidden moderation trigger words
            has_forbidden = False
            for fw in forbidden_words:
                pat = r"\b" + re.escape(fw) + r"\b" if " " not in fw else re.escape(fw)
                if re.search(pat, caption, re.IGNORECASE):
                    has_forbidden = True
                    break

            if has_valid_header and not has_forbidden:
                seo_passed.append(iid)
            else:
                seo_failed.append(iid)

        all_seo_valid = len(seo_failed) == 0
        detail_msg = f"{len(seo_passed)}/139 items fully safe & compliant" if all_seo_valid else f"Failed items: {seo_failed[:5]}..."
        self.log(cat, "TikTok Safe Collector Captions (#012-#150)", all_seo_valid, detail_msg)

        # Check 3: Zero Japanese characters or missing-word holes ("歯抜け") in slide fields (#023-#150)
        import csv as _csv
        jp_re = re.compile(r"[\u3000-\u303F\u3040-\u309F\u30A0-\u30FF\uFF00-\uFFEF\u4E00-\u9FAF]")
        gap_issues = []
        for item in scripts:
            iid = item.get("id", 0)
            if iid < 23:
                continue
            if jp_re.search(item.get("model_code", "")):
                gap_issues.append(f"JSON#{iid:03d}_model_code")
            for s in item.get("slides", []):
                dt = s.get("display_text", "")
                if jp_re.search(dt) or "  " in dt:
                    gap_issues.append(f"JSON#{iid:03d}_s{s.get('slide')}")
        csv_path = BASE_DIR / "data" / "retro_games.csv"
        if csv_path.exists():
            with open(csv_path, "r", encoding="utf-8") as cf:
                for idx, row in enumerate(_csv.DictReader(cf), 1):
                    if idx < 23:
                        continue
                    for fld in ("region_info", "why_japan", "buyer_tips"):
                        val = row.get(fld, "")
                        if jp_re.search(val) or "  " in val:
                            gap_issues.append(f"CSV#{idx:03d}_{fld}")
        no_gaps = len(gap_issues) == 0
        self.log(
            cat,
            "Slide Text Japanese/Gap Zero Audit (#023-#150)",
            no_gaps,
            "128/128 items 0 Japanese holes & 0 double-spaces" if no_gaps else f"Issues: {gap_issues[:5]}",
        )

    def audit_sns_automation(self):
        cat = "06. SNS Automation Script"
        poster_path = BASE_DIR / "marketing_tools" / "tiktok_auto_poster.py"
        if not poster_path.exists():
            self.log(cat, "tiktok_auto_poster.py existence", False, "File missing")
            return

        txt = poster_path.read_text(encoding="utf-8", errors="ignore")
        has_custom_comments = "CUSTOM_PINNED_COMMENTS" in txt
        has_dynamic_template = "generate_pinned_comment" in txt or "DEFAULT_PINNED_COMMENT" in txt
        has_slug_mapping = "CUSTOM_PINNED_COMMENTS_BY_SLUG" in txt

        self.log(cat, "Custom Pinned Comments (#016-#022)", has_custom_comments or has_slug_mapping, "Individual pinning logic present")
        self.log(cat, "Dynamic Pinned Comment Engine (#023+)", has_dynamic_template, "Generalized template generator active")

    def audit_gcp_and_studio_4k(self):
        cat = "07. GCP Budget Tracker & 4K Studio Assets"
        studio_dir = BASE_DIR / "images" / "products_studio_4k"
        studio_files = list(studio_dir.glob("*.jpg")) if studio_dir.exists() else []
        self.log(cat, "Imagen 3 4K Studio Images (#023-#029)", len(studio_files) >= 7, f"{len(studio_files)}/7 4K studio masters verified")

        status_path = BASE_DIR / "logs" / "gcp_budget_status.json"
        ledger_path = BASE_DIR / "logs" / "gcp_cost_ledger.csv"
        has_budget = status_path.exists() and ledger_path.exists()
        detail = "16,000 JPY budget ledger active"
        if has_budget:
            try:
                st = json.loads(status_path.read_text(encoding="utf-8"))
                eff_spent = st.get("total_effective_spent_jpy", 0.0)
                theo_spent = st.get("total_spent_jpy", 0.0)
                eff_rem = st.get("total_effective_remaining_jpy", 16000.0)
                detail = f"Actual(Free-Adj): {eff_spent:.2f} JPY (Theo: {theo_spent:.2f} JPY) / Rem: {eff_rem:,.2f} JPY"
            except Exception:
                pass
        self.log(cat, "GCP Cost Tracker (16,000 JPY Cap)", has_budget, detail)

    def run_all(self):
        self.audit_manifest()
        self.audit_web_media()
        self.audit_seo_crawler_files()
        self.audit_video_queue()
        self.audit_tiktok_seo_scripts()
        self.audit_sns_automation()
        self.audit_gcp_and_studio_4k()
        self.print_report()
        try:
            sys.path.insert(0, str(BASE_DIR / "marketing_tools"))
            from gcp_cost_tracker import GCPCostTracker
            GCPCostTracker().print_free_tier_report()
        except Exception as e:
            print(f"[!] Warning invoking GCPCostTracker.print_free_tier_report(): {e}")

    def print_report(self):
        total = len(self.results)
        passed = sum(1 for r in self.results if r["status"] == "PASS")
        failed = total - passed

        print("\n" + "=" * 80)
        print(" JDM RETRO GAMING HUB - FACTORY INFRASTRUCTURE AUDIT REPORT")
        print("=" * 80)
        
        current_cat = None
        for r in self.results:
            if r["category"] != current_cat:
                current_cat = r["category"]
                print(f"\n[{current_cat}]")
            
            badge = "[PASS]" if r["status"] == "PASS" else "[FAIL]"
            print(f"  {badge:<7} | {r['test']:<45} | {r['detail']}")

        print("\n" + "=" * 80)
        print(f" AUDIT SUMMARY: {passed}/{total} CHECKS PASSED  |  FAILURES: {failed}")
        if failed == 0:
            print(" [STATUS: 100% HEALTHY - ALL SYSTEMS OPERATIONAL AND SECURE]")
        else:
            print(f" [WARNING: {failed} AUDIT CHECKS REQUIRE ATTENTION]")
        print("=" * 80 + "\n")

if __name__ == "__main__":
    auditor = HubIntegrityAuditor()
    auditor.run_all()
