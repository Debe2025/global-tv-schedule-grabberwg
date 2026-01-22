import os
import sys
import requests
import json
import xml.etree.ElementTree as ET
from pathlib import Path

def build_dynamic_config(country_code: str):
    country_code = country_code.upper()
    os.makedirs('config', exist_ok=True)
    os.makedirs('epg_db', exist_ok=True)

    # 1. Load template
    config_path = Path('config/master.config.xml')
    if not config_path.exists():
        print("ERROR: master.config.xml not found!")
        sys.exit(1)

    tree = ET.parse(config_path)
    root = tree.getroot()

    # 2. Set output file
    filename_elem = root.find('filename')
    if filename_elem is not None:
        filename_elem.text = f"/data/{country_code}.xml"
    else:
        print("WARNING: <filename> tag not found in master.config.xml")

    # 3. Fetch IPTV-org data
    try:
        guides = requests.get("https://iptv-org.github.io/api/guides.json", timeout=15).json()
        channels = requests.get("https://iptv-org.github.io/api/channels.json", timeout=15).json()
    except Exception as e:
        print(f"Failed to download IPTV-org API: {e}")
        sys.exit(1)

    country_channel_ids = {c['id'] for c in channels if c.get('country') == country_code}

    # 4. Build map of available .ini files (folder-aware)
    ini_map = {}
    pack_root = Path('config/siteini.pack')
    if not pack_root.exists() or not any(pack_root.iterdir()):
        print("ERROR: siteini.pack folder is empty or missing!")
        print("Directory listing:", list(pack_root.parent.glob('*')))
        sys.exit(1)

    for ini_path in pack_root.rglob('*.ini'):
        rel_path = ini_path.relative_to(pack_root).with_suffix('')  # e.g. Canada/tv.cravetv.ca
        ini_filename = ini_path.name
        ini_map[ini_filename] = str(rel_path)

    print(f"Found {len(ini_map)} .ini files in siteini.pack")

    # 5. Add matching channels (limit for testing)
    added = 0
    channel_elements = []

    for guide in guides:
        if guide['channel'] in country_channel_ids and added < 60:  # ← raised a bit
            ini_filename = f"{guide['site']}.ini"
            if ini_filename in ini_map:
                chan = ET.Element('channel')
                chan.set('site', ini_map[ini_filename])
                chan.set('site_id', guide['site_id'])
                chan.set('xmltv_id', guide['channel'])
                chan.text = guide.get('site_name', guide['channel'])
                channel_elements.append(chan)
                added += 1

    # Remove old <channel> elements and add new ones
    for old in root.findall('channel'):
        root.remove(old)
    for ch in channel_elements:
        root.append(ch)

    # Save
    output_path = Path('config/WebGrab++.config.xml')
    tree.write(output_path, encoding='utf-8', xml_declaration=True)
    print(f"Created WebGrab++.config.xml with {added} channels for {country_code}")

    if added == 0:
        print("WARNING: No channels were added – check if .ini files match guides.json sites")

if __name__ == "__main__":
    country = sys.argv[1].upper() if len(sys.argv) > 1 else 'CA'
    build_dynamic_config(country)
