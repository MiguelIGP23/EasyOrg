from __future__ import annotations


_SIZE_UNITS = ("B", "KB", "MB", "GB", "TB")


def format_size(size_bytes: int) -> str:
    if size_bytes < 0:
        raise ValueError("size_bytes cannot be negative")

    value = float(size_bytes)
    unit_index = 0

    while value >= 1024 and unit_index < len(_SIZE_UNITS) - 1:
        value /= 1024
        unit_index += 1

    if unit_index == 0:
        return f"{int(value)} {_SIZE_UNITS[unit_index]}"

    return f"{value:.1f} {_SIZE_UNITS[unit_index]}"
