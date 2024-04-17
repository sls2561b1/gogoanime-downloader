import requests
import json
import os
from bs4 import BeautifulSoup
import bs4
import time
import re
import threading
import queue

f = open("setup.json","r")
setup = json.load(f)
f.close()
base_url = setup["gogoanime_main"]
download_folder = setup["downloads"]
captcha_v3 = setup["captcha_v3"]
download_quality = int(setup["download_quality"])
max_threads = setup["max_threads"]

def download(links,folder):
        if not os.path.exists(folder):
            os.makedirs(folder)
        task_queue = queue.Queue()
        threads = []
        for i in range(max_threads):
            t = threading.Thread(target=threaded_download, args=(task_queue,folder))
            t.start()
            threads.append(t)
        for item in links:
            task_queue.put(item)
        task_queue.join()
        for i in range(max_threads):
            task_queue.put(None)
        for t in threads:
            t.join()

def threaded_download(task_queue,folder):
    while True:
        item = task_queue.get()
        if item is None:
            break
        episode = item["episode"]
        download = download_link(item["url"])
        url = download[0]
        title = download[1]
        file_path = f"{folder}/{title}.mp4"
        if os.path.exists(file_path):
            print("File already exists, going to override current data.")
            os.remove(file_path)
        else:
            open(file_path, "x").close()
            print(f"Created new file: {title}.mp4")
        r = requests.get(url, stream=True)
        print(f"Started downloading {title}, episode {episode} to {file_path}.")
        with open(file_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=512 * 512):
                if chunk:
                    f.write(chunk)
        if os.path.getsize(file_path) == 0:
            print(f"Something went wrong while downloading {title}, retrying...")
            task_queue.put(item)
        else:
            print(f"Finished downloading {title}, episode {episode} to {file_path}.")   
        task_queue.task_done()

def download_link(link):
    soup = BeautifulSoup(requests.get(link).text,"html.parser")
    base_download_url = BeautifulSoup(str(soup.find("li",{"class":"dowloads"})),"html.parser").a.get("href")                 #typo in the webcode?
    id = base_download_url[base_download_url.find("id=")+3:base_download_url.find("&typesub")]
    base_download_url = base_download_url[:base_download_url.find("id=")]
    title = BeautifulSoup(requests.post(f"{base_download_url}&id={id}").text,"html.parser")
    title = clean_filename(title.find("span",{"id":"title"}).text)
    response = requests.post(f"{base_download_url}&id={id}&captcha_v3={captcha_v3}")                       #will this captcha work for long?
    soup = BeautifulSoup(response.text,"html.parser")
    backup_link = []
    for i in soup.find_all("div",{"class":"dowload"}):
        if str(BeautifulSoup(str(i),"html.parser").a).__contains__('download=""'):
            link = (BeautifulSoup(str(i),"html.parser").a.get("href"))
            quality = BeautifulSoup(str(i),"html.parser").a.string.replace(" ","").replace("Download","")
            try:
                quality = int(quality[2:quality.find("P")])
            except ValueError:
                print("Failed to parse quality information. Using default quality.")
                quality = 0
            if quality == download_quality:
                print(f"Downloading in {quality}p")
                return [link,title]
            backup_link = [link,quality]
    print(f"Downloading in {backup_link[1]}p")
    return [backup_link[0],title]          #if the prefered download quality is not available the highest quality will automaticly be chosen

def clean_filename(filename):
    cleaned_filename = re.sub(r'[\\/*?:"<>|]', '§', filename)
    return cleaned_filename

def estimate_chunks(size,quality):
    if quality == 360:
        return (size*0.162).__round__()
    elif quality == 480:
        return (size*0.244).__round__()
    elif quality == 720:
        return (size*0.526).__round__()
    elif quality == 1080:
        return size

def get_names(response):
    titles = response.find("ul",{"class":"items"}).find_all("li")
    names = []
    for i in titles:
        name = i.p.a.get("title")
        url = i.p.a.get("href")
        names.append([name,url])
    return names

