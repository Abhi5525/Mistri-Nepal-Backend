# 13-MOBILE-APP-GUIDE.md

# Flutter Mobile App Development Guide

## 📋 Overview

Complete guide for building the Service Manpower Flutter mobile app with offline support, real-time features, and native mobile capabilities.

---

## 🎯 Project Setup

### Prerequisites
```bash
# Install Flutter SDK
# Download from: https://flutter.dev/docs/get-started/install

# Verify installation
flutter doctor

# Create new project
flutter create service_manpower_app
cd service_manpower_app
```

### Project Structure
```
lib/
├── main.dart                    # App entry point
├── config/
│   ├── api_config.dart          # API endpoints
│   └── app_theme.dart           # App theme & colors
├── models/
│   ├── user.dart                # User model
│   ├── professional.dart        # Professional model
│   ├── booking.dart             # Booking model
│   └── review.dart              # Review model
├── services/
│   ├── api_service.dart         # HTTP client (Dio)
│   ├── auth_service.dart        # Authentication
│   ├── location_service.dart    # GPS tracking
│   ├── notification_service.dart # Push notifications
│   └── storage_service.dart     # Local storage (Hive)
├── providers/                   # State management (Riverpod)
│   ├── auth_provider.dart
│   ├── booking_provider.dart
│   └── location_provider.dart
├── screens/
│   ├── auth/
│   │   ├── login_screen.dart
│   │   ├── register_screen.dart
│   │   └── forgot_password_screen.dart
│   ├── home/
│   │   ├── home_screen.dart
│   │   ├── search_screen.dart
│   │   └── map_screen.dart
│   ├── professional/
│   │   ├── professional_list_screen.dart
│   │   ├── professional_detail_screen.dart
│   │   └── registration_screen.dart
│   ├── booking/
│   │   ├── create_booking_screen.dart
│   │   ├── booking_list_screen.dart
│   │   └── booking_detail_screen.dart
│   ├── payment/
│   │   └── payment_screen.dart
│   ├── profile/
│   │   ├── profile_screen.dart
│   │   └── edit_profile_screen.dart
│   └── admin/
│       └── admin_dashboard_screen.dart
├── widgets/                     # Reusable components
│   ├── custom_button.dart
│   ├── professional_card.dart
│   ├── booking_card.dart
│   └── loading_indicator.dart
├── utils/
│   ├── validators.dart          # Form validation
│   ├── formatters.dart          # Date/number formatting
│   └── constants.dart           # App constants
└── routes/
    └── app_routes.dart          # Navigation routes
```

---

## 📦 Dependencies (`pubspec.yaml`)

```yaml
name: service_manpower_app
description: Service Manpower Mobile Application

publish_to: 'none'

version: 1.0.0+1

environment:
  sdk: '>=3.0.0 <4.0.0'

dependencies:
  flutter:
    sdk: flutter
  
  # State Management
  flutter_riverpod: ^2.4.9
  
  # HTTP Client
  dio: ^5.4.0
  pretty_dio_logger: ^1.3.1
  
  # Authentication & Security
  flutter_secure_storage: ^9.0.0
  jwt_decoder: ^2.0.1
  
  # Location & Maps
  geolocator: ^10.1.0
  flutter_map: ^6.1.0
  latlong2: ^0.9.0
  
  # Notifications
  firebase_core: ^2.24.2
  firebase_messaging: ^14.7.0
  flutter_local_notifications: ^16.3.0
  
  # Local Storage (Offline Mode)
  hive: ^2.2.3
  hive_flutter: ^1.1.0
  
  # Image Handling
  image_picker: ^1.0.5
  cached_network_image: ^3.3.0
  
  # UI Components
  flutter_svg: ^2.0.9
  shimmer: ^3.0.0
  pull_to_refresh: ^2.0.0
  
  # Utilities
  intl: ^0.18.1
  url_launcher: ^6.2.2
  permission_handler: ^11.1.0
  connectivity_plus: ^5.0.2
  
  # Payment Integration
  webview_flutter: ^4.4.2
  
  # Biometric Auth
  local_auth: ^2.1.7

dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^3.0.0
  build_runner: ^2.4.7
  hive_generator: ^2.0.1

flutter:
  uses-material-design: true
  
  assets:
    - assets/images/
    - assets/icons/
    - assets/translations/
  
  fonts:
    - family: Poppins
      fonts:
        - asset: assets/fonts/Poppins-Regular.ttf
        - asset: assets/fonts/Poppins-Bold.ttf
          weight: 700
```

