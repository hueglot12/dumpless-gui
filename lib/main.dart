import 'package:flutter/material.dart';
import 'screens/home_screen.dart';
import 'screens/vk_input_screen.dart';
import 'screens/loading_screen.dart';
import 'screens/phone_input_screen.dart';
import 'screens/loading_phone_screen.dart';
import 'screens/text_result_screen.dart';
import 'screens/report_screen.dart';
import 'screens/domain_input_screen.dart';
import 'screens/loading_domain_screen.dart';
import 'screens/ip_input_screen.dart';
import 'screens/loading_ip_screen.dart';
import 'screens/bin_input_screen.dart';
import 'screens/loading_bin_screen.dart';
import 'screens/settings_screen.dart';
import 'screens/email_input_screen.dart';
import 'screens/loading_email_screen.dart';

void main() {
  runApp(const VkInsightApp());
}

class VkInsightApp extends StatelessWidget {
  const VkInsightApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'VK Insight',
      theme: ThemeData(
        brightness: Brightness.dark,
        scaffoldBackgroundColor: Colors.black,
        useMaterial3: true,
      ),
      initialRoute: '/',
      routes: {
        '/': (_) => const HomeScreen(),
        '/input_vk': (_) => const LinkInputScreen(),
        '/input_phone': (_) => const PhoneInputScreen(),
        '/input_domain': (_) => const DomainInputScreen(),
        '/input_ip': (_) => const IpInputScreen(),
        '/input_bin': (_) => const BinInputScreen(),
        '/input_email': (_) => const EmailInputScreen(),
        '/settings': (_) => const SettingsScreen(),
      },
      onGenerateRoute: (settings) {
        if (settings.name == '/loading_vk') {
          final link = settings.arguments as String;
          return MaterialPageRoute(
            builder: (_) => LoadingScreen(link: link),
          );
        }

        if (settings.name == '/loading_phone') {
          final phone = settings.arguments as String;
          return MaterialPageRoute(
            builder: (_) => LoadingPhoneScreen(phone: phone),
          );
        }

        if (settings.name == '/loading_domain') {
          final domain = settings.arguments as String;
          return MaterialPageRoute(
            builder: (_) => LoadingDomainScreen(domain: domain),
          );
        }

        if (settings.name == '/loading_ip') {
          final ip = settings.arguments as String;
          return MaterialPageRoute(
            builder: (_) => LoadingIpScreen(ip: ip),
          );
        }

        if (settings.name == '/loading_bin') {
          final binOrCard = settings.arguments as String;
          return MaterialPageRoute(
            builder: (_) => LoadingBinScreen(binOrCard: binOrCard),
          );
        }

        if (settings.name == '/loading_email') {
          final email = settings.arguments as String;
          return MaterialPageRoute(
            builder: (_) => LoadingEmailScreen(email: email),
          );
        }

        if (settings.name == '/text_result') {
          final text = settings.arguments as String;
          return MaterialPageRoute(
            builder: (_) => TextResultScreen(text: text),
          );
        }

        if (settings.name == '/report') {
          final html = settings.arguments as String;
          return MaterialPageRoute(
            builder: (_) => ReportScreen(htmlContent: html),
          );
        }

        return null;
      },
    );
  }
}