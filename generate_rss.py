import requests
from bs4 import BeautifulSoup
from xml.etree.ElementTree import Element, SubElement, ElementTree
from datetime import datetime, timezone

# Step 1: Get the main page and find the latest episode link
main_url = "https://www.abc.net.au/kidslisten/programs/bedtime-stories"
main_response = requests.get(main_url)
main_soup = BeautifulSoup(main_response.content, "html.parser")

# Find the 'Latest Episode' link
latest_episode_link = None
for a_tag in main_soup.find_all("a", href=True):
    if "Latest Episode" in a_tag.text:
        latest_episode_link = a_tag["href"]
        break

if not latest_episode_link:
    raise Exception("Could not find the latest episode link.")

# Construct full URL if necessary
if not latest_episode_link.startswith("http"):
    latest_episode_url = "https://www.abc.net.au" + latest_episode_link
else:
    latest_episode_url = latest_episode_link

# Step 2: Get the episode page and extract audio URL and metadata
episode_response = requests.get(latest_episode_url)
episode_soup = BeautifulSoup(episode_response.content, "html.parser")

# Find audio URL
audio_url = None
for source_tag in episode_soup.find_all("source"):
    if "audio/aac" in source_tag.get("type", ""):
        audio_url = source_tag.get("src")
        break

if not audio_url:
    raise Exception("Could not find audio/aac URL.")

# Extract title and description
title_tag = episode_soup.find("meta", attrs={"property": "og:title"})
description_tag = episode_soup.find("meta", attrs={"property": "og:description"})

title = title_tag["content"] if title_tag else "Latest Bedtime Story"
description = description_tag["content"] if description_tag else "Bedtime story from ABC Kids Listen"

# Step 3: Create RSS feed
rss = Element("rss", version="2.0")
channel = SubElement(rss, "channel")

SubElement(channel, "title").text = "ABC Kids Listen - Bedtime Stories"
SubElement(channel, "link").text = main_url
SubElement(channel, "description").text = "Latest bedtime stories from ABC Kids Listen"

item = SubElement(channel, "item")
SubElement(item, "title").text = title
SubElement(item, "description").text = description
SubElement(item, "pubDate").text = datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S %z')
SubElement(item, "link").text = latest_episode_url

enclosure = SubElement(item, "enclosure")
enclosure.set("url", audio_url)
enclosure.set("type", "audio/aac")
enclosure.set("length", "0")

# Step 4: Save to XML file
tree = ElementTree(rss)
tree.write("yoto_feed.xml", encoding="utf-8", xml_declaration=True)

print("RSS feed saved to yoto_feed.xml")

