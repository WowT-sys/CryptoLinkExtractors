import requests
import json
import time

def get_crypto_list(api_key, start=1, limit=5000):
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/map"
    headers = {
        "Accepts": "application/json",
        "X-CMC_PRO_API_KEY": api_key,
    }
    params = {
        "start": start,
        "limit": limit
    }
    while True:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json()["data"]
        elif response.status_code == 429:
            print("Rate limit exceeded. Waiting 60 seconds before retrying...")
            time.sleep(60)
        else:
            print("Error fetching cryptocurrency list:", response.text)
            return None
        
def get_crypto_info(api_key, crypto_ids, filename="websites.txt"):
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/info"
    headers = {
        "Accepts": "application/json",
        "X-CMC_PRO_API_KEY": api_key,
    }
    batch_size = 10
    for i in range(0, len(crypto_ids), batch_size):
        batch_ids = crypto_ids[i:i+batch_size]
        parmans = {"id": ",".join(map(str, batch_ids))}
        while True:
            response = requests.get(url, headers=headers, params=parmans)
            if response.status_code == 200:
                data = response.json()["data"]
                with open(filename, "a") as f:
                    for crypto_ids, info in data.items():
                        if "urls" in info and "website" in info["urls"] and info["urls"]["websites"]:
                            website = info["urls"]["website"][0]
                            name = info["name"]
                            f.write(f"{name}: {website}\n")
                            print(f"Saved {name}: {website}")

                break
            elif response.status_code == 429:
                print("Rate limit execeeded. Waiting 60 seconds before retrying...")
                time.sleep(60)
            else:
                print("Error fetching cryptocurrency info:", response.text)
                break

def main():
    banner = r"""
       ____ ___  _   _ _   _ __  __    _    ____ _  _______ ____  
      / ___/ _ \| \ | | \ | |  \/  |  / \  / ___| |/ / ____|  _ \ 
     | |  | | | |  \| |  \| | |\/| | / _ \| |   | ' /|  _| | |_) |
     | |__| |_| | |\  | |\  | |  | |/ ___ \ |___| . \| |___|  _ < 
      \____\___/|_| \_|_| \_|_|  |_/_/   \_\____|_|\_\_____|_| \_\
    """
    print(banner)
    api_key = "API-KEY-HERE"
    start = 1
    limit = 100
    filename = "COINMARKETCAP-LINKS.TXT"
    open(filename, "w").close()
    while True:
        print(f"Fatching cryptocurrency list from {start}...")
        crypto_list = get_crypto_list(api_key, start=start, limit=limit)
        if not crypto_list:
            continue
        crypto_ids = [crypto["id"]for crypto in crypto_list]
        print("Fatching cryptocurrency details in batches...")
        get_crypto_info(api_key, crypto_ids, filename)
        if len(crypto_list) < limit:
            break
        start += limit

if __name__ == "__main__":
    main()
    