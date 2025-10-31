#!/usr/bin/env python3
"""
График скорости чтения по сводной таблице
"""

import matplotlib.pyplot as plt
import numpy as np
import matplotlib
matplotlib.rcParams['font.family'] = ['DejaVu Sans', 'Arial', 'sans-serif']

def create_reading_speed_chart():
    """Создать график скорости чтения"""
    
    # Данные из сводной таблицы (MB/s)
    file_sizes = ['1KB', '10KB', '100KB', '1MB', '10MB']
    file_sizes_numeric = [1, 10, 100, 1024, 10240]  # в KB для логарифмической шкалы
    
    # Скорость чтения для каждого метода
    direct_io = [10.0, 109.3, 1127.5, 1842.4, 1668.9]
    fast_cache = [7.8, 84.2, 585.6, 1397.2, 1811.2]
    secure_cache = [8.5, 56.6, 583.0, 2034.6, 1752.6]
    gov_cache = [9.6, 56.9, 714.5, 789.5, 1046.7]
    
    # Создание фигуры с подграфиками
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    
    # График 1: Линейный масштаб
    ax1.plot(file_sizes, direct_io, 'o-', linewidth=3, markersize=8, 
             label='Прямое I/O', color='#2E8B57', markerfacecolor='#90EE90')
    ax1.plot(file_sizes, fast_cache, 's-', linewidth=3, markersize=8, 
             label='Быстрый кэш', color='#FF6347', markerfacecolor='#FFB6C1')
    ax1.plot(file_sizes, secure_cache, '^-', linewidth=3, markersize=8, 
             label='Безопасный кэш', color='#4169E1', markerfacecolor='#87CEEB')
    ax1.plot(file_sizes, gov_cache, 'd-', linewidth=3, markersize=8, 
             label='Гос. кэш', color='#8B4513', markerfacecolor='#DEB887')
    
    ax1.set_xlabel('Размер файла', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Скорость чтения (MB/s)', fontsize=12, fontweight='bold')
    ax1.set_title('Скорость чтения файлов - Линейный масштаб', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.legend(fontsize=10)
    ax1.set_ylim(0, 2200)
    
    # Добавление значений на точки
    for i, (size, direct, fast, secure, gov) in enumerate(zip(file_sizes, direct_io, fast_cache, secure_cache, gov_cache)):
        ax1.annotate(f'{direct:.0f}', (i, direct), textcoords="offset points", 
                    xytext=(0,10), ha='center', fontsize=8, fontweight='bold')
        ax1.annotate(f'{fast:.0f}', (i, fast), textcoords="offset points", 
                    xytext=(0,-15), ha='center', fontsize=8, fontweight='bold')
        ax1.annotate(f'{secure:.0f}', (i, secure), textcoords="offset points", 
                    xytext=(0,10), ha='center', fontsize=8, fontweight='bold')
        ax1.annotate(f'{gov:.0f}', (i, gov), textcoords="offset points", 
                    xytext=(0,-15), ha='center', fontsize=8, fontweight='bold')
    
    # График 2: Логарифмический масштаб
    ax2.plot(file_sizes, direct_io, 'o-', linewidth=3, markersize=8, 
             label='Прямое I/O', color='#2E8B57', markerfacecolor='#90EE90')
    ax2.plot(file_sizes, fast_cache, 's-', linewidth=3, markersize=8, 
             label='Быстрый кэш', color='#FF6347', markerfacecolor='#FFB6C1')
    ax2.plot(file_sizes, secure_cache, '^-', linewidth=3, markersize=8, 
             label='Безопасный кэш', color='#4169E1', markerfacecolor='#87CEEB')
    ax2.plot(file_sizes, gov_cache, 'd-', linewidth=3, markersize=8, 
             label='Гос. кэш', color='#8B4513', markerfacecolor='#DEB887')
    
    ax2.set_xlabel('Размер файла', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Скорость чтения (MB/s)', fontsize=12, fontweight='bold')
    ax2.set_title('Скорость чтения файлов - Логарифмический масштаб', fontsize=14, fontweight='bold')
    ax2.set_yscale('log')
    ax2.grid(True, alpha=0.3)
    ax2.legend(fontsize=10)
    
    plt.tight_layout()
    plt.savefig('reading_speed_comparison.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    # Создание графика производительности относительно прямого I/O
    fig2, ax3 = plt.subplots(1, 1, figsize=(12, 8))
    
    # Вычисление процентного изменения
    fast_percent = [((fast/direct - 1) * 100) for fast, direct in zip(fast_cache, direct_io)]
    secure_percent = [((secure/direct - 1) * 100) for secure, direct in zip(secure_cache, direct_io)]
    gov_percent = [((gov/direct - 1) * 100) for gov, direct in zip(gov_cache, direct_io)]
    
    x = np.arange(len(file_sizes))
    width = 0.25
    
    bars1 = ax3.bar(x - width, fast_percent, width, label='Быстрый кэш', color='#FF6347', alpha=0.8)
    bars2 = ax3.bar(x, secure_percent, width, label='Безопасный кэш', color='#4169E1', alpha=0.8)
    bars3 = ax3.bar(x + width, gov_percent, width, label='Гос. кэш', color='#8B4513', alpha=0.8)
    
    ax3.set_xlabel('Размер файла', fontsize=12, fontweight='bold')
    ax3.set_ylabel('Изменение скорости чтения (%)', fontsize=12, fontweight='bold')
    ax3.set_title('Производительность чтения относительно прямого I/O', fontsize=14, fontweight='bold')
    ax3.set_xticks(x)
    ax3.set_xticklabels(file_sizes)
    ax3.axhline(y=0, color='black', linestyle='-', alpha=0.3)
    ax3.grid(True, alpha=0.3, axis='y')
    ax3.legend(fontsize=10)
    
    # Добавление значений на столбцы
    def add_value_labels(bars):
        for bar in bars:
            height = bar.get_height()
            ax3.annotate(f'{height:.1f}%',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3 if height >= 0 else -15),
                        textcoords="offset points",
                        ha='center', va='bottom' if height >= 0 else 'top',
                        fontsize=9, fontweight='bold')
    
    add_value_labels(bars1)
    add_value_labels(bars2)
    add_value_labels(bars3)
    
    plt.tight_layout()
    plt.savefig('reading_performance_comparison.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    # Создание тепловой карты
    fig3, ax4 = plt.subplots(1, 1, figsize=(10, 6))
    
    # Подготовка данных для тепловой карты
    methods = ['Прямое I/O', 'Быстрый кэш', 'Безопасный кэш', 'Гос. кэш']
    data_matrix = np.array([direct_io, fast_cache, secure_cache, gov_cache])
    
    im = ax4.imshow(data_matrix, cmap='RdYlGn', aspect='auto')
    
    # Настройка осей
    ax4.set_xticks(range(len(file_sizes)))
    ax4.set_yticks(range(len(methods)))
    ax4.set_xticklabels(file_sizes)
    ax4.set_yticklabels(methods)
    
    # Добавление значений в ячейки
    for i in range(len(methods)):
        for j in range(len(file_sizes)):
            text = ax4.text(j, i, f'{data_matrix[i, j]:.0f}',
                           ha="center", va="center", color="black", fontweight='bold')
    
    ax4.set_xlabel('Размер файла', fontsize=12, fontweight='bold')
    ax4.set_ylabel('Метод кэширования', fontsize=12, fontweight='bold')
    ax4.set_title('Тепловая карта скорости чтения (MB/s)', fontsize=14, fontweight='bold')
    
    # Добавление цветовой шкалы
    cbar = plt.colorbar(im, ax=ax4)
    cbar.set_label('Скорость чтения (MB/s)', fontsize=12, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('reading_speed_heatmap.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    print("📊 Графики созданы и сохранены:")
    print("  • reading_speed_comparison.png - Сравнение скоростей")
    print("  • reading_performance_comparison.png - Производительность относительно прямого I/O")
    print("  • reading_speed_heatmap.png - Тепловая карта")


if __name__ == "__main__":
    try:
        create_reading_speed_chart()
    except ImportError:
        print("❌ Для создания графиков требуется matplotlib")
        print("Установите: pip install matplotlib")
        
        # Создание текстовой диаграммы как альтернатива
        print("\n📊 ТЕКСТОВАЯ ДИАГРАММА СКОРОСТИ ЧТЕНИЯ")
        print("=" * 60)
        
        file_sizes = ['1KB', '10KB', '100KB', '1MB', '10MB']
        direct_io = [10.0, 109.3, 1127.5, 1842.4, 1668.9]
        fast_cache = [7.8, 84.2, 585.6, 1397.2, 1811.2]
        secure_cache = [8.5, 56.6, 583.0, 2034.6, 1752.6]
        gov_cache = [9.6, 56.9, 714.5, 789.5, 1046.7]
        
        print(f"{'Размер':<8} {'Прямое I/O':<12} {'Быстрый':<12} {'Безопасный':<12} {'Гос.':<12}")
        print("-" * 60)
        
        for size, direct, fast, secure, gov in zip(file_sizes, direct_io, fast_cache, secure_cache, gov_cache):
            print(f"{size:<8} {direct:<12.1f} {fast:<12.1f} {secure:<12.1f} {gov:<12.1f}")
        
        print("\n📈 ПРОИЗВОДИТЕЛЬНОСТЬ ОТНОСИТЕЛЬНО ПРЯМОГО I/O (%)")
        print("-" * 60)
        print(f"{'Размер':<8} {'Быстрый':<12} {'Безопасный':<12} {'Гос.':<12}")
        print("-" * 60)
        
        for size, direct, fast, secure, gov in zip(file_sizes, direct_io, fast_cache, secure_cache, gov_cache):
            fast_pct = ((fast/direct - 1) * 100)
            secure_pct = ((secure/direct - 1) * 100)
            gov_pct = ((gov/direct - 1) * 100)
            print(f"{size:<8} {fast_pct:<12.1f} {secure_pct:<12.1f} {gov_pct:<12.1f}")