Install dependencies:
```bash
flutter pub get
```

---

## 🔧 Configuration Files

### `lib/config/api_config.dart`

```dart
class ApiConfig {
  // Change this to your production URL
  static const String baseUrl = 'http://YOUR_SERVER_IP:8000';
  
  // API Endpoints
  static const String auth = '$baseUrl/api/auth';
  static const String users = '$baseUrl/api/users';
  static const String professionals = '$baseUrl/api/professionals';
  static const String location = '$baseUrl/api/location';
  static const String bookings = '$baseUrl/api/bookings';
  static const String payments = '$baseUrl/api/payments';
  static const String reviews = '$baseUrl/api/reviews';
  
  // WebSocket URLs
  static const String wsChat = 'ws://YOUR_SERVER_IP:8000/ws/chat';
  static const String wsTracking = 'ws://YOUR_SERVER_IP:8000/ws/tracking';
  
  // Timeout settings
  static const int connectTimeout = 5000; // 5 seconds
  static const int receiveTimeout = 3000; // 3 seconds
}
```

### `lib/config/app_theme.dart`

```dart
import 'package:flutter/material.dart';

class AppTheme {
  // Primary Colors
  static const Color primaryColor = Color(0xFF4CAF50); // Green
  static const Color secondaryColor = Color(0xFF2196F3); // Blue
  static const Color accentColor = Color(0xFFFFC107); // Amber
  
  // Background Colors
  static const Color backgroundColor = Color(0xFFF5F5F5);
  static const Color cardColor = Colors.white;
  
  // Text Colors
  static const Color textPrimary = Color(0xFF212121);
  static const Color textSecondary = Color(0xFF757575);
  
  // Status Colors
  static const Color successColor = Color(0xFF4CAF50);
  static const Color warningColor = Color(0xFFFF9800);
  static const Color errorColor = Color(0xFFF44336);
  
  static ThemeData get lightTheme {
    return ThemeData(
      primaryColor: primaryColor,
      scaffoldBackgroundColor: backgroundColor,
      colorScheme: ColorScheme.light(
        primary: primaryColor,
        secondary: secondaryColor,
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: primaryColor,
        foregroundColor: Colors.white,
        elevation: 0,
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: primaryColor,
          foregroundColor: Colors.white,
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(8),
          ),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: Colors.white,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: BorderSide(color: Colors.grey.shade300),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: BorderSide(color: Colors.grey.shade300),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: const BorderSide(color: primaryColor, width: 2),
        ),
      ),
      fontFamily: 'Poppins',
    );
  }
}
```

---

## 🗄️ Models

### `lib/models/user.dart`

```dart
import 'package:hive/hive.dart';

part 'user.g.dart';

@HiveType(typeId: 0)
class User extends HiveObject {
  @HiveField(0)
  final int id;
  
  @HiveField(1)
  final String phoneNumber;
  
  @HiveField(2)
  final String fullName;
  
  @HiveField(3)
  final String? email;
  
  @HiveField(4)
  final bool isClient;
  
  @HiveField(5)
  final bool isProfessional;
  
  @HiveField(6)
  final bool isActive;
  
  User({
    required this.id,
    required this.phoneNumber,
    required this.fullName,
    this.email,
    required this.isClient,
    required this.isProfessional,
    required this.isActive,
  });
  
  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['id'],
      phoneNumber: json['phone_number'],
      fullName: json['full_name'],
      email: json['email'],
      isClient: json['is_client'],
      isProfessional: json['is_professional'],
      isActive: json['is_active'],
    );
  }
  
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'phone_number': phoneNumber,
      'full_name': fullName,
      'email': email,
      'is_client': isClient,
      'is_professional': isProfessional,
      'is_active': isActive,
    };
  }
}
```

Generate Hive adapter:
```bash
flutter pub run build_runner build
```

### `lib/models/professional.dart`

