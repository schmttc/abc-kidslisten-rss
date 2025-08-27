import requests
from bs4 import BeautifulSoup

# URL of the ABC Kids Listen Bedtime Stories page
main_url = "https://www.abc.net.au/kidslisten/programs/bedtime-stories"

# Fetch the page content
response = requests.get(main_url)
soup = BeautifulSoup(response.content, 'html.parser')

# Find all <a> tags and look for one that contains the text "Latest Episode"
latest_episode_url = None
for a_tag in soup.find_all('a', href=True):
    if 'Latest Episode' in a_tag.get_text(strip=True):
        latest_episode_url = a_tag['href']
        break

# Print the full episode URL for debugging
if latest_episode_url:
    full_url = requests.compat.urljoin(main_url, latest_episode_url)
    print("Latest Episode URL:", full_url)
else:
    print("Latest Episode link not found.")

