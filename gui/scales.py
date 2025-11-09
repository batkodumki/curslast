"""
Модуль для роботи зі шкалами оцінювання та уніфікації
"""

import numpy as np


def get_progressive_labels(gradations):
    """Отримати підписи для поточної кількості градацій (3-9)
    Використовує Saaty-style descriptive labels

    Args:
        gradations: Кількість градацій від 3 до 9

    Returns:
        Список підписів для сегментів
    """
    # Повний набір підписів для 9 градацій (Saaty-style)
    all_labels = [
        "Equally",                   # 1 - Рівно
        "Slightly",                  # 2 - Незначно
        "Moderately",                # 3 - Середньо
        "Moderately+",               # 4 - Середньо+
        "Strongly",                  # 5 - Сильно
        "Strongly+",                 # 6 - Сильно+
        "Very strongly",             # 7 - Дуже сильно
        "Very very strongly",        # 8 - Дуже-дуже сильно
        "Extremely"                  # 9 - Надзвичайно
    ]

    # Індекси для кожної кількості градацій
    label_indices = {
        3: [0, 1, 4],                      # Equally, Slightly, Strongly
        4: [0, 1, 2, 4],                   # + Moderately
        5: [0, 1, 2, 3, 4],                # + Moderately+
        6: [0, 1, 2, 3, 4, 5],             # + Strongly+
        7: [0, 1, 2, 3, 4, 5, 6],          # + Very strongly
        8: [0, 1, 2, 3, 4, 5, 6, 7],       # + Very very strongly
        9: [0, 1, 2, 3, 4, 5, 6, 7, 8]     # + Extremely
    }

    if gradations not in label_indices:
        gradations = 9

    indices = label_indices[gradations]
    return [all_labels[i] for i in indices]


class ScaleType:
    """Типи шкал для експертного оцінювання"""
    INTEGER = "Цілочислова"
    BALANCED = "Збалансована"
    POWER = "Степенева"
    MA_ZHENG = "Ма-Чженґа (9/9–9/1)"
    DONEGAN = "Донеган–Додд–МакМастер"


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


class IntegerScale(Scale):
    """Цілочислова шкала (3-9 градацій)

    Класична шкала Сааті з рівномірно розподіленими цілочисловими значеннями.
    Підтримує від 3 до 9 градацій з прогресивним підбором вербальних підписів.
    """

    def __init__(self, gradations=3):
        if gradations < 3 or gradations > 9:
            raise ValueError("Цілочислова шкала підтримує від 3 до 9 градацій")
        super().__init__(ScaleType.INTEGER, gradations)
        self.labels = get_progressive_labels(gradations)

    def _calculate_values(self):
        # Для n градацій вибираємо рівномірно розподілені значення з діапазону 1-9
        n = self.gradations
        if n == 9:
            return list(range(1, 10))
        else:
            # Рівномірний підсемплінг з 9 значень
            all_values = list(range(1, 10))
            step = 8 / (n - 1)  # 8 це різниця між 9 та 1
            indices = [int(i * step) for i in range(n)]
            return [all_values[i] for i in indices]


class BalancedScale(Scale):
    """Збалансована шкала: a = w/(1-w) (3-9 градацій)

    Шкала з рівномірним розподілом ваг від 1/(n+1) до n/(n+1).
    Забезпечує збалансований розподіл переваг між альтернативами.
    Підтримує від 3 до 9 градацій з прогресивним підбором вербальних підписів.
    """

    def __init__(self, gradations=3):
        if gradations < 3 or gradations > 9:
            raise ValueError("Збалансована шкала підтримує від 3 до 9 градацій")
        super().__init__(ScaleType.BALANCED, gradations)
        self.labels = get_progressive_labels(gradations)

    def _calculate_values(self):
        n = self.gradations
        values = []
        for i in range(1, n + 1):
            w = i / (n + 1)  # розподіл ваг рівномірно від 1/(n+1) до n/(n+1)
            a = w / (1 - w) if w < 1 else 9.0
            values.append(a)
        return values


