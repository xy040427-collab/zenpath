#!/usr/bin/env python3
"""
Download Urongda university logos for the 择境 ZENPATH project.

Steps:
1. Match our 111 schools to Urongda school codes by Chinese name
2. Download 1024px CDN preview images  
3. Save HTML source reference
4. For unmatched schools, use manual mappings
"""

import json
import os
import time
import urllib.request
import urllib.error
import ssl
import sys
from pathlib import Path

BASE_DIR = Path("/home/xiaoyu/projects/gaokao-volunteer")
RAW_DIR = BASE_DIR / "public" / "university-logos" / "raw"
DATA_DIR = BASE_DIR / "public" / "university-logos" / "data"
CACHE_DIR = BASE_DIR / "public" / "university-logos" / "temp"

os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)

# SSL context for HTTPS
ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}

def fetch_url(url, output_path=None, delay=0):
    """Fetch a URL, optionally saving to file. Returns content if no output_path."""
    if delay > 0:
        time.sleep(delay)
    
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        resp = urllib.request.urlopen(req, context=ssl_ctx, timeout=30)
        data = resp.read()
        if output_path:
            with open(output_path, 'wb') as f:
                f.write(data)
            return True
        return data
    except urllib.error.HTTPError as e:
        print(f"  HTTP Error {e.code} for {url}")
        return None if not output_path else False
    except Exception as e:
        print(f"  Error fetching {url}: {e}")
        return None if not output_path else False

# ====== LOAD DATA ======
print("=" * 60)
print("Loading data...")

# Load our schools
with open(BASE_DIR / "gaokao_data" / "all_universities_data.json") as f:
    our_schools = json.load(f)
print(f"Our schools: {len(our_schools)}")

# Load Urongda mapping (code -> {slug, name})
with open(DATA_DIR / "urongda_school_map.json") as f:
    urongda_map = json.load(f)
print(f"Urongda schools: {len(urongda_map)}")

# Build name-to-code lookup
name_to_code = {info['name']: code for code, info in urongda_map.items()}
name_to_slug = {info['name']: info['slug'] for code, info in urongda_map.items()}

# ====== MATCH SCHOOLS ======
print("\n" + "=" * 60)
print("Matching schools...")

# Manual mappings for renamed schools
manual_mappings = {
    '合肥学院': {'code': '4134011059', 'slug': 'hefei-university', 'name_on_urongda': '合肥大学'},
    '福建工程学院': {'code': '4135010388', 'slug': 'fujian-university-of-technology', 'name_on_urongda': '福建理工大学'},
    '国防科学技术大学': {'code': '4143091002', 'slug': 'national-university-of-defense-technology', 'name_on_urongda': '中国人民解放军国防科技大学'},
}

download_queue = []  # list of {school_info, urongda_code, urongda_slug, match_type}

for school in our_schools:
    name = school['name']
    
    # Check manual mappings first
    if name in manual_mappings:
        mm = manual_mappings[name]
        download_queue.append({
            'school': school,
            'urongda_code': mm['code'],
            'urongda_slug': mm['slug'],
            'match_type': 'manual',
            'matched_name': mm['name_on_urongda']
        })
        continue
    
    # Exact match by name
    if name in name_to_code:
        code = name_to_code[name]
        slug = name_to_slug[name]
        download_queue.append({
            'school': school,
            'urongda_code': code,
            'urongda_slug': slug,
            'match_type': 'exact',
            'matched_name': name
        })
        continue
    
    # Fuzzy match: check if our name is contained in any Urongda name or vice versa
    # Also check normalized names (remove spaces, etc.)
    name_normalized = name.replace(' ', '').replace('　', '')
    found = False
    
    for uname, code in name_to_code.items():
        uname_normalized = uname.replace(' ', '').replace('　', '')
        if name_normalized == uname_normalized:
            slug = name_to_slug[uname]
            download_queue.append({
                'school': school,
                'urongda_code': code,
                'urongda_slug': slug,
                'match_type': 'fuzzy_normalized',
                'matched_name': uname
            })
            found = True
            break
    
    if not found:
        print(f"  WARNING: No match for {name}")

