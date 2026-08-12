from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from easyorg.core.models import MediaFile, MediaType, ScanStats


IMAGE_EXTENSIONS = frozenset(
    {
        ".jpg",
        ".jpeg",
        ".png",
        ".heic",
        ".heif",
        ".webp",
        ".tif",
        ".tiff",
        ".gif",
        ".bmp",
        ".dng",
        ".raw",
        ".cr2",
        ".cr3",
        ".nef",
        ".arw",
        ".orf",
        ".rw2",
    }
)

VIDEO_EXTENSIONS = frozenset(
    {
        ".mp4",
        ".mov",
        ".m4v",
        ".avi",
        ".mkv",
        ".mts",
        ".m2ts",
        ".3gp",
        ".webm",
        ".mpg",
        ".mpeg",
    }
)


@dataclass(frozen=True)
class ScanResult:
    media_files: tuple[MediaFile, ...]
    stats: ScanStats


def scan_media_files(source_directory: Path) -> ScanResult:
    resolved_source = source_directory.resolve()
    media_files: list[MediaFile] = []
    image_count = 0
    video_count = 0
    total_bytes = 0

    for root, dir_names, file_names in os.walk(resolved_source, followlinks=False):
        root_path = Path(root)
        dir_names[:] = [
            directory_name
            for directory_name in dir_names
            if not (root_path / directory_name).is_symlink()
        ]

        for file_name in file_names:
            file_path = root_path / file_name
            if file_path.is_symlink():
                continue

            media_type = classify_media_file(file_path)
            if media_type is None:
                continue

            size_bytes = file_path.stat().st_size
            media_files.append(
                MediaFile(
                    source_path=file_path,
                    media_type=media_type,
                    size_bytes=size_bytes,
                )
            )
            total_bytes += size_bytes
            if media_type is MediaType.IMAGE:
                image_count += 1
            else:
                video_count += 1

    media_files.sort(key=lambda item: str(item.source_path).lower())

    return ScanResult(
        media_files=tuple(media_files),
        stats=ScanStats(
            total_files=len(media_files),
            image_files=image_count,
            video_files=video_count,
            total_bytes=total_bytes,
        ),
    )


def classify_media_file(file_path: Path) -> MediaType | None:
    suffix = file_path.suffix.lower()
    if suffix in IMAGE_EXTENSIONS:
        return MediaType.IMAGE
    if suffix in VIDEO_EXTENSIONS:
        return MediaType.VIDEO
    return None