class PowerScale(Scale):
    """Степенева шкала: a = 9^((x-1)/(n-1)) (3-9 градацій)

    Експоненціальна шкала з прогресивним зростанням значень.
    Забезпечує більш виражену різницю на вищих градаціях.
    Підтримує від 3 до 9 градацій з прогресивним підбором вербальних підписів.
    """

    def __init__(self, gradations=3):
        if gradations < 3 or gradations > 9:
            raise ValueError("Степенева шкала підтримує від 3 до 9 градацій")
        super().__init__(ScaleType.POWER, gradations)
        self.labels = get_progressive_labels(gradations)

    def _calculate_values(self):
        n = self.gradations
        values = []
        for x in range(1, n + 1):
            a = 9 ** ((x - 1) / (n - 1)) if n > 1 else 1.0
            values.append(a)
        return values


class MaZhengScale(Scale):
    """Шкала Ма-Чженґа (9/9–9/1) (3-9 градацій)

    Дробова шкала з значеннями від 9/9 (1.0) до 9/1 (9.0).
    Забезпечує альтернативний розподіл важливості з використанням дробів.
    Підтримує від 3 до 9 градацій з прогресивним підбором вербальних підписів.
    """

    def __init__(self, gradations=3):
        if gradations < 3 or gradations > 9:
            raise ValueError("Шкала Ма-Чженґа підтримує від 3 до 9 градацій")
        super().__init__(ScaleType.MA_ZHENG, gradations)
        self.labels = get_progressive_labels(gradations)

    def _calculate_values(self):
        # Повний набір для 9 градацій: 9/9, 9/8, 9/7, 9/6, 9/5, 9/4, 9/3, 9/2, 9/1
        all_values = [9.0 / i for i in range(9, 0, -1)]

        n = self.gradations
        if n == 9:
            return all_values
        else:
            # Рівномірний підсемплінг
            step = 8 / (n - 1)  # 8 індексів (від 0 до 8)
            indices = [int(i * step) for i in range(n)]
            return [all_values[i] for i in indices]


class DoneganScale(Scale):
    """Шкала Донеган–Додд–МакМастер (3-9 градацій)

    Експоненціальна шкала з науково обґрунтованими значеннями.
    Використовує спеціально розраховані коефіцієнти для точного оцінювання.
    Підтримує від 3 до 9 градацій з прогресивним підбором вербальних підписів.
    """

    def __init__(self, gradations=3):
        if gradations < 3 or gradations > 9:
            raise ValueError("Шкала Донеган–Додд–МакМастер підтримує від 3 до 9 градацій")
        super().__init__(ScaleType.DONEGAN, gradations)
        self.labels = get_progressive_labels(gradations)

    def _calculate_values(self):
        # Повний набір для 9 градацій
        all_values = [1.0, 1.132, 1.287, 1.477, 1.720, 2.060, 2.600, 3.732, 9.0]

        n = self.gradations
        if n == 9:
            return all_values
        else:
            # Рівномірний підсемплінг
            step = 8 / (n - 1)  # 8 індексів (від 0 до 8)
            indices = [int(i * step) for i in range(n)]
            return [all_values[i] for i in indices]


def get_scale(scale_name, gradations=3):
    """Фабрика для створення об'єктів шкал

    Args:
        scale_name: Назва шкали
        gradations: Кількість градацій (від 3 до 9)
    """
    if scale_name == ScaleType.INTEGER:
        return IntegerScale(gradations)
    elif scale_name == ScaleType.BALANCED:
        return BalancedScale(gradations)
    elif scale_name == ScaleType.POWER:
        return PowerScale(gradations)
    elif scale_name == ScaleType.MA_ZHENG:
        return MaZhengScale(gradations)
    elif scale_name == ScaleType.DONEGAN:
        return DoneganScale(gradations)
    else:
        return IntegerScale(gradations)  # за замовчуванням


def get_all_scale_names():
    """Отримати список всіх доступних шкал"""
    return [
        ScaleType.INTEGER,
        ScaleType.BALANCED,
        ScaleType.POWER,
        ScaleType.MA_ZHENG,
        ScaleType.DONEGAN
    ]
