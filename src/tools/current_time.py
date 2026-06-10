import calendar
from datetime import datetime
from zoneinfo import ZoneInfo


def get_current_time() -> str:
    """Return current datetime as an unambiguous human-readable string with locale, timezone, and a calendar for the current month."""
    tz = ZoneInfo("Asia/Jakarta")
    now = datetime.now(tz)
    weekday = now.strftime("%A")
    month = now.strftime("%B")
    day = now.day
    year = now.year
    hour = now.hour
    minute = now.minute
    second = now.second
    tz_name = now.strftime("%Z")
    tz_offset = now.strftime("%z")

    month_calendar = calendar.monthcalendar(year, now.month)
    cal_lines = [f"  Calendar for {month} {year}"]
    cal_lines.append("  Mo Tu We Th Fr Sa Su")
    for week in month_calendar:
        row = ""
        for day_num in week:
            if day_num == 0:
                row += "   "
            elif day_num == day:
                row += f"[{day_num:2d}] "
            else:
                row += f" {day_num:2d} "
        cal_lines.append(f"  {row.strip()}")

    cal_block = "\n".join(cal_lines)

    return (
        f"The current date and time is {weekday}, {month} {day}, {year} "
        f"at {hour:02d}:{minute:02d}:{second:02d} "
        f"({tz_name}, UTC{tz_offset}). "
        f"Locale: C.UTF-8 (English, United States).\n\n"
        f"{cal_block}"
    )
