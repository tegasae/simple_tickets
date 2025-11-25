import time

from fastapi import FastAPI, Request, Depends, HTTPException, status, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import httpx
from typing import Optional, Any

app = FastAPI(title="Admin Management Web App")

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Configuration
API_BASE_URL = "http://127.0.0.1:8000"

# Store tokens in memory (in production, use secure sessions)
user_sessions = {}


async def require_auth(request: Request) -> dict:
    """Dependency that automatically redirects to login if not authenticated"""
    token = request.cookies.get("access_token")
    if not token or token not in user_sessions:
        # Redirect to login if not authenticated
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": "/login"}
        )
    return user_sessions[token]


async def get_current_user_required(request: Request) -> dict:
    """Dependency that returns the current user or redirects to login"""
    token = request.cookies.get("access_token")

    if not token or token not in user_sessions:
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": "/login"}
        )

    # Check if token needs refresh (you might want to decode and check expiration)
    # For now, we'll assume all tokens might need refresh and try to refresh if API calls fail
    return user_sessions[token]


async def refresh_access_token(refresh_token: str) -> Optional[dict]:
    """Refresh the access token using refresh token"""
    try:
        response = await api_request(
            "POST",
            "/refresh",
            json_data={"refresh_token": refresh_token}
        )

        if response.status_code == 200:
            token_data = response.json()
            return token_data
        else:
            return None
    except Exception:
        return None


async def api_request_with_retry(
        method: str,
        endpoint: str,
        token: Optional[str] = None,
        form_data: Optional[dict] = None,
        json_data: Optional[Any] = None,
        params: Optional[dict] = None,
        headers_data: Optional[dict] = None,
        max_retries: int = 1
):
    """Enhanced API request that automatically refreshes token if expired"""

    # First attempt
    response = await api_request(method, endpoint, token, form_data, json_data, params, headers_data)

    # If unauthorized and we have retries left, try to refresh token
    if response.status_code == 401 and max_retries > 0 and token:
        # Find the user session
        user_session = None
        for session_token, session_data in user_sessions.items():
            if session_token == token:
                user_session = session_data
                break

        if user_session and user_session.get("refresh_token"):
            # Try to refresh the token
            new_tokens = await refresh_access_token(user_session["refresh_token"])

            if new_tokens:
                # Update user session with new tokens
                new_access_token = new_tokens["access_token"]
                new_refresh_token = new_tokens.get("refresh_token", user_session["refresh_token"])

                # Update session
                user_sessions[new_access_token] = {
                    **user_session,
                    "access_token": new_access_token,
                    "refresh_token": new_refresh_token
                }

                # Remove old token
                if token in user_sessions:
                    del user_sessions[token]

                # Retry the request with new token
                return await api_request(
                    method, endpoint, new_access_token, form_data, json_data, params, headers_data
                )

    return response


async def api_request(method: str, endpoint: str, token: Optional[str] = None,
                      form_data: Optional[dict] = None, json_data: Optional[Any] = None, params: Optional[dict] = None,
                      headers_data: Optional[dict] = None):
    """Helper function to make API requests to the backend"""
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if headers_data:
        headers.update(headers_data)

    arguments = {'headers': headers, 'params': params}

    if json_data:
        arguments['json'] = json_data
    if form_data:
        arguments['data'] = form_data
    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(method, f"{API_BASE_URL}{endpoint}", **arguments)
            return response
        except httpx.ConnectError:
            raise HTTPException(status_code=500, detail="Cannot connect to API server")


# Routes
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Redirect to login page"""
    return RedirectResponse(url="/login")


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Show login form"""
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    """Handle login form submission"""
    form_data = {
        "username": username,
        "password": password,
        "grant_type": "password"
    }

    response = await api_request("POST", "/token", form_data=form_data)

    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data["access_token"]
        refresh_token = token_data.get("refresh_token")

        # Store user session with both tokens
        user_sessions[access_token] = {
            "username": username,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "login_time": time.time()  # Track when user logged in
        }

        # Redirect to dashboard with token in cookie
        redirect_response = RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
        redirect_response.set_cookie(key="access_token", value=access_token, httponly=True)

        # Optionally store refresh token in a separate secure cookie
        if refresh_token:
            redirect_response.set_cookie(
                key="refresh_token",
                value=refresh_token,
                httponly=True,
                secure=True,  # Only send over HTTPS
                max_age=30 * 24 * 60 * 60  # 30 days
            )

        return redirect_response
    else:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Invalid username or password"
        })


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, current_user: dict = Depends(get_current_user_required)):
    """Dashboard page - shows admin list"""

    # Get admins list from API
    response = await api_request("GET", "/admins/", current_user["access_token"])

    if response.status_code == 200:
        admins = response.json()
    else:
        admins = []

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "current_user": current_user,
        "admins": admins
    })


@app.get("/admins", response_class=HTMLResponse)
async def admins_list(request: Request, current_user: dict = Depends(get_current_user_required)):
    """Admins management page"""

    # Get admins list from API
    response = await api_request("GET", "/admins/", current_user["access_token"])

    if response.status_code == 200:
        admins = response.json()
    else:
        admins = []

    return templates.TemplateResponse("admins_list.html", {
        "request": request,
        "admins": admins,
        "current_user": current_user
    })