def search():
    name = input("Anime name you are looking for: ")
    response = BeautifulSoup(requests.get(f"{base_url}/search.html?keyword={name}").text,"html.parser")
    try:
        pages = response.find("ul",{"class":"pagination-list"}).find_all("li")
    except AttributeError:
        pages = response
    
    animes = []
    if type(pages) == bs4.element.ResultSet:
        for i in pages:
            for x in get_names(BeautifulSoup(requests.get(f"{base_url}/search.html{i.a.get('href')}").text,"html.parser")):
                animes.append(x)
    else:
        for i in get_names(pages):
            animes.append(i)
    if len(animes) == 0:
        print("No anime with that name found, please try again")
        return(search())
    print("Following animes found:")
    for i in range(len(animes)):
        print(f"{i+1}: {animes[i][0]}")
    selected_anime = None
    while True:
        selected_anime = input("Enter the number of the anime chosen: ")
        try:
            selected_anime = int(selected_anime)-1
            break
        except ValueError:
            print("ERROR: please enter a number")

    anime = animes[selected_anime]
    
    links = create_links(anime)
    return links

def create_links(anime):
    response = BeautifulSoup(requests.get(f"{base_url}{anime[1]}").text, "html.parser")
    api_url = response.find("script", {"src": ""})
    start = str(api_url).find("base_url_cdn_api") + 20
    end = str(api_url).find("';", start)
    base_url_cdn_api = str(api_url)[start:end]
    movie_id = response.find("input", {"id": "movie_id"}).get("value")
    last_ep = response.find("ul", {"id": "episode_page"}).find_all("a")[-1].get("ep_end")
    response = BeautifulSoup(requests.get(f"{base_url_cdn_api}ajax/load-list-episode?ep_start=0&ep_end={last_ep}&id={movie_id}").text, "html.parser").find_all("a")
    episodes = []
    for i in response:
        ep = str(i.find("div"))
        ep = ep[ep.find("</span>") + 8:ep.find("</div")]
        episodes.insert(0, {
            "episode": ep,
            "url": f'{base_url}{i.get("href").replace(" ", "")}'
        })
    print(f"{len(episodes)} episodes were found.")
    download_type = input("Select a download type (1. Ranged 2. Selected Only): ")

    if download_type == "1":
        while True:
            start = input(f"Specify episode to start download (from 1 to {len(episodes)}): ")
            try:
                start = int(start) - 1
                if not (0 <= start < len(episodes)):
                    raise ValueError
                break
            except ValueError:
                print("ERROR: Please enter a valid episode number.")

        while True:
            end = input(f"Specify episode to end download (from {start + 1} to {len(episodes)}): ")
            try:
                end = int(end)
                if not (start < end <= len(episodes)):
                    raise ValueError
                break
            except ValueError:
                print("ERROR: Please enter a valid episode number.")

        downloads = []
        print(f"Preparing episodes {start + 1} to {end} ...")
        for i in range(start, end):
            downloads.append(episodes[i])
    elif download_type == "2":
        while True:
            selected_episodes = input(f"Enter the episodes (from 1 to {len(episodes)}) to download (separated by spaces): ")
            selected_episodes = selected_episodes.split()
            try:
                selected_episodes = [int(ep) for ep in selected_episodes]
                if not all(0 < ep <= len(episodes) for ep in selected_episodes):
                    raise ValueError
                print(f"Preparing episodes {', '.join(map(str, selected_episodes[:-1])) + (' and ' if len(selected_episodes) > 1 else '') + str(selected_episodes[-1])} ...")
                downloads = [episodes[ep - 1] for ep in selected_episodes]
                break
            except ValueError:
                print("ERROR: Please enter valid episode numbers.")
    else:
        print("Invalid download type selected. Please try again.")
        return create_links(anime)

    return downloads


if __name__ == "__main__":
    links = search()
    download(links,f"{download_folder}/{input('Anime folder: ')}")