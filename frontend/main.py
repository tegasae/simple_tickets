from fastapi import FastAPI, Request, Depends, HTTPException, status, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import httpx
from typing import Optional

app = FastAPI(title="Admin Management Web App")

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Configuration
API_BASE_URL = "http://127.0.0.1:8000"

# Store tokens in memory (in production, use secure sessions)
user_sessions = {}


async def get_current_user(request: Request):
    """Dependency to get current user from session"""
    token = request.cookies.get("access_token")
    if not token or token not in user_sessions:
        return None
    return user_sessions[token]


async def api_request(method: str, endpoint: str, token: Optional[str] = None,
                      data: Optional[dict] = None, params: Optional[dict] = None):
    """Helper function to make API requests to the backend"""
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(
                method=method,
                url=f"{API_BASE_URL}{endpoint}",
                headers=headers,
                data=data,
                params=params
            )
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
    # Authenticate with the API server
    form_data = {
        "username": username,
        "password": password,
        "grant_type": "password"
    }




    response = await api_request("POST", "/token", data=form_data)
    #response = await api_request(
    #    method="POST",
    #
    #    data=form_data,  # This automatically sets Content-Type to application/x-www-form-urlencoded
    #)
    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data["access_token"]
        refresh_token = token_data.get("refresh_token")

        # Store user session
        user_sessions[access_token] = {
            "username": username,
            "access_token": access_token,
            "refresh_token": refresh_token
        }

        # Redirect to dashboard with token in cookie
        redirect_response = RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
        redirect_response.set_cookie(key="access_token", value=access_token, httponly=True)
        return redirect_response
    else:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Invalid username or password"
        })


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, current_user: dict = Depends(get_current_user)):
    """Dashboard page - shows admin list"""
    if not current_user:
        return RedirectResponse(url="/login")

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
async def admins_list(request: Request, current_user: dict = Depends(get_current_user)):
    """Admins management page"""
    if not current_user:
        return RedirectResponse(url="/login")

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
async def create_admin_page(request: Request, current_user: dict = Depends(get_current_user)):
    """Show create admin form"""
    if not current_user:
        return RedirectResponse(url="/login")

    return templates.TemplateResponse("create_admin.html", {"request": request})


@app.post("/admins/create")
async def create_admin(
        request: Request,
        name: str = Form(...),
        email: str = Form(...),
        password: str = Form(...),
        enabled: bool = Form(True),
        current_user: dict = Depends(get_current_user)
):
    """Handle create admin form submission"""
    if not current_user:
        return RedirectResponse(url="/login")

    admin_data = {
        "name": name,
        "email": email,
        "password": password,
        "enabled": enabled
    }

    response = await api_request("POST", "/admins/", current_user["access_token"], admin_data)

    if response.status_code == 201:
        return RedirectResponse(url="/admins", status_code=status.HTTP_302_FOUND)
    else:
        return templates.TemplateResponse("create_admin.html", {
            "request": request,
            "error": f"Failed to create admin: {response.text}"
        })


@app.get("/admins/{admin_id}/edit", response_class=HTMLResponse)
async def edit_admin_page(request: Request, admin_id: int, current_user: dict = Depends(get_current_user)):
    """Show edit admin form"""
    if not current_user:
        return RedirectResponse(url="/login")

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
        current_user: dict = Depends(get_current_user)
):
    """Handle edit admin form submission"""
    if not current_user:
        return RedirectResponse(url="/login")

    admin_data = {}
    if email: admin_data["email"] = email
    if password: admin_data["password"] = password
    if enabled is not None: admin_data["enabled"] = enabled

    response = await api_request("PUT", f"/admins/{admin_id}", current_user["access_token"], admin_data)

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
async def delete_admin(admin_id: int, current_user: dict = Depends(get_current_user)):
    """Handle delete admin"""
    if not current_user:
        return RedirectResponse(url="/login")

    response = await api_request("DELETE", f"/admins/{admin_id}", current_user["access_token"])

    return RedirectResponse(url="/admins", status_code=status.HTTP_302_FOUND)


@app.post("/admins/{admin_id}/toggle-status")
async def toggle_admin_status(admin_id: int, current_user: dict = Depends(get_current_user)):
    """Toggle admin status"""
    if not current_user:
        return RedirectResponse(url="/login")

    response = await api_request("POST", f"/admins/{admin_id}/toggle-status", current_user["access_token"])

    return RedirectResponse(url="/admins", status_code=status.HTTP_302_FOUND)


@app.post("/logout")
async def logout(request: Request):
    """Handle logout"""
    token = request.cookies.get("access_token")
    if token and token in user_sessions:
        # Call API logout if needed
        refresh_token = user_sessions[token].get("refresh_token")
        if refresh_token:
            await api_request("POST", "/logout", data={"refresh_token": refresh_token})

        # Remove session
        del user_sessions[token]

    response = RedirectResponse(url="/login")
    response.delete_cookie("access_token")
    return response


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8001)