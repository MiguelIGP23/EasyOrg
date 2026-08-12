from __future__ import annotations


MONTH_NAMES = {
    1: "Enero",
    2: "Febrero",
    3: "Marzo",
    4: "Abril",
    5: "Mayo",
    6: "Junio",
    7: "Julio",
    8: "Agosto",
    9: "Septiembre",
    10: "Octubre",
    11: "Noviembre",
    12: "Diciembre",
}


def week_of_month(day: int) -> int:
    if day < 1 or day > 31:
        raise ValueError("day must be between 1 and 31")

    return ((day - 1) // 7) + 1


def month_folder_name(month: int) -> str:
    try:
        month_name = MONTH_NAMES[month]
    except KeyError as exc:
        raise ValueError("month must be between 1 and 12") from exc

    return f"{month:02d} - {month_name}"

