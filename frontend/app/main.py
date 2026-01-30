from fastapi import FastAPI, Request, Response, Cookie, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import httpx
from typing import Optional, List
import logging

# Get the base directory
BASE_DIR = Path(__file__).parent.parent

app = FastAPI(title="Admin Management Frontend")

# Mount static files
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

# Templates
templates = Jinja2Templates(directory=BASE_DIR / "app/templates")

# API server URL
API_BASE_URL = "http://127.0.0.1:8000"

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


async def verify_token(access_token: str) -> bool:
    """Verify if token is valid by calling a protected endpoint"""
    if not access_token:
        return False

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE_URL}/admins/",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            return response.status_code == 200
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        return False


async def get_current_user(request: Request) -> Optional[dict]:
    """Get current user from token"""
    access_token = request.cookies.get("access_token")
    if not access_token:
        return None

    # Verify token is still valid
    if not await verify_token(access_token):
        return None

    # Try to get user info
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE_URL}/admins/",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            if response.status_code == 200:
                admins = response.json()
                if admins:
                    return admins[0]
    except Exception as e:
        logger.error(f"Get current user error: {e}")

    return None


async def make_authenticated_request(
        request: Request,
        method: str,
        endpoint: str,
        **kwargs
) -> Optional[httpx.Response]:
    """Make authenticated request to API server"""
    access_token = request.cookies.get("access_token")
    if not access_token:
        return None

    try:
        async with httpx.AsyncClient() as client:
            headers = {
                "Authorization": f"Bearer {access_token}",
                **kwargs.get("headers", {})
            }

            if "headers" in kwargs:
                del kwargs["headers"]

            response = await client.request(
                method=method,
                url=f"{API_BASE_URL}{endpoint}",
                headers=headers,
                **kwargs
            )
            return response
    except Exception as e:
        logger.error(f"API request error: {e}")
        return None


# Home/Dashboard
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    user = await get_current_user(request)
    if not user:
        return RedirectResponse(url="/login")

    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "user": user}
    )


# Login page
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, error: Optional[str] = None):
    user = await get_current_user(request)
    if user:
        return RedirectResponse(url="/")

    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "error": error
        }
    )


# Handle login
@app.post("/login")
async def login(request: Request, response: Response):
    form_data = await request.form()
    username = form_data.get("username")
    password = form_data.get("password")

    if not username or not password:
        return RedirectResponse(url="/login?error=Missing+credentials", status_code=302)

    # Call API server login endpoint
    try:
        async with httpx.AsyncClient() as client:
            login_response = await client.post(
                f"{API_BASE_URL}/token",
                data={
                    "username": username,
                    "password": password,
                    "grant_type": "password",
                    "scope": ""
                }
            )

            if login_response.status_code == 200:
                tokens = login_response.json()

                # Set tokens as cookies
                response = RedirectResponse(url="/", status_code=302)
                response.set_cookie(
                    key="access_token",
                    value=tokens["access_token"],
                    httponly=True,
                    max_age=1800  # 30 minutes
                )
                response.set_cookie(
                    key="refresh_token",
                    value=tokens["refresh_token"],
                    httponly=True,
                    max_age=604800  # 7 days
                )
                return response
            else:
                error_detail = "Invalid credentials"
                try:
                    error_data = login_response.json()
                    error_detail = error_data.get("detail", "Invalid credentials")
                except:
                    pass
                return RedirectResponse(url=f"/login?error={error_detail.replace(' ', '+')}", status_code=302)
    except Exception as e:
        logger.error(f"Login error: {e}")
        return RedirectResponse(url=f"/login?error=Connection+error", status_code=302)


# Logout
@app.get("/logout")
async def logout(request: Request, response: Response):
    refresh_token = request.cookies.get("refresh_token")

    # Call logout endpoint if refresh token exists
    if refresh_token:
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{API_BASE_URL}/logout",
                    json={"refresh_token": refresh_token}
                )
        except Exception as e:
            logger.error(f"Logout error: {e}")

    # Clear cookies and redirect to login
    response = RedirectResponse(url="/login")
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return response


