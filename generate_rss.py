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

# Step 2: Find all episode links from divs with class 'CardLayout_content__zgsBr'
episode_links = []
for card in soup.find_all('div', class_='CardLayout_content__zgsBr'):
    a_tag = card.find('a', href=True)
    if a_tag:
        full_url = urljoin(main_url, a_tag['href'])
        episode_links.append(full_url)

# Step 3: Prepare RSS feed
rss = ET.Element('rss', version='2.0')
channel = ET.SubElement(rss, 'channel')
channel.set('xmlns:atom', 'http://www.w3.org/2005/Atom')

ET.SubElement(channel, 'atom:link', {
    'rel': 'self',
    'href': 'https://example.com/abc-kidslisten-bedtimestories.rss',  # Replace with actual feed URL
    'type': 'application/rss+xml'
})

ET.SubElement(channel, 'title').text = 'ABC Kids Listen - Bedtime Stories'
ET.SubElement(channel, 'link').text = main_url
ET.SubElement(channel, 'description').text = 'Latest bedtime stories from ABC Kids Listen'
ET.SubElement(channel, 'language').text = 'en-us'

# Step 4: Loop through each episode and extract metadata
for episode_url in episode_links:
    episode_response = requests.get(episode_url)
    episode_soup = BeautifulSoup(episode_response.content, 'html.parser')

    # Extract title and description
    title_tag = episode_soup.find('meta', property='og:title')
    description_tag = episode_soup.find('meta', property='og:description')
    title = title_tag['content'] if title_tag else "Bedtime Story"
    description = description_tag['content'] if description_tag else "Bedtime story from ABC Kids Listen"

    # Extract publish date from meta tag
    pub_date_tag = episode_soup.find('meta', attrs={'name': 'LastModifiedDate'})
    if pub_date_tag and pub_date_tag.get('content'):
        try:
            pub_date_obj = datetime.strptime(pub_date_tag['content'], '%Y-%m-%dT%H:%M:%S%z')
            pub_date = pub_date_obj.strftime('%a, %d %b %Y %H:%M:%S GMT')
        except ValueError:
            pub_date = datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S GMT')
    else:
        pub_date = datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S GMT')

    # Extract audio URL from embedded JSON
    audio_url = None
    script_tags = episode_soup.find_all('script')
    for script in script_tags:
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
        continue  # Skip if audio URL not found

    # Add item to RSS feed
    item = ET.SubElement(channel, 'item')
    ET.SubElement(item, 'title').text = title
    ET.SubElement(item, 'description').text = description
    ET.SubElement(item, 'pubDate').text = pub_date
    ET.SubElement(item, 'link').text = episode_url
    ET.SubElement(item, 'guid').text = episode_url
    ET.SubElement(item, 'enclosure', {
        'url': audio_url,
        'type': 'audio/mpeg',
        'length': '12345678'  # You can optionally fetch actual length via HEAD request
    })

# Step 5: Write RSS feed to file
tree = ET.ElementTree(rss)
tree.write('abc-kidslisten-bedtimestories.rss', encoding='utf-8', xml_declaration=True)

print("RSS feed saved to abc-kidslisten-bedtimestories.rss")