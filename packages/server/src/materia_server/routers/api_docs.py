from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

router = APIRouter()


@router.get("/api/docs", response_class=HTMLResponse, include_in_schema=False)
async def rapidoc(request: Request):
    return f"""
        <!doctype html>
        <html>
            <head>
                <meta charset="utf-8">
                <link href='http://fonts.googleapis.com/css?family=Roboto' rel='stylesheet' type='text/css'>
                <script 
                    type="module" 
                    src="https://unpkg.com/rapidoc/dist/rapidoc-min.js"
                ></script>
            </head>
            <body>
                <rapi-doc 
                    spec-url="{request.app.openapi_url}"
                    theme = "dark"
                    show-header = "false"
                    show-info = "true"
                    allow-authentication = "true"
                    allow-server-selection = "true"
                    allow-api-list-style-selection = "true"
                    theme = "dark"
                    render-style = "focused"
                    bg-color="#1e2129"
                    primary-color="#a47bea"
                    regular-font="Roboto"
                    mono-font="Roboto Mono"
                    show-method-in-nav-bar="as-colored-text">
                    <img slot="logo" style="display: none"/>
                </rapi-doc>
            </body> 
        </html>
    """
