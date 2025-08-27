import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime, timezone
import xml.etree.ElementTree as ET

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

#broken code
# Step 2: Find the <a> tag containing the text "Latest Episode"
#latest_episode_tag = soup.find('a', string=lambda text: text and "Latest Episode" in text)
#if not latest_episode_tag:
#    raise ValueError("Could not find the 'Latest Episode' link on the page.")

# Step 3: Extract the href and build the full URL
#episode_relative_url = latest_episode_tag.get('href')
#episode_url = urljoin(main_url, episode_relative_url)
#print(f"Latest episode URL: {episode_url}")


# Step 4: Fetch the episode page
episode_response = requests.get(episode_url)
episode_soup = BeautifulSoup(episode_response.content, 'html.parser')

# Step 5: Find the audio/aac URL
audio_tag = episode_soup.find('audio')
audio_url = None
if audio_tag:
    source_tag = audio_tag.find('source', {'type': 'audio/aac'})
    if source_tag:
        audio_url = source_tag.get('src')

if not audio_url:
    raise ValueError("Could not find the audio/aac URL on the episode page.")

print(f"Audio URL: {audio_url}")

# Step 6: Extract metadata
title_tag = episode_soup.find('meta', property='og:title')
description_tag = episode_soup.find('meta', property='og:description')
title = title_tag['content'] if title_tag else "Latest Bedtime Story"
description = description_tag['content'] if description_tag else "Bedtime story from ABC Kids Listen"
pub_date = datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S GMT')

# Step 7: Build RSS feed
rss = ET.Element('rss', version='2.0')
channel = ET.SubElement(rss, 'channel')
ET.SubElement(channel, 'title').text = "ABC Kids Listen - Bedtime Stories"
ET.SubElement(channel, 'link').text = main_url
ET.SubElement(channel, 'description').text = "Latest bedtime stories from ABC Kids Listen"

item = ET.SubElement(channel, 'item')
ET.SubElement(item, 'title').text = title
ET.SubElement(item, 'description').text = description
ET.SubElement(item, 'pubDate').text = pub_date
ET.SubElement(item, 'link').text = episode_url
ET.SubElement(item, 'guid').text = episode_url
enclosure = ET.SubElement(item, 'enclosure', url=audio_url, type="audio/aac", length="0")

# Step 8: Write to XML file
tree = ET.ElementTree(rss)
tree.write("yoto_feed.xml", encoding="utf-8", xml_declaration=True)

print("RSS feed saved to yoto_feed.xml")

