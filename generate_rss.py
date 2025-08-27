import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime, timezone
import xml.etree.ElementTree as ET
import re
import json


# Step 1: Fetch the main page
main_url = "https://www.abc.net.au/kidslisten/programs/bedtime-stories"
response = requests.get(main_url)
soup = BeautifulSoup(response.content, 'html.parser')

# Previously working code
# Find all <a> tags and look for one that contains the text "Latest Episode"
latest_episode_url = None
for a_tag in soup.find_all('a', href=True):
    if 'Latest Episode' in a_tag.get_text(strip=True):
        latest_episode_url = a_tag['href']
        break

# Print the full episode URL for debugging
if latest_episode_url:
    episode_url = requests.compat.urljoin(main_url, latest_episode_url)
    print("Latest Episode URL:", episode_url)
else:
    print("Latest Episode link not found.")

# Step 4: Fetch the episode page
episode_response = requests.get(episode_url)
episode_soup = BeautifulSoup(episode_response.content, 'html.parser')

# Step 5: Find the audio/aac URL
#audio_tag = episode_soup.find('audio')
#audio_url = None
#if audio_tag:
#    source_tag = audio_tag.find('source', {'type': 'audio/aac'})
#    if source_tag:
#        audio_url = source_tag.get('src')
#
#if not audio_url:
#    raise ValueError("Could not find the audio/aac URL on the episode page.")
#
#print(f"Audio URL: {audio_url}")


# Step 5: Find the audio/aac URL from embedded JSON
audio_url = None
script_tags = episode_soup.find_all('script')

for script in script_tags:
    if script.string and 'renditions' in script.string:
        # Try to extract JSON from the script content
        match = re.search(r'"renditions"\s*:\s*(\[[^\]]+\])', script.string)
        if match:
            try:
                renditions_json = json.loads(match.group(1))
                for rendition in renditions_json:
                    if rendition.get("MIMEType") == "audio/aac":
                        audio_url = rendition.get("url")
                        break
            except json.JSONDecodeError:
                continue

if not audio_url:
    raise ValueError("Could not find the audio/aac URL in the embedded JSON.")

print(f"Audio URL: {audio_url}")



# Step 6: Extract metadata
title_tag = episode_soup.find('meta', property='og:title')
description_tag = episode_soup.find('meta', property='og:description')
title = title_tag['content'] if title_tag else "Latest Bedtime Story"
description = description_tag['content'] if description_tag else "Bedtime story from ABC Kids Listen"
pub_date = datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S GMT')

# Step 7: Build RSS feed
#rss = ET.Element('rss', version='2.0')
#channel = ET.SubElement(rss, 'channel')
#ET.SubElement(channel, 'title').text = "ABC Kids Listen - Bedtime Stories"
#ET.SubElement(channel, 'link').text = main_url
#ET.SubElement(channel, 'description').text = "Latest bedtime stories from ABC Kids Listen"

#item = ET.SubElement(channel, 'item')
#ET.SubElement(item, 'title').text = title
#ET.SubElement(item, 'description').text = description
#ET.SubElement(item, 'pubDate').text = pub_date
#ET.SubElement(item, 'link').text = episode_url
#ET.SubElement(item, 'guid').text = episode_url
#enclosure = ET.SubElement(item, 'enclosure', url=audio_url, type="audio/aac", length="0")

# Step 8: Write to XML file
#tree = ET.ElementTree(rss)
#tree.write("yoto_feed.xml", encoding="utf-8", xml_declaration=True)


#----
from xml.etree.ElementTree import Element, SubElement, ElementTree

# Create the root RSS element
rss = Element('rss', version='2.0')
channel = SubElement(rss, 'channel')

# Add atom namespace to channel
channel.set('xmlns:atom', 'http://www.w3.org/2005/Atom')

# Add atom:link for feed self-reference
SubElement(channel, 'atom:link', {
    'rel': 'self',
    'href': 'https://example.com/yoto_feed.xml',  # Replace with your actual feed URL
    'type': 'application/rss+xml'
})

# Add channel metadata
SubElement(channel, 'title').text = 'ABC Kids Listen - Bedtime Stories'
SubElement(channel, 'link').text = 'https://www.abc.net.au/kidslisten/programs/bedtime-stories'
SubElement(channel, 'description').text = 'Latest bedtime stories from ABC Kids Listen'
SubElement(channel, 'language').text = 'en-us'

# Add an item
item = SubElement(channel, 'item')
SubElement(item, 'title').text = "Bedtime Stories: featuring 'The Billabong Bush Dance' and more - ABC Kids listen"
SubElement(item, 'description').text = 'Soothing stories from your favourites, including Alison Lester, Kids listen Bookshelf, Play School'
SubElement(item, 'pubDate').text = 'Wed, 27 Aug 2025 06:47:34 GMT'
SubElement(item, 'link').text = 'https://www.abc.net.au/kidslisten/programs/bedtime-stories/bedtime-stories:-featuring-the-billabong-bush-dance-and-more/105648210'
SubElement(item, 'guid').text = 'https://www.abc.net.au/kidslisten/programs/bedtime-stories/bedtime-stories:-featuring-the-billabong-bush-dance-and-more/105648210'
SubElement(item, 'enclosure', {
    'url': 'https://mediacore-live-production.akamaized.net/audio/02/ck/Z/ml.aac',
    'type': 'audio/mpeg',
    'length': '12345678'
})

# Write to file with no whitespace before XML declaration
ElementTree(rss).write('yoto_feed.xml', encoding='utf-8', xml_declaration=True)
#---

print("RSS feed saved to yoto_feed.xml")

