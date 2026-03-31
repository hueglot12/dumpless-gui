import 'package:flutter/material.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    Widget buildButton(String title, VoidCallback onTap) {
      return SizedBox(
        width: 280,
        height: 56,
        child: ElevatedButton(
          style: ElevatedButton.styleFrom(
            backgroundColor: Colors.white,
            foregroundColor: Colors.black,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(14),
            ),
          ),
          onPressed: onTap,
          child: Text(
            title,
            style: const TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.w600,
            ),
          ),
        ),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('OSINT Tool'),
        backgroundColor: Colors.black,
        actions: [
          IconButton(
            onPressed: () {
              Navigator.pushNamed(context, '/settings');
            },
            icon: const Icon(Icons.settings),
          ),
        ],
      ),
      body: SafeArea(
        child: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              buildButton(
                'Поиск по ВКонтакте',
                () => Navigator.pushNamed(context, '/input_vk'),
              ),
              const SizedBox(height: 16),
              buildButton(
                'Поиск по номеру',
                () => Navigator.pushNamed(context, '/input_phone'),
              ),
              const SizedBox(height: 16),
              buildButton(
                'Поиск по домену',
                () => Navigator.pushNamed(context, '/input_domain'),
              ),
              const SizedBox(height: 16),
              buildButton(
                'Поиск по IP',
                () => Navigator.pushNamed(context, '/input_ip'),
              ),
              const SizedBox(height: 16),
              buildButton(
                'Поиск по карте',
                () => Navigator.pushNamed(context, '/input_bin'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}