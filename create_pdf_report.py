#!/usr/bin/env python3
"""
Создание PDF отчета из HTML файла
Требует установки weasyprint: pip install weasyprint
"""

import os
import sys
from datetime import datetime

try:
    from weasyprint import HTML, CSS
    from weasyprint.text.fonts import FontConfiguration
except ImportError:
    print("Ошибка: Необходимо установить weasyprint")
    print("Выполните: pip install weasyprint")
    sys.exit(1)


def create_pdf_report():
    """Создает PDF отчет из HTML файла"""
    
    html_file = "ОПЭ_HYBRIDCACHE_ПИСЬМО.html"
    pdf_file = f"ОПЭ_HYBRIDCACHE_ПИСЬМО_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    if not os.path.exists(html_file):
        print(f"Ошибка: Файл {html_file} не найден")
        return False
    
    try:
        print(f"Создание PDF отчета: {pdf_file}")
        
        # CSS для улучшения печати
        css_styles = CSS(string='''
            @page {
                size: A4;
                margin: 2cm;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.4;
                color: #333;
            }
            
            .header h1 {
                font-size: 24pt;
                margin-bottom: 10pt;
            }
            
            .section h2 {
                font-size: 18pt;
                margin-top: 20pt;
                margin-bottom: 10pt;
                page-break-after: avoid;
            }
            
            .section h3 {
                font-size: 14pt;
                margin-top: 15pt;
                margin-bottom: 8pt;
                page-break-after: avoid;
            }
            
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 10pt;
                margin: 15pt 0;
            }
            
            .stat-card {
                padding: 10pt;
                border: 1pt solid #ddd;
                border-radius: 5pt;
                text-align: center;
                page-break-inside: avoid;
            }
            
            .stat-value {
                font-size: 20pt;
                font-weight: bold;
                color: #27ae60;
            }
            
            .performance-table {
                font-size: 9pt;
                margin: 10pt 0;
                page-break-inside: avoid;
            }
            
            .performance-table th,
            .performance-table td {
                padding: 4pt;
                border: 1pt solid #ddd;
            }
            
            .performance-table th {
                background-color: #3498db;
                color: white;
                font-weight: bold;
            }
            
            .chart-container {
                page-break-inside: avoid;
                margin: 15pt 0;
                text-align: center;
            }
            
            .benefit-item, .risk-item {
                margin: 5pt 0;
                padding: 5pt;
                page-break-inside: avoid;
            }
            
            .executive-summary {
                background-color: #f8f9fa;
                padding: 15pt;
                border: 2pt solid #3498db;
                margin-bottom: 20pt;
            }
            
            .recommendation {
                background-color: #d4edda;
                padding: 15pt;
                border: 2pt solid #28a745;
                margin: 15pt 0;
            }
            
            .file-list {
                background-color: #f8f9fa;
                padding: 10pt;
                margin: 10pt 0;
                page-break-inside: avoid;
            }
            
            .footer {
                margin-top: 30pt;
                padding-top: 10pt;
                border-top: 1pt solid #ddd;
                font-size: 8pt;
                color: #666;
            }
        ''')
        
        # Создание PDF
        HTML(filename=html_file).write_pdf(pdf_file, stylesheets=[css_styles])
        
        print(f"✅ PDF отчет успешно создан: {pdf_file}")
        return True
        
    except Exception as e:
        print(f"Ошибка при создании PDF: {e}")
        return False


def main():
    """Основная функция"""
    print("🔧 Создание PDF отчета из HTML")
    print("=" * 40)
    
    if create_pdf_report():
        print("\n✅ Отчет готов!")
        print("\nДля просмотра HTML версии откройте:")
        print("ОПЭ_HYBRIDCACHE_ПИСЬМО.html")
        print("\nPDF версия сохранена в текущей директории")
    else:
        print("\n❌ Ошибка при создании отчета")


if __name__ == "__main__":
    main()

