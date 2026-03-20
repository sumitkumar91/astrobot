from datetime import datetime
from constants import PLANET_NAMES


def _parse_dt(s):
    try:
        return datetime.strptime(s[:19], "%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        return None


def format_dasha(chart_data):
    """
    Format current Vimshottari dasha.
    Shows: current mahadasha, antardasha (if nesting=1 data available), and full mahadasha table.
    Marks the current period with ◀.
    """
    dasha = chart_data.get("chart", {}).get("dasha", {})
    if not dasha:
        return "No dasha data found."

    periods = dasha.get("periods", {})
    now = datetime.utcnow()

    # Find current mahadasha
    current_maha_key = None
    for key, period in periods.items():
        start = _parse_dt(period.get("start"))
        end = _parse_dt(period.get("end"))
        if start and end and start <= now <= end:
            current_maha_key = key
            break

    if not current_maha_key:
        return "Could not determine current dasha period."

    maha = periods[current_maha_key]
    maha_name = PLANET_NAMES.get(current_maha_key, current_maha_key)

    W = 12

    def line(label, value):
        return f"  {label:<{W}} {value}"

    lines = ["**Vimshottari Dasha**", "```",
        "── Current ───────────────────────────────",
        line("Mahadasha", maha_name),
        line("Period", f"{maha.get('start','?')[:10]}  →  {maha.get('end','?')[:10]}"),
    ]

    # Antardasha
    sub_periods = maha.get("periods", {})
    if sub_periods:
        current_antar_key = None
        for key, period in sub_periods.items():
            start = _parse_dt(period.get("start"))
            end = _parse_dt(period.get("end"))
            if start and end and start <= now <= end:
                current_antar_key = key
                break
        if current_antar_key:
            antar = sub_periods[current_antar_key]
            antar_name = PLANET_NAMES.get(current_antar_key, current_antar_key)
            lines += ["", line("Antardasha", antar_name),
                line("Period", f"{antar.get('start','?')[:10]}  →  {antar.get('end','?')[:10]}")]

            # Pratyantardasha
            sub_sub = antar.get("periods", {})
            if sub_sub:
                for key, period in sub_sub.items():
                    start = _parse_dt(period.get("start"))
                    end = _parse_dt(period.get("end"))
                    if start and end and start <= now <= end:
                        pratya_name = PLANET_NAMES.get(key, key)
                        lines += ["", line("Pratyantara", pratya_name),
                            line("Period", f"{period.get('start','?')[:10]}  →  {period.get('end','?')[:10]}")]
                        break

    lines += ["", "── All Mahadashas ────────────────────────"]
    for key, period in periods.items():
        name = PLANET_NAMES.get(key, key)
        marker = " ◀" if key == current_maha_key else ""
        lines.append(f"  {name:<8} {period.get('start','?')[:10]}  →  {period.get('end','?')[:10]}{marker}")

    lines.append("```")
    return "\n".join(lines)
