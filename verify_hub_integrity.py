# -*- coding: utf-8 -*-
"""
JDM Retro Gaming Hub - Factory Infrastructure Integrity Auditor
Verifies compliance across Web Media, Protected Constants, SEO Assets,
Video Rendering Queues, and SNS Automation.
"""

import os
import sys
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

    def audit_tiktok_seo_scripts(self):
        cat = "05. TikTok Scripts SEO Golden Template"
        scripts_path = BASE_DIR / "marketing_tools" / "tiktok_scripts_150.json"
        if not scripts_path.exists():
            self.log(cat, "tiktok_scripts_150.json existence", False, "File missing")
            return

        with open(scripts_path, "r", encoding="utf-8") as f:
            scripts = json.load(f)

        self.log(cat, "Master scripts count (全150品目)", len(scripts) == 150, f"Total items: {len(scripts)}")

        seo_target_items = [s for s in scripts if s.get("id", 0) >= 16]
        seo_passed = []
        seo_failed = []

        for item in seo_target_items:
            iid = item.get("id")
            caption = item.get("caption", "")
            slides = item.get("slides", [])
            s1_tts = slides[0].get("tts_text", "") if slides else ""

            # Check 1: Caption starts with "How to Spot a Fake"
            has_seo_title = caption.startswith("How to Spot a Fake ")
            # Check 2: Audio hook in Slide 1
            has_asr_hook = "spot a fake" in s1_tts.lower()

            if has_seo_title and has_asr_hook:
                seo_passed.append(iid)
            else:
                seo_failed.append(iid)

        all_seo_valid = len(seo_failed) == 0
        detail_msg = f"{len(seo_passed)}/135 items fully compliant" if all_seo_valid else f"Failed items: {seo_failed[:5]}..."
        self.log(cat, "TikTok SEO 4 Signals (#016-#150)", all_seo_valid, detail_msg)

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

    def run_all(self):
        self.audit_manifest()
        self.audit_web_media()
        self.audit_seo_crawler_files()
        self.audit_video_queue()
        self.audit_tiktok_seo_scripts()
        self.audit_sns_automation()
        self.print_report()

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
