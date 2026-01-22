import requests, json, sys, os

def build_country_epg_config(country_code):
    # Ensure the output directory exists
    os.makedirs('epg_db', exist_ok=True)
    
    # 1. Fetch Global Data
    channels = requests.get("https://iptv-org.github.io/api/channels.json").json()
    guides = requests.get("https://iptv-org.github.io/api/guides.json").json()
    guide_map = {g['channel']: g for g in guides}
    
    config_output = []
    for chan in channels:
        if chan.get('country') == country_code.upper():
            cid = chan['id']
            if cid in guide_map:
                config_output.append({
                    "site": guide_map[cid]['site'],
                    "site_id": guide_map[cid]['site_id'],
                    "xmltv_id": cid,
                    "display_name": chan['name'],
                    "logo": chan.get('logo') # <--- Logos included here
                })
    
    # Save a temporary config for the Node.js grabber to read
    with open('channels.json', 'w') as f:
        json.dump(config_output, f, indent=2)

if __name__ == "__main__":
    # Run: python filter_channels.py CA
    target_country = sys.argv[1] if len(sys.argv) > 1 else 'CA'
    build_country_epg_config(target_country)
