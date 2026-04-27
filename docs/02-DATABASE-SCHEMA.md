# 02-DATABASE-SCHEMA.md

# Database Schema Design - PostgreSQL with Optimized Indexes

## 📊 Overview

This document contains the complete PostgreSQL schema for the Service Manpower FastAPI backend, optimized for async operations with proper indexing for performance.

---

## 🗄️ Complete Schema

### 1. Users Table

```sql
-- ============================================
-- USERS TABLE
-- Core user authentication and profile data
-- ============================================
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    phone_number VARCHAR(10) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE,
    full_name VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_client BOOLEAN DEFAULT TRUE,
    is_professional BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    is_staff BOOLEAN DEFAULT FALSE,
    is_superuser BOOLEAN DEFAULT FALSE,
    fcm_token VARCHAR(255),  -- Firebase Cloud Messaging token for push notifications
    last_login TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for common queries
CREATE INDEX idx_users_phone ON users(phone_number);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_active ON users(is_active);
CREATE INDEX idx_users_professional ON users(is_professional) WHERE is_professional = TRUE;
CREATE INDEX idx_users_created_at ON users(created_at DESC);

-- Comments
COMMENT ON TABLE users IS 'Core user table for authentication and basic profile';
COMMENT ON COLUMN users.phone_number IS 'Primary identifier for login (Nepal format: 98XXXXXXXX)';
COMMENT ON COLUMN users.fcm_token IS 'Firebase token for push notifications (mobile app)';
```

**Key Design Decisions:**
- Phone number as primary identifier (Nepal market preference)
- Separate `is_client` and `is_professional` flags for role management
- FCM token stored for push notifications
- Indexes optimized for frequent lookups

---

### 2. Professional Profiles Table

```sql
-- ============================================
-- PROFESSIONAL PROFILES TABLE
-- Detailed professional information with geospatial support
-- ============================================
CREATE TABLE professional_profiles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    email VARCHAR(255) UNIQUE NOT NULL,
    
    -- Location hierarchy (Nepal administrative divisions)
    province VARCHAR(100) NOT NULL,
    district VARCHAR(100) NOT NULL,
    municipality VARCHAR(100) NOT NULL,
    ward INTEGER NOT NULL CHECK (ward > 0 AND ward <= 50),
    
    -- Professional details
    experience INTEGER DEFAULT 0 CHECK (experience >= 0 AND experience <= 50),
    about_yourself TEXT,
    rate DECIMAL(10, 2) NOT NULL DEFAULT 0 CHECK (rate >= 0 AND rate <= 10000),
    
    -- Rating system
    average_rating FLOAT DEFAULT 0.0 CHECK (average_rating >= 0 AND average_rating <= 5),
    total_reviews INTEGER DEFAULT 0 CHECK (total_reviews >= 0),
    
    -- Documents and images
    profile_picture VARCHAR(500),
    citizenship_front VARCHAR(500),
    citizenship_back VARCHAR(500),
    
    -- Availability and location
    is_available BOOLEAN DEFAULT TRUE,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    
    -- Verification workflow
    verification_status VARCHAR(20) DEFAULT 'PENDING' 
        CHECK (verification_status IN ('PENDING', 'APPROVED', 'REJECTED')),
    verified_at TIMESTAMP WITH TIME ZONE,
    verified_by INTEGER REFERENCES users(id),
    rejection_reason TEXT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Critical indexes for performance
CREATE INDEX idx_professional_user ON professional_profiles(user_id);
CREATE INDEX idx_professional_verification ON professional_profiles(verification_status);
CREATE INDEX idx_professional_available ON professional_profiles(is_available) WHERE is_available = TRUE;
CREATE INDEX idx_professional_district ON professional_profiles(district);
CREATE INDEX idx_professional_municipality ON professional_profiles(municipality);
CREATE INDEX idx_professional_created ON professional_profiles(created_at DESC);

-- Geospatial index for location-based queries (using earthdistance extension)
-- Note: Requires PostgreSQL earthdistance module
CREATE INDEX idx_professional_location 
ON professional_profiles USING gist(ll_to_earth(latitude, longitude))
WHERE latitude IS NOT NULL AND longitude IS NOT NULL;

-- Alternative: Simple index if earthdistance not available
CREATE INDEX idx_professional_lat_lng 
ON professional_profiles(latitude, longitude)
WHERE latitude IS NOT NULL AND longitude IS NOT NULL;

-- Composite index for common filter combinations
CREATE INDEX idx_professional_search 
ON professional_profiles(verification_status, is_available, district)
WHERE verification_status = 'APPROVED' AND is_available = TRUE;

-- Comments
COMMENT ON TABLE professional_profiles IS 'Professional profiles with KYC documents and verification status';
COMMENT ON COLUMN professional_profiles.rate IS 'Hourly rate in NPR (validated by experience level)';
COMMENT ON COLUMN professional_profiles.verification_status IS 'PENDING/APPROVED/REJECTED - controls booking eligibility';
```

