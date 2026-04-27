# 12-PERFORMANCE-OPTIMIZATION.md

# Performance Optimization Guide

## 📋 Overview

Comprehensive optimization strategies for FastAPI backend including caching, query optimization, async patterns, and scaling.

---

## ⚡ Caching with Redis

### Setup Redis

```bash
# Install Redis
sudo apt-get install redis-server  # Linux
brew install redis                 # macOS

# Start Redis
redis-server

# Install Python package
pip install aioredis
```

### `app/services/cache_service.py`

```python
import json
import aioredis
from typing import Optional, Any
from app.config import settings

class CacheService:
    """Redis caching service"""
    
    def __init__(self):
        self.redis = aioredis.from_url(
            "redis://localhost:6379",
            encoding="utf-8",
            decode_responses=True
        )
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            value = await self.redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception:
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Set value in cache with TTL (default 5 minutes)"""
        try:
            await self.redis.setex(
                key,
                ttl,
                json.dumps(value, default=str)
            )
            return True
        except Exception:
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            await self.redis.delete(key)
            return True
        except Exception:
            return False
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching pattern"""
        try:
            keys = await self.redis.keys(pattern)
            if keys:
                return await self.redis.delete(*keys)
            return 0
        except Exception:
            return 0

# Global cache instance
cache = CacheService()
```

### Caching Examples

```python
# Example 1: Cache professional search results
async def get_nearby_professionals_cached(lat, lng, radius, skill):
    cache_key = f"nearby:{lat}:{lng}:{radius}:{skill}"
    
    # Try cache first
    cached = await cache.get(cache_key)
    if cached:
        return cached
    
    # Fetch from database
    professionals = await LocationService.find_nearby_professionals(
        db, lat, lng, radius, skill
    )
    
    # Cache for 5 minutes
    await cache.set(cache_key, professionals, ttl=300)
    
    return professionals

# Example 2: Cache user profile
async def get_user_profile_cached(user_id: int):
    cache_key = f"user_profile:{user_id}"
    
    cached = await cache.get(cache_key)
    if cached:
        return cached
    
    profile = await UserService.get_user_profile(db, user_id)
    await cache.set(cache_key, profile, ttl=600)  # 10 minutes
    
    return profile

# Example 3: Invalidate cache on update
async def update_professional_location(user_id, lat, lng):
    # Update database
    await LocationService.update_professional_location(db, user_id, lat, lng)
    
    # Invalidate related caches
    await cache.invalidate_pattern(f"nearby:*")  # Clear all nearby searches
    await cache.delete(f"user_profile:{user_id}")  # Clear user profile
```

---

## 🔍 Database Query Optimization

### 1. Use Specific Column Selection

```python
# ✅ GOOD: Select only needed columns
query = """
    SELECT id, full_name, rate, latitude, longitude
    FROM professional_profiles
    WHERE verification_status = 'APPROVED'
"""

# ❌ BAD: Select all columns
query = "SELECT * FROM professional_profiles"
```

### 2. Batch Operations

```python
# ✅ GOOD: Batch insert
async def assign_skills_batch(professional_id: int, skill_ids: List[int]):
    values = [
        {"professional_id": professional_id, "skill_id": sid}
        for sid in skill_ids
    ]
    query = """
        INSERT INTO professional_skills (professional_id, skill_id)
        VALUES (:professional_id, :skill_id)
    """
    await database.execute_many(query, values)

# ❌ BAD: Individual inserts
for skill_id in skill_ids:
    await database.execute(query, {...})
```

### 3. Use Indexes Effectively

```sql
-- Ensure these indexes exist
CREATE INDEX idx_professional_verification ON professional_profiles(verification_status);
CREATE INDEX idx_professional_available ON professional_profiles(is_available);
CREATE INDEX idx_bookings_professional_time ON bookings(professional_id, booking_time);

-- Check index usage
SELECT schemaname, relname, indexrelname, idx_scan
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
```

### 4. Optimize JOIN Queries

```python
# ✅ GOOD: Use JOIN instead of multiple queries
query = """
    SELECT 
        pp.id,
        pp.rate,
        u.full_name,
        s.name as skill_name
    FROM professional_profiles pp
    JOIN users u ON pp.user_id = u.id
    LEFT JOIN professional_skills ps ON pp.id = ps.professional_id
    LEFT JOIN skills s ON ps.skill_id = s.id
    WHERE pp.verification_status = 'APPROVED'
"""

# ❌ BAD: N+1 queries
professionals = await get_all_professionals()
for pro in professionals:
    user = await get_user(pro.user_id)  # Separate query for each
    skills = await get_skills(pro.id)   # Separate query for each
```

### 5. Pagination

```python
async def get_professionals_paginated(page: int = 1, per_page: int = 20):
    offset = (page - 1) * per_page
    
    # Get total count
    count_result = await db.execute(
        select(func.count()).select_from(ProfessionalProfile)
    )
    total = count_result.scalar()
    
    # Get paginated results
    result = await db.execute(
        select(ProfessionalProfile)
        .offset(offset)
        .limit(per_page)
        .order_by(ProfessionalProfile.created_at.desc())
    )
    professionals = result.scalars().all()
    
    return {
        "data": professionals,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page
    }
```

---

## 🚀 Async Patterns

