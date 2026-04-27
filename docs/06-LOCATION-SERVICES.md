# 06-LOCATION-SERVICES.md

# Location Services & Geospatial Queries

## 📋 Overview

Complete location-based services including professional search by distance, real-time GPS tracking, and route calculation using free open-source tools.

---

## 🗺️ Technology Stack (All Free)

| Service | Purpose | Cost |
|---------|---------|------|
| **PostgreSQL earthdistance** | Distance calculations | Free |
| **OpenStreetMap (OSM)** | Map tiles & geocoding | Free |
| **OSRM (Open Source Routing Machine)** | Route calculation | Free (self-hosted) |
| **Nominatim** | Address geocoding | Free |
| **Flutter geolocator** | GPS tracking in app | Free |

---

## 🔧 Location Service Implementation

### `app/services/location_service.py`

```python
import math
from typing import List, Dict, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from app.models.professional import ProfessionalProfile
from app.models.skill import Skill

class LocationService:
    """Location-based services using PostgreSQL earthdistance"""
    
    EARTH_RADIUS_KM = 6371.0
    
    @staticmethod
    def calculate_distance(
        lat1: float, lon1: float,
        lat2: float, lon2: float
    ) -> float:
        """
        Calculate distance between two points using Haversine formula
        Returns distance in kilometers
        """
        # Convert to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Differences
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        # Haversine formula
        a = (math.sin(dlat/2)**2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        distance = LocationService.EARTH_RADIUS_KM * c
        return round(distance, 2)
    
    @staticmethod
    async def find_nearby_professionals(
        db: AsyncSession,
        latitude: float,
        longitude: float,
        radius_km: float = 10.0,
        skill_query: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """
        Find professionals within radius using PostgreSQL earthdistance
        Optimized query with proper indexing
        """
        
        # Build base query
        query = """
            SELECT 
                pp.id,
                pp.user_id,
                u.full_name,
                pp.rate,
                pp.experience,
                pp.average_rating,
                pp.total_reviews,
                pp.profile_picture,
                pp.latitude,
                pp.longitude,
                pp.is_available,
                earth_distance(
                    ll_to_earth(:user_lat, :user_lng),
                    ll_to_earth(pp.latitude, pp.longitude)
                ) / 1000 AS distance_km
            FROM professional_profiles pp
            JOIN users u ON pp.user_id = u.id
            WHERE pp.verification_status = 'APPROVED'
              AND pp.is_available = TRUE
              AND pp.latitude IS NOT NULL
              AND pp.longitude IS NOT NULL
              AND earth_box(ll_to_earth(:user_lat, :user_lng), :radius_meters) 
                  @> ll_to_earth(pp.latitude, pp.longitude)
        """
        
        params = {
            "user_lat": latitude,
            "user_lng": longitude,
            "radius_meters": radius_km * 1000
        }
        
        # Add skill filter if provided
        if skill_query:
            query += """
                AND pp.id IN (
                    SELECT DISTINCT ps.professional_id
                    FROM professional_skills ps
                    JOIN skills s ON ps.skill_id = s.id
                    WHERE s.name ILIKE :skill_query
                       OR s.category ILIKE :skill_query
                       OR s.aliases @> to_jsonb(array[:skill_query])
                )
            """
            params["skill_query"] = f"%{skill_query}%"
        
        # Order by distance and limit
        query += """
            ORDER BY distance_km ASC
            LIMIT :limit
        """
        params["limit"] = limit
        
        # Execute query
        result = await db.execute(text(query), params)
        rows = result.fetchall()
        
        # Format results
        professionals = []
        for row in rows:
            professionals.append({
                "id": row.id,
                "user_id": row.user_id,
                "name": row.full_name,
                "rate": row.rate,
                "experience": row.experience,
                "average_rating": row.average_rating,
                "total_reviews": row.total_reviews,
                "profile_picture": row.profile_picture,
                "latitude": row.latitude,
                "longitude": row.longitude,
                "is_available": row.is_available,
                "distance_km": row.distance_km
            })
        
        return professionals
    
    @staticmethod
    async def get_professional_distance(
        db: AsyncSession,
        professional_id: int,
        user_latitude: float,
        user_longitude: float
    ) -> float:
        """Get distance to specific professional"""
        
        result = await db.execute(
            select(ProfessionalProfile).where(ProfessionalProfile.id == professional_id)
        )
        profile = result.scalar_one_or_none()
        
        if not profile or not profile.latitude or not profile.longitude:
            return -1.0
        
        return LocationService.calculate_distance(
            user_latitude, user_longitude,
            profile.latitude, profile.longitude
        )
    
    @staticmethod
    async def update_professional_location(
        db: AsyncSession,
        user_id: int,
        latitude: float,
        longitude: float
    ) -> dict:
        """Update professional's current location (for live tracking)"""
        
        result = await db.execute(
            select(ProfessionalProfile).where(ProfessionalProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()
        
        if not profile:
            raise ValueError("Professional profile not found")
        
        profile.latitude = latitude
        profile.longitude = longitude
        await db.flush()
        
        return {"message": "Location updated", "latitude": latitude, "longitude": longitude}
```

