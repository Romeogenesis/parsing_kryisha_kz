from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import json

url = 'https://krisha.kz/arenda/kvartiry/?das[who]=1'

with webdriver.Chrome() as browser:
    browser.get(url)
    data = []
    main_feed = browser.find_elements(By.CLASS_NAME, 'a-card__title')
    links = [card.get_attribute('href') for card in main_feed[:5]] 

    for link in links:
        browser.get(link)

        meta_element = browser.find_element(By.CSS_SELECTOR, 'meta[name="description"]')

        content = meta_element.get_attribute('content')

        start_index = content.index("объявление №") + len("объявление №")
        end_index = content.index(" ", start_index)
        id_card = content[start_index:end_index]

        name = browser.find_element(By.CLASS_NAME, 'offer__advert-title').find_element(By.TAG_NAME, 'h1').text

        try:
            description = browser.find_element(By.CSS_SELECTOR, '.js-description.a-text.a-text-white-spaces').text
        except:
             city = 'информация отсутствует'

        address = name.split(',')[1].strip()

        try:
            city = browser.find_element(By.CLASS_NAME, 'offer__location offer__advert-short-info').text
        except:
             city = 'информация отсутствует'

        map = ''

        price_element = browser.find_element(By.CLASS_NAME, 'offer__price').text.replace('\n', '').strip('')
        
        # WebDriverWait(browser, 20).until(
        #      EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR, "iframe[title='reCAPTCHA']"))
        # )

        # WebDriverWait(browser, 20).until(
        #     EC.element_to_be_clickable((By.ID, 'recaptcha-anchor'))
        # ).click()

        # browser.switch_to.default_content()

        # mobile_phone = browser.find_element(By.CLASS_NAME, 'offer__contacts-phones').text

        square = browser.find_elements(By.CLASS_NAME, 'offer__advert-short-info')[3].text

        since = browser.find_element(By.CLASS_NAME, 'a-nb-views-text').text

        map_element = ''

        photo_elements = browser.find_elements(By.CLASS_NAME, 'gallery__small-item')
        links_photo = [photo.get_attribute('src') for photo in photo_elements]

        data.append({
                    "id": id_card,
                    "name": name,
                    #"description": description,
                    "address": address,
                    "city": city,
                    #"coordinates": coordinates,
                    "price": price_element,
                    #"mobile_phone": mobile_phone,
                    "square": square,
                    "since": since,
                    "links_photo": links_photo
                })
        
        browser.back()


with open("output.json", "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


