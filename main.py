from os import link
from fastapi import FastAPI, Request
from bs4 import BeautifulSoup
import lxml
import requests
import json

from requests.api import request
def bsoup(text):
    soup = BeautifulSoup(text,'lxml')
    return soup

base_url = 'https://gogoanime.ai/'

def search_anime(text):
    search_url = f'{base_url}/search.html?keyword={text}'
    html = requests.get(search_url)
    soup = bsoup(html.text)
    search_items = soup.find('div',attrs = {'class':'last_episodes'}).find_all('li')
    data = [{
        "title": x.a.get('title'),
        "slug": x.a.get('href').split('/')[-1],
        "thumbnail": x.img.get('src')
    } for x in search_items]
    return data

def gogo_play(url):
    url = 'https:'+  url.replace('streaming','ajax').replace('load','ajax')
    html = json.loads(requests.get(url).text)
    return html["source"][0]['file']

def streamsb(slug):    
    url = f"https://streamsb.net/d/{slug}"
    html = requests.get(url)
    soup = bsoup(html.text)
    list = soup.find('table',attrs={"width":"60%"}).find_all('a')[-1].get('onclick').replace('download_video(','').replace(')','').replace("'",'').split(',')
    url = f'https://streamsb.net/dl?op=download_orig&id={list[0]}&mode={list[1]}&hash={list[2]}'
    print(url)
    html = requests.get(url)
    soup = bsoup(html.text)
    link = soup.find("a",text="Direct Download Link").get('href')
    return link


app = FastAPI()
@app.get('/')
def root(request: Request):
    return {"root": request.url.hostname}

@app.get('/search')
async def search(name: str):
    data = search_anime(name)
    return {'response': data}


@app.get('/details')
def anime_details(slug:str , request: Request):
    details_url = f"{base_url}category/{slug}"
    html = requests.get(details_url)
    soup = bsoup(html.text)
    title = soup.find('div',attrs={"class":"anime_info_body_bg"}).h1.text
    thumbnail = soup.find('div',attrs={"class":"anime_info_body_bg"}).img.get('src')
    ep_end = soup.find('ul',attrs={"id":"episode_page"}).find('li').a.get("ep_end")
    desc_info =soup.find('div',attrs={"class":"anime_info_body_bg"}).find_all('p',attrs={"class":"type"})
    type = desc_info[0].text.replace('\n','').strip()
    desc = desc_info[1].text.replace('\n','').strip()
    genre = desc_info[2].text.replace('\n','').strip()
    released = desc_info[3].text.replace('\n','').strip()
    status = desc_info[4].text.replace('\n','').strip()
    other_name = desc_info[5].text.replace('\n','').strip()

    data = {
        "title":title,
        "thumbnail":thumbnail,
        "type":type,
        "summary":desc,
        "genre":genre,
        "release_year":released,
        "status":status,
        "other_name":other_name,
        "episodes":[{
            f'{x}': f"{request.url.hostname}/episode?slug={slug}&ep={x+1}"
        } for x in range(0,int(ep_end)+1)]
    }
    return {'response':data}


@app.get('/episode')
def episode_link(slug,ep):
    episode_url = f"{base_url}{slug}-episode-{ep}"
    html = requests.get(episode_url)
    soup = bsoup(html.text)
    links_div = soup.find('div',attrs={"class":"anime_muti_link"}).find_all('a')
    data = {
        "stream_links":[
            {
            "link": gogo_play(links_div[0]['data-video']),
            "server":"GGA"
            }
        ]
    }
    return {'response':data}

