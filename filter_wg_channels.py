import os
import sys
import requests
import json
import xml.etree.ElementTree as ET

def build_dynamic_config(country_code):
    print(f"Building config for: {country_code}")
    country_code = country_code.upper()
    
    # 1. Fetch EPG mappings from IPTV-org API
    try:
        guides = requests.get("https://iptv-org.github.io/api/guides.json").json()
        channels_api = requests.get("https://iptv-org.github.io/api/channels.json").json()
    except Exception as e:
        print(f"Error fetching API: {e}")
        return

    # 2. Filter channels for the specific country
    country_channels = [c['id'] for c in channels_api if c.get('country') == country_code]
    site_configs = [g for g in guides if g['channel'] in country_channels]

    if not site_configs:
        print(f"No EPG sources found for {country_code}.")
        return

    # 3. Load Master Template
    os.makedirs('config', exist_ok=True)
    os.makedirs('epg_db', exist_ok=True) # Ensure epg_db exists
    tree = ET.parse('config/master.config.xml')
    root = tree.getroot()

    # 4. Update the output filename (Docker internal path)
    root.find('filename').text = f"/data/{country_code}.xml"

    # 5. Add dynamic channels
    for entry in site_configs[:50]:
        chan_elem = ET.SubElement(root, 'channel')
        chan_elem.set('site', entry['site'])
        chan_elem.set('site_id', entry['site_id'])
        chan_elem.set('xmltv_id', entry['channel'])
        chan_elem.text = entry['site_name']

    # 6. Save final config
    tree.write('config/WebGrab++.config.xml', encoding='utf-8', xml_declaration=True)
    
    # 7. Create status file (Fixed the 'os.open' error here)
    status_data = {
        "country": country_code,
        "status": "processing",
        "timestamp": str(os.popen('date').read()).strip()
    }
    with open('epg_db/status.json', 'w') as f:
        json.dump(status_data, f)
        
    print(f"Success: Config created with {len(site_configs[:50])} channels.")

if __name__ == "__main__":
    code = sys.argv[1] if len(sys.argv) > 1 else 'US'
    build_dynamic_config(code)
