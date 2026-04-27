# 01-PROJECT-OVERVIEW.md

# Service Manpower - FastAPI Backend Migration Guide

## 📋 Complete Project Overview

### Current System Analysis (Django)

Your current Django application is a **service marketplace platform** connecting clients with local professionals (plumbers, electricians, carpenters, etc.) featuring:

#### Core Features:
1. **User Management**: Phone-based authentication with CustomUser model
2. **Professional System**: Registration → Verification workflow (PENDING/APPROVED/REJECTED states)
3. **Location Services**: GPS-based professional search with distance calculation using geopy
4. **Booking Engine**: Time slot management with 30-minute gaps, advance booking rules (minimum 30 mins)
5. **Payment Gateway**: eSewa integration for 10% deposit payments
6. **Rating System**: Post-service reviews affecting professional rankings
7. **Admin Panel**: Professional verification and booking oversight
8. **Real-time Features**: Availability tracking and status updates

#### Technology Stack (Current):
- **Backend**: Django 4.2
- **Database**: PostgreSQL
- **Authentication**: Session-based + JWT (DRF SimpleJWT)
- **Maps**: OpenRouteService API + GalliMaps
- **Payment**: eSewa (Nepal)
- **File Storage**: Local media files
- **Frontend**: Django Templates (HTML/CSS/JS)

---

### Target Architecture (FastAPI + Flutter)

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│ Flutter App │◄───────►│  FastAPI     │◄───────►│ PostgreSQL  │
│ (iOS/Android)│  HTTPS  │  Backend     │ Async   │ Database    │
└─────────────┘         └──────┬───────┘         └─────────────┘
                               │
                    ┌──────────┴──────────┐
                    ▼                     ▼
              ┌──────────┐        ┌──────────────┐
              │  Redis   │        │  MinIO/S3    │
              │ Cache    │        │ File Storage │
              └──────────┘        └──────────────┘
                    │
                    ▼
              ┌──────────────┐
              │ Firebase FCM │
              │ Push Notifs  │
              └──────────────┘
```

---

## 🎯 Why FastAPI Over Django?

| Feature | Django | FastAPI | Benefit |
|---------|--------|---------|---------|
| **Performance** | Synchronous | Async/Await | 10x faster request handling |
| **API Design** | DRF needed | Native API | Cleaner, auto-documented |
| **Validation** | Forms/Serializers | Pydantic | Type-safe, automatic |
| **Documentation** | Manual | Auto-generated Swagger | Always up-to-date |
| **WebSockets** | Channels (complex) | Built-in | Real-time features easier |
| **Learning Curve** | Steep | Moderate | Faster development |
| **Mobile Integration** | Session-based | JWT tokens | Better for mobile apps |
| **Concurrency** | Limited | High | Handle 1000s of requests/sec |

### Performance Comparison:
- **Django**: ~100-200 requests/second
- **FastAPI**: ~1,000-2,000 requests/second (with async)
- **Response Time**: FastAPI is 5-10x faster for I/O operations

---

## 📱 Mobile-Only Features (Impossible in Web)

### 1. **Real-Time GPS Tracking** ⭐ NEW
**What You Can Build:**
- Live professional location during travel to client
- Turn-by-turn navigation integration
- ETA calculations with traffic data
- Geofencing alerts ("Professional is 500m away")

**Why Not Possible in Web:**
- Browsers limit background location access
- No continuous GPS when browser is closed
- Poor battery optimization
- Cannot run in background reliably

**Implementation Preview:**
```python
# WebSocket endpoint for live tracking
@app.websocket("/ws/tracking/{booking_id}")
async def track_location(websocket: WebSocket, booking_id: int):
    await websocket.accept()
    while True:
        # Receive GPS coordinates every 5 seconds
        location = await websocket.receive_json()
        # Broadcast to client app
        await broadcast_to_client(booking_id, location)
