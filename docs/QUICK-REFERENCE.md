# QUICK-REFERENCE.md

# ⚡ Quick Reference Guide - FastAPI Migration

## 📌 Essential Commands

### Project Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install fastapi uvicorn[standard] sqlalchemy asyncpg
pip install python-jose[cryptography] passlib[bcrypt]
pip install pydantic[email] python-multipart
pip install aioredis firebase-admin httpx

# Save requirements
pip freeze > requirements.txt
```

### Database
```bash
# Start PostgreSQL
sudo systemctl start postgresql  # Linux
brew services start postgresql   # Mac

# Connect to database
psql -U postgres -d service_manpower

# Run schema
psql -U postgres -d service_manpower -f schema.sql

# Check tables
\dt

# Exit
\q
```

### Redis
```bash
# Start Redis
redis-server

# Test connection
redis-cli ping  # Should return PONG
```

### Run FastAPI
```bash
# Development mode
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Docker
```bash
# Build and run
docker-compose up -d --build

# View logs
docker-compose logs -f api

# Stop
docker-compose down

# Rebuild
docker-compose up -d --build --force-recreate
```

---

## 🔑 Code Snippets

### Basic FastAPI App
```python
# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Service Manpower API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS for mobile app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "healthy"}
```

### JWT Authentication
```python
# app/core/security.py
from jose import jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=30))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
```

### Database Connection
```python
# app/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql+asyncpg://user:pass@localhost/dbname"

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except:
            await session.rollback()
            raise
        finally:
            await session.close()
```

### Pydantic Schema
```python
# app/schemas/user.py
from pydantic import BaseModel, EmailStr, Field

class UserCreate(BaseModel):
    full_name: str = Field(..., min_length=3)
    phone_number: str = Field(..., pattern=r'^98\d{8}$')
    password: str = Field(..., min_length=8)

class UserResponse(BaseModel):
    id: int
    full_name: str
    phone_number: str
    
    class Config:
        from_attributes = True
```

### Protected Route
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    # Validate token and return user
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        return await get_user_by_id(user_id)
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/api/profile")
def get_profile(current_user = Depends(get_current_user)):
    return current_user
```

### File Upload
```python
from fastapi import UploadFile, File

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    # Validate
    if not file.content_type.startswith('image/'):
        raise HTTPException(400, "Must be an image")
    
    # Save
    contents = await file.read()
    with open(f"uploads/{file.filename}", "wb") as f:
        f.write(contents)
    
    return {"filename": file.filename}
```

### Background Task
```python
from fastapi import BackgroundTasks

def send_email(email: str, message: str):
    # Simulate sending email
    print(f"Sending to {email}: {message}")

@app.post("/register")
async def register(background_tasks: BackgroundTasks, user_data: UserCreate):
    # Create user
    user = await create_user(user_data)
    
    # Send email in background
    background_tasks.add_task(send_email, user.email, "Welcome!")
    
    return user
```

### WebSocket
```python
from fastapi import WebSocket

@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Echo: {data}")
```

---

## 🗄️ Common SQL Queries

### Find Nearby Professionals
```sql
SELECT 
    pp.*,
    earth_distance(
        ll_to_earth(:user_lat, :user_lng),
        ll_to_earth(pp.latitude, pp.longitude)
    ) / 1000 AS distance_km
FROM professional_profiles pp
WHERE pp.verification_status = 'APPROVED'
  AND pp.is_available = TRUE
ORDER BY distance_km
LIMIT 20;
```

### Check Booking Conflicts
```sql
SELECT COUNT(*) FROM bookings
WHERE professional_id = :prof_id
  AND status IN ('upcoming', 'ongoing')
  AND tsrange(booking_time, end_time + INTERVAL '30 minutes')
      OVERLAPS tsrange(:new_start, :new_end);
```

### Get Professional Stats
```sql
SELECT 
    COUNT(*) as total_bookings,
    AVG(rating) as avg_rating,
    SUM(total_fee) as total_earnings
FROM bookings b
LEFT JOIN reviews r ON b.id = r.booking_id
WHERE b.professional_id = :prof_id
  AND b.status = 'completed';
```

---

## 🐛 Debugging Tips

### Check Logs
```bash
# FastAPI logs
uvicorn app.main:app --log-level debug

# Database logs
tail -f /var/log/postgresql/postgresql-15-main.log