print(f"Matched {len(download_queue)}/{len(our_schools)} schools")

# ====== DOWNLOAD CDN IMAGES ======
print("\n" + "=" * 60)
print("Downloading CDN 1024px preview images...")

successful = []
failed = []

for i, item in enumerate(download_queue):
    school = item['school']
    code = item['urongda_code']
    slug = item['urongda_slug']
    name = school['name']
    our_slug = school.get('slug', school.get('id', ''))
    
    print(f"\n[{i+1}/{len(download_queue)}] {name} (code={code}, slug={slug})")
    
    # Create directory for this school
    school_dir_name = f"{our_slug}_{name}"
    school_dir = RAW_DIR / school_dir_name
    os.makedirs(school_dir, exist_ok=True)
    
    # CDN URL for 1024px PNG
    cdn_url = f"https://cdn.urongda.com/images/normal/medium/{slug}-logo-1024px.png"
    png_path = school_dir / f"{slug}-logo-1024px.png"
    
    if png_path.exists() and png_path.stat().st_size > 1000:
        print(f"  ✓ PNG already exists ({png_path.stat().st_size} bytes)")
    else:
        print(f"  Downloading: {cdn_url}")
        result = fetch_url(cdn_url, output_path=str(png_path), delay=3)
        if result and png_path.exists():
            size = png_path.stat().st_size
            print(f"  ✓ Downloaded PNG ({size} bytes)")
        else:
            print(f"  ✗ Failed to download PNG from CDN")
            # Try alternative: 1024w webp format
            alt_url = f"https://cdn.urongda.com/images/schools/{slug}/1024w/{slug}-1024w.webp"
            webp_path = school_dir / f"{slug}-1024w.webp"
            print(f"  Trying alternative: {alt_url}")
            result = fetch_url(alt_url, output_path=str(webp_path), delay=2)
            if result and webp_path.exists():
                size = webp_path.stat().st_size
                print(f"  ✓ Downloaded WEBP ({size} bytes)")
            else:
                print(f"  ✗ Failed both CDN URLs")
                failed.append({
                    'school_name': name,
                    'school_slug': our_slug,
                    'urongda_code': code,
                    'urongda_slug': slug,
                    'reason': 'CDN download failed'
                })
                continue
    
    # Save school page HTML as source reference
    page_url = f"https://www.urongda.com/logos/{code}"
    html_path = school_dir / f"{code}_page.html"
    if not html_path.exists():
        print(f"  Fetching page: {page_url}")
        result = fetch_url(page_url, output_path=str(html_path), delay=3)
        if result:
            print(f"  ✓ Page saved ({html_path.stat().st_size} bytes)")
        else:
            print(f"  ⚠ Page fetch failed (non-critical)")
    else:
        print(f"  ✓ Page already saved")
    
    successful.append({
        'school_name': name,
        'school_slug': our_slug,
        'urongda_code': code,
        'urongda_slug': slug,
        'png_path': str(png_path) if png_path.exists() else '',
        'webp_path': str(webp_path) if 'webp_path' in dir() and webp_path.exists() else '',
    })

# ====== SUMMARY ======
print("\n" + "=" * 60)
print("DOWNLOAD SUMMARY")
print(f"Successful: {len(successful)}")
print(f"Failed: {len(failed)}")

if failed:
    print("\nFailed downloads:")
    for f_item in failed:
        print(f"  ✗ {f_item['school_name']} ({f_item['urongda_slug']}): {f_item['reason']}")

# Save results
results = {
    'successful': successful,
    'failed': failed,
    'total_attempted': len(download_queue),
    'total_our_schools': len(our_schools)
}
with open(DATA_DIR / 'download_results.json', 'w') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print(f"\nResults saved to {DATA_DIR / 'download_results.json'}")