### 1. Concurrent Database Queries

```python
import asyncio

# ✅ GOOD: Run queries concurrently
async def get_dashboard_data(user_id: int):
    # Run multiple queries in parallel
    user_task = get_user_profile(user_id)
    bookings_task = get_user_bookings(user_id)
    reviews_task = get_user_reviews(user_id)
    
    # Wait for all to complete
    user, bookings, reviews = await asyncio.gather(
        user_task, bookings_task, reviews_task
    )
    
    return {
        "user": user,
        "bookings": bookings,
        "reviews": reviews
    }

# ❌ BAD: Sequential queries
user = await get_user_profile(user_id)
bookings = await get_user_bookings(user_id)  # Waits for previous
reviews = await get_user_reviews(user_id)    # Waits for previous
```

### 2. Background Tasks

```python
from fastapi import BackgroundTasks

async def send_email_notification(email: str, message: str):
    """Simulate sending email (slow operation)"""
    await asyncio.sleep(2)  # Simulate API call
    print(f"Email sent to {email}")

@app.post("/bookings/create")
async def create_booking(
    background_tasks: BackgroundTasks,
    booking_data: BookingCreate
):
    # Create booking (fast)
    booking = await create_booking_in_db(booking_data)
    
    # Send email notification (background, doesn't block response)
    background_tasks.add_task(
        send_email_notification,
        booking.client_email,
        "Your booking is confirmed!"
    )
    
    return {"booking_id": booking.id}
```

### 3. Connection Pooling

```python
# app/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_size=20,           # Max connections in pool
    max_overflow=10,        # Extra connections beyond pool_size
    pool_timeout=30,        # Timeout waiting for connection
    pool_recycle=1800,      # Recycle connections after 30 min
    pool_pre_ping=True      # Test connections before use
)

AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)
```

---

## 📊 Monitoring & Profiling

### 1. Request Timing Middleware

```python
import time
from fastapi import Request

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    # Log slow requests
    if process_time > 1.0:  # More than 1 second
        print(f"Slow request: {request.url.path} took {process_time:.2f}s")
    
    return response
```

### 2. Database Query Logging

```python
# Enable SQLAlchemy query logging
import logging

logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# In production, log only slow queries
from sqlalchemy import event

@event.listens_for(engine.sync_engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    conn.info.setdefault('query_start_time', []).append(time.time())

@event.listens_for(engine.sync_engine, "after_cursor_execute")
def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total_time = time.time() - conn.info['query_start_time'].pop(-1)
    
    if total_time > 0.5:  # Log queries taking more than 500ms
        print(f"Slow query ({total_time:.2f}s): {statement}")
```

### 3. Prometheus Metrics

```bash
pip install prometheus-fastapi-instrumentator
```

```python
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()
Instrumentator().instrument(app).expose(app)

# Metrics available at /metrics
# - Request count
# - Request duration
# - HTTP status codes
```

---

## 🔧 Scaling Strategies

### 1. Horizontal Scaling with Multiple Workers

```bash
# Run with multiple workers
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# Or use Gunicorn with Uvicorn workers
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### 2. Load Balancing

```nginx
# nginx.conf
upstream fastapi_backend {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
    server 127.0.0.1:8003;
}

server {
    listen 80;
    
    location / {
        proxy_pass http://fastapi_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 3. Database Read Replicas

```python
# Separate read/write databases
write_engine = create_async_engine(DATABASE_URL_WRITE)
read_engine = create_async_engine(DATABASE_URL_READ)

async def get_write_db():
    async with AsyncSession(write_engine) as session:
        yield session

async def get_read_db():
    async with AsyncSession(read_engine) as session:
        yield session

# Use write DB for mutations
@app.post("/bookings")
async def create_booking(db = Depends(get_write_db)):
    ...

# Use read DB for queries
@app.get("/bookings")
async def get_bookings(db = Depends(get_read_db)):
    ...
```

---

## 📈 Performance Benchmarks

### Target Metrics

| Metric | Target | Current |
|--------|--------|---------|
| Response Time (p95) | < 200ms | ? |
| Requests/Second | > 500 | ? |
| Database Query Time | < 50ms | ? |
| Cache Hit Rate | > 80% | ? |
| CPU Usage | < 70% | ? |
| Memory Usage | < 2GB | ? |

### Load Testing

```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Test endpoint
ab -n 1000 -c 50 http://localhost:8000/api/professionals/nearby?lat=27.7172&lng=85.3240

# Results:
# Requests per second:    523.45 [#/sec]
# Time per request:       95.523 [ms]
```

---

## ✅ Optimization Checklist

- [ ] Enable Redis caching for frequently accessed data
- [ ] Add database indexes for common queries
- [ ] Use connection pooling
- [ ] Implement pagination for list endpoints
- [ ] Use async/await for I/O operations
- [ ] Run independent queries concurrently
- [ ] Offload slow tasks to background
- [ ] Monitor slow queries and optimize
- [ ] Enable gzip compression
- [ ] Use CDN for static files
- [ ] Implement rate limiting
- [ ] Set up horizontal scaling
- [ ] Configure proper logging
- [ ] Regular database maintenance (VACUUM, ANALYZE)

---

**Next:** Deployment guide ➡️ See `14-DEPLOYMENT.md`