```dart
class Professional {
  final int id;
  final int userId;
  final String name;
  final String email;
  final double rate;
  final int experience;
  final double averageRating;
  final int totalReviews;
  final String? profilePicture;
  final bool isAvailable;
  final double? latitude;
  final double? longitude;
  final String verificationStatus;
  final List<String> skills;
  final double? distanceKm;
  
  Professional({
    required this.id,
    required this.userId,
    required this.name,
    required this.email,
    required this.rate,
    required this.experience,
    required this.averageRating,
    required this.totalReviews,
    this.profilePicture,
    required this.isAvailable,
    this.latitude,
    this.longitude,
    required this.verificationStatus,
    required this.skills,
    this.distanceKm,
  });
  
  factory Professional.fromJson(Map<String, dynamic> json) {
    return Professional(
      id: json['id'],
      userId: json['user_id'],
      name: json['name'] ?? json['full_name'],
      email: json['email'],
      rate: json['rate'].toDouble(),
      experience: json['experience'],
      averageRating: json['average_rating'].toDouble(),
      totalReviews: json['total_reviews'],
      profilePicture: json['profile_picture'],
      isAvailable: json['is_available'],
      latitude: json['latitude']?.toDouble(),
      longitude: json['longitude']?.toDouble(),
      verificationStatus: json['verification_status'],
      skills: List<String>.from(json['skills'] ?? []),
      distanceKm: json['distance_km']?.toDouble(),
    );
  }
}
```

### `lib/models/booking.dart`

```dart
class Booking {
  final int id;
  final int clientId;
  final int professionalId;
  final String clientName;
  final String clientPhone;
  final DateTime bookingTime;
  final DateTime endTime;
  final double durationHours;
  final double totalFee;
  final double depositAmount;
  final String status;
  final bool isConfirmed;
  
  Booking({
    required this.id,
    required this.clientId,
    required this.professionalId,
    required this.clientName,
    required this.clientPhone,
    required this.bookingTime,
    required this.endTime,
    required this.durationHours,
    required this.totalFee,
    required this.depositAmount,
    required this.status,
    required this.isConfirmed,
  });
  
  factory Booking.fromJson(Map<String, dynamic> json) {
    return Booking(
      id: json['id'],
      clientId: json['client_id'],
      professionalId: json['professional_id'],
      clientName: json['client_name'],
      clientPhone: json['client_phone'],
      bookingTime: DateTime.parse(json['booking_time']),
      endTime: DateTime.parse(json['end_time']),
      durationHours: json['duration_hours'].toDouble(),
      totalFee: json['total_fee'].toDouble(),
      depositAmount: json['deposit_amount'].toDouble(),
      status: json['status'],
      isConfirmed: json['is_confirmed'],
    );
  }
}
```

---

## 🔌 Services

### `lib/services/api_service.dart`

```dart
import 'package:dio/dio.dart';
import 'package:pretty_dio_logger/pretty_dio_logger.dart';
import '../config/api_config.dart';
import 'storage_service.dart';

class ApiService {
  late Dio _dio;
  final StorageService _storage = StorageService();
  
  ApiService() {
    _dio = Dio(BaseOptions(
      baseUrl: ApiConfig.baseUrl,
      connectTimeout: Duration(milliseconds: ApiConfig.connectTimeout),
      receiveTimeout: Duration(milliseconds: ApiConfig.receiveTimeout),
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
    ));
    
    // Add interceptor for logging (remove in production)
    _dio.interceptors.add(PrettyDioLogger(
      requestHeader: true,
      requestBody: true,
      responseBody: true,
      responseHeader: false,
      error: true,
      compact: true,
    ));
    
    // Add auth token interceptor
    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        final token = await _storage.getAuthToken();
        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        return handler.next(options);
      },
      onError: (error, handler) {
        if (error.response?.statusCode == 401) {
          // Token expired, handle logout
          _storage.clearAuth();
        }
        return handler.next(error);
      },
    ));
  }
  
  // GET request
  Future<Response> get(String path, {Map<String, dynamic>? queryParameters}) async {
    try {
      return await _dio.get(path, queryParameters: queryParameters);
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }
  
  // POST request
  Future<Response> post(String path, {dynamic data}) async {
    try {
      return await _dio.post(path, data: data);
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }
  
  // PUT request
  Future<Response> put(String path, {dynamic data}) async {
    try {
      return await _dio.put(path, data: data);
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }
  
  // DELETE request
  Future<Response> delete(String path) async {
    try {
      return await _dio.delete(path);
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }
  
  // File upload
  Future<Response> uploadFile(String path, FormData formData) async {
    try {
      return await _dio.post(path, data: formData);
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }
  
  Exception _handleError(DioException error) {
    switch (error.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.sendTimeout:
      case DioExceptionType.receiveTimeout:
        return Exception('Connection timeout. Please check your internet.');
      case DioExceptionType.badResponse:
        final message = error.response?.data['detail'] ?? 'An error occurred';
        return Exception(message);
      case DioExceptionType.cancel:
        return Exception('Request cancelled');
      default:
        return Exception('Network error. Please try again.');
    }
  }
}
```

