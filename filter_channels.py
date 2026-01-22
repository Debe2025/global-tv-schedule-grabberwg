import requests
import xml.etree.ElementTree as ET

def update_wg_config(country_code):
    # 1. Get channel list from API
    channels = requests.get("https://iptv-org.github.io/api/channels.json").json()
    
    # 2. Open your base WG++ config
    tree = ET.parse('config/WebGrab++.config.xml')
    root = tree.getroot()
    
    # 3. Clear existing channels and add new ones for the country
    for channel in channels:
        if channel.get('country') == country_code.upper():
            # You must manually map these to a 'site' and 'site_id' 
            # that exists in your siteini.pack
            new_chan = ET.SubElement(root, 'channel')
            new_chan.set('site', 'example.com') # Replace with actual site
            new_chan.set('site_id', channel['id'])
            new_chan.set('xmltv_id', channel['id'])
            new_chan.text = channel['name']
            
    tree.write('config/WebGrab++.config.xml')

update_wg_config('CA')
