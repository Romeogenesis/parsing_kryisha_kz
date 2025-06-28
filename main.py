import aiohttp
import asyncio
from bs4 import BeautifulSoup
import json
from re import search
from urllib.parse import urljoin
from playwright.async_api import async_playwright
import requests


def catch_the_number(id_card):
    url = "https://krisha.kz/my/ajaxPopUpRecommendAdvert" 

    headers = {
        "accept": "*/*",
        "accept-encoding": "utf-8",
        "accept-language": "ru,en;q=0.9,en-GB;q=0.8,en-US;q=0.7",
        "content-length": "0",
        "cookie": cookie_header,
        "origin": "https://krisha.kz", 
        "priority": "u=1, i",
        "referer": f"https://krisha.kz/a/show/{id_card}?srchid=0197982a-ab81-72d6-9aff-8f0c990b29a0&srchtype=filter&srchpos=1",
        "sec-ch-ua": '"Microsoft Edge";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0",
        "x-requested-with": "XMLHttpRequest"
    }

    try:
        response = requests.post(url, headers=headers)

        if response.status_code == 200:
            print("Успешный запрос!")
            print("Текст ответа:", response.text)
        else:
            print(f"Ошибка: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Произошла ошибка при выполнении запроса: {e}")


def process_card_page(html):
    soup = BeautifulSoup(html, 'html.parser')
    data = {}

    try:
        meta_description = soup.find('meta', attrs={'name': 'description'})
        meta_content = meta_description['content'] if meta_description else None
        if meta_content and "объявление №" in meta_content:
            start_index = meta_content.index("объявление №") + len("объявление №")
            end_index = meta_content.index(" ", start_index)
            id_card = meta_content[start_index:end_index]
        else:
            id_card = None
    except Exception:
        id_card = None

    try:
        name = soup.find('h1').text.replace('\n', '').strip() if soup.find('h1') else None
        address = name.split(',')[1].strip() if name and ',' in name else None
    except Exception:
        name, address = None, None

    try:
        description = soup.find('div', class_='js-description a-text a-text-white-spaces').text.replace('\n', '')
    except Exception:
        description = 'информация отсутствует'

    try:
        city = soup.find('div', class_='offer__location offer__advert-short-info').find('span').text.strip()
    except Exception:
        city = None

    try:
        price_element = soup.find('div', class_='offer__price').text.replace('\n', '').strip()
    except Exception:
        price_element = None

    try:
        square = name.split('·')[1].strip() if name and '·' in name else None
    except Exception:
        square = None

    try:
        date_elements = soup.find('div', class_='offer__date').find_all('span', class_='offer__date-text')
        creation_date = date_elements[0].text.strip() if len(date_elements) > 0 else None
        archive_date = date_elements[1].text.strip() if len(date_elements) > 1 else None
    except Exception:
        creation_date, archive_date = None, None

    try:
        photo_elements = soup.find_all('picture')
        links_photo = [
            photo.find('img')['src'] for photo in photo_elements if photo.find('img') and 'src' in photo.find('img').attrs
        ]
    except Exception:
        links_photo = []

    try:
        match_red = soup.find_all('span', class_='red-price')
        match_green = soup.find_all('span', class_='green-price')
        match_text = match_red[1].text.strip() if len(match_red) > 0 else match_green[1].text.strip()
        expensive_cheaper = search(r'(\d+\.?\d*)%', match_text).group(0) if match_text else None
    except Exception:
        expensive_cheaper = None
    
    try:
        catch_the_number(id_card)
        phone_div = soup.find('div', class_='offer__contacts-phones')
        phone_number = phone_div.get_text(strip=True)
    except:
        phone_number = None

    data = {
        "id": id_card,
        "name": name,
        "description": description,
        "address": address,
        "city": city,
        "price": price_element,
        "square": square,
        "phone_number": phone_number,
        "creation_date": creation_date,
        "archive_date": archive_date,
        "links_photo": links_photo,
        "% more expensive/cheaper": expensive_cheaper
    }

    return data

async def fetch_page(session, url):
    try:
        async with session.get(url, timeout=60) as response:
            if response.status == 200:
                return await response.text()
            else:
                print(f"Ошибка при загрузке {url}: статус {response.status}")
                return None
    except Exception as e:
        print(f"Ошибка при загрузке {url}: {e}")
        return None

async def process_links(all_links):
    all_data = []

    async with aiohttp.ClientSession() as session:
        tasks = []
        for links in all_links:
            for link in links:
                tasks.append(fetch_page(session, link))

        pages_html = await asyncio.gather(*tasks)

        for html_content in pages_html:
            if html_content:
                data = process_card_page(html_content)
                all_data.append(data)

    return all_data


async def main():
    login_url = "https://krisha.kz/arenda/kvartiry/?das[who]=1&pro[storage]=archive"
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        all_links = []

        await page.goto(login_url, timeout=60000)

        print("Введите логин и пароль вручную, затем нажмите 'Войти'.")
        print("Ожидание завершения авторизации...")
        
        await asyncio.sleep(20)
        cookies = await context.cookies()
        global cookie_header
        cookie_header = "; ".join([f"{cookie['name']}={cookie['value']}" for cookie in cookies])
        for page_num in range(1, 2):
    
            current_url = login_url if page_num == 1 else f"{login_url}&page={page_num}"

            await page.goto(current_url, timeout=60000)

            links = await page.query_selector_all('.a-card__title')
            link_urls = [
                urljoin('https://krisha.kz', await link.get_attribute('href'))
                for link in links
            ]
            all_links.append(link_urls)
        
        
        await browser.close()
            
    all_data = await process_links(all_links)

    with open("output.json", "w", encoding="utf-8") as file:
        json.dump(all_data, file, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    asyncio.run(main())