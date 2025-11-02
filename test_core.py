"""
Тестовий скрипт для перевірки основної функціональності
"""

import numpy as np
from gui.scales import get_scale, get_all_scale_names, ScaleType
from gui.calculations import (
    build_comparison_matrix,
    calculate_weights_eigenvector,
    calculate_weights_geometric_mean,
    check_consistency
)


def test_scales():
    """Тестування шкал"""
    print("=" * 60)
    print("ТЕСТУВАННЯ ШКАЛ")
    print("=" * 60)

    scale_names = get_all_scale_names()
    print(f"\nДоступно шкал: {len(scale_names)}")

    for scale_name in scale_names:
        scale = get_scale(scale_name)
        print(f"\n{scale.name}:")
        print(f"  Градацій: {scale.gradations}")
        print(f"  Значення: {[f'{v:.2f}' for v in scale.values]}")

        # Перевірка уніфікації
        unified = [scale.unify(i) for i in range(scale.gradations)]
        print(f"  Уніфіковані: {[f'{v:.2f}' for v in unified]}")


def test_calculations():
    """Тестування розрахунків"""
    print("\n" + "=" * 60)
    print("ТЕСТУВАННЯ РОЗРАХУНКІВ")
    print("=" * 60)

    # Приклад: 3 альтернативи
    alternatives = ["Фактор 1", "Фактор 2", "Фактор 3"]
    n = len(alternatives)

    print(f"\nАльтернативи: {alternatives}")

    # Симулювати порівняння
    # Фактор 1 vs Фактор 2: Фактор 1 трохи краще (3.0)
    # Фактор 1 vs Фактор 3: Фактор 1 сильно краще (7.0)
    # Фактор 2 vs Фактор 3: Фактор 2 помірно краще (5.0)
    comparisons = [
        (0, 1, 3.0),
        (0, 2, 7.0),
        (1, 2, 5.0)
    ]

    print("\nПорівняння:")
    for i, j, value in comparisons:
        print(f"  {alternatives[i]} vs {alternatives[j]}: {value:.2f}")

    # Побудувати матрицю
    matrix = build_comparison_matrix(n, comparisons)
    print("\nМатриця парних порівнянь:")
    print(matrix)

    # Розрахувати ваги (метод власного вектора)
    weights_ev = calculate_weights_eigenvector(matrix)
    print("\nВаги (метод власного вектора):")
    for i, (alt, weight) in enumerate(zip(alternatives, weights_ev)):
        print(f"  {alt}: {weight:.4f}")

    # Розрахувати ваги (геометричне середнє)
    weights_gm = calculate_weights_geometric_mean(matrix)
    print("\nВаги (геометричне середнє):")
    for i, (alt, weight) in enumerate(zip(alternatives, weights_gm)):
        print(f"  {alt}: {weight:.4f}")

    # Перевірити узгодженість
    consistency = check_consistency(matrix, weights_ev)

    print("\nУзгодженість:")
    print(f"  λ_max = {consistency['lambda_max']:.4f}")
    print(f"  CI = {consistency['CI']:.4f}")
    print(f"  CR = {consistency['CR']:.4f}")
    print(f"  Узгоджено: {'Так' if consistency['is_consistent'] else 'Ні'}")

    print("\nРекомендації:")
    for rec in consistency['recommendations']:
        print(f"  • {rec}")

    # Ранги
    ranks = np.argsort(-weights_ev) + 1
    print("\nРанги:")
    for i, (alt, rank) in enumerate(zip(alternatives, ranks)):
        print(f"  {alt}: Ранг {rank}")


def test_unification():
    """Тестування уніфікації"""
    print("\n" + "=" * 60)
    print("ТЕСТУВАННЯ УНІФІКАЦІЇ")
    print("=" * 60)

    # Порівняти уніфікацію для різних шкал
    test_cases = [
        (ScaleType.INTEGER, 4),      # 5-та градація цілочислової шкали
        (ScaleType.BALANCED_9, 4),   # 5-та градація збалансованої (9)
        (ScaleType.POWER_9, 4),      # 5-та градація степеневої (9)
        (ScaleType.MA_ZHENG, 4),     # 5-та градація Ма-Чженга
    ]

    print("\nПорівняння уніфікації 5-ї градації різних шкал:")
    for scale_name, gradation_idx in test_cases:
        scale = get_scale(scale_name)
        original_value = scale.get_value(gradation_idx)
        unified_value = scale.unify(gradation_idx)
        print(f"\n  {scale.name}:")
        print(f"    Оригінальне значення: {original_value:.4f}")
        print(f"    Уніфіковане значення: {unified_value:.4f}")


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("ТЕСТУВАННЯ СИСТЕМИ ЕКСПЕРТНОГО ОЦІНЮВАННЯ")
    print("=" * 60)

    test_scales()
    test_calculations()
    test_unification()

    print("\n" + "=" * 60)
    print("ВСІ ТЕСТИ ВИКОНАНО УСПІШНО!")
    print("=" * 60)
    print("\nПримітка: GUI застосунок можна запустити командою:")
    print("  python main.py")
    print("  або")
    print("  python -m gui.app")
    print()