# Admin pages
@app.get("/admins", response_class=HTMLResponse)
async def admins_list(request: Request):
    user = await get_current_user(request)
    if not user:
        return RedirectResponse(url="/login")

    # Fetch admins from API server
    response = await make_authenticated_request(request, "GET", "/admins/")
    admins = []

    if response and response.status_code == 200:
        admins = response.json()

    return templates.TemplateResponse(
        "admins/list.html",
        {"request": request, "user": user, "admins": admins}
    )


@app.get("/admins/create", response_class=HTMLResponse)
async def create_admin_page(request: Request):
    user = await get_current_user(request)
    if not user:
        return RedirectResponse(url="/login")

    return templates.TemplateResponse(
        "admins/create.html",
        {"request": request, "user": user}
    )


# Handle admin creation
@app.post("/admins/create")
async def create_admin(request: Request, response: Response):
    user = await get_current_user(request)
    if not user:
        return RedirectResponse(url="/login")

    form_data = await request.form()

    # Prepare admin data
    admin_data = {
        "name": form_data.get("name"),
        "email": form_data.get("email"),
        "password": form_data.get("password"),
        "enabled": form_data.get("enabled") == "on",
    }

    # Handle roles (if provided)
    roles = form_data.getlist("roles")
    if roles:
        admin_data["roles"] = [int(r) for r in roles]

    # Send to API server
    api_response = await make_authenticated_request(
        request, "POST", "/admins/", json=admin_data
    )

    if api_response and api_response.status_code == 200:
        return RedirectResponse(url="/admins?success=Admin+created", status_code=302)
    else:
        error_msg = "Failed to create admin"
        if api_response:
            try:
                error_data = api_response.json()
                error_msg = error_data.get("detail", error_msg)
            except:
                pass
        return RedirectResponse(url=f"/admins/create?error={error_msg.replace(' ', '+')}", status_code=302)


@app.get("/admins/edit/{admin_id}", response_class=HTMLResponse)
async def edit_admin_page(request: Request, admin_id: int):
    user = await get_current_user(request)
    if not user:
        return RedirectResponse(url="/login")

    # Fetch admin data
    api_response = await make_authenticated_request(request, "GET", f"/admins/{admin_id}")
    admin = None

    if api_response and api_response.status_code == 200:
        admin = api_response.json()

    return templates.TemplateResponse(
        "admins/edit.html",
        {"request": request, "user": user, "admin": admin, "admin_id": admin_id}
    )


# Handle admin update
@app.post("/admins/edit/{admin_id}")
async def update_admin(request: Request, admin_id: int):
    user = await get_current_user(request)
    if not user:
        return RedirectResponse(url="/login")

    form_data = await request.form()

    # Prepare update data (only include fields with values)
    admin_data = {}

    email = form_data.get("email")
    password = form_data.get("password")
    enabled = form_data.get("enabled")

    if email:
        admin_data["email"] = email
    if password:
        admin_data["password"] = password
    if enabled in ["true", "false"]:
        admin_data["enabled"] = enabled == "true"

    # Send to API server
    api_response = await make_authenticated_request(
        request, "PUT", f"/admins/{admin_id}", json=admin_data
    )

    if api_response and api_response.status_code == 200:
        return RedirectResponse(url="/admins?success=Admin+updated", status_code=302)
    else:
        error_msg = "Failed to update admin"
        return RedirectResponse(url=f"/admins/edit/{admin_id}?error={error_msg.replace(' ', '+')}", status_code=302)


# Client pages - SERVER-SIDE RENDERING
@app.get("/clients", response_class=HTMLResponse)
async def clients_list(
        request: Request,
        error: Optional[str] = None,
        success: Optional[str] = None
):
    user = await get_current_user(request)
    if not user:
        return RedirectResponse(url="/login")

    # Fetch clients from API server
    response = await make_authenticated_request(request, "GET", "/clients/")
    clients = []

    if response:
        if response.status_code == 200:
            clients = response.json()
        else:
            error = f"Failed to load clients: {response.status_code}"

    return templates.TemplateResponse(
        "clients/list.html",
        {
            "request": request,
            "user": user,
            "clients": clients,
            "error": error,
            "success": success
        }
    )