**Rate Validation Rules (Enforced in Application Layer):**
```python
# Experience-based rate limits
if experience < 1: max_rate = 200
elif experience < 3: max_rate = 300
elif experience < 5: max_rate = 400
else: max_rate = 600
```

---

### 3. Skills System (Many-to-Many)

```sql
-- ============================================
-- SKILLS TABLE
-- Professional skills with search aliases
-- ============================================
CREATE TABLE skills (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    category VARCHAR(50) DEFAULT 'General' CHECK (category IN (
        'Plumbing', 'Electrical', 'Carpentry', 'Cleaning', 
        'Painting', 'Masonry', 'General', 'Other'
    )),
    description TEXT,
    aliases JSONB DEFAULT '[]'::jsonb,  -- For fuzzy search
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for skill search
CREATE INDEX idx_skills_name ON skills(name);
CREATE INDEX idx_skills_category ON skills(category);
CREATE INDEX idx_skills_aliases ON skills USING gin(aliases);  -- GIN index for JSONB

-- Sample data insertion
INSERT INTO skills (name, category, aliases) VALUES
('Plumbing', 'Plumbing', '["plumber", "plumbing", "pipe fitting", "water repair"]'),
('Electrical Work', 'Electrical', '["electrician", "electrical", "wiring", "power repair"]'),
('Carpentry', 'Carpentry', '["carpenter", "carpentry", "woodwork", "furniture repair"]'),
('House Cleaning', 'Cleaning', '["cleaner", "cleaning", "housekeeping", "maid service"]'),
('Wall Painting', 'Painting', '["painter", "painting", "wall paint", "color work"]'),
('Masonry Work', 'Masonry', '["mason", "masonry", "bricklayer", "cement work"]');

-- ============================================
-- PROFESSIONAL-SKILLS RELATIONSHIP TABLE
-- Many-to-many relationship
-- ============================================
CREATE TABLE professional_skills (
    professional_id INTEGER REFERENCES professional_profiles(id) ON DELETE CASCADE,
    skill_id INTEGER REFERENCES skills(id) ON DELETE CASCADE,
    PRIMARY KEY (professional_id, skill_id)
);

-- Indexes for quick lookups
CREATE INDEX idx_professional_skills_professional ON professional_skills(professional_id);
CREATE INDEX idx_professional_skills_skill ON professional_skills(skill_id);

-- Constraint: Maximum 3 skills per professional (enforced in application layer)
COMMENT ON TABLE professional_skills IS 'Links professionals to their skills (max 3 per professional)';
```

**Skill Search with Aliases:**
```python
# Example: Search for "plumber" matches skills with alias "plumber"
async def search_skills(query: str):
    result = await db.fetch_all("""
        SELECT DISTINCT s.* FROM skills s
        WHERE s.name ILIKE $1 
           OR $1 = ANY(s.aliases)
    """, f"%{query}%")
    return result
```

---

### 4. Bookings Table

