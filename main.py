import os
import json
from colorama import Fore, init
import time
from bs4 import BeautifulSoup

init(autoreset=True)

def get_favorites(asset_type_id, items_per_page, page_number, user_id, cookie):
    base_url = "https://www.roblox.com/users/favorites/list-json?assetTypeId=%d&itemsPerPage=%d&pageNumber=%d&userId=%d"
    url = base_url % (asset_type_id, items_per_page, page_number, user_id)

    try:
        response = requests.get(url, cookies={".ROBLOSECURITY": cookie})
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(Fore.RED + f"Failed to fetch favorited games: {e}")
        return None

def get_xsrf_token(cookie):
    try:
        home_page = requests.get("https://www.roblox.com/home", cookies={".ROBLOSECURITY": cookie})
        soup = BeautifulSoup(home_page.text, "html.parser")
        csrf_tag = soup.find("meta", {"name": "csrf-token"})
        return csrf_tag["data-token"]
    except Exception as e:
        print(Fore.RED + f"Failed to fetch XSRF token: {e}")
        return None

def unfavor_game(cookie, game_id, xsrf_token):
    url = "https://www.roblox.com/favorite/toggle"
    headers = {
        "Content-Type": "application/json",
        "X-CSRF-TOKEN": xsrf_token,
    }
    payload = {"assetId": game_id}

    try:
        response = requests.post(url, cookies={".ROBLOSECURITY": cookie}, headers=headers, json=payload)
        response.raise_for_status()
        return response.status_code
    except requests.exceptions.RequestException as e:
        print(Fore.RED + f"Failed to unfavor game: {game_id}. {e}")
        return None

def main(settings):
    os.system('cls' if os.name == 'nt' else 'clear')
    cookie = settings["cookie"]
    mass_unfavor = settings["mass_unfavor"]
    whitelist = set(settings.get("whitelist", []))
    
    try:
        id = requests.get("https://users.roblox.com/v1/users/authenticated", cookies={".ROBLOSECURITY": cookie}).json()["id"]
    except Exception as e:
        print(Fore.RED + "Please provide a valid cookie in settings.json")
        os.system("pause")
        return

    xsrf_token = get_xsrf_token(cookie)

    if xsrf_token is None:
        os.system("pause")
        return

    favorites = get_favorites(9, 500, 1, id, cookie)

    if favorites is None or 'Data' not in favorites:
        os.system("pause")
        return

    games = favorites['Data'].get('Items', [])
    print(Fore.GREEN + f"You currently have {len(games)} favorited games.\n")

    if mass_unfavor:
        input(Fore.LIGHTRED_EX + "!!! Warning: Mass unfavor is enabled. This will unfavorite all your favorited games except the games you've added to the whitelist! Press Enter to continue.")
        os.system('cls' if os.name == 'nt' else 'clear')
        print(Fore.GREEN + f"You currently have {len(games)} favorited games.\n")

    unfavorited = 0
    retry_delay = 10
    total_attempts = 0

    for item in games:
        game_name = item['Item']['Name']
        game_id = item['Item']['AssetId']

        if game_id not in whitelist:
            unfavor = 'y' if mass_unfavor else input(Fore.LIGHTWHITE_EX + f"Do you want to unfavor game {game_name} (ID: {game_id})? (y/n): ").strip().lower()

            if unfavor == 'y':
                while True:
                    response_code = unfavor_game(cookie, game_id, xsrf_token)
                    total_attempts += 1

                    if response_code == 200:
                        print(Fore.GREEN + f"Unfavorited game: {game_name} (ID: {game_id})")
                        unfavorited += 1
                        retry_delay = max(10, total_attempts * 2) 
                        break
                    else:
                        print(Fore.RED + f"Failed to unfavor game: {game_name} (ID: {game_id}).")

                
                        time.sleep(retry_delay)
                        
                        xsrf_token = get_xsrf_token(cookie)
                        if xsrf_token is None:
                            os.system("pause")
                            return
        else:
            print(Fore.YELLOW + f"Skipping game: {game_name} (ID: {game_id})")

    print(Fore.MAGENTA + f"Unfavorited {unfavorited} games.")
    os.system("pause")

if __name__ == "__main__":
    with open("settings.json", 'r') as file:
        settings = json.load(file)
    main(settings)