### `lib/services/auth_service.dart`

```dart
import 'dart:convert';
import '../models/user.dart';
import 'api_service.dart';
import 'storage_service.dart';
import '../config/api_config.dart';

class AuthService {
  final ApiService _api = ApiService();
  final StorageService _storage = StorageService();
  
  // Login
  Future<Map<String, dynamic>> login(String phone, String password) async {
    try {
      final response = await _api.post('${ApiConfig.auth}/login', data: {
        'phone_number': phone,
        'password': password,
      });
      
      final data = response.data;
      
      // Save tokens
      await _storage.saveAuthToken(data['access_token']);
      await _storage.saveRefreshToken(data['refresh_token']);
      
      // Save user data
      final user = User.fromJson(data['user']);
      await _storage.saveUser(user);
      
      return data;
    } catch (e) {
      rethrow;
    }
  }
  
  // Register
  Future<Map<String, dynamic>> register({
    required String fullName,
    required String phone,
    required String password,
    required String confirmPassword,
  }) async {
    try {
      final response = await _api.post('${ApiConfig.auth}/register', data: {
        'full_name': fullName,
        'phone_number': phone,
        'password': password,
        'confirm_password': confirmPassword,
      });
      
      final data = response.data;
      
      // Save tokens and user
      await _storage.saveAuthToken(data['access_token']);
      await _storage.saveRefreshToken(data['refresh_token']);
      final user = User.fromJson(data['user']);
      await _storage.saveUser(user);
      
      return data;
    } catch (e) {
      rethrow;
    }
  }
  
  // Logout
  Future<void> logout() async {
    await _storage.clearAuth();
  }
  
  // Get current user
  Future<User?> getCurrentUser() async {
    return await _storage.getUser();
  }
  
  // Check if logged in
  Future<bool> isLoggedIn() async {
    final token = await _storage.getAuthToken();
    return token != null;
  }
  
  // Refresh token
  Future<void> refreshToken() async {
    final refreshToken = await _storage.getRefreshToken();
    if (refreshToken == null) return;
    
    try {
      final response = await _api.post('${ApiConfig.auth}/refresh', data: {
        'refresh_token': refreshToken,
      });
      
      await _storage.saveAuthToken(response.data['access_token']);
    } catch (e) {
      await logout();
      rethrow;
    }
  }
}
```

### `lib/services/location_service.dart`

```dart
import 'package:geolocator/geolocator.dart';
import 'api_service.dart';
import '../config/api_config.dart';

class LocationService {
  final ApiService _api = ApiService();
  
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
    
    if (permission == LocationPermission.deniedForever) {
      throw Exception('Location permissions permanently denied');
    }
    
    return await Geolocator.getCurrentPosition(
      desiredAccuracy: LocationAccuracy.high,
    );
  }
  
  // Get nearby professionals
  Future<List<dynamic>> getNearbyProfessionals({
    required double latitude,
    required double longitude,
    double radius = 10.0,
    String? skill,
  }) async {
    try {
      final response = await _api.get('${ApiConfig.location}/professionals/nearby',
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
      final response = await _api.get('${ApiConfig.location}/distance/$professionalId',
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
  
  // Update professional location (for live tracking)
  Future<void> updateLocation(double latitude, double longitude) async {
    try {
      await _api.post('${ApiConfig.location}/update-location', data: {
        'latitude': latitude,
        'longitude': longitude,
      });
    } catch (e) {
      print('Failed to update location: $e');
    }
  }
}
```

### `lib/services/storage_service.dart`

