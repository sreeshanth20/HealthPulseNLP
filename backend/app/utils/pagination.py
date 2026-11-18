"""Request pagination helpers."""

from __future__ import annotations

import fastapi


def pagination_params(
    page: int = fastapi.Query(1, ge=1),
    page_size: int = fastapi.Query(20, ge=1, le=100),
) -> tuple[int, int]:
    return page, page_size