---

## 🌐 API Endpoints

### `app/api/location.py`

```python
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.location_service import LocationService

router = APIRouter(prefix="/api/location", tags=["Location"])

@router.get("/professionals/nearby")
async def get_nearby_professionals(
    latitude: float = Query(..., description="User latitude"),
    longitude: float = Query(..., description="User longitude"),
    radius: float = Query(10.0, ge=1, le=50, description="Search radius in km"),
    skill: str = Query(None, description="Skill filter"),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Find nearby approved professionals"""
    professionals = await LocationService.find_nearby_professionals(
        db, latitude, longitude, radius, skill, limit
    )
    
    return {
        "count": len(professionals),
        "professionals": professionals
    }

@router.get("/distance/{professional_id}")
async def get_distance_to_professional(
    professional_id: int,
    latitude: float = Query(...),
    longitude: float = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """Calculate distance to specific professional"""
    distance = await LocationService.get_professional_distance(
        db, professional_id, latitude, longitude
    )
    
    if distance < 0:
        raise HTTPException(status_code=404, detail="Professional location not available")
    
    return {
        "professional_id": professional_id,
        "distance_km": distance
    }

@router.post("/update-location")
async def update_my_location(
    latitude: float,
    longitude: float,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update professional's current location (for live tracking)"""
    if not current_user.is_professional:
        raise HTTPException(status_code=403, detail="Not a professional")
    
    try:
        result = await LocationService.update_professional_location(
            db, current_user.id, latitude, longitude
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
```

---

## 🗺️ Route Calculation Service (OSRM)

### `app/services/route_service.py`

```python
import httpx
from typing import Dict, List, Optional

class RouteService:
    """Calculate routes using OSRM (Open Source Routing Machine)"""
    
    # Use public OSRM demo server (or self-host for production)
    OSRM_BASE_URL = "http://router.project-osrm.org/route/v1/driving"
    
    @staticmethod
    async def get_route(
        start_lat: float,
        start_lon: float,
        end_lat: float,
        end_lon: float
    ) -> Dict:
        """
        Get route between two points
        Returns distance, duration, and geometry
        """
        
        # OSRM expects coordinates in lon,lat format
        url = f"{RouteService.OSRM_BASE_URL}/{start_lon},{start_lat};{end_lon},{end_lat}"
        
        params = {
            "overview": "full",
            "geometries": "geojson",
            "steps": "true"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            
            if response.status_code != 200:
                return {"error": "Failed to calculate route"}
            
            data = response.json()
            
            if data["code"] != "Ok":
                return {"error": "No route found"}
            
            route = data["routes"][0]
            
            return {
                "distance_meters": route["distance"],
                "distance_km": round(route["distance"] / 1000, 2),
                "duration_seconds": route["duration"],
                "duration_minutes": round(route["duration"] / 60, 2),
                "geometry": route["geometry"],  # GeoJSON LineString
                "steps": [
                    {
                        "instruction": step["maneuver"]["instruction"],
                        "distance": step["distance"],
                        "duration": step["duration"]
                    }
                    for step in route["legs"][0]["steps"]
                ]
            }
    
    @staticmethod
    async def get_eta(
        start_lat: float,
        start_lon: float,
        end_lat: float,
        end_lon: float,
        current_speed_kmh: float = 30.0
    ) -> Dict:
        """
        Calculate ETA considering traffic
        current_speed_kmh: Average speed (default 30 km/h for city)
        """
        
        route = await RouteService.get_route(
            start_lat, start_lon, end_lat, end_lon
        )
        
        if "error" in route:
            return route
        
        # Calculate ETA based on distance and speed
        distance_km = route["distance_km"]
        eta_minutes = (distance_km / current_speed_kmh) * 60
        
        # Add buffer for traffic (20%)
        eta_with_traffic = eta_minutes * 1.2
        
        return {
            "distance_km": distance_km,
            "eta_minutes": round(eta_minutes, 2),
            "eta_with_traffic_minutes": round(eta_with_traffic, 2),
            "route_geometry": route["geometry"]
        }
```

---

## 📍 Geocoding Service (Nominatim)