```sql
-- ============================================
-- BOOKINGS TABLE
-- Core booking system with time slot management
-- ============================================
CREATE TABLE bookings (
    id SERIAL PRIMARY KEY,
    client_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    
    -- Client details (snapshot at booking time)
    client_name VARCHAR(100) NOT NULL,
    client_phone VARCHAR(10) NOT NULL CHECK (client_phone ~ '^98\d{8}$'),
    
    professional_id INTEGER REFERENCES professional_profiles(id) ON DELETE CASCADE,
    
    -- Time management
    booking_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    duration_hours FLOAT NOT NULL CHECK (duration_hours >= 0.5 AND duration_hours <= 24),
    
    -- Pricing
    total_fee DECIMAL(10, 2) NOT NULL CHECK (total_fee > 0),
    deposit_amount DECIMAL(10, 2) NOT NULL CHECK (deposit_amount > 0),
    remaining_payment DECIMAL(10, 2) GENERATED ALWAYS AS (total_fee - deposit_amount) STORED,
    
    -- Status tracking
    is_confirmed BOOLEAN DEFAULT FALSE,
    status VARCHAR(20) DEFAULT 'upcoming' 
        CHECK (status IN ('upcoming', 'ongoing', 'completed', 'cancelled')),
    
    -- Location data (for distance calculation and navigation)
    user_latitude DOUBLE PRECISION,
    user_longitude DOUBLE PRECISION,
    professional_latitude DOUBLE PRECISION,
    professional_longitude DOUBLE PRECISION,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- CRITICAL indexes for booking queries
CREATE INDEX idx_bookings_professional_time 
ON bookings(professional_id, booking_time, end_time);

CREATE INDEX idx_bookings_client_time 
ON bookings(client_id, booking_time DESC);

CREATE INDEX idx_bookings_status ON bookings(status);
CREATE INDEX idx_bookings_confirmed ON bookings(is_confirmed);
CREATE INDEX idx_bookings_upcoming 
ON bookings(booking_time) WHERE status IN ('upcoming', 'ongoing');

-- Index for overlap detection (time slot conflicts)
CREATE INDEX idx_bookings_time_range 
ON bookings USING gist(tsrange(booking_time, end_time));

-- Partial index for active bookings only
CREATE INDEX idx_bookings_active 
ON bookings(professional_id, booking_time, end_time)
WHERE status IN ('upcoming', 'ongoing');

-- Comments
COMMENT ON TABLE bookings IS 'Service bookings with time slots and payment tracking';
COMMENT ON COLUMN bookings.deposit_amount IS '10% of total fee paid via eSewa';
COMMENT ON COLUMN bookings.remaining_payment IS 'Automatically calculated: total_fee - deposit_amount';
```

**Time Slot Conflict Detection Query:**
```sql
-- Check if new booking overlaps with existing bookings + 30-min gap
SELECT COUNT(*) FROM bookings
WHERE professional_id = $1
  AND status IN ('upcoming', 'ongoing')
  AND tsrange(booking_time, end_time + INTERVAL '30 minutes') 
      OVERLAPS tsrange($2, $2 + ($3 || ' hours')::interval);
```

---

### 5. Payments Table

```sql
-- ============================================
-- PAYMENTS TABLE
-- Payment tracking with eSewa integration
-- ============================================
CREATE TABLE payments (
    id SERIAL PRIMARY KEY,
    booking_id INTEGER REFERENCES bookings(id) ON DELETE CASCADE,
    
    -- Transaction identifiers
    transaction_uuid UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    esewa_order_id VARCHAR(50),
    esewa_ref_id VARCHAR(50),
    
    -- Payment details
    amount DECIMAL(10, 2) NOT NULL CHECK (amount > 0),
    is_paid BOOLEAN DEFAULT FALSE,
    payment_date TIMESTAMP WITH TIME ZONE,
    payment_method VARCHAR(50) DEFAULT 'esewa' CHECK (payment_method IN ('esewa', 'khalti', 'cash')),
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for payment queries
CREATE INDEX idx_payments_transaction_uuid ON payments(transaction_uuid);
CREATE INDEX idx_payments_booking ON payments(booking_id);
CREATE INDEX idx_payments_paid ON payments(is_paid) WHERE is_paid = TRUE;
CREATE INDEX idx_payments_date ON payments(payment_date DESC);

-- Unique constraint: One payment per booking
CREATE UNIQUE INDEX idx_payments_one_per_booking ON payments(booking_id);

COMMENT ON TABLE payments IS 'Payment records for booking deposits (10%)';
COMMENT ON COLUMN payments.transaction_uuid IS 'Unique ID for eSewa transaction verification';
```

---

### 6. Reviews and Ratings Table

