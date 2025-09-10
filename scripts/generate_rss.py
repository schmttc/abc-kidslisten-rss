import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from datetime import datetime, timezone, timedelta
import xml.etree.ElementTree as ET
import re
import json
import html
import os

# --- Config ---
main_url = os.getenv("main_url")
feed_link = os.getenv("feed_link")
now_rfc2822 = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S %z")

# Step 1: Fetch the main page
response = requests.get(main_url)
soup = BeautifulSoup(response.content, 'html.parser')

# Program metadata from main_url
meta_title = soup.find('meta', attrs={'name': 'title'})
program_title = meta_title.get('content')

program_link = main_url

meta_description = soup.find('meta', attrs={'name': 'description'})
program_description = meta_description.get('content')

# Step 2: Extract hero image URL
hero_image_url = None
aspect_ratio_div = soup.find('div', class_='AspectRatio_container__FC_XH')
if aspect_ratio_div:
    img_tag = aspect_ratio_div.find('img')
    if img_tag and img_tag.get('src'):
        hero_image_url = img_tag['src'].split('?')[0]

# Step 3: Collect episode links
# Currently only work for the episodes on the first page
episode_links = []
for card in soup.find_all('div', class_='CardLayout_content__zgsBr'):
    a_tag = card.find('a', href=True)
    if a_tag:
        full_url = urljoin(main_url, a_tag['href'])
        episode_links.append(full_url)

# Limit max number of episodes
#episode_links = episode_links[:5]  # last 5 episodes

# Step 4: Build RSS feed root
rss = ET.Element('rss', version='2.0')
rss.attrib['xmlns:itunes'] = 'http://www.itunes.com/dtds/podcast-1.0.dtd'
rss.attrib['xmlns:atom'] = 'http://www.w3.org/2005/Atom'
rss.attrib['xmlns:content'] = 'http://purl.org/rss/1.0/modules/content/'
channel = ET.SubElement(rss, 'channel')

# --- Channel Metadata ---
ET.SubElement(channel, "itunes:category", text="Kids & Family")
ET.SubElement(channel, "itunes:image", href=hero_image_url)
itunes_owner = ET.SubElement(channel, "itunes:owner")
ET.SubElement(itunes_owner, "itunes:name").text = "Australian Broadcasting Corporation"
ET.SubElement(itunes_owner, "itunes:email").text = "abcpodcasts@abc.net.au"

ET.SubElement(channel, "itunes:author").text = "ABC Kids listen"
ET.SubElement(channel, "title").text = program_title
ET.SubElement(channel, "link").text = program_link
ET.SubElement(channel, "description").text = program_description
ET.SubElement(channel, "language").text = "en"
ET.SubElement(channel, "copyright").text = "Copyright 2025, Australian Broadcasting Corporation. All rights reserved."
ET.SubElement(channel, "pubDate").text = now_rfc2822
ET.SubElement(channel, "lastBuildDate").text = now_rfc2822

# Standard <image> tag
if hero_image_url:
    image = ET.SubElement(channel, 'image')
    ET.SubElement(image, 'title').text = program_title
    ET.SubElement(image, 'url').text = hero_image_url
    ET.SubElement(image, 'link').text = main_url
    ET.SubElement(image, "description").text = program_description

#continue channel metadata
ET.SubElement(channel, "ttl").text = "30"
ET.SubElement(channel, "atom:link", {
    "href": feed_link,
    "rel": "self",
    "type": "application/rss+xml"
})
ET.SubElement(channel, "itunes:explicit").text = "false"
ET.SubElement(channel, "itunes:author").text = "ABC KIDS listen"    #duplicate, same as Dino Dome example
ET.SubElement(channel, "itunes:summary").text = program_description
ET.SubElement(channel, "itunes:subtitle").text = program_description
#ET.SubElement(channel, "itunes:image", href=hero_image_url)        #duplicate, is already included above

# Step 5: Loop through episodes
for episode_url in episode_links:
    episode_response = requests.get(episode_url)
    episode_soup = BeautifulSoup(episode_response.content, 'html.parser')

    # Title & description
    title_tag = episode_soup.find('meta', property='og:title')
    description_tag = episode_soup.find('meta', property='og:description')
    title = title_tag['content'] if title_tag else meta_title
    description = description_tag['content'] if description_tag else program_description

    # Date
    pub_date = None
    for script in episode_soup.find_all('script', type='application/ld+json'):
        try:
            data = json.loads(script.string)
            if isinstance(data, dict) and 'datePublished' in data:
                pub_date_obj = datetime.strptime(data['datePublished'], '%Y-%m-%dT%H:%M:%S%z')
                pub_date = pub_date_obj.strftime('%a, %d %b %Y %H:%M:%S GMT')
                break
        except (json.JSONDecodeError, ValueError, TypeError):
            continue
    if not pub_date:
        pub_date = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')

    # Audio URL
    # As of Aug 2025, audio/aac doens't play on Yoto v3 device. MP3 is the more widely supported podcast format in general
    audio_url = None
    for script in episode_soup.find_all('script'):
        if script.string and 'renditions' in script.string:
            match = re.search(r'"renditions"\s*:\s*(\[[^\]]+\])', script.string)
            if match:
                try:
                    renditions_json = json.loads(match.group(1))
                    for rendition in renditions_json:
                        if rendition.get("MIMEType") == "audio/mpeg":  
                            audio_url = rendition.get("url")
                            audio_type = rendition.get("MIMEType")
                            audio_fileSize = rendition.get("fileSize")
                            break
                except json.JSONDecodeError:
                    continue
    if not audio_url:
        continue

    # Duration (find not working)
    media_duration = 0

    for script in episode_soup.find_all('script'):
        script_text = script.get_text()
        match = re.search(r'"duration"\s*:\s*(\d+)', script_text)
        if match:
            media_duration = str(match.group(1))
            print("Duration:", media_duration)
            break


    # Keywords
    keywords = None
    json_ld_tag = soup.find("script", type="application/ld+json")
    if json_ld_tag and json_ld_tag.string:
        try:
            data = json.loads(json_ld_tag.string)
            if "keywords" in data:
                keywords = data["keywords"]
        except json.JSONDecodeError:
            pass

    # RSS <item>
    item = ET.SubElement(channel, 'item')
    ET.SubElement(item, 'title').text = title
    ET.SubElement(item, 'link').text = episode_url
    ET.SubElement(item, 'description').text = description
    ET.SubElement(item, 'enclosure', {
        'url': audio_url,
        'type': audio_type or 'audio/mpeg',
        'length': audio_fileSize or '12345678'
    })
    ET.SubElement(item, "guid", {"isPermaLink": "true"}).text = episode_url
    ET.SubElement(item, 'pubDate').text = pub_date
    ET.SubElement(item, "itunes:author").text = "Australian Broadcasting Corporation" 
    ET.SubElement(item, "itunes:summary").text = description
    ET.SubElement(item, "itunes:subtitle").text = description
    ET.SubElement(item, "itunes:image", href=hero_image_url)    # Need to add a search for the episode image
    ET.SubElement(item, "itunes:duration").text = media_duration # str(timedelta(seconds=media_duration))
    ET.SubElement(item, "itunes:explicit").text = "false"
    ET.SubElement(item, "itunes:keywords").text = keywords


# Step 6: Save feed
tree = ET.ElementTree(rss)
tree.write(os.path.basename(urlparse(feed_link).path), encoding="UTF-8", xml_declaration=True)

print("✅ RSS feed saved to ", os.path.basename(urlparse(feed_link).path))
