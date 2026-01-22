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
    # Pre-scan the siteini pack to map filenames to their subfolders
    # This makes the script much faster than running os.walk for every single channel
    ini_map = {}
    pack_path = 'config/siteini.pack'
    for r, d, f in os.walk(pack_path):
        for filename in f:
            if filename.endswith('.ini'):
                # Get path relative to the pack folder (e.g., "Canada/tv.cravetv.ca.ini")
                rel_path = os.path.relpath(os.path.join(r, filename), pack_path)
                # Remove the .ini extension for the 'site' attribute
                site_name_with_path = rel_path.replace('.ini', '')
                ini_map[filename] = site_name_with_path

    for g in guides:
        if g['channel'] in country_channels and added < 50:
            ini_filename = f"{g['site']}.ini"
            
            if ini_filename in ini_map:
                chan = ET.SubElement(root, 'channel')
                # Use the path-based site name so WebGrab finds it in subfolders
                chan.set('site', ini_map[ini_filename])
                chan.set('site_id', g['site_id'])
                chan.set('xmltv_id', g['channel'])
                chan.text = g['site_name']
                added += 1

    tree.write('config/WebGrab++.config.xml', encoding='utf-8', xml_declaration=True)
    print(f"Created config with {added} verified channels.")

if __name__ == "__main__":
    build_dynamic_config(sys.argv[1] if len(sys.argv) > 1 else 'CA')
