import 'package:flutter/material.dart';
import 'package:flutter_html/flutter_html.dart';

class ReportScreen extends StatelessWidget {
  final String htmlContent;

  const ReportScreen({super.key, required this.htmlContent});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Отчет'),
        backgroundColor: Colors.black,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(12),
        child: Html(
          data: htmlContent,
          style: {
            "body": Style(
              margin: Margins.zero,
              padding: HtmlPaddings.zero,
              backgroundColor: Colors.white,
              color: Colors.black,
              fontSize: FontSize(14),
            ),
          },
          onLinkTap: (url, attributes, element) {
            debugPrint('link: $url');
          },
        ),
      ),
    );
  }
}