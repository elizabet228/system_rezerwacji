import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from jose import jwt, JWTError

app = FastAPI(title="Roomly Booking Service")

current_dir = os.path.dirname(os.path.realpath(__file__))

templates_path = os.path.join(current_dir, "templates")

templates = Jinja2Templates(directory=templates_path)

SECRET_KEY = "69b167520e5e0199799f9116e788e0e378c858593a2e3794348507204f11467e"
ALGORITHM = "HS256"

@app.get("/rooms", response_class=HTMLResponse)
async def list_rooms(request: Request):
    token = request.cookies.get("access_token")
    
    if not token:
        raise HTTPException(status_code=401, detail="Brak tokena access_token w ciasteczkach. Zaloguj się ponownie.")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email = payload.get("sub")
        
        if user_email is None:
            raise HTTPException(status_code=401, detail="Token nie zawiera adresu email.")

        rooms = [
            {"id": 1, "name": "Pokój Standard (Fioletowy)", "price": 150},
            {"id": 2, "name": "Apartament Deluxe", "price": 350},
            {"id": 3, "name": "Studio z widokiem", "price": 250}
        ]
        
        return templates.TemplateResponse("rooms.html", {
            "request": request, 
            "user": user_email, 
            "rooms": rooms
        })
        
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Błąd weryfikacji tokena: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Wystąpił nieoczekiwany błąd: {str(e)}")