# Redis logs
redis-cli MONITOR
```

### Common Errors

**Import Error:**
```
ModuleNotFoundError: No module named 'xxx'
→ pip install xxx
```

**Database Connection Failed:**
```
could not connect to server
→ Check PostgreSQL is running: sudo systemctl status postgresql
```

**CORS Error:**
```
No 'Access-Control-Allow-Origin' header
→ Add CORSMiddleware to FastAPI app
```

**JWT Invalid:**
```
Invalid token
→ Check SECRET_KEY matches, token not expired
```

---

## 📱 Flutter Quick Start

### Create Project
```bash
flutter create service_manpower_app
cd service_manpower_app
```

### Add Dependencies (`pubspec.yaml`)
```yaml
dependencies:
  dio: ^5.4.0
  provider: ^6.1.1
  geolocator: ^10.1.0
  flutter_map: ^6.1.0
  firebase_messaging: ^14.7.0
  hive: ^2.2.3
```

### API Service Template
```dart
// lib/services/api_service.dart
import 'package:dio/dio.dart';

class ApiService {
  final Dio _dio = Dio(BaseOptions(
    baseUrl: 'http://your-server-ip:8000/api',
    connectTimeout: Duration(seconds: 5),
    receiveTimeout: Duration(seconds: 3),
  ));
  
  // Add auth token to all requests
  void setAuthToken(String token) {
    _dio.options.headers['Authorization'] = 'Bearer $token';
  }
  
  Future<Map<String, dynamic>> login(String phone, String password) async {
    try {
      final response = await _dio.post('/auth/login', data: {
        'phone_number': phone,
        'password': password,
      });
      return response.data;
    } catch (e) {
      throw Exception('Login failed: $e');
    }
  }
  
  Future<List<dynamic>> getProfessionals({
    required double lat,
    required double lng,
    String? skill,
  }) async {
    try {
      final response = await _dio.get('/location/professionals/nearby',
        queryParameters: {
          'latitude': lat,
          'longitude': lng,
          if (skill != null) 'skill': skill,
        },
      );
      return response.data['professionals'];
    } catch (e) {
      throw Exception('Failed to fetch professionals: $e');
    }
  }
}
```

---

## 🔒 Security Checklist

- [ ] Use HTTPS in production
- [ ] Set strong SECRET_KEY (min 64 chars)
- [ ] Validate all inputs with Pydantic
- [ ] Hash passwords with bcrypt (12+ rounds)
- [ ] Use parameterized queries (no SQL injection)
- [ ] Implement rate limiting
- [ ] Set proper CORS origins
- [ ] Sanitize file uploads
- [ ] Use environment variables for secrets
- [ ] Enable SQL query logging in dev only

---

## 📊 Performance Checklist

- [ ] Enable Redis caching
- [ ] Add database indexes
- [ ] Use connection pooling
- [ ] Implement pagination
- [ ] Run independent queries concurrently
- [ ] Offload slow tasks to background
- [ ] Compress responses (gzip)
- [ ] Use CDN for static files
- [ ] Monitor slow queries
- [ ] Profile response times

---

## 🚀 Deployment Checklist

- [ ] Set DEBUG=False
- [ ] Configure production DATABASE_URL
- [ ] Set up SSL certificates
- [ ] Enable firewall (UFW)
- [ ] Configure Nginx reverse proxy
- [ ] Set up database backups
- [ ] Enable monitoring (Prometheus/Grafana)
- [ ] Configure log rotation
- [ ] Test rollback procedure
- [ ] Document support contacts

---

## 📞 Useful Links

- **FastAPI Docs**: https://fastapi.tiangolo.com
- **SQLAlchemy Docs**: https://docs.sqlalchemy.org
- **PostgreSQL Docs**: https://www.postgresql.org/docs/
- **Redis Commands**: https://redis.io/commands
- **Flutter Docs**: https://flutter.dev/docs
- **Docker Docs**: https://docs.docker.com
- **Stack Overflow**: Tag questions with `fastapi`

---

## 💡 Pro Tips

1. **Use Swagger UI** at `/docs` for testing APIs
2. **Enable auto-reload** during development: `--reload`
3. **Use Pydantic models** for automatic validation
4. **Write tests early** - don't wait until the end
5. **Monitor performance** from day one
6. **Document decisions** as you make them
7. **Backup regularly** - daily minimum
8. **Keep dependencies updated** - monthly check
9. **Use environment variables** - never hardcode secrets
10. **Test on real devices** - emulators aren't enough

---

**Keep this guide handy for quick reference!** 📌
