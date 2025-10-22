from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from models import Team
import config as conf
import requests
from typing import Dict, List, Tuple
import time
from utils import get_match_id

def get_teams(url: str) -> Dict[str, Team]:
    options = Options()
    options.add_argument("--headless=new")

    browser = webdriver.Chrome(options=options)
    browser.get(url)

    teams = {}

    try:
        table = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "tableWrapper"))
        )
        table_html = (table.get_attribute("outerHTML")) 
        soup = BeautifulSoup(table_html, features="html.parser")
        elems = soup.find_all("a")

        for elem in elems:
            path = elem.get("href").strip()
            ru_title = elem.text
            if path.startswith("/team") and ru_title:
                _, _, title, team_id, _ = path.split("/")
                teams[ru_title] = Team(ru_title, title, team_id) 

        return teams

    except Exception as e:
        print("❌ Ошибка:", e)
    finally:
        browser.quit()

def get_matches(url: str) -> List[Tuple[str, str, str]]:
    browser = webdriver.Chrome()
    browser.get(url)

    matches = []

    try:
        cookie_accept_btn = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.ID, 'onetrust-accept-btn-handler'))
        )
        cookie_accept_btn.click()

        show_more_btn = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="live-table"]/div[1]/div/div/a/span'))
        )
        browser.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", show_more_btn)
        time.sleep(0.3)
        show_more_btn.click()
        time.sleep(0.3)
        
        table = browser.find_element(By.ID, "live-table")
        table_html = (table.get_attribute("outerHTML"))
        
        soup = BeautifulSoup(table_html, features="html.parser")
        elems = soup.find_all(class_="event__match")
        for elem in elems:
            link = elem.find("a").get("href")
            match_id = get_match_id(link)

            teams = elem.find_all("img")
            team_1 = teams[0].get("alt")
            team_2 = teams[1].get("alt")

            matches.append((match_id, team_1, team_2))

        return matches

    except Exception as e:
        print("❌ Ошибка:", e)
    finally:
        browser.quit()


def get_stat(match_id: str) -> str:
    url = conf.STAT_API_URL + match_id
    response = requests.get(url=url, headers=conf.HEADERS)
    if response:
        return response.text
    else:
        return None
