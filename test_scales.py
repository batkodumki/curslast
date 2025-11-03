"""
Тест для перевірки роботи шкал
"""

from gui.scales import (
    get_scale, get_all_scale_names, ScaleType,
    IntegerScale, BalancedScale, PowerScale,
    MaZhengScale, DoneganScale
)


def test_scale(scale_name, gradations=9):
    """Протестувати шкалу"""
    print(f"\n{'='*60}")
    print(f"Шкала: {scale_name}")
    if scale_name in [ScaleType.BALANCED, ScaleType.POWER]:
        print(f"Градацій: {gradations}")
        scale = get_scale(scale_name, gradations)
    else:
        scale = get_scale(scale_name)

    print(f"Кількість градацій: {scale.gradations}")
    print(f"\nВербальні підписи:")
    if hasattr(scale, 'labels'):
        for i, label in enumerate(scale.labels):
            value = scale.get_value(i)
            unified = scale.unify(i)
            print(f"  {i}: {label:30} | значення: {value:8.4f} | уніфіковане: {unified:.4f}")
    else:
        print("  Немає підписів")
    print(f"{'='*60}")


def main():
    """Головна функція"""
    print("Тестування всіх шкал оцінювання\n")

    # Тестуємо всі шкали
    test_scale(ScaleType.INTEGER)
    test_scale(ScaleType.BALANCED, 9)
    test_scale(ScaleType.BALANCED, 3)
    test_scale(ScaleType.POWER, 9)
    test_scale(ScaleType.POWER, 3)
    test_scale(ScaleType.MA_ZHENG)
    test_scale(ScaleType.DONEGAN)

    print("\n\nСписок всіх доступних шкал:")
    for scale_name in get_all_scale_names():
        print(f"  - {scale_name}")


if __name__ == '__main__':
    main()
