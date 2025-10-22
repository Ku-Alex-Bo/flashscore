import csv
import logging
from parser import get_matches, get_stat, get_teams

import config as conf
from utils import get_corners

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-5s %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def pipeline():
    # 1.Парсим команды
    logger.info("Парсим команды...")
    teams: dict = get_teams(conf.LALIGA_TABLE)
    teams.update(get_teams(conf.APL_TABLE))

    # 2.Парсим матчи
    logger.info("Парсим матчи...")
    matches: list = get_matches(conf.LALIGA_MATCHES)
    matches += get_matches(conf.APL_MATCHES)

    # 3. Получаем стату по угловым
    logger.info("Получаем стату по угловым...")
    for match in matches:
        stat: str = get_stat(match[0])
        corners: dict = get_corners(stat)

        teams[match[1]].team_corners.append(corners["team_1"])
        teams[match[1]].enemy_corners.append(corners["team_2"])
        teams[match[1]].total_corners.append(corners["total"])

        teams[match[2]].team_corners.append(corners["team_2"])
        teams[match[2]].enemy_corners.append(corners["team_1"])
        teams[match[2]].total_corners.append(corners["total"])

    # 4. Сортируем от наибольшего среднего тотала к меньшему:
    logger.info("Сортируем...")
    sorted_teams = sorted(
        teams.values(), key=lambda team: team.avg_total_corners, reverse=True
    )

    # 5. Сохраняем в csv формат
    logger.info("Сохраняем в csv формат")
    with open("corners.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["team", "avg_total_corners", "avg_team_corners", "avg_enemy_corners"]
        )

        for team in sorted_teams:
            writer.writerow(
                [
                    team.ru_title,
                    team.avg_total_corners,
                    team.avg_team_corners,
                    team.avg_enemy_corners,
                ]
            )

    logger.info("Готово!")


if __name__ == "__main__":
    pipeline()
