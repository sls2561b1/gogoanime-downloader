import requests
import json
import os
from bs4 import BeautifulSoup
import bs4
import time
from tqdm import tqdm
import re

f = open("setup.json","r")
setup = json.load(f)
f.close()
base_url = setup["gogoanime_main"]
download_folder = setup["downloads"]
captcha_v3 = setup["captcha_v3"]
download_quality = int(setup["download_quality"])

def download(links,folder):
        if not os.path.exists(folder):
            os.makedirs(folder)
        for i in links:
            episode = i["episode"]
            download = download_link(i["url"])
            url = download[0]
            chunk_estimate = download[1]
            title = download[2]

            if os.path.exists(f"{folder}/{title}.mp4"):
                print("file already exists, going to override current data")
                os.remove(f"{folder}/{title}.mp4")
            else:
                open(f"{folder}/{title}.mp4","x").close()
                print(f"created new file: {title}.mp4")
            r = requests.get(url,stream=True)
            print(f"started downloading {title}, episode {episode} to {folder}/{title}.mp4")

            with open(f"{folder}/{title}.mp4", 'wb') as f:
                with tqdm(total=chunk_estimate, desc="Downloading") as bar:
                    for chunk in r.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            f.write(chunk)
                            bar.update(1)
            print(f"finished downloading {title}, episode {episode} to {folder}/{title}.mp4")

def download_link(link):
    soup = BeautifulSoup(requests.get(link).text,"html.parser")
    base_download_url = BeautifulSoup(str(soup.find("li",{"class":"dowloads"})),"html.parser").a.get("href")                 #typo in the webcode?
    id = base_download_url[base_download_url.find("id=")+3:base_download_url.find("&typesub")]
    base_download_url = base_download_url[:base_download_url.find("id=")]
    size = BeautifulSoup(requests.post(f"{base_download_url}&id={id}").text,"html.parser")
    title = clean_filename(size.find("span",{"id":"title"}).text)
    size = size.find("span",{"id":"filesize"}).text
    size = int(float(size[:size.find(" ")]).__round__())
    response = requests.post(f"{base_download_url}&id={id}&captcha_v3={captcha_v3}")                       #will this captcha work for long?
    soup = BeautifulSoup(response.text,"html.parser")
    backup_link = []
    for i in soup.find_all("div",{"class":"dowload"}):
        if str(BeautifulSoup(str(i),"html.parser").a).__contains__('download=""'):
            link = (BeautifulSoup(str(i),"html.parser").a.get("href"))
            quality = BeautifulSoup(str(i),"html.parser").a.string.replace(" ","").replace("Download","")
            quality = int(quality[2:quality.find("P")])
            if quality == download_quality:
                print(f"downloading in {quality}p")
                return [link,int(estimate_chunks(size,quality)),title]
            backup_link = [link,quality]
    print(f"downloading in {backup_link[1]}p")
    return [backup_link[0],int(estimate_chunks(size,backup_link[1])),title]          #if the prefered download quality is not available the highest quality will automaticly be chosen

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
        print("no anime with that name found, please try again")
        return(search())
    print("following animes found:")
    for i in range(len(animes)):
        print(f"{i+1}: {animes[i][0]}")
    selected_anime = None
    while True:
        selected_anime = input("give the Number of the anime chosen: ")
        try:
            selected_anime = int(selected_anime)-1
            break
        except ValueError:
            print("error: please enter a number")

    anime = animes[selected_anime]
    
    links = create_links(anime)
    return links

def create_links(anime):
    response = BeautifulSoup(requests.get(f"{base_url}{anime[1]}").text,"html.parser")
    api_url = response.find("script",{"src":""})
    start = str(api_url).find("base_url_cdn_api")+20
    end = str(api_url).find("';",start)
    base_url_cdn_api = str(api_url)[start:end]
    movie_id = response.find("input",{"id":"movie_id"}).get("value")
    last_ep = response.find("ul",{"id":"episode_page"}).find_all("a")[len(response.find("ul",{"id":"episode_page"}).find_all("a"))-1].get("ep_end")
    response = BeautifulSoup(requests.get(f"{base_url_cdn_api}ajax/load-list-episode?ep_start=0&ep_end={last_ep}&id={movie_id}").text,"html.parser").find_all("a")
    episodes = []
    for i in response:
        ep = str(i.find("div"))
        ep = ep[ep.find("</span>")+8:ep.find("</div")]
        episodes.insert(0,{
            "episode":ep,
            "url":f'{base_url}{i.get("href").replace(" ","")}'
        })

    while True:
        start = input(f"{len(episodes)} episodes were found, specify episode to start download (from 1 to {len(episodes)}): ")
        try:
            start = int(start)-1
            break
        except ValueError:
            print("error: please enter a number")
    while True:
        end = input(f"specify episode to end download (from 1 to {len(episodes)}): ")
        try:
            end = int(end)
            break
        except ValueError:
            print("error: please enter a number")
    
    downloads = []
    print(f"downloading episodes {start+1} to {end}:")
    for i in range(start,end):
        downloads.append(episodes[i])
    
    return downloads


if __name__ == "__main__":
    links = search()
    download(links,f"{download_folder}/{input('anime folder: ')}")   