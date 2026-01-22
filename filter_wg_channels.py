import os, sys, requests, json
import xml.etree.ElementTree as ET

def build_dynamic_config(country_code):
    country_code = country_code.upper()
    os.makedirs('config', exist_ok=True)
    os.makedirs('epg_db', exist_ok=True)

    # 1. Load Template
    tree = ET.parse('config/master.config.xml')
    root = tree.getroot()

    # 2. Set Paths
    root.find('filename').text = f"/data/{country_code}.xml"
    
    # 3. Fetch Data
    guides = requests.get("https://iptv-org.github.io/api/guides.json").json()
    channels_api = requests.get("https://iptv-org.github.io/api/channels.json").json()
    
    country_channels = [c['id'] for c in channels_api if c.get('country') == country_code]
    
    # 4. Only add channels if the .ini file exists in the pack
    added = 0
    for g in guides:
        if g['channel'] in country_channels and added < 50:
            ini_filename = f"{g['site']}.ini"
            # Search for ini file recursively in the pack
            ini_found = False
            for r, d, f in os.walk('config/siteini.pack'):
                if ini_filename in f:
                    ini_found = True
                    break
            
            if ini_found:
                chan = ET.SubElement(root, 'channel')
                chan.set('site', g['site'])
                chan.set('site_id', g['site_id'])
                chan.set('xmltv_id', g['channel'])
                chan.text = g['site_name']
                added += 1

    tree.write('config/WebGrab++.config.xml', encoding='utf-8', xml_declaration=True)
    print(f"Created config with {added} verified channels.")

if __name__ == "__main__":
    build_dynamic_config(sys.argv[1] if len(sys.argv) > 1 else 'CA')
