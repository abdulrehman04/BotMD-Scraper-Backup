
import requests
import time
import os
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from flask import Flask, render_template, request
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

app = Flask(__name__)


chrome_options = webdriver.ChromeOptions()
chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("window-size=800,600")

@app.route('/', methods=['POST', "GET"])
def home():
    return "Hello World"

@app.route('/test', methods=['POST', "GET"])
def test():
    return "Hello Test"

@app.route('/scrape/<lat>/<long>', methods=['POST', "GET"])
def scrapeData(lat, long):
    try:
        driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), chrome_options=chrome_options)
        driver.get("https://www.google.com/maps/search/COVID-19+Vaccine/@{},{},13z".format(lat, long))

        All_labs = []
        results = driver.find_element(By.XPATH ,'//*[@id="pane"]/div/div[1]/div/div/div[2]/div[1]')
        nextPageButton = driver.find_element(By.XPATH ,'/html/body/div[3]/div[9]/div[8]/div/div[1]/div/div/div[2]/div[2]/div/div[1]/div/button[2]')

        while True:
            totalResults = driver.find_element(By.XPATH ,'/html/body/div[3]/div[9]/div[8]/div/div[1]/div/div/div[2]/div[2]/div/div[1]/span/span[2]')
            while All_labs.__len__() < (int(totalResults.text) - 5):
                allTags = results.find_elements(By.TAG_NAME ,'a')
                for tag in allTags:
                    if tag.get_attribute('aria-label') not in All_labs:
                        All_labs.append(tag.get_attribute('aria-label'))

                results.send_keys(Keys.ARROW_DOWN)
                results.send_keys(Keys.ARROW_DOWN)
                results.send_keys(Keys.ARROW_DOWN)
                results.send_keys(Keys.ARROW_DOWN)
                results.send_keys(Keys.ARROW_DOWN)
            if nextPageButton.get_attribute('disabled') == 'true':
                break
            nextPageButton.click()
            print("Donee")
            time.sleep(4)

        labData = []
        
        for lab in All_labs:
            response = requests.get("https://maps.googleapis.com/maps/api/place/textsearch/json?query={}&key=AIzaSyBfBHArwvW8-iMXSBPr0FuHhba924pzuf8".format(lab))
            jsonResponse = response.json()
            if jsonResponse['status'] != 'ZERO_RESULTS':
                photo = {'content': None}
                hasPhoto = False
                hasRating = False
                userRating = False
                for key in jsonResponse['results'][0]:
                    if key == 'photos':
                        hasPhoto = True
                    if key == 'rating':
                        hasRating = True
                    if key == 'user_ratings_total':
                        userRating = True
                if hasPhoto == True:
                    photo = requests.get("https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photo_reference={}&key=AIzaSyBfBHArwvW8-iMXSBPr0FuHhba924pzuf8".format(jsonResponse['results'][0]['photos'][0]['photo_reference']))
            
                db.collection("Labs").add({
                    'name': jsonResponse['results'][0]['name'],
                    'formatted_address': jsonResponse['results'][0]['formatted_address'],
                    'place_id': jsonResponse['results'][0]['place_id'],
                    'photo': photo.content if hasPhoto else None,
                    'geometry': jsonResponse['results'][0]['geometry'],
                    'rating': jsonResponse['results'][0]['rating'] if hasRating else None,
                    'user_ratings_total': jsonResponse['results'][0]['user_ratings_total'] if userRating else None,
                })

        return {"data": labData}
    except Exception as e:
        db.collection("Errors").add({
            'error': e,
        })
        return {"data": "Error"}

if __name__ == "__main__":
    app.run(host='0.0.0.0',port=5000,debug=True)
