import requests
from bs4 import BeautifulSoup
from xml.etree.ElementTree import Element, SubElement, ElementTree
from datetime import datetime, timezone

# Step 1: Get the latest episode page
base_url = "https://www.abc.net.au/kidslisten/programs/bedtime-stories"
response = requests.get(base_url)
soup = BeautifulSoup(response.content, "html.parser")

# Find the latest episode link
latest_link_tag = soup.find("a", href=True)
latest_episode_url = "https://www.abc.net.au" + latest_link_tag["href"]

# Step 2: Get the audio URL and metadata from the episode page
episode_response = requests.get(latest_episode_url)
episode_soup = BeautifulSoup(episode_response.content, "html.parser")

audio_tag = episode_soup.find("source", {"type": "audio/aac"})
audio_url = audio_tag["src"] if audio_tag else ""

title_tag = episode_soup.find("meta", {"property": "og:title"})
title = title_tag["content"] if title_tag and title_tag.get("content") else "Bedtime Story"

desc_tag = episode_soup.find("meta", {"property": "og:description"})
description = desc_tag["content"] if desc_tag and desc_tag.get("content") else "ABC Kids Listen Bedtime Story"

pub_date = datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S GMT')

# Step 3: Build RSS XML
rss = Element("rss", version="2.0")
channel = SubElement(rss, "channel")

SubElement(channel, "title").text = "Yoto Bedtime Stories"
SubElement(channel, "link").text = base_url
SubElement(channel, "description").text = "Latest bedtime story from ABC Kids Listen"

item = SubElement(channel, "item")
SubElement(item, "title").text = title
SubElement(item, "description").text = description
SubElement(item, "pubDate").text = pub_date
SubElement(item, "guid").text = audio_url
enclosure = SubElement(item, "enclosure", url=audio_url or "", type="audio/aac", length="0")

# Step 4: Write to file
tree = ElementTree(rss)
tree.write("yoto_feed.xml", encoding="utf-8", xml_declaration=True)

print("RSS feed generated successfully.")