### `app/services/geocoding_service.py`

```python
import httpx
from typing import Optional, Dict

class GeocodingService:
    """Convert addresses to coordinates using Nominatim (OpenStreetMap)"""
    
    NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
    
    @staticmethod
    async def geocode_address(address: str) -> Optional[Dict]:
        """
        Convert address to latitude/longitude
        Example: "Kathmandu, Nepal"
        """
        
        params = {
            "q": address,
            "format": "json",
            "limit": 1
        }
        
        headers = {
            "User-Agent": "ServiceManpowerApp/1.0"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                GeocodingService.NOMINATIM_URL,
                params=params,
                headers=headers
            )
            
            if response.status_code != 200:
                return None
            
            results = response.json()
            
            if not results:
                return None
            
            location = results[0]
            
            return {
                "latitude": float(location["lat"]),
                "longitude": float(location["lon"]),
                "display_name": location["display_name"]
            }
    
    @staticmethod
    async def reverse_geocode(
        latitude: float,
        longitude: float
    ) -> Optional[str]:
        """
        Convert coordinates to address
        """
        
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {
            "lat": latitude,
            "lon": longitude,
            "format": "json"
        }
        
        headers = {
            "User-Agent": "ServiceManpowerApp/1.0"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=headers)
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            return data.get("display_name")
```

---

## 🔄 Real-Time Location Tracking (WebSocket)

### `app/websockets/location_tracking.py`

```python
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict
import json
import asyncio

class LocationTracker:
    """Manage real-time location tracking via WebSockets"""
    
    def __init__(self):
        # Store active connections: booking_id -> list of websockets
        self.active_connections: Dict[int, list] = {}
    
    async def connect(self, websocket: WebSocket, booking_id: int):
        """Connect client to location tracking"""
        await websocket.accept()
        
        if booking_id not in self.active_connections:
            self.active_connections[booking_id] = []
        
        self.active_connections[booking_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, booking_id: int):
        """Disconnect client"""
        if booking_id in self.active_connections:
            self.active_connections[booking_id].remove(websocket)
            
            if not self.active_connections[booking_id]:
                del self.active_connections[booking_id]
    
    async def broadcast_location(self, booking_id: int, location_data: dict):
        """Broadcast location to all connected clients for a booking"""
        if booking_id in self.active_connections:
            disconnected = []
            
            for connection in self.active_connections[booking_id]:
                try:
                    await connection.send_json(location_data)
                except Exception:
                    disconnected.append(connection)
            
            # Remove disconnected clients
            for conn in disconnected:
                self.disconnect(conn, booking_id)

# Global tracker instance
location_tracker = LocationTracker()

@app.websocket("/ws/tracking/{booking_id}")
async def websocket_location_tracking(
    websocket: WebSocket,
    booking_id: int
):
    """
    WebSocket endpoint for real-time location tracking
    Used during active bookings
    """
    
    await location_tracker.connect(websocket, booking_id)
    
    try:
        while True:
            # Receive location updates from professional
            data = await websocket.receive_json()
            
            # Validate and enrich data
            location_update = {
                "type": "location_update",
                "booking_id": booking_id,
                "latitude": data.get("latitude"),
                "longitude": data.get("longitude"),
                "timestamp": data.get("timestamp"),
                "accuracy": data.get("accuracy", 0)
            }
            
            # Broadcast to client
            await location_tracker.broadcast_location(
                booking_id, location_update
            )
            
            # Small delay to prevent flooding
            await asyncio.sleep(0.1)
    
    except WebSocketDisconnect:
        location_tracker.disconnect(websocket, booking_id)
```

---

## 📱 Flutter Integration

### `lib/services/location_service.dart`

