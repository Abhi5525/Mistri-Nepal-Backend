# 📱 Mistri Nepal - Flutter Mobile App Developer Guide & Architecture Overview

---

## 📌 Executive Summary & Project Objectives

**App Name**: **Mistri Nepal** (formerly *Service Manpower*)  
**Platform Scope**: iOS & Android Mobile Applications built with Flutter (3.19+)  
**Backend API**: FastAPI (Python 3.10+, PostgreSQL, Redis, Cloudinary, eSewa, Firebase FCM)

### 🎯 Primary Objectives
**Mistri Nepal** is an on-demand local service marketplace platform designed to bridge the gap between household/commercial clients and vetted skilled local professionals (*Mistris*—plumbers, electricians, carpenters, mechanics, painters, HVAC technicians, etc.) across Nepal.

Key Platform Objectives:
1. **Instant & Proximity-Based Discovery**: Enable clients to find verified professionals near their exact GPS coordinates within seconds.
2. **Transparent Booking & Time Slot Management**: Provide real-time availability calendar slots with automatic conflict detection and buffer time rules.
3. **Vetted Professional Network (KYC Verification)**: Streamline professional onboarding through mandatory document upload (Citizenship card, Licenses, Skill certificates) and manual/automated Admin review.
4. **Secure Digital Payments (eSewa)**: Support 10% advance deposit payments via Nepal’s leading digital wallet (eSewa) to confirm bookings and prevent client no-shows.
5. **Real-time Proximity & Updates**: Provide live GPS tracking of moving professionals, WebSocket alerts, and Firebase Push Notifications for booking state changes.
6. **Trust & Quality Assurance**: Ratings, reviews, emergency service modes, and transparent pricing structures.

---

## 👥 User Roles & Core Workflows

The application handles three distinct user roles within a unified/role-switched Flutter mobile application or modular app architecture:

```
                          ┌───────────────────────────┐
                          │   Mistri Nepal Flutter    │
                          └─────────────┬─────────────┘
                                        │
           ┌────────────────────────────┼────────────────────────────┐
           ▼                            ▼                            ▼
┌─────────────────────┐      ┌─────────────────────┐      ┌─────────────────────┐
│     CLIENT ROLE     │      │  PROFESSIONAL ROLE  │      │     ADMIN ROLE      │
├─────────────────────┤      ├─────────────────────┤      ├─────────────────────┤
│ • Search nearby tech│      │ • KYC Application   │      │ • Review KYC apps   │
│ • Select time slot  │      │ • Availability toggle│     │ • Approve/Reject    │
│ • Pay 10% deposit   │      │ • Accept/Decline job│      │ • Platform metrics  │
│ • Live GPS tracking │      │ • Navigation & OTP  │      │ • Dispute audit     │
│ • Post service review│     │ • Earnings ledger   │      │ • User management   │
└─────────────────────┘      └─────────────────────┘      └─────────────────────┘
```

---

## 🔍 Codebase Implementation Status vs. Documentation Roadmap

The backend codebase is actively transitioning from a legacy Django application to a modern, async **FastAPI** architecture. Below is the state of implementation:

### 🟢 Fully Implemented in FastAPI Backend (`app/modules/`)
* **Authentication (`app/modules/auth`)**: JWT access/refresh token generation, password hashing (Bcrypt), phone number login/register.
* **User Management (`app/modules/users`)**: Profile fetch, updates, role assignment (`CLIENT`, `PROFESSIONAL`, `ADMIN`).
* **Media & Cloud Storage (`app/modules/file` & `app/modules/cloudinary`)**: Multipart file uploads to Cloudinary for user avatars and document images.
* **Skill Catalog (`app/modules/skills`)**: Skill definitions, categories, icon metadata.
* **Professional KYC Applications (`app/modules/professional_applications`)**: Application submission, status tracking (`PENDING`, `APPROVED`, `REJECTED`), and Admin approval endpoint promoting users to `PROFESSIONAL` role.
* **Professional Profiles (`app/modules/professionals`)**: Profile queries, bio, skills linking.

