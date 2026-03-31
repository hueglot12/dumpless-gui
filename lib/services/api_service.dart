import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiService {
  static const String baseUrl = 'http://127.0.0.1:5000';

  static Future<String> analyzeVkProfile(String link) async {
    final response = await http.post(
      Uri.parse('$baseUrl/analyze'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'link': link}),
    );

    final data = jsonDecode(response.body);

    if (response.statusCode != 200) {
      throw Exception(data['error'] ?? 'Ошибка сервера');
    }

    return data['report_url'] as String;
  }

  static Future<String> searchPhoneNumber(String phone) async {
    final response = await http.post(
      Uri.parse('$baseUrl/phone_search'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'phone': phone}),
    );

    final data = jsonDecode(response.body);

    if (response.statusCode != 200) {
      throw Exception(data['error'] ?? 'Ошибка сервера');
    }

    return data['result'] as String;
  }

  static Future<String> analyzeDomain(String domain) async {
    final response = await http.post(
      Uri.parse('$baseUrl/domain_analyze'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'domain': domain}),
    );

    final data = jsonDecode(response.body);

    if (response.statusCode != 200) {
      throw Exception(data['error'] ?? 'Ошибка сервера');
    }

    return data['report_url'] as String;
  }

  static Future<String> analyzeIp(String ip) async {
    final response = await http.post(
      Uri.parse('$baseUrl/ip_analyze'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'ip': ip}),
    );

    final data = jsonDecode(response.body);

    if (response.statusCode != 200) {
      throw Exception(data['error'] ?? 'Ошибка сервера');
    }

    return data['report_url'] as String;
  }
    static Future<String> analyzeEmail(String email) async {
    final response = await http.post(
      Uri.parse('$baseUrl/email_analyze'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'email': email}),
    );

    final data = jsonDecode(response.body);

    if (response.statusCode != 200) {
      throw Exception(data['error'] ?? 'Ошибка сервера');
    }

    return data['report_url'] as String;
  }

  static Future<String> searchBin(String binOrCard) async {
    final response = await http.post(
      Uri.parse('$baseUrl/bin_search'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'bin': binOrCard}),
    );

    final data = jsonDecode(response.body);

    if (response.statusCode != 200) {
      throw Exception(data['error'] ?? 'Ошибка сервера');
    }

    return data['result'] as String;
  }

  static Future<String> getVkApiToken() async {
    final response = await http.get(
      Uri.parse('$baseUrl/settings/vk_api'),
    );

    final data = jsonDecode(response.body);

    if (response.statusCode != 200) {
      throw Exception(data['error'] ?? 'Ошибка сервера');
    }

    return (data['token'] as String?) ?? '';
  }

  static Future<void> saveVkApiToken(String token) async {
    final response = await http.post(
      Uri.parse('$baseUrl/settings/vk_api'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'token': token}),
    );

    final data = jsonDecode(response.body);

    if (response.statusCode != 200) {
      throw Exception(data['error'] ?? 'Ошибка сервера');
    }

    if (data['ok'] != true) {
      throw Exception(data['error'] ?? 'Не удалось сохранить токен');
    }
  }
}