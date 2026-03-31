import 'dart:async';
import 'dart:io';
import 'package:flutter/material.dart';
import '../services/api_service.dart';

class LoadingDomainScreen extends StatefulWidget {
  final String domain;

  const LoadingDomainScreen({super.key, required this.domain});

  @override
  State<LoadingDomainScreen> createState() => _LoadingDomainScreenState();
}

class _LoadingDomainScreenState extends State<LoadingDomainScreen> {
  final List<String> steps = const [
    'обращаюсь к серверу',
    'получаю whois',
    'ищу поддомены',
    'создаю отчет (может занять некоторое время)',
  ];

  int currentStep = 0;
  int progress = 5;
  Timer? timer;

  @override
  void initState() {
    super.initState();
    _startFlow();
  }

  Future<void> _openInBrowser(String url) async {
    if (Platform.isLinux) {
      await Process.start('xdg-open', [url]);
      return;
    }
    throw Exception('Этот способ сейчас сделан только для Linux');
  }

  Future<void> _startFlow() async {
    timer = Timer.periodic(const Duration(milliseconds: 300), (_) {
      if (!mounted) return;

      setState(() {
        if (progress < 25) {
          progress += 4;
          currentStep = 0;
        } else if (progress < 50) {
          progress += 4;
          currentStep = 1;
        } else if (progress < 75) {
          progress += 3;
          currentStep = 2;
        } else if (progress < 92) {
          progress += 2;
          currentStep = 3;
        }
      });
    });

    try {
      final reportUrl = await ApiService.analyzeDomain(widget.domain);

      timer?.cancel();

      if (!mounted) return;
      setState(() {
        progress = 100;
        currentStep = 3;
      });

      await Future.delayed(const Duration(milliseconds: 300));
      await _openInBrowser(reportUrl);

      if (!mounted) return;
      Navigator.pop(context);
    } catch (e) {
      timer?.cancel();

      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Ошибка: $e')),
      );
      Navigator.pop(context);
    }
  }

  @override
  void dispose() {
    timer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final visibleSteps = steps.take(currentStep + 1).toList();

    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const SizedBox(
                  width: 64,
                  height: 64,
                  child: CircularProgressIndicator(strokeWidth: 4),
                ),
                const SizedBox(height: 30),
                ...visibleSteps.map(
                  (step) => Padding(
                    padding: const EdgeInsets.only(bottom: 10),
                    child: Text(step, style: const TextStyle(fontSize: 18)),
                  ),
                ),
                const SizedBox(height: 24),
                Text(
                  '$progress%',
                  style: const TextStyle(
                    fontSize: 28,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 12),
                ClipRRect(
                  borderRadius: BorderRadius.circular(20),
                  child: LinearProgressIndicator(
                    value: progress / 100,
                    minHeight: 10,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}