### 🟡 Specified in Documentation (`docs/`) & Remaining for Implementation
*(Developers should reference the indicated `docs/` files when integrating these APIs)*:
* **Booking Engine & Slot Management** (`docs/07-BOOKING-SYSTEM.md` & `app/modules/booking/models.py`): Time slot generation, 30-minute buffer enforcement, advance booking rules, status state machine (`PENDING` ➔ `ACCEPTED` ➔ `IN_PROGRESS` ➔ `COMPLETED` / `CANCELLED`).
* **Geospatial & Distance Queries** (`docs/06-LOCATION-SERVICES.md`): Haversine distance calculations, radius searches using PostgreSQL `earthdistance`, and OSRM route duration estimates.
* **eSewa Payment Integration** (`docs/08-PAYMENT-INTEGRATION.md`): eSewa ePay v2 HMAC-SHA256 signature generation, transaction verification callbacks, 10% deposit calculations.
* **Real-time WebSockets & FCM Push Notifications** (`docs/11-REALTIME-FEATURES.md`): WebSocket endpoint `/ws/tracking/{booking_id}` for live GPS streaming and Firebase Cloud Messaging payload handlers.
* **Ratings & Review System** (`docs/09-RATING-REVIEWS.md`): 1-to-5 star ratings, feedback comments, automatic recalculation of professional rating score.
* **Enhanced Modules** (`docs/15-ENHANCED-FEATURES.md`): Dynamic surge pricing multipliers, emergency priority service queue, neighbor group discounts, subscription memberships.

---

## 🛠️ Key Technical Considerations for Flutter Developers

### 1. State Management & Architecture
* **Recommended Pattern**: **Riverpod (v2.x)** with `AsyncNotifierProvider` or **BLoC / Cubit** with Clean Architecture layers (`Data` ➔ `Domain` ➔ `Presentation`).
* Keep UI components purely declarative, utilizing immutable state models generated via `freezed` or `json_serializable`.

### 2. Authentication Lifecycle & Token Management
* Store JWT Access Tokens and Refresh Tokens securely in **Flutter Secure Storage** (`Keychain` on iOS, `EncryptedSharedPreferences` on Android).
* Implement a **Dio Interceptor** for handling:
  * Injection of `Authorization: Bearer <access_token>` header on requests.
  * Automatic token refresh loop when HTTP `401 Unauthorized` is encountered.
  * Force logout & redirection to Login Screen if refresh token is expired or revoked.

### 3. Geolocation & Interactive Maps
* **Location Service**: Use `geolocator` plugin with fine location permissions (`ACCESS_FINE_LOCATION`).
* **Map Tile Rendering**: Use `flutter_map` with OpenStreetMap or GalliMaps tile servers (free, open source).
* **Background Tracking**: For professionals on active bookings, implement `workmanager` or `flutter_background_service` to stream lat/lng coordinates to the WebSocket endpoint `/ws/tracking/{booking_id}` every 10–30 seconds.

### 4. KYC Document Capture & Upload
* Use `image_picker` + `camera` for document scanning.
* Apply local client-side compression (e.g. `flutter_image_compress`) to limit payload sizes under 5MB.
* Upload image files via `/api/v1/file/upload` to receive a hosted Cloudinary URL before embedding the URL into the `/api/v1/professionalApplication` POST request payload.

### 5. eSewa Payment Integration Workflow
* Generate eSewa request parameters (including total amount, product code, unique transaction UUID, and HMAC-SHA256 signature) via backend endpoints.
* Open eSewa web gateway in a `webview_flutter` modal.
* Intercept redirect URLs (`success_url` and `failure_url`). Upon detecting a successful redirect, trigger backend verification `/api/v1/payment/esewa/verify`.

### 6. Offline Support & Local Caching
* Use **Hive** or **Isar** database for offline caching:
  * Cache client booking list, professional details, and skill catalogs for instant app launch.
  * Queue offline actions (e.g., app reviews, booking requests) and flush them when `connectivity_plus` detects connection restoration.

---

## 📱 Folder Structure for Flutter Project

```
lib/
├── main.dart                       # Entry point (ProviderScope / Global overrides)
├── config/
│   ├── api_config.dart             # API base URL (/api/v1), timeout constants
│   ├── app_theme.dart              # Color tokens, Google Fonts typography, dark mode
│   └── routes.dart                 # GoRouter configuration & role guards
├── core/
│   ├── network/
│   │   ├── dio_client.dart         # Custom Dio setup
│   │   ├── api_interceptors.dart   # Auth token injection & refresh handler
│   │   └── error_handler.dart      # Standardized failure handling
│   ├── storage/
│   │   ├── secure_storage.dart     # JWT token storage
│   │   └── hive_storage.dart       # Offline box definitions
│   └── utils/
│       ├── distance_formatter.dart # Format meters/kilometers
│       └── currency_formatter.dart # NPR (रु) currency formatting
├── features/
│   ├── auth/                       # Login, Register, Forgot Password
│   ├── kyc_registration/           # Professional application flow & file picker
│   ├── home_discovery/             # Category browser, search, radius filter map
│   ├── professional_profile/       # Bio, skills list, portfolio, reviews
│   ├── booking/                    # Slot picker, address map, confirmation
│   ├── tracking/                   # Real-time WebSocket map & status updates
│   ├── payment/                    # eSewa WebView controller & verification
│   └── reviews/                    # Rating dialog & customer feedback
└── widgets/                        # Shared reusable widgets (Buttons, Shimmers, Cards)
```
