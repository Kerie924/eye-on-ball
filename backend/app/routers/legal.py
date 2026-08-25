from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from app.legal_pages import privacy_html, terms_html

router = APIRouter(prefix="/legal", tags=["legal"])


@router.get("/privacy", response_class=HTMLResponse, include_in_schema=False)
def privacy_policy():
    return privacy_html()


@router.get("/terms", response_class=HTMLResponse, include_in_schema=False)
def terms_of_use():
    return terms_html()
