"""Time checks and group recommendations, implemented entirely in Python."""
import math
import re
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

TAIWAN = ZoneInfo('Asia/Taipei')


@dataclass(frozen=True)
class Diner:
    name: str = '用餐者'
    budget: float = 2.5
    cuisine: str = '不限'
    area: str = '不限'


@dataclass(frozen=True)
class Weights:
    price: int = 35
    cuisine: int = 45
    area: int = 20

    def normalized(self):
        values = (self.price, self.cuisine, self.area)
        if any(value < 0 for value in values):
            raise ValueError('權重不得為負數')
        total = sum(values)
        return tuple(value / total for value in values) if total else (1 / 3,) * 3


def taiwan_now():
    return datetime.now(TAIWAN)


def opening_status(restaurant, at):
    """Opening endpoints are exclusive; naive datetimes mean Taiwan wall time."""
    if at is None:
        return 'unknown', '營業時間待確認'
    if at.tzinfo is not None:
        at = at.astimezone(TAIWAN)
    special = restaurant.get('specialHours', '')
    if ('每週日' in special and at.weekday() == 6) or ('每週一' in special and at.weekday() == 0):
        return 'closed', '當日公休'
    hours = restaurant.get('hours', '')
    if at.weekday() in (5, 6) and '假日' in special:
        hours = special.replace('假日', '')
    if not hours:
        return 'unknown', '營業時間待確認'
    if '24小時' in hours:
        return 'open', '營業中'
    spans = re.findall(r'(\d{1,2}):(\d{2})~(\d{1,2}):(\d{2})', hours)
    if not spans:
        return 'unknown', '營業時間待確認'
    current = at.hour * 60 + at.minute
    for sh, sm, eh, em in spans:
        start, end = int(sh) * 60 + int(sm), int(eh) * 60 + int(em)
        is_open = start <= current < end if end > start else current >= start or current < end
        if is_open:
            return 'open', '營業中'
    return 'closed', '非營業時間'


def individual_scores(restaurant, diner):
    """Never use invented distances, coordinates or travel times in scoring."""
    price = max(0.0, 1 - max(0, restaurant['price'] - diner.budget) / 1.5)
    cuisine = 1.0 if diner.cuisine == '不限' or diner.cuisine in restaurant['types'] else 0.15
    area = 1.0 if diner.area == '不限' or diner.area == restaurant['location'] else 0.25
    return price, cuisine, area


def recommendation_reasons(restaurant, diners):
    in_budget = sum(restaurant['price'] <= diner.budget for diner in diners)
    liked = sum(diner.cuisine != '不限' and diner.cuisine in restaurant['types'] for diner in diners)
    area_liked = sum(diner.area != '不限' and diner.area == restaurant['location'] for diner in diners)
    reasons = ['符合所有人的預算' if in_budget == len(diners) else f'{in_budget}/{len(diners)} 人預算內']
    if liked:
        reasons.append(f'符合 {liked} 人的料理偏好')
    elif all(diner.cuisine == '不限' for diner in diners):
        reasons.append('大家都願意嘗試的口味')
    else:
        reasons.append('換個口味的折衷選擇')
    if area_liked:
        reasons.append(f'位於 {area_liked} 人偏好的區域')
    return reasons


def recommend(restaurants, diners, weights=Weights(), *, at=None, search='',
              area='全部', occasion='不限', strict=True, open_only=False):
    """Filter first, then rank the average fit of every diner in the group."""
    if not diners:
        return []
    normalized = weights.normalized()
    results = []
    for restaurant in restaurants:
        state, label = opening_status(restaurant, at)
        if open_only and state != 'open':
            continue
        if area != '全部' and restaurant['location'] != area:
            continue
        if occasion != '不限' and occasion not in restaurant['occasions']:
            continue
        searchable = ' '.join([restaurant['name'], restaurant['location'], *restaurant['types']])
        if search.strip().casefold() not in searchable.casefold():
            continue
        if strict and any(restaurant['price'] > diner.budget for diner in diners):
            continue
        scores = [individual_scores(restaurant, diner) for diner in diners]
        averaged = [sum(part[index] for part in scores) / len(diners) for index in range(3)]
        weighted = sum(part * weight for part, weight in zip(averaged, normalized))
        results.append({
            **restaurant, 'score': math.floor(100 * weighted + 0.5),
            'status': state, 'status_label': label,
            'reasons': recommendation_reasons(restaurant, diners),
        })
    return sorted(results, key=lambda r: (-r['score'], r['price'], r['id']))
