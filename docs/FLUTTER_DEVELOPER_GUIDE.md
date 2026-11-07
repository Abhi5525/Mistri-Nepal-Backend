# Mistri Nepal Flutter Developer Guide

## Platform scope

Mistri Nepal is one Flutter mobile application with role-based UI:

- **Client UI**: discovers professionals, creates bookings, pays, and reviews completed services.
- **Professional UI**: completes onboarding, manages a professional profile, and manages received bookings.

Both roles are delivered from the same mobile codebase and app binary. After
authentication, the app reads the user's role and selects the appropriate
navigation shell, dashboard, routes, permissions, and actions. Shared features
such as authentication, profile settings, uploads, notifications, and booking
details should be implemented once and reused by both role-specific sections.

The **Admin experience is a separate web panel**. Do not add Admin navigation,
Admin screens, or Admin-only actions to the Flutter mobile application. The web
panel uses an admin account and the same `/api/v1` backend to review records,
manage users and professionals, and approve or reject professional applications.

## Product purpose

Mistri Nepal connects customers with local service professionals across Nepal.
The single mobile app supports professional discovery, location-based search,
professional onboarding, booking, payment, and reviews. The backend is a
FastAPI service backed by PostgreSQL.

## Current backend capabilities

All routes below are prefixed with `/api/v1`.

### Shared mobile features

- `POST /auth/register` and `POST /auth/login` for phone-based authentication.
- `GET /users/me` and `PUT /users/me` for the current user's profile.
- `POST /file/upload` for multipart uploads backed by Cloudinary.
- `GET /skills` for the paginated skill catalog.
- `GET /professionals/{profile_id}` for professional details.
- `GET /professionals/search/location` for district and optional skill search.

### Client features

- `POST /booking` creates a booking with professional, start/end time, notes,
  and customer location.
- `GET /booking/me` lists the client's bookings.
- `GET /booking/{booking_id}` returns an authorized booking.
- `POST /payments/initiate` starts an eSewa or Khalti payment.
- `POST /payments/verify` verifies the provider result.
- `POST /reviews/{booking_id}/rate` submits a 1-5 rating.
- `POST /reviews/{booking_id}/text` submits written feedback.
- `GET /reviews/professional/{profile_id}` lists professional reviews.

### Professional features

- `POST /professionalApplication` submits an application after document
  uploads.
- `GET /professionalApplication/me` reads the current application status.
- `GET /professionals/me` and `PUT /professionals/me` manage the professional
  profile after approval.
- `GET /booking/professional/me` lists bookings received by the professional.
- `PATCH /booking/{booking_id}/status` updates booking status.
- `PATCH /booking/{booking_id}/payment` updates booking payment details.

### Admin web-panel features

These are for the separate web panel, not Flutter:

- `GET /professionalApplication` lists applications with pagination and filters.
- `PATCH /professionalApplication/{application_id}/status` approves or rejects
  an application and promotes an approved applicant to `PROFESSIONAL`.
- Admin-only user and professional record lookup and management routes.
- `GET /professionals/admin/pending` lists pending professional profiles.

Booking, payment, and review modules were recently added to the backend. The
current API does **not** expose the previously proposed tracking WebSocket,
in-app chat, arrival OTP, or live FCM workflow. Do not present those as
implemented features in the mobile app until corresponding backend routes are
added.

## Flutter architecture

Use Riverpod or BLoC/Cubit with a layered structure:

```text
Data -> Domain -> Presentation
```

Keep API models immutable and generate serialization code with
`freezed`/`json_serializable` where appropriate. Use one mobile router with
role guards. It should select a Client or Professional shell after login,
while keeping shared routes outside both shells:

```text
lib/
├── main.dart
├── config/
│   ├── api_config.dart
│   ├── app_theme.dart
│   └── routes.dart
├── core/
│   ├── network/
│   │   ├── dio_client.dart
│   │   ├── api_interceptors.dart
│   │   └── error_handler.dart
│   ├── storage/
│   │   └── secure_storage.dart
│   └── utils/
├── features/
│   ├── auth/
│   ├── shared/
│   │   ├── profile/
│   │   ├── booking_details/
│   │   └── file_upload/
│   ├── client/                    # Client-only screens and navigation
│   │   ├── discovery/
│   │   ├── professional_profile/
│   │   ├── booking/
│   │   ├── payment/
│   │   └── reviews/
│   └── professional/              # Professional-only screens and navigation
│       ├── application/
│       ├── profile/
│       └── bookings/
└── widgets/
```

## Authentication

Store access and refresh tokens in Flutter Secure Storage. Configure a Dio
interceptor to attach `Authorization: Bearer <access-token>` and handle `401`
responses. If refresh is unavailable or rejected, clear credentials and route
the user to login.

The API uses the role values `CLIENT`, `PROFESSIONAL`, and `ADMIN`. `CLIENT`
and `PROFESSIONAL` select role-based UI within the same app. `ADMIN` must be
rejected by the mobile router and directed to the separate web-panel flow
rather than rendered as a mobile dashboard.

If a client applies to become a professional, keep the user in the same app
while showing application status screens. Only show the Professional shell
after the backend has approved the application and the authenticated role is
`PROFESSIONAL`. Do not create a second professional app.

## Uploading professional documents

1. Capture or select documents with `image_picker`/`camera`.
2. Compress images locally and keep uploads within the configured 5 MB limit.
3. Upload each file to `POST /api/v1/file/upload`.
4. Send the returned file reference in the
   `POST /api/v1/professionalApplication` payload.

## Payment flow

1. Call `POST /api/v1/payments/initiate` with `booking_id`, `payment_method`
   (`ESEWA` or `KHALTI`), and the required `payment_type`.
2. Open the returned eSewa payload or Khalti `payment_url`.
3. After the provider completes, call `POST /api/v1/payments/verify`.
4. Send `esewa_data` for eSewa or `pidx` for Khalti.

Do not generate payment signatures in Flutter; payment initialization and
verification belong to the backend.

## Local caching and permissions

Use `connectivity_plus` with Hive or Isar only for read caching and resilient
UI states. Do not queue a booking or payment as successful while offline.
Request location permission only for discovery/search experiences that need it.
The current backend supports district-based professional search; a live map or
background tracking UI requires a future backend location contract.

## UI implementation guidance

Use the companion [Google Stitch UI specification](./GOOGLE_STITCH_UI_SPEC.json)
for visual tokens and screen prompts. The mobile UI specification covers only
Client and Professional screens. Admin tables, application review, filters,
and record details belong in the separate web-panel design system.