```sql
-- ============================================
-- REVIEWS TABLE
-- Post-service ratings and feedback
-- ============================================
CREATE TABLE reviews (
    id SERIAL PRIMARY KEY,
    booking_id INTEGER REFERENCES bookings(id) ON DELETE CASCADE UNIQUE,
    reviewer_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    professional_id INTEGER REFERENCES professional_profiles(id) ON DELETE CASCADE,
    
    -- Rating and feedback
    rating SMALLINT NOT NULL CHECK (rating >= 1 AND rating <= 5),
    comment TEXT CHECK (LENGTH(comment) <= 500),
    
    -- Moderation
    is_verified BOOLEAN DEFAULT TRUE,  -- Only verified bookings can review
    is_flagged BOOLEAN DEFAULT FALSE,  -- For inappropriate content
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for review queries
CREATE INDEX idx_reviews_professional ON reviews(professional_id);
CREATE INDEX idx_reviews_reviewer ON reviews(reviewer_id);
CREATE INDEX idx_reviews_booking ON reviews(booking_id);
CREATE INDEX idx_reviews_rating ON reviews(rating);
CREATE INDEX idx_reviews_created ON reviews(created_at DESC);

-- Composite index for professional rating calculation
CREATE INDEX idx_reviews_professional_rating 
ON reviews(professional_id, rating)
WHERE is_verified = TRUE AND is_flagged = FALSE;

-- Constraint: One review per booking
CREATE UNIQUE INDEX idx_reviews_one_per_booking ON reviews(booking_id);

COMMENT ON TABLE reviews IS 'Customer reviews and ratings for professionals';
COMMENT ON COLUMN reviews.rating IS 'Star rating: 1-5 stars';
```

**Average Rating Calculation (Materialized View for Performance):**
```sql
-- Create materialized view for fast rating lookups
CREATE MATERIALIZED VIEW professional_ratings_summary AS
SELECT 
    professional_id,
    COUNT(*) as total_reviews,
    AVG(rating) as average_rating,
    COUNT(*) FILTER (WHERE rating = 5) as five_star_count,
    COUNT(*) FILTER (WHERE rating = 4) as four_star_count,
    COUNT(*) FILTER (WHERE rating = 3) as three_star_count,
    COUNT(*) FILTER (WHERE rating = 2) as two_star_count,
    COUNT(*) FILTER (WHERE rating = 1) as one_star_count
FROM reviews
WHERE is_verified = TRUE AND is_flagged = FALSE
GROUP BY professional_id;

-- Index on materialized view
CREATE UNIQUE INDEX idx_ratings_summary_professional 
ON professional_ratings_summary(professional_id);

-- Refresh strategy: Update after each new review
CREATE OR REPLACE FUNCTION refresh_ratings_summary()
RETURNS TRIGGER AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY professional_ratings_summary;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_refresh_ratings
AFTER INSERT OR UPDATE OR DELETE ON reviews
FOR EACH STATEMENT
EXECUTE FUNCTION refresh_ratings_summary();
```

---

### 7. Location Hierarchy Tables

```sql
-- ============================================
-- PROVINCES TABLE
-- Nepal's 7 provinces
-- ============================================
CREATE TABLE provinces (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL
);

-- Sample data
INSERT INTO provinces (name) VALUES
('Province No. 1'),
('Madhesh Province'),
('Bagmati Province'),
('Gandaki Province'),
('Lumbini Province'),
('Karnali Province'),
('Sudurpashchim Province');

-- ============================================
-- DISTRICTS TABLE
-- 77 districts of Nepal
-- ============================================
CREATE TABLE districts (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    province_id INTEGER REFERENCES provinces(id) ON DELETE CASCADE,
    UNIQUE(name, province_id)
);

CREATE INDEX idx_districts_province ON districts(province_id);
CREATE INDEX idx_districts_name ON districts(name);

-- ============================================
-- MUNICIPALITIES TABLE
-- Local municipalities with ward counts
-- ============================================
CREATE TABLE municipalities (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    district_id INTEGER REFERENCES districts(id) ON DELETE CASCADE,
    ward_count INTEGER DEFAULT 35 CHECK (ward_count > 0 AND ward_count <= 50),
    UNIQUE(name, district_id)
);

CREATE INDEX idx_municipalities_district ON municipalities(district_id);
CREATE INDEX idx_municipalities_name ON municipalities(name);

COMMENT ON TABLE municipalities IS 'Local municipalities with ward information';
COMMENT ON COLUMN municipalities.ward_count IS 'Number of wards in this municipality';
```

---

### 8. Admin and Audit Tables

