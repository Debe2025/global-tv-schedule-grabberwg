import os
import sys
import json
import time
import requests
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict

API_TIMEOUT = 20
API_RETRIES = 3
MAX_CHANNELS = 60   # adjust as needed

def fetch_json(url):
    for attempt in range(API_RETRIES):
        try:
            r = requests.get(url, timeout=API_TIMEOUT)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            if attempt == API_RETRIES - 1:
                raise
            time.sleep(2)

def build_dynamic_config(country_code: str):
    country_code = country_code.upper()

    Path("config").mkdir(exist_ok=True)
    Path("epg_db").mkdir(exist_ok=True)

    # ── Load template ─────────────────────────────────────
    template = Path("config/master.config.xml")
    if not template.exists():
        sys.exit("ERROR: master.config.xml not found")

    tree = ET.parse(template)
    root = tree.getroot()

    # ── Set filename for Docker container ─────────────────
    filename = root.find("filename")
    if filename is not None:
        # Docker maps epg_db to /data
        filename.text = f"/data/{country_code}.xml"
    else:
        print("WARNING: <filename> missing in template")

    # ── Fetch IPTV-org data ───────────────────────────────
    try:
        guides = fetch_json("https://iptv-org.github.io/api/guides.json")
        channels = fetch_json("https://iptv-org.github.io/api/channels.json")
    except Exception as e:
        sys.exit(f"ERROR: IPTV-org API failed: {e}")

    country_channels = {
        c["id"] for c in channels if c.get("country") == country_code
    }

    # ── Build siteini map (folder-aware, multi-hit safe) ──
    pack_root = Path("config/siteini.pack")
    if not pack_root.exists():
        sys.exit("ERROR: siteini.pack missing")

    ini_map = defaultdict(list)

    for ini in pack_root.rglob("*.ini"):
        rel = ini.relative_to(pack_root).with_suffix("")
        ini_map[ini.name].append(str(rel))

    print(f"Indexed {sum(len(v) for v in ini_map.values())} siteini files")

    # ── Build channel list ────────────────────────────────
    added = 0
    channels_xml = []

    for g in guides:
        if added >= MAX_CHANNELS:
            break

        if g["channel"] not in country_channels:
            continue

        ini_name = f"{g['site']}.ini"
        if ini_name not in ini_map:
            continue

        # Prefer country-specific folder if possible
        site_path = ini_map[ini_name][0]

        ch = ET.Element("channel")
        ch.set("site", site_path)
        ch.set("site_id", g["site_id"])
        ch.set("xmltv_id", g["channel"])
        ch.text = g.get("site_name", g["channel"])

        channels_xml.append(ch)
        added += 1

    # ── Replace existing <channel> entries ────────────────
    for old in root.findall("channel"):
        root.remove(old)

    for ch in channels_xml:
        root.append(ch)

    # ── Save config ───────────────────────────────────────
    out = Path("config/WebGrab++.config.xml")
    tree.write(out, encoding="utf-8", xml_declaration=True)

    print(f"Generated WebGrab++.config.xml")
    print(f"Country: {country_code}")
    print(f"Channels added: {added}")
    print(f"Output file: /data/{country_code}.xml")

    if added == 0:
        print("WARNING: No matching channels found")

if __name__ == "__main__":
    country = sys.argv[1].upper() if len(sys.argv) > 1 else "CA"
    build_dynamic_config(country)
