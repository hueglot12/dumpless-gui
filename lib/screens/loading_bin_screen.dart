import 'dart:async';
import 'package:flutter/material.dart';
import '../services/api_service.dart';

class LoadingBinScreen extends StatefulWidget {
  final String binOrCard;

  const LoadingBinScreen({super.key, required this.binOrCard});

  @override
  State<LoadingBinScreen> createState() => _LoadingBinScreenState();
}

class _LoadingBinScreenState extends State<LoadingBinScreen> {
  final List<String> steps = const [
    'обращаюсь к серверу',
    'получаю информацию о BIN',
  ];

  int currentStep = 0;
  int progress = 5;
  Timer? timer;

  @override
  void initState() {
    super.initState();
    _startFlow();
  }

  Future<void> _startFlow() async {
    timer = Timer.periodic(const Duration(milliseconds: 300), (_) {
      if (!mounted) return;

      setState(() {
        if (progress < 50) {
          progress += 6;
          currentStep = 0;
        } else if (progress < 92) {
          progress += 3;
          currentStep = 1;
        }
      });
    });

    try {
      final result = await ApiService.searchBin(widget.binOrCard);

      timer?.cancel();

      if (!mounted) return;
      setState(() {
        progress = 100;
        currentStep = 1;
      });

      await Future.delayed(const Duration(milliseconds: 300));

      if (!mounted) return;
      Navigator.pushReplacementNamed(
        context,
        '/text_result',
        arguments: result,
      );
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