@app.get("/admins/create", response_class=HTMLResponse)
async def create_admin_page(request: Request, current_user: dict = Depends(get_current_user_required)):
    """Show create admin form"""

    return templates.TemplateResponse("create_admin.html", {"request": request})


@app.post("/admins/create")
async def create_admin(
        request: Request,
        name: str = Form(...),
        email: str = Form(...),
        password: str = Form(...),
        enabled: bool = Form(True),
        current_user: dict = Depends(get_current_user_required)
):
    """Handle create admin form submission"""

    admin_data = {
        "name": name,
        "email": email,
        "password": password,
        "enabled": enabled
    }

    response = await api_request("POST", "/admins/", current_user["access_token"], json_data=admin_data,
                                 headers_data={'Content-Type': 'application/json'})

    if response.status_code == 201:
        return RedirectResponse(url="/admins", status_code=status.HTTP_302_FOUND)
    else:
        return templates.TemplateResponse("create_admin.html", {
            "request": request,
            "error": f"Failed to create admin: {response.text}"
        })


@app.get("/admins/{admin_id}/edit", response_class=HTMLResponse)
async def edit_admin_page(request: Request, admin_id: int, current_user: dict = Depends(get_current_user_required)):
    """Show edit admin form"""

    # Get admin data from API
    response = await api_request("GET", f"/admins/{admin_id}", current_user["access_token"])

    if response.status_code == 200:
        admin = response.json()
        return templates.TemplateResponse("edit_admin.html", {
            "request": request,
            "admin": admin
        })
    else:
        return RedirectResponse(url="/admins")


@app.post("/admins/{admin_id}/edit")
async def edit_admin(
        request: Request,
        admin_id: int,
        email: str = Form(None),
        password: str = Form(None),
        enabled: bool = Form(None),
        current_user: dict = Depends(get_current_user_required)
):
    """Handle edit admin form submission"""

    admin_data = {}
    if email: admin_data["email"] = email
    if password: admin_data["password"] = password
    if enabled is not None:
        admin_data["enabled"] = enabled
    else:
        admin_data["enabled"] = False
    # json_data=json.dumps(admin_data)
    response = await api_request("PUT", f"/admins/{admin_id}", current_user["access_token"],
                                 json_data=admin_data, headers_data={'Content-Type': 'application/json'})

    if response.status_code == 200:
        return RedirectResponse(url="/admins", status_code=status.HTTP_302_FOUND)
    else:
        # Get admin data again for the form
        admin_response = await api_request("GET", f"/admins/{admin_id}", current_user["access_token"])
        admin = admin_response.json() if admin_response.status_code == 200 else {}

        return templates.TemplateResponse("edit_admin.html", {
            "request": request,
            "admin": admin,
            "error": f"Failed to update admin: {response.text}"
        })


@app.post("/admins/{admin_id}/delete")
async def delete_admin(admin_id: int, current_user: dict = Depends(get_current_user_required)):
    """Handle delete admin"""

    response = await api_request("DELETE", f"/admins/{admin_id}", current_user["access_token"])

    return RedirectResponse(url="/admins", status_code=status.HTTP_302_FOUND)


@app.post("/admins/{admin_id}/toggle-status")
async def toggle_admin_status(admin_id: int, current_user: dict = Depends(get_current_user_required)):
    """Toggle admin status"""
    if not current_user:
        return RedirectResponse(url="/login")

    response = await api_request("POST", f"/admins/{admin_id}/toggle-status", current_user["access_token"])

    return RedirectResponse(url="/admins", status_code=status.HTTP_302_FOUND)


@app.post("/logout")
async def logout(request: Request):
    """Handle logout - revoke both tokens"""
    access_token = request.cookies.get("access_token")
    refresh_token = request.cookies.get("refresh_token")

    if access_token and access_token in user_sessions:
        # Call API logout with refresh token if available
        session_refresh_token = user_sessions[access_token].get("refresh_token")
        if session_refresh_token:
            await api_request("POST", "/logout", json_data={"refresh_token": session_refresh_token})

        # Remove session
        del user_sessions[access_token]

    # Also try to revoke the cookie refresh token
    if refresh_token:
        await api_request("POST", "/logout", json_data={"refresh_token": refresh_token})

    response = RedirectResponse(url="/login")
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return response


async def validate_token(token: str) -> bool:
    """Validate if the token is still valid"""
    try:
        response = await api_request("GET", "/users/me", token)
        return response.status_code == 200
    except Exception:
        return False


@app.get("/validate-session")
async def validate_session(request: Request):
    """Endpoint to validate and potentially refresh session"""
    access_token = request.cookies.get("access_token")
    refresh_token = request.cookies.get("refresh_token")

    if access_token and access_token in user_sessions:
        # Check if token is still valid
        is_valid = await validate_token(access_token)

        if is_valid:
            return {"status": "valid"}
        elif refresh_token:
            # Try to refresh
            new_tokens = await refresh_access_token(refresh_token)
            if new_tokens:
                return {"status": "refreshed", "new_token": new_tokens["access_token"]}

    return {"status": "invalid"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8001)
