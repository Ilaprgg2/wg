from fastapi import FastAPI, Header, HTTPException
from fastapi.routing import APIRoute
from typing import Callable, Optional
from pydantic import BaseModel
import mainapp
from fastapi.responses import JSONResponse
import database
from dotenv import load_dotenv
import os
# Load the .env file
load_dotenv()

VALID_API_KEY = os.getenv('API_KEY')
INTERFACE = "wgg"

app = FastAPI()



async def verify_api_key(x_api_key: Optional[str] = Header(None)):
    if x_api_key is None:
        raise HTTPException(status_code=400, detail="API Key is missing")
    if x_api_key != VALID_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return x_api_key

class VerifyAPIKeyRoute(APIRoute):
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request):
            if request.method == "POST":
                await verify_api_key(request.headers.get("X-API-Key"))
            return await original_route_handler(request)

        return custom_route_handler

app.router.route_class = VerifyAPIKeyRoute

# Define a Pydantic model for the request body
class UserCreate(BaseModel):
    name: str
    date: int
    usage: float
    interface: str

# Add user
@app.post("/api/create_user")
async def main(user: UserCreate):
    # do some stuff
    private_key, allowed_ips = mainapp.add_wg_user(user.name, user.date, user.usage, user.interface)
    if private_key:
        return JSONResponse(content={"private_key": private_key, "allowed_ips": allowed_ips }, status_code=200)
    else:
        return JSONResponse(content={"message": "Failed to create user"}, status_code=500)
    


# Define a Pydantic model for the request body
class UserRemove(BaseModel):
    name: str
    interface: str

# Remove user
@app.post("/api/remove_user")
async def remove_user(user: UserRemove):
    try:
        result = mainapp.remove_wg_user(user.name, user.interface)
        # Consider any non-False result as success
        if result is not False:
            return JSONResponse(content={"message": "User removed successfully", "details": str(result)}, status_code=200)
        else:
            return JSONResponse(content={"message": "Failed to remove user", "error": "Unknown error"}, status_code=400)
    except Exception as e:
        return JSONResponse(content={"message": "An error occurred", "error": str(e)}, status_code=500)



# Define a Pydantic model for the request body
class handshake(BaseModel):
    interface: str
    public_key: int

# Latest handshake
@app.post("/api/handshake")
async def main(user: handshake):
    handshake = mainapp.get_latest_handshake(user.interface, user.public_key)
    if handshake:
        return JSONResponse(content={"message": handshake}, status_code=200)
    else:
        return JSONResponse(content={"message": "error getting handshake time"}, status_code=500)
    

# Define a Pydantic model for the request body
class userinfo(BaseModel):
    name: str

# get user info
@app.post("/api/userinfo")
async def main(user: userinfo):
    _ ,name ,private_key , public_key , allowed_ips ,date ,usage, used, last_used ,status,_,_ = database.get_user_by_name(user.name)
    if name:
        return JSONResponse(content={"name": name, "private_key": private_key, "public_key": public_key, "allowed_ips": allowed_ips, "date": date, "usage": usage, "used": used, "status": status}, status_code=200)
    else:
        return JSONResponse(content={"message": "error, user not found"}, status_code=500)



# Define a Pydantic model for the request body
class wginterface(BaseModel):
    name: str

# check if wireguard interface id up or down
@app.post("/api/interface_status")
async def main(user: wginterface):
    if mainapp.check_wg_interface(user.name):
        return JSONResponse(content={"status": "up"}, status_code=200)
    else:
        return JSONResponse(content={"status": "down"}, status_code=202)
    


# Define a Pydantic model for the request body
class interfacekey(BaseModel):
    name: str

# check if wireguard interface id up or down
@app.post("/api/interface_pubkey")
async def main(user: interfacekey):
    public_key = mainapp.get_wireguard_public_key(user.name)
    if public_key:
        return JSONResponse(content={"public_key": public_key}, status_code=200)
    elif public_key == "down":
        return JSONResponse(content={"status": "Error"}, status_code=202)
    


# Define a Pydantic model for the request body
class change(BaseModel):
    name: str
    traffic: int
    date: int

# change traffic and or date
@app.post("/api/change")
async def main(user: change):
    if user.date == 0 and user.traffic != 0:
        if database.change_usage(user.name, user.traffic):
            mainapp.enable_wg_user(user.name, INTERFACE)
            return JSONResponse(content={"message":"success"}, status_code=200)
        else:
            return JSONResponse(content={"message":"error setting traffic"}, status_code=202)

    if user.date != 0 and user.traffic == 0:
        if database.change_date(user.name, user.date):
            mainapp.enable_wg_user(user.name, INTERFACE)
            return JSONResponse(content={"message":"success"}, status_code=200)
        else:
            return JSONResponse(content={"message":"error setting date"}, status_code=202)
    
    else:
        if database.change_usage(user.name, user.traffic) and database.change_date(user.name, user.date):
            mainapp.enable_wg_user(user.name, INTERFACE)
            return JSONResponse(content={"message":"success"}, status_code=200)
        else:
            return JSONResponse(content={"message":"error setting date and traffic"}, status_code=202)
