"""
Модуль для роботи зі шкалами оцінювання та уніфікації
"""

import numpy as np


class ScaleType:
    """Типи шкал для експертного оцінювання"""
    INTEGER = "Цілочислова"
    BALANCED = "Збалансована"
    POWER = "Степенева"
    MA_ZHENG = "Ма-Чженґа (9/9–9/1)"
    DONEGAN = "Донеган–Додд–МакМастер"
    ORDINAL = "Ординальна"


class Scale:
    """Базовий клас для шкал оцінювання"""

    def __init__(self, name, gradations):
        self.name = name
        self.gradations = gradations
        self.values = self._calculate_values()

    def _calculate_values(self):
        """Розрахувати значення для кожної градації"""
        raise NotImplementedError

    def get_value(self, gradation_index):
        """Отримати числове значення для градації"""
        if 0 <= gradation_index < len(self.values):
            return self.values[gradation_index]
        return 1.0

    def unify(self, gradation_index):
        """Уніфікувати оцінку до кардинальної шкали з межами 1.5-9.5"""
        n = len(self.values)
        i = gradation_index + 1  # градації нумеруються з 1
        l = 1.5
        p = 9.5
        return l + (i - 0.5) * (p - l) / n


class OrdinalScale(Scale):
    """Ординальна шкала (2 градації)"""

    def __init__(self):
        super().__init__(ScaleType.ORDINAL, 2)
        self.labels = ["Менше", "Сильно"]

    def _calculate_values(self):
        return [1.0, 9.0]


class IntegerScale(Scale):
    """Цілочислова шкала (9 градацій)"""

    def __init__(self):
        super().__init__(ScaleType.INTEGER, 9)
        self.labels = [
            "Менше",
            "Слабке або незначно",
            "Середнє",
            "Більше ніж середнє",
            "Сильно",
            "Більше ніж сильно",
            "Дуже сильно",
            "Дуже-дуже сильно",
            "Абсолютно"
        ]

    def _calculate_values(self):
        return list(range(1, 10))


class BalancedScale(Scale):
    """Збалансована шкала: a = w/(1-w)"""

    def __init__(self, gradations=9):
        if gradations not in [3, 9]:
            raise ValueError("Збалансована шкала підтримує 3 або 9 градацій")
        super().__init__(ScaleType.BALANCED, gradations)

        if gradations == 9:
            self.labels = [
                "Менше",
                "Слабке або незначно",
                "Середнє",
                "Більше ніж середнє",
                "Сильно",
                "Більше ніж сильно",
                "Дуже сильно",
                "Дуже-дуже сильно",
                "Абсолютно"
            ]
        else:  # 3 градації
            self.labels = [
                "Менше",
                "Слабке або незначно",
                "Сильно"
            ]

    def _calculate_values(self):
        n = self.gradations
        values = []
        for i in range(1, n + 1):
            w = i / (n + 1)  # розподіл ваг рівномірно від 1/(n+1) до n/(n+1)
            a = w / (1 - w) if w < 1 else 9.0
            values.append(a)
        return values


class PowerScale(Scale):
    """Степенева шкала: a = ⁸√(9^(x-1))"""

    def __init__(self, gradations=9):
        if gradations not in [3, 9]:
            raise ValueError("Степенева шкала підтримує 3 або 9 градацій")
        super().__init__(ScaleType.POWER, gradations)

        if gradations == 9:
            self.labels = [
                "Менше",
                "Слабке або незначно",
                "Середнє",
                "Більше ніж середнє",
                "Сильно",
                "Більше ніж сильно",
                "Дуже сильно",
                "Дуже-дуже сильно",
                "Абсолютно"
            ]
        else:  # 3 градації
            self.labels = [
                "Менше",
                "Слабке або незначно",
                "Сильно"
            ]

    def _calculate_values(self):
        n = self.gradations
        values = []
        for x in range(1, n + 1):
            a = 9 ** ((x - 1) / (n - 1)) if n > 1 else 1.0
            values.append(a)
        return values


class MaZhengScale(Scale):
    """Шкала Ма-Чженґа (9/9–9/1)"""

    def __init__(self):
        super().__init__(ScaleType.MA_ZHENG, 9)
        self.labels = [
            "Менше",
            "Слабке або незначно",
            "Середнє",
            "Більше ніж середнє",
            "Сильно",
            "Більше ніж сильно",
            "Дуже сильно",
            "Дуже-дуже сильно",
            "Абсолютно"
        ]

    def _calculate_values(self):
        # Внутрішні значення: 9/9, 9/8, 9/7, 9/6, 9/5, 9/4, 9/3, 9/2, 9/1
        values = []
        for i in range(9, 0, -1):
            values.append(9.0 / i)
        return values


class DoneganScale(Scale):
    """Шкала Донеган–Додд–МакМастер"""

    def __init__(self):
        super().__init__(ScaleType.DONEGAN, 9)
        self.labels = [
            "Менше",
            "Слабке або незначно",
            "Середнє",
            "Більше ніж середнє",
            "Сильно",
            "Більше ніж сильно",
            "Дуже сильно",
            "Дуже-дуже сильно",
            "Абсолютно"
        ]

    def _calculate_values(self):
        # Внутрішні значення рівнів згідно зі шкалою Донеган–Додд–МакМастер
        return [1.0, 1.132, 1.287, 1.477, 1.720, 2.060, 2.600, 3.732, 9.0]


def get_scale(scale_name, gradations=9):
    """Фабрика для створення об'єктів шкал

    Args:
        scale_name: Назва шкали
        gradations: Кількість градацій (для збалансованої та степеневої шкал)
    """
    if scale_name == ScaleType.INTEGER:
        return IntegerScale()
    elif scale_name == ScaleType.BALANCED:
        return BalancedScale(gradations)
    elif scale_name == ScaleType.POWER:
        return PowerScale(gradations)
    elif scale_name == ScaleType.MA_ZHENG:
        return MaZhengScale()
    elif scale_name == ScaleType.DONEGAN:
        return DoneganScale()
    elif scale_name == ScaleType.ORDINAL:
        return OrdinalScale()
    else:
        return IntegerScale()  # за замовчуванням


def get_all_scale_names():
    """Отримати список всіх доступних шкал"""
    return [
        ScaleType.INTEGER,
        ScaleType.BALANCED,
        ScaleType.POWER,
        ScaleType.MA_ZHENG,
        ScaleType.DONEGAN,
        ScaleType.ORDINAL
    ]
