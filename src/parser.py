import time
from typing import Dict, List, Tuple

import asyncio
import aiohttp
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import config as conf
from models import Team
from utils import get_match_id, get_corners


def get_teams(url: str) -> Dict[str, Team]:
    """
    Парсим команды 
    - С помощью selenium получаем html
    - С bs4 находим команды ссылки на команды и русское название 
    - Из ссылок берем title, team_id
    - Возвращаем в словаре, где ключ - русское название, значение - объект Team
    """
    options = Options()
    options.add_argument("--headless=new")

    browser = webdriver.Chrome(options=options)
    browser.get(url)

    teams = {}

    try:
        table = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "tableWrapper"))
        )
        table_html = table.get_attribute("outerHTML")
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
    """
    Парсим матчи 
    - С помощью selenium получаем html
    - С bs4 находим матчи 
    - С каждого матча берем кортеж вида: (match_id, team_1, team_2)
    - Возвращаем список кортежей
    """
    browser = webdriver.Chrome()
    browser.get(url)

    matches = []

    try:
        cookie_accept_btn = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.ID, 'onetrust-accept-btn-handler'))
        )
        cookie_accept_btn.click()

        show_more_btn = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, '//*[@id="live-table"]/div[1]/div/div/a/span')
            )
        )
        browser.execute_script(
            "arguments[0].scrollIntoView({block: 'center', inline: 'center'});",
            show_more_btn,
        )
        time.sleep(0.3)
        show_more_btn.click()
        time.sleep(0.3)

        table = browser.find_element(By.ID, "live-table")
        table_html = table.get_attribute("outerHTML")

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


async def async_get_stat(session: aiohttp.ClientSession, match_id: str, sem: asyncio.Semaphore) -> str | None:
    """
    Асинхронный запрос к api flashscore на получение статы по матчу
    """
    url = conf.STAT_API_URL + match_id
    headers = conf.HEADERS
    async with sem:
        try:
            async with session.get(url, headers=headers, timeout=10) as resp:
                if resp.status == 200:
                    return await resp.text()
                return None
        except Exception:
            return None


async def fetch_stats_for_matches(matches: List[Tuple[str, str, str]], concurrency: int = 10) -> Dict[str, str | None]:
    """
    Асинхронно получаем стату на каждый матч
    matches: список кортежей (match_id, team1, team2)
    возвращает dict match_id -> stat_text|None
    """
    sem = asyncio.Semaphore(concurrency)
    connector = aiohttp.TCPConnector(limit_per_host=concurrency)
    timeout = aiohttp.ClientTimeout(total=None)

    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        tasks = [asyncio.create_task(async_get_stat(session, match_id, sem)) for match_id, *_ in matches]
        results = await asyncio.gather(*tasks)
    return {matches[i][0]: results[i] for i in range(len(matches))}


async def apply_stats_to_teams_async(teams: dict, matches: List[Tuple[str, str, str]], concurrency: int = 10):
    """
    Загружает stat для всех matches параллельно и добавляет угловые в teams.
    """
    stats_map = await fetch_stats_for_matches(matches, concurrency=concurrency)

    for match_id, team1_name, team2_name in matches:
        stat_text = stats_map.get(match_id)
        if not stat_text:
            # пропускаем, если stat не получен
            continue

        corners = get_corners(stat_text)
        if not corners:
            continue

        if team1_name in teams:
            teams[team1_name].team_corners.append(corners["team_1"])
            teams[team1_name].enemy_corners.append(corners["team_2"])
            teams[team1_name].total_corners.append(corners["total"])

        if team2_name in teams:
            teams[team2_name].team_corners.append(corners["team_2"])
            teams[team2_name].enemy_corners.append(corners["team_1"])
            teams[team2_name].total_corners.append(corners["total"])
