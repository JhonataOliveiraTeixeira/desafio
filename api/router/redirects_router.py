
from fastapi import APIRouter
from fastapi.responses import RedirectResponse


router_redirect = APIRouter()

@router_redirect.get('/', include_in_schema=False)
def redirect_root():
    return RedirectResponse(url='/docs')