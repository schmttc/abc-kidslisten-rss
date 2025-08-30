import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime
import xml.etree.ElementTree as ET
import re
import json

# Step 1: Fetch the main page
main_url = "https://www.abc.net.au/kidslisten/programs/bedtime-stories"
response = requests.get(main_url)
soup = BeautifulSoup(response.content, 'html.parser')

# Step 2: Extract hero image URL
hero_image_url = None
aspect_ratio_div = soup.find('div', class_='AspectRatio_container__FC_XH')
if aspect_ratio_div:
    img_tag = aspect_ratio_div.find('img')
    if img_tag and img_tag.get('src'):
        base_url = img_tag['src'].split('?')[0]
        hero_image_url = (
            f"{base_url}?impolicy=wcms_crop_resize"
            f"&cropH=700&cropW=700&xPos=0&yPos=0"
            f"&width=1400&height=1400"
        )

# Step 3: Collect episode links
episode_links = []
for card in soup.find_all('div', class_='CardLayout_content__zgsBr'):
    a_tag = card.find('a', href=True)
    if a_tag:
        full_url = urljoin(main_url, a_tag['href'])
        episode_links.append(full_url)

# Step 4: Build RSS feed root
rss = ET.Element('rss', version='2.0')
rss.attrib['xmlns:itunes'] = 'http://www.itunes.com/dtds/podcast-1.0.dtd'
rss.attrib['xmlns:atom'] = 'http://www.w3.org/2005/Atom'
channel = ET.SubElement(rss, 'channel')

# Feed-level metadata
ET.SubElement(channel, 'atom:link', {
    'rel': 'self',
    'href': 'https://example.com/abc-kidslisten-bedtimestories.rss',  # Replace with actual feed URL
    'type': 'application/rss+xml'
})
ET.SubElement(channel, 'title').text = 'ABC Kids Listen - Bedtime Stories'
ET.SubElement(channel, 'link').text = main_url
ET.SubElement(channel, 'description').text = 'Latest bedtime stories from ABC Kids Listen'
ET.SubElement(channel, 'language').text = 'en-us'
ET.SubElement(channel, 'itunes:author').text = 'ABC Kids Listen'
ET.SubElement(channel, 'itunes:keywords').text = "kids, stories, bedtime, abc, podcast, children, audio, tales"
ET.SubElement(channel, 'itunes:image', {
    'href': hero_image_url or "https://megaphone.imgix.net/podcasts/eafbefea-648f-11ee-a501-67c7bb4c65b5/image/RBA_logo_pirate-2500.png" #fix this
})

# Standard <image> tag
if hero_image_url:
    image = ET.SubElement(channel, 'image')
    ET.SubElement(image, 'url').text = hero_image_url
    ET.SubElement(image, 'title').text = 'ABC Kids Listen - Bedtime Stories'
    ET.SubElement(image, 'link').text = main_url

# Step 5: Loop through episodes
for episode_url in episode_links:
    episode_response = requests.get(episode_url)
    episode_soup = BeautifulSoup(episode_response.content, 'html.parser')

    # Title & description
    title_tag = episode_soup.find('meta', property='og:title')
    description_tag = episode_soup.find('meta', property='og:description')
    title = title_tag['content'] if title_tag else "Bedtime Story"
    description = description_tag['content'] if description_tag else "Bedtime story from ABC Kids Listen"

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
    audio_url = None
    for script in episode_soup.find_all('script'):
        if script.string and 'renditions' in script.string:
            match = re.search(r'"renditions"\s*:\s*(\[[^\]]+\])', script.string)
            if match:
                try:
                    renditions_json = json.loads(match.group(1))
                    for rendition in renditions_json:
                        if rendition.get("MIMEType") in ["audio/aac", "audio/mpeg"]:
                            audio_url = rendition.get("url")
                            break
                except json.JSONDecodeError:
                    continue
    if not audio_url:
        continue

    # RSS <item>
    item = ET.SubElement(channel, 'item')
    ET.SubElement(item, 'title').text = title
    ET.SubElement(item, 'description').text = description
    ET.SubElement(item, 'pubDate').text = pub_date
    ET.SubElement(item, 'link').text = episode_url
    ET.SubElement(item, 'guid').text = episode_url
    ET.SubElement(item, 'enclosure', {
        'url': audio_url,
        'type': 'audio/mpeg',
        'length': '12345678'
    })

# Step 6: Save feed
tree = ET.ElementTree(rss)
tree.write('abc-kidslisten-bedtimestories.rss', encoding='utf-8', xml_declaration=True)

print("✅ RSS feed saved to abc-kidslisten-bedtimestories.rss")
