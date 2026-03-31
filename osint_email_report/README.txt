Файлы:
- email_osint.py — backend логика запуска holehe/mailcat/blackbird, парсинг и генерация html
- email_report.html — шаблон отчета
- email_report.css — стили отчета
- app_email_patch.py.txt — что добавить в Flask app.py
- flutter_email_patch.txt — что добавить в ApiService.dart

Как подключить:
1. Положи email_osint.py рядом с app.py
2. Положи email_report.html и email_report.css в папку htmls/
3. Добавь роуты из app_email_patch.py.txt в app.py
4. Укажи правильные cwd для mailcat/blackbird, если они запускаются из своих директорий
5. На Flutter стороне добавь новый input/loading экран по образцу domain/ip/bin
