import requests
from bs4 import BeautifulSoup

# Step 1: Fetch the main Bedtime Stories page
main_url = "https://www.abc.net.au/kidslisten/programs/bedtime-stories"
response = requests.get(main_url)
soup = BeautifulSoup(response.content, 'html.parser')

# Step 2: Search for the button element that precedes the "Latest Episode" text
latest_episode_url = None
for button in soup.find_all('a'):
    if button.find_next(string="Latest Episode"):
        latest_episode_url = button.get('href')
        print("Found URL:", latest_episode_url)
        break

# If no URL was found, print a message
if not latest_episode_url:
    print("Could not find the latest episode URL.")

