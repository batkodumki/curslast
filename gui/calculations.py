"""
Модуль для розрахунку ваг та перевірки узгодженості
"""

import numpy as np
from scipy import linalg


# Випадковий індекс (Random Index) для різних розмірів матриці
RANDOM_INDEX = {
    1: 0.00,
    2: 0.00,
    3: 0.58,
    4: 0.90,
    5: 1.12,
    6: 1.24,
    7: 1.32,
    8: 1.41,
    9: 1.45,
    10: 1.49,
    11: 1.51,
    12: 1.48,
    13: 1.56,
    14: 1.57,
    15: 1.59
}


def calculate_weights_eigenvector(comparison_matrix):
    """
    Розрахувати ваги методом власного вектора

    Args:
        comparison_matrix: матриця парних порівнянь (numpy array)

    Returns:
        normalized_weights: нормалізовані ваги (сума = 1)
    """
    n = len(comparison_matrix)

    # Знайти власні значення та власні вектори
    eigenvalues, eigenvectors = linalg.eig(comparison_matrix)

    # Знайти індекс максимального власного значення
    max_eigenvalue_index = np.argmax(eigenvalues.real)

    # Отримати відповідний власний вектор
    principal_eigenvector = eigenvectors[:, max_eigenvalue_index].real

    # Нормалізувати (всі значення додатні, сума = 1)
    weights = np.abs(principal_eigenvector)
    normalized_weights = weights / np.sum(weights)

    return normalized_weights


def calculate_weights_geometric_mean(comparison_matrix):
    """
    Розрахувати ваги методом геометричного середнього

    Args:
        comparison_matrix: матриця парних порівнянь (numpy array)

    Returns:
        normalized_weights: нормалізовані ваги (сума = 1)
    """
    n = len(comparison_matrix)

    # Обчислити геометричне середнє для кожного рядка
    geometric_means = np.zeros(n)
    for i in range(n):
        product = np.prod(comparison_matrix[i, :])
        geometric_means[i] = product ** (1.0 / n)

    # Нормалізувати
    normalized_weights = geometric_means / np.sum(geometric_means)

    return normalized_weights


def calculate_lambda_max(comparison_matrix, weights):
    """
    Розрахувати максимальне власне значення λ_max

    Args:
        comparison_matrix: матриця парних порівнянь
        weights: вектор ваг

    Returns:
        lambda_max: максимальне власне значення
    """
    n = len(weights)

    # λ_max = сума[(A·w)_i / w_i] / n
    weighted_sum = np.dot(comparison_matrix, weights)
    lambda_max = np.sum(weighted_sum / weights) / n

    return lambda_max


def calculate_consistency_index(lambda_max, n):
    """
    Розрахувати індекс узгодженості (Consistency Index)

    Args:
        lambda_max: максимальне власне значення
        n: розмір матриці

    Returns:
        CI: індекс узгодженості
    """
    if n <= 1:
        return 0.0

    CI = (lambda_max - n) / (n - 1)
    return CI


def calculate_consistency_ratio(CI, n):
    """
    Розрахувати коефіцієнт узгодженості (Consistency Ratio)

    Args:
        CI: індекс узгодженості
        n: розмір матриці

    Returns:
        CR: коефіцієнт узгодженості
    """
    if n <= 2:
        return 0.0

    RI = RANDOM_INDEX.get(n, 1.49)
    CR = CI / RI if RI > 0 else 0.0

    return CR


def check_consistency(comparison_matrix, weights, threshold=0.10):
    """
    Перевірити узгодженість матриці парних порівнянь

    Args:
        comparison_matrix: матриця парних порівнянь
        weights: вектор ваг
        threshold: порогове значення CR (за замовчуванням 0.10)

    Returns:
        dict з результатами: lambda_max, CI, CR, is_consistent, recommendations
    """
    n = len(weights)

    # Розрахувати λ_max
    lambda_max = calculate_lambda_max(comparison_matrix, weights)

    # Розрахувати CI
    CI = calculate_consistency_index(lambda_max, n)

    # Розрахувати CR
    CR = calculate_consistency_ratio(CI, n)

    # Перевірити узгодженість
    is_consistent = CR <= threshold

    # Рекомендації
    recommendations = []
    if not is_consistent:
        recommendations.append(f"Коефіцієнт узгодженості CR = {CR:.4f} перевищує поріг {threshold}")
        recommendations.append("Рекомендується переглянути парні порівняння")
        recommendations.append("Знайдіть найбільш неузгоджені пари та скоригуйте оцінки")
    else:
        recommendations.append(f"Оцінки узгоджені (CR = {CR:.4f} ≤ {threshold})")

    return {
        'lambda_max': lambda_max,
        'CI': CI,
        'CR': CR,
        'is_consistent': is_consistent,
        'recommendations': recommendations
    }


def build_comparison_matrix(n, comparisons):
    """
    Побудувати матрицю парних порівнянь

    Args:
        n: кількість альтернатив
        comparisons: список порівнянь у форматі [(i, j, value), ...]
                    де i, j - індекси альтернатив, value - уніфіковане значення

    Returns:
        comparison_matrix: матриця парних порівнянь (numpy array)
    """
    matrix = np.ones((n, n))

    for i, j, value in comparisons:
        matrix[i, j] = value
        matrix[j, i] = 1.0 / value if value > 0 else 1.0

    return matrix
