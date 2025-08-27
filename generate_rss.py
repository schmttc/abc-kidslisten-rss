import requests
from bs4 import BeautifulSoup
from datetime import datetime
import xml.etree.ElementTree as ET

# Step 1: Get the latest episode link from the main page
main_url = "https://www.abc.net.au/kidslisten/programs/bedtime-stories"
response = requests.get(main_url)
soup = BeautifulSoup(response.content, 'html.parser')

# Find the first episode link
episode_link_tag = soup.find('a', href=True)
latest_episode_url = "https://www.abc.net.au" + episode_link_tag['href']

# Step 2: Visit the episode page and find the audio/aac URL
episode_response = requests.get(latest_episode_url)
episode_soup = BeautifulSoup(episode_response.content, 'html.parser')

# Find the audio/aac URL
audio_url = None
for source in episode_soup.find_all('source'):
    if 'audio/aac' in source.get('type', ''):
        audio_url = source.get('src')
        break

# Step 3: Extract metadata
title_tag = episode_soup.find('meta', property='og:title')
description_tag = episode_soup.find('meta', property='og:description')

title = title_tag['content'] if title_tag else "Bedtime Story"
description = description_tag['content'] if description_tag else "Latest bedtime story from ABC Kids Listen"
pub_date = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')

# Step 4: Generate RSS XML
rss = ET.Element('rss', version='2.0')
channel = ET.SubElement(rss, 'channel')

ET.SubElement(channel, 'title').text = "Yoto Bedtime Stories"
ET.SubElement(channel, 'link').text = main_url
ET.SubElement(channel, 'description').text = "Latest bedtime stories for Yoto player"
ET.SubElement(channel, 'language').text = "en-us"

item = ET.SubElement(channel, 'item')
ET.SubElement(item, 'title').text = title
ET.SubElement(item, 'description').text = description
ET.SubElement(item, 'pubDate').text = pub_date
ET.SubElement(item, 'link').text = latest_episode_url

enclosure = ET.SubElement(item, 'enclosure')
enclosure.set('url', audio_url)
enclosure.set('type', 'audio/aac')
enclosure.set('length', '0')

# Step 5: Save to file
tree = ET.ElementTree(rss)
tree.write("yoto_feed.xml", encoding="utf-8", xml_declaration=True)

print("RSS feed generated and saved to yoto_feed.xml")

