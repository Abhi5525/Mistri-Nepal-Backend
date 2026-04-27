# 11-REALTIME-FEATURES.md

# Real-Time Features - WebSockets & Push Notifications

## 📋 Overview

Implement real-time communication using WebSockets for live tracking and Firebase Cloud Messaging (FCM) for push notifications.

---

## 🔌 WebSocket Implementation

### `app/websockets/chat.py`

```python
from fastapi import WebSocket, WebSocketDisconnect, Depends
from typing import Dict, List
import json
import asyncio
from datetime import datetime

class ConnectionManager:
    """Manage WebSocket connections"""
    
    def __init__(self):
        # Store connections: room_id -> list of websockets
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, room_id: str):
        """Connect to a room"""
        await websocket.accept()
        
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        
        self.active_connections[room_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, room_id: str):
        """Disconnect from a room"""
        if room_id in self.active_connections:
            if websocket in self.active_connections[room_id]:
                self.active_connections[room_id].remove(websocket)
            
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send message to specific websocket"""
        await websocket.send_text(message)
    
    async def broadcast(self, message: str, room_id: str):
        """Broadcast message to all connections in a room"""
        if room_id in self.active_connections:
            disconnected = []
            
            for connection in self.active_connections[room_id]:
                try:
                    await connection.send_text(message)
                except Exception:
                    disconnected.append(connection)
            
            # Remove disconnected clients
            for conn in disconnected:
                self.disconnect(conn, room_id)

# Global manager instance
manager = ConnectionManager()

@app.websocket("/ws/chat/{booking_id}")
async def websocket_chat_endpoint(
    websocket: WebSocket,
    booking_id: int
):
    """
    WebSocket endpoint for real-time chat between client and professional
    Room ID format: chat:{booking_id}
    """
    
    room_id = f"chat:{booking_id}"
    await manager.connect(websocket, room_id)
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Add metadata
            enriched_message = {
                "type": "chat_message",
                "booking_id": booking_id,
                "sender_id": message_data.get("sender_id"),
                "message": message_data.get("message"),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Save to database
            await save_chat_message(
                booking_id=booking_id,
                sender_id=message_data.get("sender_id"),
                message=message_data.get("message")
            )
            
            # Broadcast to all participants
            await manager.broadcast(
                json.dumps(enriched_message),
                room_id
            )
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)

@app.websocket("/ws/tracking/{booking_id}")
async def websocket_tracking_endpoint(
    websocket: WebSocket,
    booking_id: int
):
    """
    WebSocket endpoint for live location tracking
    Professional sends updates, client receives them
    """
    
    room_id = f"tracking:{booking_id}"
    await manager.connect(websocket, room_id)
    
    try:
        while True:
            # Receive location update
            data = await websocket.receive_json()
            
            location_update = {
                "type": "location_update",
                "booking_id": booking_id,
                "latitude": data.get("latitude"),
                "longitude": data.get("longitude"),
                "accuracy": data.get("accuracy", 0),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Update professional location in database
            await update_professional_location(
                booking_id=booking_id,
                latitude=data.get("latitude"),
                longitude=data.get("longitude")
            )
            
            # Broadcast to client
            await manager.broadcast(
                json.dumps(location_update),
                room_id
            )
            
            # Rate limit (max 1 update per second)
            await asyncio.sleep(1)
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)
```

---

## 📱 Push Notifications with Firebase FCM

### Setup Firebase

1. Create Firebase project at https://console.firebase.google.com
2. Download `serviceAccountKey.json`
3. Install Firebase Admin SDK:

```bash
pip install firebase-admin
```

### `app/services/notification_service.py`

