import 'dart:convert';
import 'package:http/http.dart' as http;

class SessionService {
  final String baseUrl;

  SessionService({required this.baseUrl});

  Future<Map<String, dynamic>> createSession({
    required int userId,
    required int vehicleId,
    required int carparkId,
    required int durationSeconds,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/parking-session'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'user_id': userId,
          'vehicle_id': vehicleId,
          'carpark_id': carparkId,
          'duration': durationSeconds,
        }),
      );

      if (response.statusCode == 200) {
        return {'success': true, 'data': jsonDecode(response.body)};
      } else {
        final errorBody = jsonDecode(response.body);
        return {
          'success': false,
          'error': errorBody['error'] ?? 'Failed to create session',
        };
      }
    } catch (e) {
      return {'success': false, 'error': 'Network error: $e'};
    }
  }

  Future<Map<String, dynamic>> extendSession({
    required int userId,
    required int sessionId,
    required int durationSeconds,
  }) async {
    try {
      final response = await http.put(
        Uri.parse('$baseUrl/parking-session'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'user_id': userId,
          'session_id': sessionId,
          'action': 'extend',
          'action_data': durationSeconds.toString(),
        }),
      );

      if (response.statusCode == 200) {
        return {'success': true, 'data': jsonDecode(response.body)};
      } else {
        final errorBody = jsonDecode(response.body);
        return {
          'success': false,
          'error': errorBody['error'] ?? 'Failed to extend session',
        };
      }
    } catch (e) {
      return {'success': false, 'error': 'Network error: $e'};
    }
  }

  Future<Map<String, dynamic>> cancelSession({
    required int userId,
    required int sessionId,
  }) async {
    try {
      final response = await http.put(
        Uri.parse('$baseUrl/parking-session'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'user_id': userId,
          'session_id': sessionId,
          'action': 'cancel',
        }),
      );

      if (response.statusCode == 200) {
        return {'success': true, 'data': jsonDecode(response.body)};
      } else {
        final errorBody = jsonDecode(response.body);
        return {
          'success': false,
          'error': errorBody['error'] ?? 'Failed to cancel session',
        };
      }
    } catch (e) {
      return {'success': false, 'error': 'Network error: $e'};
    }
  }
}
