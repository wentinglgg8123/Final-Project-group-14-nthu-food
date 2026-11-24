"""Evaluate the catalog's recurring opening hours in Taipei local time."""

from datetime import datetime
from functools import lru_cache
import re
import unicodedata
from zoneinfo import ZoneInfo


TAIPEI = ZoneInfo("Asia/Taipei")
_DAY_INDEX = {day: index for index, day in enumerate("一二三四五六日")}
_DAY_INDEX["天"] = 6
_DAY_SELECTOR = re.compile(
    r"平日|假日|週末|週[一二三四五六日天](?:\s*(?:[、,]|至|到|~|-)\s*週?[一二三四五六日天])*"
)
_RANGE = re.compile(r"([0-9]{1,2}):([0-9]{2})\s*[~-]\s*([0-9]{1,2}):([0-9]{2})")
_CLOSED = re.compile(r"^(?:公休|店休|休息|暫停營業|不營業|休業)(?:$|[ 　,;、/。])")
_MINUTES_PER_DAY = 24 * 60

Periods = tuple[tuple[int, int], ...]


def _weekdays(selector: str) -> set[int]:
    if selector == "平日":
        return set(range(5))
    if selector in {"假日", "週末"}:
        return {5, 6}
    days = set()
    for part in re.split(r"[、,]", selector):
        first, *last = re.split(r"\s*(?:至|到|~|-)\s*", part.replace("週", "").strip())
        start = _DAY_INDEX[first]
        if not last:
            days.add(start)
        else:
            length = (_DAY_INDEX[last[0]] - start) % 7 + 1
            days.update((start + offset) % 7 for offset in range(length))
    return days


def _periods(text: str) -> Periods | None:
    text = text.strip(" \t\n,;、/:")
    if _CLOSED.match(text):
        return ()
    periods = []
    for part in re.split(r"[,;、/\n]", text):
        part = part.strip()
        if part in {"24小時", "24小時營業", "全天營業"}:
            periods.append((0, _MINUTES_PER_DAY))
            continue
        if not (match := _RANGE.fullmatch(part)):
            continue
        start_hour, start_minute, end_hour, end_minute = map(int, match.groups())
        if start_hour > 23 or end_hour > 24 or start_minute > 59 or end_minute > 59:
            continue
        if end_hour == 24 and end_minute:
            continue
        start = start_hour * 60 + start_minute
        end = end_hour * 60 + end_minute or _MINUTES_PER_DAY
        if end < start:
            end += _MINUTES_PER_DAY
        periods.append((start, end))
    return tuple(periods) or None


@lru_cache(maxsize=2048)
def _weekly_hours(text: str | None) -> tuple[Periods | None, ...]:
    text = unicodedata.normalize("NFKC", text or "").translate(str.maketrans("—–−", "---"))
    text = re.sub(r"每?(?:星期|禮拜|周|週)", "週", text)
    selectors = list(_DAY_SELECTOR.finditer(text))
    first = selectors[0].start() if selectors else len(text)
    days = [_periods(text[:first])] * 7
    for index, selector in enumerate(selectors):
        end = selectors[index + 1].start() if index + 1 < len(selectors) else len(text)
        # A named day with no usable times (for example, hours to be announced)
        # does not inherit ordinary hours for that day.
        periods = _periods(text[selector.end():end]) or ()
        for day in _weekdays(selector.group()):
            days[day] = periods
    return tuple(days)


def is_open_now(
    opening_hours: str | None,
    now: datetime | None = None,
    *,
    special_opening_hours: str | None = None,
) -> bool:
    """Check the supplied timetable. A naive timestamp denotes Taipei local time."""
    if now is None:
        now = datetime.now(TAIPEI)
    elif now.tzinfo is not None:
        now = now.astimezone(TAIPEI)

    regular = _weekly_hours(opening_hours)
    special = _weekly_hours(special_opening_hours)
    day = now.weekday()
    minute = now.hour * 60 + now.minute
    for weekday, check_time in ((day, minute), ((day - 1) % 7, minute + _MINUTES_PER_DAY)):
        periods = special[weekday] if special[weekday] is not None else regular[weekday]
        if periods and any(start <= check_time < end for start, end in periods):
            return True
    return False