```python
import firebase_admin
from firebase_admin import credentials, messaging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from typing import Optional, Dict

# Initialize Firebase Admin (only once)
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

class NotificationService:
    """Firebase Cloud Messaging push notifications"""
    
    @staticmethod
    async def send_push_notification(
        user_id: int,
        title: str,
        body: str,
        data: Optional[Dict] = None,
        image_url: Optional[str] = None
    ) -> bool:
        """Send push notification to user's device"""
        
        # Get user's FCM token
        from app.database import get_db
        
        async for db in get_db():
            result = await db.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if not user or not user.fcm_token:
                return False
            
            # Build message
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                    image=image_url
                ),
                data=data or {},
                token=user.fcm_token,
                android=messaging.AndroidConfig(
                    priority='high',
                    notification=messaging.AndroidNotification(
                        sound='default',
                        color='#4CAF50'
                    )
                ),
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            sound='default',
                            badge=1
                        )
                    )
                )
            )
            
            try:
                # Send message
                response = messaging.send(message)
                print(f"Notification sent: {response}")
                return True
                
            except Exception as e:
                print(f"Failed to send notification: {e}")
                
                # Invalid token - remove it
                if 'invalid-registration-token' in str(e):
                    user.fcm_token = None
                    await db.flush()
                
                return False
    
    @staticmethod
    async def send_booking_confirmation(user_id: int, booking_id: int):
        """Send booking confirmation notification"""
        await NotificationService.send_push_notification(
            user_id=user_id,
            title="✅ Booking Confirmed!",
            body=f"Your booking #{booking_id} has been confirmed.",
            data={
                "type": "booking_confirmed",
                "booking_id": str(booking_id)
            }
        )
    
    @staticmethod
    async def send_professional_arrived(user_id: int, booking_id: int):
        """Notify client that professional has arrived"""
        await NotificationService.send_push_notification(
            user_id=user_id,
            title="🚗 Professional Arrived!",
            body="Your professional has arrived at your location.",
            data={
                "type": "professional_arrived",
                "booking_id": str(booking_id)
            }
        )
    
    @staticmethod
    async def send_payment_success(user_id: int, booking_id: int, amount: float):
        """Send payment success notification"""
        await NotificationService.send_push_notification(
            user_id=user_id,
            title="💰 Payment Successful!",
            body=f"Payment of Rs {amount:.2f} received.",
            data={
                "type": "payment_success",
                "booking_id": str(booking_id),
                "amount": str(amount)
            }
        )
    
    @staticmethod
    async def send_review_reminder(user_id: int, booking_id: int):
        """Send review reminder after service completion"""
        await NotificationService.send_push_notification(
            user_id=user_id,
            title="⭐ Rate Your Experience",
            body="How was your service? Please leave a review.",
            data={
                "type": "review_reminder",
                "booking_id": str(booking_id)
            }
        )
    
    @staticmethod
    async def send_emergency_alert(professional_user_id: int, details: Dict):
        """Send high-priority emergency service alert"""
        await NotificationService.send_push_notification(
            user_id=professional_user_id,
            title="🚨 Emergency Service Request",
            body=f"Urgent {details['skill']} needed nearby. Rate: Rs {details['rate']}/hr",
            data={
                "type": "emergency_request",
                **details
            }
        )
```

---

## 🌐 API Endpoints

### `app/api/notifications.py`

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import FCMTokenUpdate

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])