```dart
import 'package:hive_flutter/hive_flutter.dart';
import '../models/user.dart';

class StorageService {
  static const String authTokenBox = 'auth_token';
  static const String refreshTokenBox = 'refresh_token';
  static const String userBox = 'user';
  
  // Initialize Hive
  Future<void> init() async {
    await Hive.initFlutter();
    Hive.registerAdapter(UserAdapter());
  }
  
  // Auth Token
  Future<void> saveAuthToken(String token) async {
    final box = await Hive.openBox(authTokenBox);
    await box.put('token', token);
  }
  
  Future<String?> getAuthToken() async {
    final box = await Hive.openBox(authTokenBox);
    return box.get('token');
  }
  
  // Refresh Token
  Future<void> saveRefreshToken(String token) async {
    final box = await Hive.openBox(refreshTokenBox);
    await box.put('token', token);
  }
  
  Future<String?> getRefreshToken() async {
    final box = await Hive.openBox(refreshTokenBox);
    return box.get('token');
  }
  
  // User
  Future<void> saveUser(User user) async {
    final box = await Hive.openBox(userBox);
    await box.put('user', user);
  }
  
  Future<User?> getUser() async {
    final box = await Hive.openBox(userBox);
    return box.get('user');
  }
  
  // Clear all auth data
  Future<void> clearAuth() async {
    final authBox = await Hive.openBox(authTokenBox);
    final refreshBox = await Hive.openBox(refreshTokenBox);
    final userBox = await Hive.openBox(userBox);
    
    await authBox.clear();
    await refreshBox.clear();
    await userBox.clear();
  }
}
```

### `lib/services/notification_service.dart`

```dart
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'api_service.dart';
import '../config/api_config.dart';

class NotificationService {
  final ApiService _api = ApiService();
  final FirebaseMessaging _firebaseMessaging = FirebaseMessaging.instance;
  final FlutterLocalNotificationsPlugin _localNotifications = 
      FlutterLocalNotificationsPlugin();
  
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
    
    // Initialize local notifications
    await _initializeLocalNotifications();
  }
  
  Future<void> _registerToken(String token) async {
    try {
      await _api.post('${ApiConfig.users}/notifications/register-device', data: {
        'fcm_token': token,
      });
      print('FCM token registered');
    } catch (e) {
      print('Failed to register FCM token: $e');
    }
  }
  
  void _handleForegroundMessage(RemoteMessage message) {
    print('Received foreground message: ${message.notification?.title}');
    
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
Future<void> firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  print('Handling background message: ${message.messageId}');
}
```

---

## 📱 Key Screens

### `lib/screens/auth/login_screen.dart`

```dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../providers/auth_provider.dart';
import '../../widgets/custom_button.dart';

class LoginScreen extends ConsumerStatefulWidget {
  @override
  _LoginScreenState createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _phoneController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _isLoading = false;
  
  @override
  void dispose() {
    _phoneController.dispose();
    _passwordController.dispose();
    super.dispose();
  }
  
  Future<void> _handleLogin() async {
    if (!_formKey.currentState!.validate()) return;
    
    setState(() => _isLoading = true);
    
    try {
      await ref.read(authProvider.notifier).login(
        _phoneController.text.trim(),
        _passwordController.text,
      );
      
      if (mounted) {
        Navigator.pushReplacementNamed(context, '/home');
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(e.toString())),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Login')),
      body: Padding(
        padding: EdgeInsets.all(16),
        child: Form(
          key: _formKey,
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              TextFormField(
                controller: _phoneController,
                decoration: InputDecoration(
                  labelText: 'Phone Number',
                  hintText: '98XXXXXXXX',
                  prefixIcon: Icon(Icons.phone),
                ),
                keyboardType: TextInputType.phone,
                validator: (value) {
                  if (value == null || value.isEmpty) {
                    return 'Please enter phone number';
                  }
                  if (!RegExp(r'^98\d{8}$').hasMatch(value)) {
                    return 'Invalid phone number format';
                  }
                  return null;
                },
              ),
              SizedBox(height: 16),
              TextFormField(
                controller: _passwordController,
                decoration: InputDecoration(
                  labelText: 'Password',
                  prefixIcon: Icon(Icons.lock),
                ),
                obscureText: true,
                validator: (value) {
                  if (value == null || value.isEmpty) {
                    return 'Please enter password';
                  }
                  return null;
                },
              ),
              SizedBox(height: 24),
              CustomButton(
                text: 'Login',
                isLoading: _isLoading,
                onPressed: _handleLogin,
              ),
              SizedBox(height: 16),
              TextButton(
                onPressed: () {
                  Navigator.pushNamed(context, '/register');
                },
                child: Text('Don\'t have an account? Register'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
```

### `lib/screens/home/home_screen.dart`

```dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../providers/location_provider.dart';
import '../../widgets/professional_card.dart';

class HomeScreen extends ConsumerStatefulWidget {
  @override
  _HomeScreenState createState() => _HomeScreenState();
}

class _HomeScreenState extends ConsumerState<HomeScreen> {
  final _searchController = TextEditingController();
  
  @override
  void initState() {
    super.initState();
    // Load nearby professionals on startup
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(locationProvider.notifier).loadNearbyProfessionals();
    });
  }
  
  @override
  Widget build(BuildContext context) {
    final locationState = ref.watch(locationProvider);
    
    return Scaffold(
      appBar: AppBar(
        title: Text('Service Manpower'),
        actions: [
          IconButton(
            icon: Icon(Icons.notifications),
            onPressed: () {
              // Navigate to notifications
            },
          ),
        ],
      ),
      body: Column(
        children: [
          // Search bar
          Padding(
            padding: EdgeInsets.all(16),
            child: TextField(
              controller: _searchController,
              decoration: InputDecoration(
                hintText: 'Search for plumber, electrician...',
                prefixIcon: Icon(Icons.search),
                suffixIcon: IconButton(
                  icon: Icon(Icons.filter_list),
                  onPressed: () {
                    // Show filter dialog
                  },
                ),
              ),
              onSubmitted: (value) {
                ref.read(locationProvider.notifier).searchProfessionals(value);
              },
            ),
          ),
          
          // Professional list
          Expanded(
            child: locationState.when(
              data: (professionals) {
                if (professionals.isEmpty) {
                  return Center(
                    child: Text('No professionals found nearby'),
                  );
                }
                
                return ListView.builder(
                  itemCount: professionals.length,
                  itemBuilder: (context, index) {
                    final pro = professionals[index];
                    return ProfessionalCard(professional: pro);
                  },
                );
              },
              loading: () => Center(child: CircularProgressIndicator()),
              error: (error, stack) => Center(
                child: Text('Error: $error'),
              ),
            ),
          ),
        ],
      ),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: 0,
        items: [
          BottomNavigationBarItem(
            icon: Icon(Icons.home),
            label: 'Home',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.book_online),
            label: 'Bookings',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.person),
            label: 'Profile',
          ),
        ],
        onTap: (index) {
          // Navigate to different tabs
        },
      ),
    );
  }
}
```

---

## 🔄 State Management (Riverpod)

### `lib/providers/auth_provider.dart`

```dart
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../services/auth_service.dart';
import '../models/user.dart';

final authServiceProvider = Provider((ref) => AuthService());

final authProvider = StateNotifierProvider<AuthNotifier, AsyncValue<User?>>((ref) {
  return AuthNotifier(ref.watch(authServiceProvider));
});

class AuthNotifier extends StateNotifier<AsyncValue<User?>> {
  final AuthService _authService;
  
  AuthNotifier(this._authService) : super(const AsyncValue.loading()) {
    _init();
  }
  
  Future<void> _init() async {
    try {
      final user = await _authService.getCurrentUser();
      state = AsyncValue.data(user);
    } catch (e, stack) {
      state = AsyncValue.error(e, stack);
    }
  }
  
  Future<void> login(String phone, String password) async {
    state = const AsyncValue.loading();
    try {
      final data = await _authService.login(phone, password);
      final user = await _authService.getCurrentUser();
      state = AsyncValue.data(user);
    } catch (e, stack) {
      state = AsyncValue.error(e, stack);
      rethrow;
    }
  }
  
  Future<void> register({
    required String fullName,
    required String phone,
    required String password,
    required String confirmPassword,
  }) async {
    state = const AsyncValue.loading();
    try {
      await _authService.register(
        fullName: fullName,
        phone: phone,
        password: password,
        confirmPassword: confirmPassword,
      );
      final user = await _authService.getCurrentUser();
      state = AsyncValue.data(user);
    } catch (e, stack) {
      state = AsyncValue.error(e, stack);
      rethrow;
    }
  }
  
  Future<void> logout() async {
    await _authService.logout();
    state = const AsyncValue.data(null);
  }
}
```

### `lib/providers/location_provider.dart`

