from urllib import response
import requests
import time
import os
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from flask import Flask, render_template, request
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import json

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

app = Flask(__name__)

options = Options()
options.add_argument("--headless")
options.add_argument("window-size=1400,1500")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("start-maximized")
options.add_argument("enable-automation")
options.add_argument("--disable-infobars")
options.add_argument("--disable-dev-shm-usage")

@app.route("/", methods =["GET"])
def home():
    return "Hello there"
    
@app.route('/scrape/<lat>/<long>', methods=['POST', "GET"])
def scrapeData(lat, long):
    try:
        driver = webdriver.Chrome(options=options)
        driver.get("https://www.google.com/maps/search/COVID-19+Vaccine/@{},{},13z".format(lat, long))

        print("https://www.google.com/maps/search/COVID-19+Vaccine/@{},{},13z".format(lat, long))
        All_labs = []
        results = driver.find_element(By.XPATH ,'//*[@id="pane"]/div/div[1]/div/div/div[2]/div[1]')
        nextPageButton = driver.find_element(By.XPATH ,'/html/body/div[3]/div[9]/div[8]/div/div[1]/div/div/div[2]/div[2]/div/div[1]/div/button[2]')

        run = True
        while run:
            for _ in range(60):
                results.send_keys(Keys.ARROW_DOWN)
                results.send_keys(Keys.ARROW_DOWN)
                results.send_keys(Keys.ARROW_DOWN)
                results.send_keys(Keys.ARROW_DOWN)
                results.send_keys(Keys.ARROW_DOWN)
            all_scroller_children_by_xpath = results.find_elements_by_xpath('//*[@id="pane"]/div/div[1]/div/div/div[2]/div[1]/div')

            for child in all_scroller_children_by_xpath:
                if(all_scroller_children_by_xpath.index(child) > 1):
                    print(child.get_attribute("jstcache"))
                    if all_scroller_children_by_xpath.index(child) == (all_scroller_children_by_xpath.__len__()-1) :
                    # if child.get_attribute("jstcache") != '184':
                        print('ended')
                        if nextPageButton.get_attribute('disabled') == 'true':
                            run = False
                            break
                        nextPageButton.click()
                        time.sleep(4)
                    else:
                        tag = child.find_elements(By.TAG_NAME ,'a')
                        print("Here")
                        if tag.__len__() != 0:
                            print(tag[0].get_attribute("aria-label"))
                            if tag[0].get_attribute('aria-label') not in All_labs:
                                All_labs.append(tag[0].get_attribute("aria-label"))

        driver.quit()
        for lab in All_labs:
            response = requests.get("https://maps.googleapis.com/maps/api/place/textsearch/json?query={}&key=AIzaSyBfBHArwvW8-iMXSBPr0FuHhba924pzuf8".format(lab))
            jsonResponse = response.json()
            if jsonResponse['status'] != 'ZERO_RESULTS':
                photo = {'content': None}
                hasPhoto = False
                hasRating = False
                userRating = False
                hasAddress = False
                print(lab)
                
                for key in jsonResponse['results'][0]:
                    if key == 'photos':
                        hasPhoto = True
                    if key == 'formatted_address':
                        hasAddress = True
                    if key == 'rating':
                        hasRating = True
                    if key == 'user_ratings_total':
                        userRating = True
                if hasPhoto == True:
                    photo = requests.get("https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photo_reference={}&key=AIzaSyBfBHArwvW8-iMXSBPr0FuHhba924pzuf8".format(jsonResponse['results'][0]['photos'][0]['photo_reference']))

                db.collection("Labs").add({
                    'name': jsonResponse['results'][0]['name'],
                    'formatted_address': jsonResponse['results'][0]['formatted_address'] if hasAddress else "",
                    'place_id': jsonResponse['results'][0]['place_id'],
                    'photo': photo.content if hasPhoto else None,
                    'geometry': jsonResponse['results'][0]['geometry'],
                    'rating': jsonResponse['results'][0]['rating'] if hasRating else None,
                    'user_ratings_total': jsonResponse['results'][0]['user_ratings_total'] if userRating else None,
                })
                print("Added")
                print("Index is: {}".format(All_labs.index(lab)))
            else:
                print("sleeping now")
                time.sleep(5)

        return {"data": All_labs}
    except Exception as e:
        db.collection("Errors").add({
            'error': e,
        })
        return {"data": "Error"}


if __name__ == "__main__":
    app.run(host='0.0.0.0',port=8080,debug=True)