@router.post("/register-device")
async def register_device(
    token_data: FCMTokenUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Register device FCM token for push notifications"""
    
    current_user.fcm_token = token_data.fcm_token
    await db.flush()
    
    return {"message": "Device registered successfully"}

@router.post("/test-notification")
async def test_notification(
    current_user: User = Depends(get_current_user)
):
    """Send test notification to current user"""
    from app.services.notification_service import NotificationService
    
    await NotificationService.send_push_notification(
        user_id=current_user.id,
        title="Test Notification",
        body="This is a test notification from Service Manpower",
        data={"type": "test"}
    )
    
    return {"message": "Test notification sent"}
```

---

## 📱 Flutter Integration

### `lib/services/notification_service.dart`

```dart
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:dio/dio.dart';

class NotificationService {
  final Dio _dio;
  final FirebaseMessaging _firebaseMessaging = FirebaseMessaging.instance;
  final FlutterLocalNotificationsPlugin _localNotifications = 
      FlutterLocalNotificationsPlugin();
  
  NotificationService(this._dio);
  
  // Initialize notifications
  Future<void> initialize() async {
    // Request permission
    await _firebaseMessaging.requestPermission(
      alert: true,
      badge: true,
      sound: true,
    );
    
    // Get FCM token
    String? token = await _firebaseMessaging.getToken();
    if (token != null) {
      await _registerToken(token);
    }
    
    // Listen for token refresh
    _firebaseMessaging.onTokenRefresh.listen(_registerToken);
    
    // Handle foreground messages
    FirebaseMessaging.onMessage.listen(_handleForegroundMessage);
    
    // Handle background messages
    FirebaseMessaging.onBackgroundMessage(_firebaseMessagingBackgroundHandler);
    
    // Initialize local notifications
    await _initializeLocalNotifications();
  }
  
  Future<void> _registerToken(String token) async {
    try {
      await _dio.post('/api/notifications/register-device', data: {
        'fcm_token': token,
      });
      print('FCM token registered');
    } catch (e) {
      print('Failed to register FCM token: $e');
    }
  }
  
  void _handleForegroundMessage(RemoteMessage message) {
    print('Received foreground message: ${message.notification?.title}');
    
    // Show local notification
    _showLocalNotification(
      title: message.notification?.title ?? '',
      body: message.notification?.body ?? '',
      payload: message.data.toString(),
    );
  }
  
  Future<void> _initializeLocalNotifications() async {
    const AndroidInitializationSettings androidSettings = 
        AndroidInitializationSettings('@mipmap/ic_launcher');
    
    const DarwinInitializationSettings iOSSettings = 
        DarwinInitializationSettings();
    
    const InitializationSettings settings = InitializationSettings(
      android: androidSettings,
      iOS: iOSSettings,
    );
    
    await _localNotifications.initialize(settings);
  }
  
  Future<void> _showLocalNotification({
    required String title,
    required String body,
    String? payload,
  }) async {
    const AndroidNotificationDetails androidDetails = 
        AndroidNotificationDetails(
      'service_manpower_channel',
      'Service Manpower Notifications',
      importance: Importance.max,
      priority: Priority.high,
    );
    
    const DarwinNotificationDetails iOSDetails = 
        DarwinNotificationDetails();
    
    const NotificationDetails details = NotificationDetails(
      android: androidDetails,
      iOS: iOSDetails,
    );
    
    await _localNotifications.show(
      DateTime.now().millisecondsSinceEpoch ~/ 1000,
      title,
      body,
      details,
      payload: payload,
    );
  }
}

// Background message handler (must be top-level function)
@pragma('vm:entry-point')
Future<void> _firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  print('Handling background message: ${message.messageId}');
}

// Usage in main.dart
void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Firebase.initializeApp();
  
  final notificationService = NotificationService(Dio());
  await notificationService.initialize();
  
  runApp(MyApp());
}
```

---

## ✅ Testing

```python
# tests/test_websockets.py
import pytest
from fastapi.testclient import TestClient
from starlette.testclient import WebSocketTestSession

def test_chat_websocket(client):
    """Test WebSocket chat connection"""
    with client.websocket_connect("/ws/chat/1") as websocket:
        # Send message
        websocket.send_json({
            "sender_id": 1,
            "message": "Hello!"
        })
        
        # Receive broadcast
        data = websocket.receive_json()
        assert data["type"] == "chat_message"
        assert data["message"] == "Hello!"

@pytest.mark.asyncio
async def test_push_notification(client, auth_token):
    """Test sending push notification"""
    response = await client.post(
        "/api/notifications/test-notification",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 200
```

---

**Next:** Performance optimization ➡️ See `12-PERFORMANCE-OPTIMIZATION.md`