```dart
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../services/location_service.dart';
import '../models/professional.dart';

final locationServiceProvider = Provider((ref) => LocationService());

final locationProvider = StateNotifierProvider<LocationNotifier, AsyncValue<List<Professional>>>((ref) {
  return LocationNotifier(ref.watch(locationServiceProvider));
});

class LocationNotifier extends StateNotifier<AsyncValue<List<Professional>>> {
  final LocationService _locationService;
  
  LocationNotifier(this._locationService) : super(const AsyncValue.loading());
  
  Future<void> loadNearbyProfessionals() async {
    state = const AsyncValue.loading();
    try {
      final position = await _locationService.getCurrentLocation();
      final professionals = await _locationService.getNearbyProfessionals(
        latitude: position.latitude,
        longitude: position.longitude,
      );
      
      final profList = professionals.map((p) => Professional.fromJson(p)).toList();
      state = AsyncValue.data(profList);
    } catch (e, stack) {
      state = AsyncValue.error(e, stack);
    }
  }
  
  Future<void> searchProfessionals(String query) async {
    state = const AsyncValue.loading();
    try {
      final position = await _locationService.getCurrentLocation();
      final professionals = await _locationService.getNearbyProfessionals(
        latitude: position.latitude,
        longitude: position.longitude,
        skill: query,
      );
      
      final profList = professionals.map((p) => Professional.fromJson(p)).toList();
      state = AsyncValue.data(profList);
    } catch (e, stack) {
      state = AsyncValue.error(e, stack);
    }
  }
}
```

---

## 🎨 Reusable Widgets

### `lib/widgets/professional_card.dart`

```dart
import 'package:flutter/material.dart';
import 'package:cached_network_image/cached_network_image.dart';
import '../models/professional.dart';
import '../config/app_theme.dart';

class ProfessionalCard extends StatelessWidget {
  final Professional professional;
  
  const ProfessionalCard({Key? key, required this.professional}) : super(key: key);
  
  @override
  Widget build(BuildContext context) {
    return Card(
      margin: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: InkWell(
        onTap: () {
          Navigator.pushNamed(
            context,
            '/professional-detail',
            arguments: professional,
          );
        },
        child: Padding(
          padding: EdgeInsets.all(16),
          child: Row(
            children: [
              // Profile picture
              CircleAvatar(
                radius: 30,
                backgroundImage: professional.profilePicture != null
                    ? CachedNetworkImageProvider(professional.profilePicture!)
                    : AssetImage('assets/images/default_avatar.png') as ImageProvider,
              ),
              SizedBox(width: 16),
              
              // Details
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      professional.name,
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    SizedBox(height: 4),
                    Text(
                      professional.skills.join(', '),
                      style: TextStyle(color: AppTheme.textSecondary),
                    ),
                    SizedBox(height: 4),
                    Row(
                      children: [
                        Icon(Icons.star, color: Colors.amber, size: 16),
                        Text(' ${professional.averageRating.toStringAsFixed(1)}'),
                        SizedBox(width: 8),
                        Text('(${professional.totalReviews} reviews)'),
                      ],
                    ),
                  ],
                ),
              ),
              
              // Rate & Distance
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Text(
                    'Rs ${professional.rate}/hr',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                      color: AppTheme.primaryColor,
                    ),
                  ),
                  if (professional.distanceKm != null)
                    Text(
                      '${professional.distanceKm!.toStringAsFixed(1)} km',
                      style: TextStyle(color: AppTheme.textSecondary),
                    ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
```

---

## 🚀 Running the App

### Development
```bash
# Run on connected device/emulator
flutter run

# Run on specific platform
flutter run -d chrome    # Web
flutter run -d windows   # Windows
flutter run -d android   # Android
flutter run -d ios       # iOS
```

### Building for Production

#### Android
```bash
# Build APK
flutter build apk --release

# Build App Bundle (for Play Store)
flutter build appbundle --release
```

#### iOS
```bash
# Build for iOS
flutter build ios --release
```

---

## ✅ Testing

### Unit Tests
```bash
# Run all tests
flutter test

# Run specific test
flutter test test/services/auth_service_test.dart
```

### Integration Tests
```bash
# Run integration tests
flutter test integration_test/
```

---

## 📱 Mobile-Specific Features Implementation

See detailed implementations in:
- **GPS Tracking**: `lib/services/location_service.dart`
- **Push Notifications**: `lib/services/notification_service.dart`
- **Offline Mode**: `lib/services/storage_service.dart` (Hive)
- **Biometric Auth**: Use `local_auth` package
- **Camera Integration**: Use `image_picker` package

---

## 🎯 Next Steps

1. Set up Flutter environment
2. Create project structure
3. Implement authentication flow
4. Build core screens
5. Integrate with FastAPI backend
6. Test on real devices
7. Deploy to Play Store/App Store

**Your mobile app is ready to be built!** 🚀