@app.get("/clients/create", response_class=HTMLResponse)
async def create_client_page(request: Request, error: Optional[str] = None):
    user = await get_current_user(request)
    if not user:
        return RedirectResponse(url="/login")

    return templates.TemplateResponse(
        "clients/create.html",
        {"request": request, "user": user, "error": error}
    )


# Handle client creation
@app.post("/clients/create")
async def create_client(request: Request, response: Response):
    user = await get_current_user(request)
    if not user:
        return RedirectResponse(url="/login")

    form_data = await request.form()

    # Prepare client data
    client_data = {
        "name": form_data.get("name"),
        "email": form_data.get("email"),
        "address": form_data.get("address") or None,
        "phones": form_data.get("phones") or None,
        "enabled": form_data.get("enabled") == "on",
    }

    # Handle admin_id
    admin_id = form_data.get("admin_id")
    if admin_id:
        client_data["admin_id"] = int(admin_id)

    # Send to API server
    api_response = await make_authenticated_request(
        request, "POST", "/clients/", json=client_data
    )

    if api_response and api_response.status_code == 200:
        return RedirectResponse(url="/clients?success=Client+created", status_code=302)
    else:
        error_msg = "Failed to create client"
        if api_response:
            try:
                error_data = api_response.json()
                error_msg = error_data.get("detail", error_msg)
            except:
                pass
        return RedirectResponse(url=f"/clients/create?error={error_msg.replace(' ', '+')}", status_code=302)


@app.get("/clients/edit/{client_id}", response_class=HTMLResponse)
async def edit_client_page(request: Request, client_id: int, error: Optional[str] = None):
    user = await get_current_user(request)
    if not user:
        return RedirectResponse(url="/login")

    # Fetch client data
    api_response = await make_authenticated_request(request, "GET", f"/clients/{client_id}")
    client = None

    if api_response and api_response.status_code == 200:
        client = api_response.json()

    return templates.TemplateResponse(
        "clients/edit.html",
        {
            "request": request,
            "user": user,
            "client": client,
            "client_id": client_id,
            "error": error
        }
    )


# Handle client update
@app.post("/clients/edit/{client_id}")
async def update_client(request: Request, client_id: int):
    user = await get_current_user(request)
    if not user:
        return RedirectResponse(url="/login")

    form_data = await request.form()

    # Prepare update data
    client_data = {}

    fields = ["name", "email", "address", "phones"]
    for field in fields:
        value = form_data.get(field)
        if value is not None:
            client_data[field] = value if value != "" else None

    # Handle enabled
    enabled = form_data.get("enabled")
    if enabled in ["true", "false"]:
        client_data["enabled"] = enabled == "true"

    # Handle admin_id
    admin_id = form_data.get("admin_id")
    if admin_id is not None:
        client_data["admin_id"] = int(admin_id) if admin_id != "" else None

    # Send to API server
    api_response = await make_authenticated_request(
        request, "PUT", f"/clients/{client_id}", json=client_data
    )

    if api_response and api_response.status_code == 200:
        return RedirectResponse(url="/clients?success=Client+updated", status_code=302)
    else:
        error_msg = "Failed to update client"
        if api_response:
            try:
                error_data = api_response.json()
                error_msg = error_data.get("detail", error_msg)
            except:
                pass
        return RedirectResponse(url=f"/clients/edit/{client_id}?error={error_msg.replace(' ', '+')}", status_code=302)


# Handle client deletion
@app.post("/clients/delete/{client_id}")
async def delete_client(request: Request, client_id: int):
    user = await get_current_user(request)
    if not user:
        return RedirectResponse(url="/login")

    # Send delete request to API server
    api_response = await make_authenticated_request(
        request, "DELETE", f"/clients/{client_id}"
    )

    if api_response and api_response.status_code == 200:
        return RedirectResponse(url="/clients?success=Client+deleted", status_code=302)
    else:
        error_msg = "Failed to delete client"
        return RedirectResponse(url=f"/clients?error={error_msg.replace(' ', '+')}", status_code=302)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=3000, reload=True)