```sql
-- ============================================
-- ADMIN ACTIONS LOG
-- Track all admin decisions
-- ============================================
CREATE TABLE admin_actions (
    id SERIAL PRIMARY KEY,
    admin_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    action_type VARCHAR(50) NOT NULL CHECK (action_type IN (
        'approve_professional', 'reject_professional', 
        'toggle_availability', 'cancel_booking', 'refund_payment'
    )),
    target_type VARCHAR(50) NOT NULL,  -- 'professional', 'booking', etc.
    target_id INTEGER NOT NULL,
    reason TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_admin_actions_admin ON admin_actions(admin_id);
CREATE INDEX idx_admin_actions_type ON admin_actions(action_type);
CREATE INDEX idx_admin_actions_created ON admin_actions(created_at DESC);

-- ============================================
-- SYSTEM CONFIGURATION
-- Dynamic configuration values
-- ============================================
CREATE TABLE system_config (
    key VARCHAR(100) PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Default configuration
INSERT INTO system_config (key, value, description) VALUES
('booking_advance_minutes', '30', 'Minimum advance booking time in minutes'),
('booking_gap_minutes', '30', 'Required gap between consecutive bookings'),
('booking_start_hour', '6', 'Earliest booking hour (24-hour format)'),
('booking_end_hour', '20', 'Latest booking start hour (24-hour format)'),
('deposit_percentage', '10', 'Deposit percentage of total fee'),
('max_skills_per_professional', '3', 'Maximum skills a professional can have'),
('emergency_surcharge_percentage', '50', 'Emergency booking surcharge percentage');
```

---

### 9. Enhanced Features Tables (Optional)

```sql
-- ============================================
-- SUBSCRIPTIONS TABLE
-- Monthly subscription plans
-- ============================================
CREATE TABLE subscriptions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    plan_type VARCHAR(20) NOT NULL CHECK (plan_type IN ('basic', 'premium', 'business')),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    auto_renew BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_subscriptions_user ON subscriptions(user_id);
CREATE INDEX idx_subscriptions_active ON subscriptions(is_active) WHERE is_active = TRUE;

-- ============================================
-- GROUP BOOKINGS TABLE
-- Multi-client group bookings
-- ============================================
CREATE TABLE group_bookings (
    id SERIAL PRIMARY KEY,
    organizer_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    professional_id INTEGER REFERENCES professional_profiles(id) ON DELETE CASCADE,
    scheduled_time TIMESTAMP WITH TIME ZONE NOT NULL,
    total_duration_hours FLOAT NOT NULL,
    group_size INTEGER NOT NULL CHECK (group_size >= 2 AND group_size <= 5),
    discount_applied DECIMAL(5, 2) NOT NULL,  -- e.g., 0.15 for 15%
    total_cost DECIMAL(10, 2) NOT NULL,
    cost_per_person DECIMAL(10, 2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending_confirmation'
        CHECK (status IN ('pending_confirmation', 'confirmed', 'cancelled')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE group_booking_participants (
    group_booking_id INTEGER REFERENCES group_bookings(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    has_confirmed BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (group_booking_id, user_id)
);

-- ============================================
-- EMERGENCY REQUESTS TABLE
-- Urgent service requests
-- ============================================
CREATE TABLE emergency_requests (
    id SERIAL PRIMARY KEY,
    client_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    skill_required VARCHAR(100) NOT NULL,
    location JSONB NOT NULL,  -- {latitude, longitude}
    urgency_level VARCHAR(20) NOT NULL CHECK (urgency_level IN ('urgent', 'critical')),
    description TEXT,
    emergency_rate DECIMAL(10, 2) NOT NULL,
    notified_professionals INTEGER[],  -- Array of professional IDs
    accepted_by INTEGER REFERENCES professional_profiles(id),
    status VARCHAR(30) DEFAULT 'waiting_for_acceptance'
        CHECK (status IN ('waiting_for_acceptance', 'accepted', 'expired', 'cancelled')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL
);

CREATE INDEX idx_emergency_status ON emergency_requests(status);
CREATE INDEX idx_emergency_created ON emergency_requests(created_at DESC);
```

---

## 🔧 Database Setup Commands

### 1. Install PostgreSQL Extensions

```sql
-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For fuzzy text search
CREATE EXTENSION IF NOT EXISTS "earthdistance";  -- For geospatial calculations
CREATE EXTENSION IF NOT EXISTS "cube";  -- Required by earthdistance
```

### 2. Create Database and User

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE service_manpower_fastapi;

# Create user (optional, for security)
CREATE USER fastapi_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE service_manpower_fastapi TO fastapi_user;

# Connect to the database
\c service_manpower_fastapi

# Grant schema permissions
GRANT ALL ON SCHEMA public TO fastapi_user;
```

### 3. Run Schema Migration

```bash
# Save the schema to a file
# Then run:
psql -U postgres -d service_manpower_fastapi -f schema.sql
```

### 4. Verify Installation

```sql
-- Check tables
\dt

-- Check indexes
SELECT tablename, indexname FROM pg_indexes WHERE schemaname = 'public';

