"""
Модуль для експорту візуальних порівнянь у PNG зображення
Генерує спрощені зображення терезів з кубиками на балці
"""

import os
import math
from PIL import Image, ImageDraw


# Визначення рівнів впливу (тільки More напрямок, без Less і проміжного "Більше ніж сильно")
IMPACT_LEVELS = {
    "slabko-abo-neznachno": {
        "tilt": 0.05,      # мінімальний нахил
        "size_ratio": 1.15  # правий трохи більший
    },
    "serednie": {
        "tilt": 0.15,
        "size_ratio": 1.35
    },
    "bil-she-nizh-serednie": {
        "tilt": 0.25,
        "size_ratio": 1.55
    },
    "sylno": {
        "tilt": 0.35,
        "size_ratio": 1.75
    },
    "duzhe-sylno": {
        "tilt": 0.45,
        "size_ratio": 2.0
    },
    "duzhe-duzhe-sylno": {
        "tilt": 0.60,
        "size_ratio": 2.3
    },
    "absolutno": {
        "tilt": 0.75,      # екстремальний нахил
        "size_ratio": 2.7
    }
}


class SimpleBalanceVisualizer:
    """Клас для створення спрощених візуалізацій терезів"""

    def __init__(self, size=512):
        self.size = size
        self.bg_color = (248, 248, 248)  # Світлий фон

        # Кольори
        self.left_cube_color = (74, 144, 226)    # Синій
        self.right_cube_color = (255, 107, 107)  # Червоний
        self.outline_color = (60, 60, 60)        # Темно-сірий
        self.beam_color = (100, 100, 100)        # Сірий

    def draw_cube_on_beam(self, draw, center_x, beam_y, size, color):
        """
        Намалювати 3D кубик що стоїть НА балці
        center_x: центр кубика по X
        beam_y: Y-координата верху балки (кубик стоїть на цій лінії)
        size: розмір кубика
        """
        half_size = size // 2

        # Кубик стоїть на балці, тому його низ на beam_y
        bottom_y = beam_y
        top_y = beam_y - size
        left_x = center_x - half_size
        right_x = center_x + half_size

        # 3D ефект: глибина для перспективи
        depth = size // 3

        # Передня грань (основна)
        draw.rectangle(
            [left_x, top_y, right_x, bottom_y],
            fill=color,
            outline=self.outline_color,
            width=2
        )

        # Верхня грань (паралелограм, світліший)
        lighter_color = tuple(min(c + 40, 255) for c in color)
        top_face = [
            (left_x, top_y),
            (left_x + depth, top_y - depth),
            (right_x + depth, top_y - depth),
            (right_x, top_y)
        ]
        draw.polygon(top_face, fill=lighter_color, outline=self.outline_color)

        # Права грань (паралелограм, темніший)
        darker_color = tuple(max(c - 40, 0) for c in color)
        right_face = [
            (right_x, top_y),
            (right_x + depth, top_y - depth),
            (right_x + depth, bottom_y - depth),
            (right_x, bottom_y)
        ]
        draw.polygon(right_face, fill=darker_color, outline=self.outline_color)

    def create_visual(self, tilt_angle, size_ratio):
        """
        Створити візуалізацію терезів
        tilt_angle: кут нахилу (0-1, де 1 = максимальний нахил)
        size_ratio: співвідношення розміру правого кубика до лівого
        """
        # Створити зображення
        img = Image.new('RGB', (self.size, self.size), self.bg_color)
        draw = ImageDraw.Draw(img)

        # Параметри композиції
        center_x = self.size // 2
        center_y = self.size // 2

        # Розміри
        beam_length = 180  # довжина балки від центру до краю
        fulcrum_size = 25  # розмір опори-трикутника
        base_cube_size = 50  # базовий розмір лівого кубика

        # Позиція опори (трикутника)
        fulcrum_y = center_y + 40

        # Намалювати опору (трикутник)
        fulcrum_points = [
            (center_x, fulcrum_y - fulcrum_size),
            (center_x - fulcrum_size, fulcrum_y + 15),
            (center_x + fulcrum_size, fulcrum_y + 15)
        ]
        draw.polygon(
            fulcrum_points,
            fill=self.beam_color,
            outline=self.outline_color,
            width=2
        )

        # Обчислити нахил балки
        # Правий важчий - правий кінець нижче
        max_tilt_pixels = 60  # максимальний зсув по Y
        tilt_pixels = int(tilt_angle * max_tilt_pixels)

        # Координати кінців балки
        left_x = center_x - beam_length
        right_x = center_x + beam_length

        beam_base_y = fulcrum_y - fulcrum_size + 5  # балка трохи вище вершини трикутника
        left_y = beam_base_y - tilt_pixels  # лівий кінець вище
        right_y = beam_base_y + tilt_pixels  # правий кінець нижче

        # Намалювати балку
        draw.line(
            [(left_x, left_y), (right_x, right_y)],
            fill=self.outline_color,
            width=4
        )

        # Розміри кубиків
        left_cube_size = base_cube_size
        right_cube_size = int(base_cube_size * size_ratio)

        # Позиції кубиків на балці
        # Кубики стоять на балці, трохи ближче до країв
        cube_offset = beam_length * 0.7  # 70% від довжини

        left_cube_x = int(center_x - cube_offset)
        right_cube_x = int(center_x + cube_offset)

        # Y-координати верху балки де стоять кубики (інтерполюємо по балці)
        left_cube_beam_y = int(left_y + (right_y - left_y) * (1 - cube_offset / beam_length) / 2)
        right_cube_beam_y = int(left_y + (right_y - left_y) * (1 + cube_offset / beam_length) / 2)

        # Намалювати кубики
        self.draw_cube_on_beam(draw, left_cube_x, left_cube_beam_y, left_cube_size, self.left_cube_color)
        self.draw_cube_on_beam(draw, right_cube_x, right_cube_beam_y, right_cube_size, self.right_cube_color)

        return img


def export_all_visuals(output_dir="exported_visuals"):
    """
    Пакетна генерація всіх візуальних порівнянь
    """
    # Створити папку якщо не існує
    os.makedirs(output_dir, exist_ok=True)

    # Створити візуалізатор
    visualizer = SimpleBalanceVisualizer(size=512)

    print(f"Генерація візуальних порівнянь у папку {output_dir}/\n")

    # Згенерувати зображення для кожного рівня
    for filename, params in IMPACT_LEVELS.items():
        tilt = params["tilt"]
        size_ratio = params["size_ratio"]

        print(f"  Генерація: {filename}.png (нахил={tilt:.2f}, розмір={size_ratio:.2f})")

        # Створити зображення
        img = visualizer.create_visual(tilt, size_ratio)

        # Зберегти
        output_path = os.path.join(output_dir, f"{filename}.png")
        img.save(output_path, "PNG")

        print(f"    ✓ Збережено: {output_path}")

    print(f"\n✓ Готово! Згенеровано {len(IMPACT_LEVELS)} зображень у {output_dir}/")


if __name__ == "__main__":
    # Запустити пакетну генерацію
    export_all_visuals()
