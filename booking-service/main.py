import os
from fastapi import FastAPI, Request, HTTPException, Depends, Form , Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from jose import jwt, JWTError
from sqlalchemy.orm import Session

import models
from database import get_db, engine, SessionLocal

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Roomly - Conference Room Booking")

def seed_rooms():
    db = SessionLocal()
    if db.query(models.Room).count() == 0:
        conference_rooms = [
            models.Room(
                name="Sala Diamentowa", 
                capacity=20, 
                location="Piętro 3, Skrzydło A", 
                price=500,
                is_active=True
            ),
            models.Room(
                name="Boardroom (Fioletowa)", 
                capacity=8, 
                location="Piętro 1, obok Recepcji", 
                price=250,
                is_active=True
            ),
            models.Room(
                name="Focus Room 1", 
                capacity=4, 
                location="Piętro 2, Strefa Ciszy", 
                price=100,
                is_active=True
            ),
            models.Room(
                name="Creative Space", 
                capacity=15, 
                location="Parter, wejście od ogrodu", 
                price=300,
                is_active=True
            )
        ]
        db.add_all(conference_rooms)
        db.commit()
        print("Pomyślnie dodano sale konferencyjne Roomly do bazy!")
    db.close()


seed_rooms()


current_dir = os.path.dirname(os.path.realpath(__file__))
templates_path = os.path.join(current_dir, "templates")
static_path = os.path.join(current_dir, "static")

templates = Jinja2Templates(directory=templates_path)
app.mount("/static", StaticFiles(directory=static_path), name="static")

SECRET_KEY = "69b167520e5e0199799f9116e788e0e378c858593a2e3794348507204f11467e"
ALGORITHM = "HS256"

@app.get("/rooms", response_class=HTMLResponse)
async def list_rooms(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    
    if not token:
        raise HTTPException(status_code=401, detail="Brak dostępu. Zaloguj się w systemie Roomly.")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email = payload.get("sub")
        
        rooms = db.query(models.Room).filter(models.Room.is_active == True).all()
        
        return templates.TemplateResponse("rooms.html", {
            "request": request, 
            "user": user_email, 
            "rooms": rooms
        })
    except JWTError:
        raise HTTPException(status_code=401, detail="Sesja wygasła. Proszę zalogować się ponownie.")
    

@app.get("/book/{room_id}", response_class=HTMLResponse)
async def show_booking_form(room_id: int, request: Request, db: Session = Depends(get_db)):
    room = db.query(models.Room).filter(models.Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Nie znaleziono sali")
    return templates.TemplateResponse("booking_form.html", {"request": request, "room": room})


@app.post("/confirm_booking/{room_id}")
async def confirm_booking(
    room_id: int, 
    request: Request, 
    first_name: str = Form(...),    
    last_name: str = Form(...),     
    contact_email: str = Form(...), 
    booking_date: str = Form(...), 
    booking_time: str = Form(...), 
    contact_info: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        token = request.cookies.get("access_token")
        if not token:
             return HTMLResponse(content="<h1>Błąd: Nie jesteś zalogowany!</h1>", status_code=401)

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email = payload.get("sub")
        
        user = db.query(models.User).filter(models.User.email == user_email).first()

        info = f"Klient: {first_name} {last_name}, Data: {booking_date} {booking_time}"

        new_booking = models.Booking(
            user_id=user.id if user else 1,
            room_id=room_id,
            status=info
        )
        db.add(new_booking)
        db.commit()
        return "OK" 
    except Exception as e:
        return Response(content=str(e), status_code=400)
    
@app.get("/my_bookings", response_class=HTMLResponse)
async def my_bookings(request: Request, db: Session = Depends(get_db)):
   
    token = request.cookies.get("access_token")
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    user_email = payload.get("sub")
    user = db.query(models.User).filter(models.User.email == user_email).first()

    bookings = db.query(models.Booking).filter(models.Booking.user_id == user.id).all()
    
    return templates.TemplateResponse("my_bookings.html", {"request": request, "bookings": bookings})

@app.delete("/delete_booking/{booking_id}")
async def delete_booking(booking_id: int, db: Session = Depends(get_db)):
    booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Rezerwacja nie istnieje")
    
    db.delete(booking)
    db.commit()
    return {"message": "Usunięto pomyślnie"}