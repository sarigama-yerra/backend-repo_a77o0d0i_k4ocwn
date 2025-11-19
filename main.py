import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import User, BlogPost, ContactMessage

app = FastAPI(title="SaaS Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "SaaS backend running"}


# Helper for ObjectId parsing
class IdModel(BaseModel):
    id: str


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = getattr(db, 'name', None) or "Unknown"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    return response


# Auth (basic email/password register + login with salted hash)
import hashlib, secrets

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class AuthResponse(BaseModel):
    token: str
    name: str
    plan: str


def hash_password(password: str, salt: str) -> str:
    return hashlib.sha256((salt + password).encode()).hexdigest()


@app.post("/api/auth/register", response_model=AuthResponse)
def register(req: RegisterRequest):
    # check if user exists
    existing = db["user"].find_one({"email": req.email}) if db else None
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    salt = secrets.token_hex(16)
    pwd_hash = hash_password(req.password, salt)
    user = User(
        name=req.name,
        email=req.email,
        password_hash=pwd_hash,
        password_salt=salt,
        plan="free",
        is_verified=False,
    )
    user_id = create_document("user", user)
    token = hashlib.sha256((req.email + salt).encode()).hexdigest()
    return AuthResponse(token=token, name=user.name, plan=user.plan)


@app.post("/api/auth/login", response_model=AuthResponse)
def login(req: LoginRequest):
    u = db["user"].find_one({"email": req.email}) if db else None
    if not u:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    salt = u.get("password_salt")
    expected = u.get("password_hash")
    if hash_password(req.password, salt) != expected:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = hashlib.sha256((req.email + salt).encode()).hexdigest()
    return AuthResponse(token=token, name=u.get("name"), plan=u.get("plan", "free"))


# Blog endpoints
class BlogSummary(BaseModel):
    title: str
    slug: str
    excerpt: str
    tags: List[str] = []
    author: str = "Team"
    cover_image: Optional[str] = None

class BlogDetail(BlogSummary):
    content: str


@app.get("/api/blog", response_model=List[BlogSummary])
def list_blog():
    posts = get_documents("blogpost", {"published": True}, limit=50) if db else []
    res: List[BlogSummary] = []
    for p in posts:
        res.append(BlogSummary(
            title=p.get("title"),
            slug=p.get("slug"),
            excerpt=p.get("excerpt"),
            tags=p.get("tags", []),
            author=p.get("author", "Team"),
            cover_image=p.get("cover_image")
        ))
    return res


@app.get("/api/blog/{slug}", response_model=BlogDetail)
def get_blog(slug: str):
    p = db["blogpost"].find_one({"slug": slug, "published": True}) if db else None
    if not p:
        raise HTTPException(status_code=404, detail="Not found")
    return BlogDetail(
        title=p.get("title"),
        slug=p.get("slug"),
        excerpt=p.get("excerpt"),
        tags=p.get("tags", []),
        author=p.get("author", "Team"),
        cover_image=p.get("cover_image"),
        content=p.get("content", "")
    )


# Contact form endpoint
class ContactRequest(BaseModel):
    name: str
    email: EmailStr
    company: Optional[str] = None
    topic: Optional[str] = "General"
    message: str

class ContactResponse(BaseModel):
    ok: bool


@app.post("/api/contact", response_model=ContactResponse)
def contact(req: ContactRequest):
    msg = ContactMessage(
        name=req.name,
        email=req.email,
        company=req.company,
        topic=req.topic,
        message=req.message
    )
    _id = create_document("contactmessage", msg)
    return ContactResponse(ok=True)


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
