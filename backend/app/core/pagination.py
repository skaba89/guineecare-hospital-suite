from typing import Optional

from fastapi import Query
from pydantic import BaseModel


class PaginationParams:
    def __init__(
        self,
        page: int = Query(1, ge=1, description="Page number"),
        page_size: int = Query(20, ge=1, le=100, description="Items per page"),
        search: Optional[str] = Query(None, description="Search term"),
    ):
        self.page = page
        self.page_size = page_size
        self.search = search


class PaginatedResponse(BaseModel):
    data: list
    total: int
    page: int
    page_size: int
    total_pages: int


def paginate(query, pagination: PaginationParams):
    total = query.count()
    items = query.offset((pagination.page - 1) * pagination.page_size).limit(pagination.page_size).all()
    total_pages = (total + pagination.page_size - 1) // pagination.page_size if total > 0 else 0
    return {
        "data": items,
        "total": total,
        "page": pagination.page,
        "page_size": pagination.page_size,
        "total_pages": total_pages,
    }
