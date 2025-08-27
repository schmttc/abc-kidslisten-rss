import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime, timezone
import re
import json
from xml.etree.ElementTree import Element, SubElement, ElementTree

main_url = "https://www.abc.net.au/kidslisten/programs/bedtime-stories"
response = requests.get(main_url)
soup = BeautifulSoup(response.content, "html.parser")

# --- Step 1: Get the last 5 episode links ---
episode_links = []
for div in soup.find_all("div", class_="CardLayout_content__zgsBr"):
    a_tag = div.find("a", href=True)
    if a_tag:
        full_url = urljoin(main_url, a_tag["href"])
        episode_links.append(full_url)
    if len(episode_links) >= 5:
        break

print("Found episode links:", episode_links)

# --- Step 2: Parse each episode page ---
episodes = []
for url in episode_links:
    ep_resp = requests.get(url)
    ep_soup = BeautifulSoup(ep_resp.content, "html.parser")

    # Title & description from meta tags
    title_tag = ep_soup.find("meta", property="og:title")
    desc_tag = ep_soup.find("meta", property="og:description")
    title = title_tag["content"] if title_tag else "Bedtime Story"
    description = desc_tag["content"] if desc_tag else "ABC Kids Listen story"

    # Extract AAC audio URL from embedded JSON
    audio_url = None
    for script in ep_soup.find_all("script"):
        if script.string and "renditions" in script.string:
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
        print(f"⚠️ No audio URL found for {url}")
        continue

    # PubDate - if page doesn’t provide, fallback to "now"
    pub_date = datetime.now(timezone.utc).strftime(
        "%a, %d %b %Y %H:%M:%S GMT"
    )

    episodes.append({
        "title": title,
        "description": description,
        "link": url,
        "guid": url,
        "pubDate": pub_date,
        "audio_url": audio_url
    })

# --- Step 3: Build RSS feed ---
rss = Element("rss", {
    "version": "2.0",
    "xmlns:atom": "http://www.w3.org/2005/Atom"
})
channel = SubElement(rss, "channel")

SubElement(channel, "atom:link", {
    "rel": "self",
    "href": "https://example.com/yoto_feed.xml",  # Replace with your actual feed URL
    "type": "application/rss+xml"
})

SubElement(channel, "title").text = "ABC Kids Listen - Bedtime Stories"
SubElement(channel, "link").text = main_url
SubElement(channel, "description").text = "Latest bedtime stories from ABC Kids Listen"
SubElement(channel, "language").text = "en-us"

# Add up to 5 items
for ep in episodes:
    item = SubElement(channel, "item")
    SubElement(item, "title").text = ep["title"]
    SubElement(item, "description").text = ep["description"]
    SubElement(item, "pubDate").text = ep["pubDate"]
    SubElement(item, "link").text = ep["link"]
    SubElement(item, "guid").text = ep["guid"]
    SubElement(item, "enclosure", {
        "url": ep["audio_url"],
        "type": "audio/aac",
        "length": "0"
    })

ElementTree(rss).write("yoto_feed.xml", encoding="UTF-8", xml_declaration=True)

print("✅ RSS feed with last 5 episodes saved to yoto_feed.xml")
