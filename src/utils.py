import re
from typing import Dict


def get_corners(stat: str) -> Dict[str, str] | None:
    """
    С помощью регулярки получаем количество угловых первой и второй команды
    """
    pattern = r"Угловые¬SH÷(\d+)¬SI÷(\d+)"
    match = re.search(pattern, stat)
    if match:
        team_1 = int(match.group(1))
        team_2 = int(match.group(2))
        return {"team_1": team_1, "team_2": team_2, "total": team_1 + team_2}
    return None


def get_match_id(link: str) -> str:
    """
    С помощью id матча из ссылки
    """
    pattern = r"mid=([A-Za-z0-9]+)"
    m = re.search(pattern, link)
    return m.group(1)
