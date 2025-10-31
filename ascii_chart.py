#!/usr/bin/env python3
"""
ASCII графики скорости чтения на основе сводной таблицы
"""

def create_ascii_charts():
    """Создать ASCII графики скорости чтения"""
    
    # Данные из сводной таблицы (MB/s)
    file_sizes = ['1KB', '10KB', '100KB', '1MB', '10MB']
    direct_io = [10.0, 109.3, 1127.5, 1842.4, 1668.9]
    fast_cache = [7.8, 84.2, 585.6, 1397.2, 1811.2]
    secure_cache = [8.5, 56.6, 583.0, 2034.6, 1752.6]
    gov_cache = [9.6, 56.9, 714.5, 789.5, 1046.7]
    
    print("📊 ГРАФИК СКОРОСТИ ЧТЕНИЯ ФАЙЛОВ")
    print("=" * 80)
    
    # ASCII график - линейный масштаб
    print("\n📈 ЛИНЕЙНЫЙ ГРАФИК СКОРОСТИ ЧТЕНИЯ")
    print("-" * 80)
    
    # Находим максимальное значение для масштабирования
    max_value = max(max(direct_io), max(fast_cache), max(secure_cache), max(gov_cache))
    scale = 50  # ширина графика в символах
    step = max_value / scale
    
    print(f"Максимальная скорость: {max_value:.1f} MB/s")
    print(f"Масштаб: 1 символ = {step:.1f} MB/s")
    print()
    
    # Создаем график для каждого размера файла
    for i, size in enumerate(file_sizes):
        print(f"{size:>6} |", end="")
        
        # Прямое I/O (зеленый)
        direct_bars = int(direct_io[i] / step)
        print("█" * direct_bars, end="")
        print(f" {direct_io[i]:>6.1f} MB/s", end="")
        
        print()
        
        # Быстрый кэш (красный)
        print("       |", end="")
        fast_bars = int(fast_cache[i] / step)
        print("▓" * fast_bars, end="")
        print(f" {fast_cache[i]:>6.1f} MB/s (Быстрый)", end="")
        
        print()
        
        # Безопасный кэш (синий)
        print("       |", end="")
        secure_bars = int(secure_cache[i] / step)
        print("▒" * secure_bars, end="")
        print(f" {secure_cache[i]:>6.1f} MB/s (Безопасный)", end="")
        
        print()
        
        # Гос. кэш (коричневый)
        print("       |", end="")
        gov_bars = int(gov_cache[i] / step)
        print("░" * gov_bars, end="")
        print(f" {gov_cache[i]:>6.1f} MB/s (Гос.)", end="")
        
        print()
        print("-" * 80)
    
    # Легенда
    print("\n🔍 ЛЕГЕНДА:")
    print("█ Прямое I/O    ▓ Быстрый кэш    ▒ Безопасный кэш    ░ Гос. кэш")
    
    # Таблица процентных изменений
    print("\n📊 ТАБЛИЦА ПРОИЗВОДИТЕЛЬНОСТИ ОТНОСИТЕЛЬНО ПРЯМОГО I/O")
    print("=" * 80)
    print(f"{'Размер':<8} {'Прямое I/O':<12} {'Быстрый':<12} {'Безопасный':<12} {'Гос.':<12}")
    print("-" * 80)
    
    for size, direct, fast, secure, gov in zip(file_sizes, direct_io, fast_cache, secure_cache, gov_cache):
        print(f"{size:<8} {direct:<12.1f} {fast:<12.1f} {secure:<12.1f} {gov:<12.1f}")
    
    print("\n📈 ИЗМЕНЕНИЕ ПРОИЗВОДИТЕЛЬНОСТИ (%)")
    print("-" * 80)
    print(f"{'Размер':<8} {'Быстрый':<12} {'Безопасный':<12} {'Гос.':<12}")
    print("-" * 80)
    
    for size, direct, fast, secure, gov in zip(file_sizes, direct_io, fast_cache, secure_cache, gov_cache):
        fast_pct = ((fast/direct - 1) * 100)
        secure_pct = ((secure/direct - 1) * 100)
        gov_pct = ((gov/direct - 1) * 100)
        
        # Цветовая индикация
        fast_color = "🔴" if fast_pct < -10 else "🟡" if fast_pct < 0 else "🟢"
        secure_color = "🔴" if secure_pct < -10 else "🟡" if secure_pct < 0 else "🟢"
        gov_color = "🔴" if gov_pct < -10 else "🟡" if gov_pct < 0 else "🟢"
        
        print(f"{size:<8} {fast_color} {fast_pct:>8.1f}% {secure_color} {secure_pct:>8.1f}% {gov_color} {gov_pct:>8.1f}%")
    
    # График процентных изменений
    print("\n📊 ГРАФИК ИЗМЕНЕНИЯ ПРОИЗВОДИТЕЛЬНОСТИ (%)")
    print("-" * 80)
    
    # Масштабируем для процентного графика
    max_percent = 60  # максимальный процент для отображения
    percent_scale = 50  # ширина в символах
    percent_step = max_percent / percent_scale
    
    print(f"Максимальное изменение: ±{max_percent}%")
    print(f"Масштаб: 1 символ = {percent_step:.1f}%")
    print()
    
    for i, size in enumerate(file_sizes):
        print(f"{size:>6} |", end="")
        
        # Быстрый кэш
        fast_pct = ((fast_cache[i]/direct_io[i] - 1) * 100)
        fast_bars = int(abs(fast_pct) / percent_step)
        if fast_pct < 0:
            print("▓" * fast_bars, end="")
            print(f" {fast_pct:>6.1f}%", end="")
        else:
            print(" " * 25, end="")
            print("▓" * fast_bars, end="")
            print(f" {fast_pct:>6.1f}%", end="")
        
        print()
        
        # Безопасный кэш
        print("       |", end="")
        secure_pct = ((secure_cache[i]/direct_io[i] - 1) * 100)
        secure_bars = int(abs(secure_pct) / percent_step)
        if secure_pct < 0:
            print("▒" * secure_bars, end="")
            print(f" {secure_pct:>6.1f}%", end="")
        else:
            print(" " * 25, end="")
            print("▒" * secure_bars, end="")
            print(f" {secure_pct:>6.1f}%", end="")
        
        print()
        
        # Гос. кэш
        print("       |", end="")
        gov_pct = ((gov_cache[i]/direct_io[i] - 1) * 100)
        gov_bars = int(abs(gov_pct) / percent_step)
        if gov_pct < 0:
            print("░" * gov_bars, end="")
            print(f" {gov_pct:>6.1f}%", end="")
        else:
            print(" " * 25, end="")
            print("░" * gov_bars, end="")
            print(f" {gov_pct:>6.1f}%", end="")
        
        print()
        print("-" * 80)
    
    # Легенда для процентного графика
    print("\n🔍 ЛЕГЕНДА:")
    print("▓ Быстрый кэш    ▒ Безопасный кэш    ░ Гос. кэш")
    print("(слева от | = снижение, справа от | = улучшение)")
    
    # Анализ результатов
    print("\n📋 АНАЛИЗ РЕЗУЛЬТАТОВ")
    print("=" * 80)
    
    print("\n🎯 ЛУЧШИЕ РЕЗУЛЬТАТЫ ПО РАЗМЕРАМ ФАЙЛОВ:")
    for i, size in enumerate(file_sizes):
        speeds = [
            ("Прямое I/O", direct_io[i]),
            ("Быстрый кэш", fast_cache[i]),
            ("Безопасный кэш", secure_cache[i]),
            ("Гос. кэш", gov_cache[i])
        ]
        best_method = max(speeds, key=lambda x: x[1])
        print(f"  {size}: {best_method[0]} ({best_method[1]:.1f} MB/s)")
    
    print("\n📈 СРЕДНЯЯ ПРОИЗВОДИТЕЛЬНОСТЬ:")
    avg_direct = sum(direct_io) / len(direct_io)
    avg_fast = sum(fast_cache) / len(fast_cache)
    avg_secure = sum(secure_cache) / len(secure_cache)
    avg_gov = sum(gov_cache) / len(gov_cache)
    
    print(f"  Прямое I/O: {avg_direct:.1f} MB/s")
    print(f"  Быстрый кэш: {avg_fast:.1f} MB/s ({(avg_fast/avg_direct-1)*100:+.1f}%)")
    print(f"  Безопасный кэш: {avg_secure:.1f} MB/s ({(avg_secure/avg_direct-1)*100:+.1f}%)")
    print(f"  Гос. кэш: {avg_gov:.1f} MB/s ({(avg_gov/avg_direct-1)*100:+.1f}%)")
    
    print("\n🏆 РЕЙТИНГ ПО ОБЩЕЙ ПРОИЗВОДИТЕЛЬНОСТИ:")
    performances = [
        ("Прямое I/O", avg_direct),
        ("Быстрый кэш", avg_fast),
        ("Безопасный кэш", avg_secure),
        ("Гос. кэш", avg_gov)
    ]
    performances.sort(key=lambda x: x[1], reverse=True)
    
    for i, (method, speed) in enumerate(performances, 1):
        emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "🏅"
        print(f"  {emoji} {i}. {method}: {speed:.1f} MB/s")


if __name__ == "__main__":
    create_ascii_charts()