```

---

### 2. **Push Notifications** ⭐ NEW
**Use Cases:**
- Instant booking confirmations (< 1 second delivery)
- Payment success/failure alerts
- "Your professional has arrived" notifications
- Review reminders 24 hours after service
- Emergency service availability alerts

**Why Better Than Email/SMS:**
- Instant delivery (< 1 second vs minutes for email)
- Completely free (Firebase Cloud Messaging)
- Rich media support (images, action buttons)
- Works offline (queued until device is online)
- Higher engagement rates (90% vs 20% for email)

---

### 3. **Offline Mode** ⭐ NEW
**Features:**
- View upcoming bookings without internet
- Cached professional profiles and photos
- Queue booking requests (send when online)
- Offline maps for navigation
- Sync data when connection restored

**Technical Implementation:**
```dart
// Flutter Hive database for offline storage
@HiveType(typeId: 0)
class OfflineBooking {
  @HiveField(0) int id;
  @HiveField(1) String professionalName;
  @HiveField(2) DateTime bookingTime;
}
```

---

### 4. **Biometric Authentication** ⭐ NEW
- Fingerprint login (Android)
- Face ID / Face Unlock (iOS)
- Quick secure access (no password typing)
- Enhanced security

---

### 5. **Camera Integration for KYC** ⭐ ENHANCED
**Advanced Features:**
- Real-time image quality validation (blur detection)
- Auto-crop and perspective correction
- OCR for citizenship card text extraction
- Liveness detection (prevent photo-of-photo fraud)
- Front/back camera switching

---

### 6. **Background Location Services** ⭐ NEW
- Track professional location even when app is minimized
- Automatic check-in at client location
- Battery-optimized updates (every 30 seconds vs 5 seconds)
- Geofence triggers

---

### 7. **In-App Chat** ⭐ NEW
- Real-time messaging between client and professional
- Image/location sharing
- Automated responses ("I'm 10 minutes away")
- Message history stored locally
- Typing indicators

---

### 8. **Voice Commands** ⭐ NEW
- "Find plumbers near me" (voice search)
- Voice input for booking descriptions
- Accessibility for visually impaired users
- Hands-free operation

---

### 9. **QR Code Features** ⭐ NEW
- Quick professional profile scanning
- Contactless booking confirmation
- Digital business cards
- Payment verification codes

---

### 10. **Augmented Reality** (Future) ⭐ FUTURE
- AR preview of painting colors on walls
- Visual guides for DIY repairs
- Measure distances using camera
- Virtual furniture placement

---

## ✨ Enhanced Features (Better Than Current System)

The guide includes detailed implementations for:

1. **Intelligent Professional Ranking** - Multi-factor scoring (distance, rating, experience, response time)
2. **Dynamic Pricing Engine** - Demand-based pricing with surge multipliers
3. **Smart Scheduling Assistant** - AI-powered time slot suggestions
4. **Automated Dispute Resolution** - AI-assisted complaint handling
5. **Predictive Maintenance Reminders** - Automated recurring service suggestions
6. **Group Booking Discounts** - Neighbor group bookings with discounts
7. **Service Quality Analytics** - Professional performance dashboards
8. **Emergency Service Mode** - Priority booking for urgent needs
9. **Subscription Plans** - Monthly memberships with benefits
10. **Multi-Language Support** - English and Nepali (expandable)

---

## 📚 Documentation Structure

This guide is organized into separate files for easy navigation:

1. **01-PROJECT-OVERVIEW.md** ← You are here
2. **02-DATABASE-SCHEMA.md** - Complete PostgreSQL schema with indexes
3. **03-AUTHENTICATION.md** - JWT auth, password hashing, token management
4. **04-USER-MANAGEMENT.md** - CRUD operations, profile updates
5. **05-PROFESSIONAL-REGISTRATION.md** - KYC, verification workflow
6. **06-LOCATION-SERVICES.md** - Geospatial queries, distance calculation
7. **07-BOOKING-SYSTEM.md** - Time slots, conflict detection, scheduling
8. **08-PAYMENT-INTEGRATION.md** - eSewa integration, webhooks
9. **09-RATING-REVIEWS.md** - Rating system, review moderation
10. **10-ADMIN-PANEL.md** - Admin APIs, verification management
11. **11-REALTIME-FEATURES.md** - WebSockets, push notifications
12. **12-PERFORMANCE-OPTIMIZATION.md** - Caching, query optimization
13. **13-MOBILE-APP-GUIDE.md** - Flutter app structure, best practices
14. **14-DEPLOYMENT.md** - Production deployment, monitoring
15. **15-ENHANCED-FEATURES.md** - All 10 enhanced features with code

---

## 🛠️ Technology Stack (All Free & Open Source)

### Backend Technologies:

| Component | Technology | Purpose | Cost |
|-----------|-----------|---------|------|
| **Framework** | FastAPI 0.109+ | High-performance async web framework | Free |
| **Database** | PostgreSQL 15+ | Primary database with JSONB support | Free |
| **ORM** | SQLAlchemy 2.0+ (async) | Async database operations | Free |
| **Migration** | Alembic | Database schema migrations | Free |
| **Cache** | Redis 7+ | Session cache, rate limiting | Free |
| **Auth** | PyJWT + Passlib | JWT tokens, password hashing | Free |
| **Validation** | Pydantic 2.0+ | Request/response validation | Free |
| **File Storage** | MinIO | Self-hosted S3-compatible storage | Free |
| **Task Queue** | Celery + Redis | Background tasks | Free |
| **WebSocket** | FastAPI WebSocket | Real-time updates | Built-in |
| **Email** | SMTP (Gmail) | Email notifications | Free tier |
| **Maps** | OpenStreetMap + OSRM | Free routing and geocoding | Free |
| **Push Notifs** | Firebase FCM | Push notifications | Free |
| **Monitoring** | Prometheus + Grafana | Performance monitoring | Free |

### Mobile App Technologies:

| Component | Technology | Purpose | Cost |
|-----------|-----------|---------|------|
| **Framework** | Flutter 3.19+ | Cross-platform mobile development | Free |
| **State Management** | Riverpod or Bloc | State management | Free |
| **HTTP Client** | Dio | API communication | Free |
| **Maps** | flutter_map | Interactive maps | Free |
| **Location** | geolocator | GPS tracking | Free |
| **Notifications** | firebase_messaging | Push notifications | Free |
| **Local Storage** | Hive | Offline data storage | Free |
| **Camera** | camera + image_picker | KYC photo capture | Free |
| **Payment** | eSewa SDK / WebView | Payment integration | Free |

**Total Cost: $0** - Everything is free and open source!

---

## 🚀 Getting Started

### Prerequisites:
- Python 3.10+
- PostgreSQL 15+
- Redis 7+
- Flutter 3.19+ (for mobile app)
- Git

### Quick Start:
1. Read through all documentation files in order
2. Set up PostgreSQL and Redis
3. Follow `03-AUTHENTICATION.md` to set up auth
4. Implement core features following each guide
5. Test with Swagger UI (auto-generated at `/docs`)
6. Build Flutter app using `13-MOBILE-APP-GUIDE.md`
7. Deploy using `14-DEPLOYMENT.md`

---

## 📞 Support

For questions or issues while building:
- Check the detailed code examples in each file
- Refer to official FastAPI documentation: https://fastapi.tiangolo.com
- Flutter docs: https://flutter.dev/docs
- Community forums and Stack Overflow

---

**Ready to build? Let's start with the database schema!** ➡️ See `02-DATABASE-SCHEMA.md`
