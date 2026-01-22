import os
import sys
import requests
import json
import xml.etree.ElementTree as ET

def build_dynamic_config(country_code):
    country_code = country_code.upper()
    print(f"--- Starting Config Build for {country_code} ---")
    
    # Ensure folders exist
    os.makedirs('config', exist_ok=True)
    os.makedirs('epg_db', exist_ok=True)

    # 1. Load Master Template
    template_path = 'config/master.config.xml'
    if not os.path.exists(template_path):
        print(f"CRITICAL ERROR: {template_path} not found!")
        sys.exit(1)

    try:
        tree = ET.parse(template_path)
        root = tree.getroot()
    except Exception as e:
        print(f"XML Parse Error: {e}")
        sys.exit(1)

    # 2. Set Output Filename for Docker (/data/ maps to epg_db/)
    filename_tag = root.find('filename')
    if filename_tag is not None:
        filename_tag.text = f"/data/{country_code}.xml"
    else:
        ET.SubElement(root, 'filename').text = f"/data/{country_code}.xml"

    # 3. Fetch Channels from IPTV-org
    try:
        guides = requests.get("https://iptv-org.github.io/api/guides.json").json()
        channels_api = requests.get("https://iptv-org.github.io/api/channels.json").json()
        
        country_channels = [c['id'] for c in channels_api if c.get('country') == country_code]
        site_configs = [g for g in guides if g['channel'] in country_channels]
    except Exception as e:
        print(f"API Error: {e}")
        sys.exit(1)

    # 4. Add Channels to XML (Top 50)
    for entry in site_configs[:50]:
        chan_elem = ET.SubElement(root, 'channel')
        chan_elem.set('site', entry['site'])
        chan_elem.set('site_id', entry['site_id'])
        chan_elem.set('xmltv_id', entry['channel'])
        chan_elem.text = entry['site_name']

    # 5. Save the WebGrab instruction file
    output_path = 'config/WebGrab++.config.xml'
    tree.write(output_path, encoding='utf-8', xml_declaration=True)
    
    # 6. Create Status file (Processing)
    status_data = {"country": country_code, "status": "processing", "file_found": False}
    with open('epg_db/status.json', 'w') as f:
        json.dump(status_data, f)
        
    print(f"--- SUCCESS: {output_path} created ---")

if __name__ == "__main__":
    code = sys.argv[1] if len(sys.argv) > 1 else 'US'
    build_dynamic_config(code)