-- Test geospatial function
SELECT earth_distance(
    ll_to_earth(27.7172, 85.3240),  -- Kathmandu
    ll_to_earth(27.6976, 85.3206)   -- Lalitpur
) / 1000 AS distance_km;
```

---

## 📈 Performance Optimization Tips

### 1. Connection Pooling

```python
# Use asyncpg connection pool in FastAPI
from databases import Database

DATABASE_URL = "postgresql://user:password@localhost/service_manpower_fastapi"

database = Database(
    DATABASE_URL,
    min_size=5,   # Minimum connections
    max_size=20,  # Maximum connections
    pool_recycle=3600  # Recycle connections after 1 hour
)
```

### 2. Query Optimization Examples

```python
# ✅ GOOD: Use specific columns instead of SELECT *
async def get_professionals():
    query = """
        SELECT id, user_id, rate, latitude, longitude, average_rating
        FROM professional_profiles
        WHERE verification_status = 'APPROVED'
          AND is_available = TRUE
    """
    return await database.fetch_all(query)

# ❌ BAD: Selecting all columns
async def get_professionals_bad():
    return await database.fetch_all("SELECT * FROM professional_profiles")
```

### 3. Batch Operations

```python
# ✅ GOOD: Batch insert for multiple skills
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

# ❌ BAD: Individual inserts in loop
for skill_id in skill_ids:
    await database.execute(query, {...})
```

### 4. Caching Strategy

```python
# Cache frequently accessed data in Redis
import aioredis

redis = aioredis.from_url("redis://localhost")

async def get_professional_cached(professional_id: int):
    # Try cache first
    cached = await redis.get(f"professional:{professional_id}")
    if cached:
        return json.loads(cached)
    
    # Fetch from database
    professional = await fetch_from_db(professional_id)
    
    # Cache for 1 hour
    await redis.setex(
        f"professional:{professional_id}",
        3600,
        json.dumps(professional)
    )
    
    return professional
```

---

## 🔐 Security Considerations

### 1. Row-Level Security (RLS)

```sql
-- Enable RLS for sensitive tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only view their own data
CREATE POLICY users_view_own ON users
    FOR SELECT
    USING (auth.uid() = id);

-- Policy: Professionals can update their own profile
CREATE POLICY professionals_update_own ON professional_profiles
    FOR UPDATE
    USING (auth.uid() = user_id);
```

### 2. Data Encryption

```python
# Encrypt sensitive data at rest
from cryptography.fernet import Fernet

cipher = Fernet(os.getenv('ENCRYPTION_KEY'))

def encrypt_data(data: str) -> bytes:
    return cipher.encrypt(data.encode())

def decrypt_data(encrypted: bytes) -> str:
    return cipher.decrypt(encrypted).decode()
```

### 3. SQL Injection Prevention

```python
# ✅ SAFE: Parameterized queries
query = "SELECT * FROM users WHERE phone_number = $1"
result = await database.fetch_one(query, phone_number)

# ❌ DANGEROUS: String formatting
query = f"SELECT * FROM users WHERE phone_number = '{phone_number}'"
```

---

## 📊 Monitoring and Maintenance

### 1. Database Statistics

```sql
-- Check table sizes
SELECT 
    table_name,
    pg_size_pretty(pg_total_relation_size(table_name)) AS size
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY pg_total_relation_size(table_name) DESC;

-- Check index usage
SELECT 
    schemaname,
    relname AS table_name,
    indexrelname AS index_name,
    idx_scan AS times_used,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;

-- Find slow queries
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    rows
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
```

### 2. Regular Maintenance

```sql
-- Vacuum and analyze (run weekly)
VACUUM ANALYZE;

-- Reindex (run monthly)
REINDEX DATABASE service_manpower_fastapi;

-- Update statistics
ANALYZE;
```

### 3. Backup Strategy

```bash
# Daily backup (cron job)
0 2 * * * pg_dump -U postgres service_manpower_fastapi > /backups/db_$(date +\%Y\%m\%d).sql

# Restore from backup
psql -U postgres service_manpower_fastapi < /backups/db_20240101.sql
```

---

## 🎯 Next Steps

Now that you have the complete database schema:

1. ✅ Set up PostgreSQL and create the database
2. ✅ Run the schema SQL to create all tables
3. ✅ Insert sample data for testing
4. ✅ Proceed to **03-AUTHENTICATION.md** for JWT setup

**Ready for authentication?** ➡️ See `03-AUTHENTICATION.md`
