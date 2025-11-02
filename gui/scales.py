"""
Модуль для роботи зі шкалами оцінювання та уніфікації
"""

import numpy as np


class ScaleType:
    """Типи шкал для експертного оцінювання"""
    ORDINAL = "Порядкова"
    INTEGER = "Цілочислова (9)"
    BALANCED_3 = "Збалансована (3)"
    BALANCED_5 = "Збалансована (5)"
    BALANCED_9 = "Збалансована (9)"
    POWER_3 = "Степенева (3)"
    POWER_5 = "Степенева (5)"
    POWER_9 = "Степенева (9)"
    MA_ZHENG = "Ма-Чженга"
    DONEGAN = "Донегана-Додд-МакМастера"


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
    """Порядкова шкала (2 градації)"""

    def __init__(self):
        super().__init__(ScaleType.ORDINAL, 2)
        self.labels = ["Менше", "Більше"]

    def _calculate_values(self):
        return [1.0, 9.0]


class IntegerScale(Scale):
    """Цілочислова шкала (9 градацій)"""

    def __init__(self):
        super().__init__(ScaleType.INTEGER, 9)
        self.labels = [
            "Рівноцінно",
            "Незначно краще",
            "Слабко краще",
            "Помірно краще",
            "Сильно краще",
            "Дуже сильно краще",
            "Очевидно краще",
            "Явно краще",
            "Абсолютно краще"
        ]

    def _calculate_values(self):
        return list(range(1, 10))


class BalancedScale(Scale):
    """Збалансована шкала: a = w/(1-w)"""

    def __init__(self, gradations):
        if gradations not in [3, 5, 9]:
            raise ValueError("Збалансована шкала підтримує 3, 5 або 9 градацій")
        super().__init__(f"{ScaleType.BALANCED_3.split(' ')[0]} ({gradations})", gradations)

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

    def __init__(self, gradations):
        if gradations not in [3, 5, 9]:
            raise ValueError("Степенева шкала підтримує 3, 5 або 9 градацій")
        super().__init__(f"{ScaleType.POWER_3.split(' ')[0]} ({gradations})", gradations)

    def _calculate_values(self):
        n = self.gradations
        values = []
        for x in range(1, n + 1):
            a = 9 ** ((x - 1) / (n - 1)) if n > 1 else 1.0
            values.append(a)
        return values


class MaZhengScale(Scale):
    """Шкала Ма-Чженга: a = y/(y+1-x)"""

    def __init__(self):
        self.y = 9
        super().__init__(ScaleType.MA_ZHENG, 9)

    def _calculate_values(self):
        values = []
        for x in range(1, 10):
            a = self.y / (self.y + 1 - x)
            values.append(a)
        return values


class DoneganScale(Scale):
    """Шкала Донегана-Додд-МакМастера: a = exp[arctanh((x-1)/(h-1))]"""

    def __init__(self):
        self.h = 9
        super().__init__(ScaleType.DONEGAN, 9)

    def _calculate_values(self):
        values = []
        for x in range(1, 10):
            if self.h > 1:
                arg = (x - 1) / (self.h - 1)
                # arctanh(z) = 0.5 * ln((1+z)/(1-z))
                if abs(arg) < 0.99:  # Запобігаємо переповненню
                    arctanh_val = 0.5 * np.log((1 + arg) / (1 - arg))
                    a = np.exp(arctanh_val)
                elif arg >= 0.99:
                    # Для arg близького до 1, використовуємо велике значення
                    a = 9.0  # максимальне значення шкали
                else:
                    a = 1.0
            else:
                a = 1.0
            values.append(a)
        return values


def get_scale(scale_name):
    """Фабрика для створення об'єктів шкал"""
    if scale_name == ScaleType.ORDINAL:
        return OrdinalScale()
    elif scale_name == ScaleType.INTEGER:
        return IntegerScale()
    elif scale_name == ScaleType.BALANCED_3:
        return BalancedScale(3)
    elif scale_name == ScaleType.BALANCED_5:
        return BalancedScale(5)
    elif scale_name == ScaleType.BALANCED_9:
        return BalancedScale(9)
    elif scale_name == ScaleType.POWER_3:
        return PowerScale(3)
    elif scale_name == ScaleType.POWER_5:
        return PowerScale(5)
    elif scale_name == ScaleType.POWER_9:
        return PowerScale(9)
    elif scale_name == ScaleType.MA_ZHENG:
        return MaZhengScale()
    elif scale_name == ScaleType.DONEGAN:
        return DoneganScale()
    else:
        return IntegerScale()  # за замовчуванням


def get_all_scale_names():
    """Отримати список всіх доступних шкал"""
    return [
        ScaleType.ORDINAL,
        ScaleType.INTEGER,
        ScaleType.BALANCED_3,
        ScaleType.BALANCED_5,
        ScaleType.BALANCED_9,
        ScaleType.POWER_3,
        ScaleType.POWER_5,
        ScaleType.POWER_9,
        ScaleType.MA_ZHENG,
        ScaleType.DONEGAN
    ]
