from fastapi import FastAPI, Depends, HTTPException, status, Request, Response
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext
import models, database, schemas 
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

app = FastAPI(title="Roomly Auth Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

SECRET_KEY = "69b167520e5e0199799f9116e788e0e378c858593a2e3794348507204f11467e"
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

models.Base.metadata.create_all(bind=database.engine)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=60)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@app.get("/", response_class=HTMLResponse)
async def serve_frontend(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/auth/register", status_code=201)
def register(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Ten adres e-mail jest juz zarejestrowany")
    
    hashed_password = pwd_context.hash(user.password)
    new_user = models.User(email=user.email, password_hash=hashed_password, role="employee")
    db.add(new_user)
    db.commit()
    return {"message": "Uzytkownik zarejestrowany"}

@app.post("/login")
def login(response: Response, user: schemas.UserLogin, db: Session = Depends(database.get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    
    if not db_user or not pwd_context.verify(user.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Bledne dane logowania")
    
    token = create_access_token(data={"sub": db_user.email, "role": db_user.role})
    response.set_cookie(
        key="access_token", 
        value=token, 
        httponly=True, 
        max_age=3600,
        samesite="lax"
    )
    
    return {
        "message": "Zalogowano pomyślnie", 
        "redirect_url": "http://localhost:8002/rooms" 
    }

@app.get("/auth/verify")
def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Nieprawidlowy token")