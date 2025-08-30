import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime, timezone
import xml.etree.ElementTree as ET
import html

# --- Config ---
main_url = "https://www.abc.net.au/kidslisten/programs/bedtime-stories"
feed_link = "https://example.com/abc-kidslisten-bedtimestories.rss"  # your final RSS URL
now_rfc2822 = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S %z")

# --- Step 1: Fetch main program page ---
response = requests.get(main_url)
soup = BeautifulSoup(response.content, "html.parser")

# Program metadata (fallbacks if not found)
program_title = "ABC Kids Listen Bedtime Stories"
program_description = "Bedtime stories from ABC Kids Listen."
program_image = "https://www.abc.net.au/cm/rimage/12084658-1x1-large.jpg?v=2"
program_link = main_url

# Hero image (if present)
hero_img = soup.find("img")
if hero_img and hero_img.get("src"):
    program_image = urljoin(main_url, hero_img["src"])

# --- Step 2: Collect episode links ---
episodes = []
for a in soup.find_all("a", href=True):
    href = a["href"]
    if "/kidslisten/programs/bedtime-stories/" in href and href.count("/") > 5:
        full_url = urljoin(main_url, href)
        if full_url not in episodes:
            episodes.append(full_url)

episodes = episodes[:5]  # last 5 episodes

# --- Step 3: Build XML ---
ET.register_namespace('', "http://www.itunes.com/dtds/podcast-1.0.dtd")
ET.register_namespace('itunes', "http://www.itunes.com/dtds/podcast-1.0.dtd")
ET.register_namespace('atom', "http://www.w3.org/2005/Atom")

rss = ET.Element("rss", {
    "version": "2.0",
    "xmlns:itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd",
    "xmlns:atom": "http://www.w3.org/2005/Atom"
})

channel = ET.SubElement(rss, "channel")

# --- Channel Metadata ---
ET.SubElement(channel, "itunes:category", text="Kids & Family")
ET.SubElement(channel, "itunes:image", href=program_image)
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

image = ET.SubElement(channel, "image")
ET.SubElement(image, "title").text = program_title
ET.SubElement(image, "url").text = program_image
ET.SubElement(image, "link").text = program_link
ET.SubElement(image, "description").text = program_description

ET.SubElement(channel, "ttl").text = "30"
ET.SubElement(channel, "atom:link", {
    "href": feed_link,
    "rel": "self",
    "type": "application/rss+xml"
})
ET.SubElement(channel, "itunes:explicit").text = "no"
ET.SubElement(channel, "itunes:summary").text = program_description
ET.SubElement(channel, "itunes:subtitle").text = program_description

# Add channel-level keywords (static)
ET.SubElement(channel, "itunes:keywords").text = "kids, stories, bedtime, abc, podcast, children, audio, tales"

# --- Step 4: Scrape each episode ---
for ep_url in episodes:
    ep_res = requests.get(ep_url)
    ep_soup = BeautifulSoup(ep_res.content, "html.parser")

    # Title
    title_tag = ep_soup.find("title")
    ep_title = title_tag.text.strip() if title_tag else "Untitled Episode"

    # Description
    desc_tag = ep_soup.find("meta", {"name": "description"})
    ep_desc = desc_tag["content"].strip() if desc_tag else ep_title

    # JSON-LD audio extraction
    ep_audio = None
    ep_duration = None
    keywords = None
    for script in ep_soup.find_all("script", type="application/ld+json"):
        try:
            data = script.string.strip()
            if '"@type": "AudioObject"' in data:
                import json
                j = json.loads(data)
                ep_audio = j.get("contentUrl")
                ep_duration = j.get("duration")
                keywords = j.get("keywords")
                break
        except Exception:
            pass

    if not ep_audio:
        continue  # skip if no audio

    item = ET.SubElement(channel, "item")
    ET.SubElement(item, "title").text = ep_title
    ET.SubElement(item, "link").text = ep_url

    desc_elem = ET.SubElement(item, "description")
    desc_elem.text = f"<![CDATA[{ep_desc}]]>"

    ET.SubElement(item, "enclosure", {
        "url": ep_audio,
        "length": "0",  # ABC doesn’t expose reliably, leave 0
        "type": "audio/mpeg"
    })
    ET.SubElement(item, "guid", {"isPermaLink": "true"}).text = ep_url
    ET.SubElement(item, "pubDate").text = now_rfc2822

    ET.SubElement(item, "itunes:author").text = "Australian Broadcasting Corporation"
    ET.SubElement(item, "itunes:summary").text = ep_desc
    ET.SubElement(item, "itunes:subtitle").text = ep_desc
    ET.SubElement(item, "itunes:image", href=program_image)

    if ep_duration:
        ET.SubElement(item, "itunes:duration").text = ep_duration

    if keywords:
        ET.SubElement(item, "itunes:keywords").text = keywords

# --- Step 5: Output XML ---
xml_str = ET.tostring(rss, encoding="utf-8", xml_declaration=True).decode("utf-8")
print(xml_str)