```dart
import 'package:geolocator/geolocator.dart';
import 'package:dio/dio.dart';
import 'dart:async';

class LocationService {
  final Dio _dio;
  StreamSubscription<Position>? _locationStream;
  
  LocationService(this._dio);
  
  // Get current location
  Future<Position> getCurrentLocation() async {
    bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
    if (!serviceEnabled) {
      throw Exception('Location services are disabled');
    }
    
    LocationPermission permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
      if (permission == LocationPermission.denied) {
        throw Exception('Location permissions denied');
      }
    }
    
    return await Geolocator.getCurrentPosition(
      desiredAccuracy: LocationAccuracy.high,
    );
  }
  
  // Start continuous location tracking
  void startTracking(void Function(Position) onLocationUpdate) {
    _locationStream = Geolocator.getPositionStream(
      locationSettings: LocationSettings(
        accuracy: LocationAccuracy.high,
        distanceFilter: 10, // Update every 10 meters
      ),
    ).listen(onLocationUpdate);
  }
  
  // Stop tracking
  void stopTracking() {
    _locationStream?.cancel();
  }
  
  // Update location on server
  Future<void> updateLocationOnServer({
    required double latitude,
    required double longitude,
  }) async {
    try {
      await _dio.post('/api/location/update-location', data: {
        'latitude': latitude,
        'longitude': longitude,
      });
    } catch (e) {
      print('Failed to update location: $e');
    }
  }
  
  // Get nearby professionals
  Future<List<dynamic>> getNearbyProfessionals({
    required double latitude,
    required double longitude,
    double radius = 10.0,
    String? skill,
  }) async {
    try {
      final response = await _dio.get('/api/location/professionals/nearby',
        queryParameters: {
          'latitude': latitude,
          'longitude': longitude,
          'radius': radius,
          if (skill != null) 'skill': skill,
        },
      );
      
      return response.data['professionals'];
    } catch (e) {
      throw Exception('Failed to fetch professionals: $e');
    }
  }
  
  // Calculate distance to professional
  Future<double> getDistanceToProfessional({
    required int professionalId,
    required double latitude,
    required double longitude,
  }) async {
    try {
      final response = await _dio.get('/api/location/distance/$professionalId',
        queryParameters: {
          'latitude': latitude,
          'longitude': longitude,
        },
      );
      
      return response.data['distance_km'];
    } catch (e) {
      throw Exception('Failed to get distance: $e');
    }
  }
}

// Usage in Flutter
class NearbyProfessionalsScreen extends StatefulWidget {
  @override
  _NearbyProfessionalsScreenState createState() => _NearbyProfessionalsScreenState();
}

class _NearbyProfessionalsScreenState extends State<NearbyProfessionalsScreen> {
  final LocationService _locationService = LocationService(Dio());
  List<dynamic> _professionals = [];
  
  @override
  void initState() {
    super.initState();
    _loadNearbyProfessionals();
  }
  
  Future<void> _loadNearbyProfessionals() async {
    try {
      Position position = await _locationService.getCurrentLocation();
      
      final professionals = await _locationService.getNearbyProfessionals(
        latitude: position.latitude,
        longitude: position.longitude,
        radius: 10.0,
      );
      
      setState(() {
        _professionals = professionals;
      });
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e.toString())),
      );
    }
  }
  
  @override
  Widget build(BuildContext context) {
    return ListView.builder(
      itemCount: _professionals.length,
      itemBuilder: (context, index) {
        final pro = _professionals[index];
        return ListTile(
          title: Text(pro['name']),
          subtitle: Text('${pro['distance_km']} km away'),
          trailing: Text('Rs ${pro['rate']}/hr'),
        );
      },
    );
  }
}
```

---

## ✅ Testing

```python
# tests/test_location.py
@pytest.mark.asyncio
async def test_find_nearby_professionals(client):
    """Test finding nearby professionals"""
    response = await client.get(
        "/api/location/professionals/nearby",
        params={
            "latitude": 27.7172,
            "longitude": 85.3240,
            "radius": 10,
            "limit": 10
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "professionals" in data
    assert isinstance(data["professionals"], list)

@pytest.mark.asyncio
async def test_calculate_distance(client):
    """Test distance calculation"""
    response = await client.get(
        "/api/location/distance/1",
        params={"latitude": 27.7172, "longitude": 85.3240}
    )
    
    assert response.status_code == 200
    assert "distance_km" in response.json()
```

---

## 🚀 Performance Optimization

### Database Indexes for Location Queries

```sql
-- Ensure these indexes exist (already in schema)
CREATE INDEX idx_professional_location 
ON professional_profiles USING gist(ll_to_earth(latitude, longitude))
WHERE latitude IS NOT NULL AND longitude IS NOT NULL;

-- Composite index for common filters
CREATE INDEX idx_professional_search_location 
ON professional_profiles(verification_status, is_available, latitude, longitude)
WHERE verification_status = 'APPROVED' AND is_available = TRUE;
```

### Caching Strategy

```python
# Cache nearby professionals search results
import aioredis

redis = aioredis.from_url("redis://localhost")

async def get_cached_nearby_professionals(lat, lng, radius, skill):
    cache_key = f"nearby:{lat}:{lng}:{radius}:{skill}"
    
    # Try cache
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Fetch from database
    professionals = await LocationService.find_nearby_professionals(...)
    
    # Cache for 5 minutes
    await redis.setex(cache_key, 300, json.dumps(professionals))
    
    return professionals
```

---

**Next:** Booking system implementation ➡️ See `07-BOOKING-SYSTEM.md`
