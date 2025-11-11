"""
Модуль для експорту візуальних порівнянь у PNG зображення
Генерує зображення терезів з кубиками для кожного рівня впливу
"""

import os
from PIL import Image, ImageDraw, ImageFont


# Визначення рівнів впливу та відповідних значень
# Значення показують інтенсивність впливу (більше значення = більший вплив)
IMPACT_LEVELS = {
    "Слабко або незначно": {
        "filename": "slabko-abo-neznachno.png",
        "value": 1.5
    },
    "Середнє": {
        "filename": "serednie.png",
        "value": 3.0
    },
    "Більше ніж середнє": {
        "filename": "bil-she-nizh-serednie.png",
        "value": 4.5
    },
    "Сильно": {
        "filename": "sylno.png",
        "value": 5.0
    },
    "Більше ніж сильно": {
        "filename": "bil-she-nizh-sylno.png",
        "value": 6.0
    },
    "Дуже сильно": {
        "filename": "duzhe-sylno.png",
        "value": 7.0
    },
    "Дуже-дуже сильно": {
        "filename": "duzhe-duzhe-sylno.png",
        "value": 8.0
    },
    "Абсолютно": {
        "filename": "absolutno.png",
        "value": 9.0
    },
    "Абсолютна перевага": {
        "filename": "absolutna-perevaha.png",
        "value": 9.5
    }
}


class BalanceScaleVisualizer:
    """Клас для створення візуалізацій терезів"""

    def __init__(self, width=800, height=600):
        self.width = width
        self.height = height
        self.bg_color = (255, 255, 255)  # Білий фон

        # Кольори (з app.py)
        self.primary_color = (74, 144, 226)      # Синій для лівого кубика
        self.accent_color = (255, 107, 107)      # Коралевий для правого кубика
        self.text_color = (44, 62, 80)           # Темний текст
        self.gray_color = (127, 140, 141)        # Сірий для терезів

    def draw_balance_scale(self, draw, center_x, center_y, tilt_angle=0):
        """
        Намалювати терези з нахилом
        tilt_angle: додатний - нахил вліво (лівий важчий), від'ємний - вправо
        """
        # Розміри терезів
        fulcrum_size = 30
        beam_length = 200
        chain_height = 60

        # Намалювати опору (трикутник)
        fulcrum_points = [
            (center_x, center_y - fulcrum_size),
            (center_x - fulcrum_size, center_y + 15),
            (center_x + fulcrum_size, center_y + 15)
        ]
        draw.polygon(fulcrum_points, fill=self.gray_color, outline=self.text_color)

        # Обчислити позиції кінців балки з урахуванням нахилу
        left_x = center_x - beam_length
        right_x = center_x + beam_length

        # Нахил: позитивний - ліва сторона вище, негативний - права сторона вище
        left_y = center_y - fulcrum_size - int(tilt_angle * 20)
        right_y = center_y - fulcrum_size + int(tilt_angle * 20)

        # Намалювати балку
        draw.line([(left_x, left_y), (right_x, right_y)],
                 fill=self.text_color, width=6)

        # Намалювати ланцюжки для чаш
        # Ліва чаша
        draw.line([(left_x - 40, left_y), (left_x - 40, left_y + chain_height)],
                 fill=self.gray_color, width=3)
        draw.line([(left_x + 40, left_y), (left_x + 40, left_y + chain_height)],
                 fill=self.gray_color, width=3)

        # Права чаша
        draw.line([(right_x - 40, right_y), (right_x - 40, right_y + chain_height)],
                 fill=self.gray_color, width=3)
        draw.line([(right_x + 40, right_y), (right_x + 40, right_y + chain_height)],
                 fill=self.gray_color, width=3)

        # Намалювати чаші (плоскі платформи)
        plate_width = 90
        plate_height = 8

        # Ліва чаша
        left_plate_y = left_y + chain_height
        draw.rectangle([left_x - plate_width//2, left_plate_y,
                       left_x + plate_width//2, left_plate_y + plate_height],
                      fill=self.gray_color, outline=self.text_color, width=2)

        # Права чаша
        right_plate_y = right_y + chain_height
        draw.rectangle([right_x - plate_width//2, right_plate_y,
                       right_x + plate_width//2, right_plate_y + plate_height],
                      fill=self.gray_color, outline=self.text_color, width=2)

        return left_x, left_plate_y, right_x, right_plate_y

    def draw_cube(self, draw, center_x, bottom_y, size, color, label=None):
        """
        Намалювати кубик НА чаші (bottom_y - це низ кубика)
        label: текст для відображення на кубику (наприклад, значення)
        """
        # Кубик малюється знизу вгору
        top_y = bottom_y - size
        left_x = center_x - size // 2
        right_x = center_x + size // 2

        # Основний прямокутник (передня грань)
        draw.rectangle([left_x, top_y, right_x, bottom_y],
                      fill=color, outline=self.text_color, width=3)

        # Додати 3D ефект (верхня грань)
        depth = size // 4
        top_points = [
            (left_x, top_y),
            (left_x + depth, top_y - depth),
            (right_x + depth, top_y - depth),
            (right_x, top_y)
        ]
        # Зробити верхню грань трохи світлішою
        lighter_color = tuple(min(c + 30, 255) for c in color)
        draw.polygon(top_points, fill=lighter_color, outline=self.text_color)

        # Права грань для 3D ефекту
        right_points = [
            (right_x, top_y),
            (right_x + depth, top_y - depth),
            (right_x + depth, bottom_y - depth),
            (right_x, bottom_y)
        ]
        # Зробити праву грань трохи темнішою
        darker_color = tuple(max(c - 30, 0) for c in color)
        draw.polygon(right_points, fill=darker_color, outline=self.text_color)

        # Додати підпис значення на кубику
        if label:
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                                         max(16, size // 3))
            except:
                font = ImageFont.load_default()

            # Центрувати текст на передній грані кубика
            bbox = draw.textbbox((0, 0), label, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            text_x = center_x - text_width // 2
            text_y = (top_y + bottom_y) // 2 - text_height // 2

            # Білий текст з чорною обводкою для контрасту
            for offset in [(-1,-1), (-1,1), (1,-1), (1,1)]:
                draw.text((text_x + offset[0], text_y + offset[1]),
                         label, font=font, fill=(0, 0, 0))
            draw.text((text_x, text_y), label, font=font, fill=(255, 255, 255))

    def create_visual(self, impact_name, impact_value):
        """
        Створити візуалізацію для рівня впливу
        impact_value: значення від 1 до 9.5
        """
        # Створити зображення
        img = Image.new('RGB', (self.width, self.height), self.bg_color)
        draw = ImageDraw.Draw(img)

        # Центр терезів
        center_x = self.width // 2
        center_y = self.height // 2

        # Розрахувати нахил та розміри кубиків
        # Більше значення = правий кубик важчий = нахил вправо (негативний кут)
        # ВИПРАВЛЕНО: Використовуємо квадратний корінь замість кубічного для кращої візуалізації
        # Це робить різницю більш помітною
        scale_factor = (impact_value / 5.0) ** 0.5

        # Базовий розмір кубика
        base_cube_size = 60  # Збільшено для кращої видимості підписів

        # Розміри кубиків
        left_cube_size = base_cube_size  # Лівий завжди базовий (значення 1.0)
        right_cube_size = int(base_cube_size * scale_factor)

        # Нахил терезів (більше значення = більший нахил)
        # ВИПРАВЛЕНО: Збільшено діапазон нахилу для кращої візуалізації
        if impact_value > 5.0:
            tilt_angle = -min((impact_value - 5.0) / 3.0, 1.5)  # Нахил вправо (посилений)
        elif impact_value < 5.0:
            tilt_angle = min((5.0 - impact_value) / 2.5, 1.5)   # Нахил вліво (посилений)
        else:
            tilt_angle = 0  # Рівновага

        # Намалювати терези та отримати позиції чаш
        left_x, left_plate_y, right_x, right_plate_y = \
            self.draw_balance_scale(draw, center_x, center_y, tilt_angle)

        # Намалювати кубики НА чашах з підписами значень
        # Кубики розміщуються на платформах чаш
        # Лівий кубик завжди має значення 1.0 (базова одиниця)
        self.draw_cube(draw, left_x, left_plate_y, left_cube_size,
                      self.primary_color, label="1.0")
        # Правий кубик показує значення впливу
        self.draw_cube(draw, right_x, right_plate_y, right_cube_size,
                      self.accent_color, label=f"{impact_value:.1f}")

        # Додати підпис знизу
        try:
            # Спробувати завантажити системний шрифт
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
        except:
            # Якщо не вдалося, використати стандартний
            font = ImageFont.load_default()

        # Намалювати текст по центру знизу
        text = impact_name

        # Отримати розмір тексту для центрування
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        text_x = (self.width - text_width) // 2
        text_y = self.height - 80

        # Малювати текст з обводкою для кращої читабельності
        # Обводка
        for offset_x in [-2, 0, 2]:
            for offset_y in [-2, 0, 2]:
                if offset_x != 0 or offset_y != 0:
                    draw.text((text_x + offset_x, text_y + offset_y),
                            text, font=font, fill=(255, 255, 255))

        # Основний текст
        draw.text((text_x, text_y), text, font=font, fill=self.text_color)

        # Додати пояснення шкали (легенда)
        try:
            legend_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
        except:
            legend_font = ImageFont.load_default()

        legend_text = f"Співвідношення ваги: 1.0 : {impact_value:.1f}"
        bbox = draw.textbbox((0, 0), legend_text, font=legend_font)
        legend_width = bbox[2] - bbox[0]
        legend_x = (self.width - legend_width) // 2
        legend_y = self.height - 45

        draw.text((legend_x, legend_y), legend_text, font=legend_font,
                 fill=self.gray_color)

        return img


def export_all_visuals(output_dir="exported_visuals"):
    """
    Пакетна генерація всіх візуальних порівнянь
    """
    # Створити папку якщо не існує
    os.makedirs(output_dir, exist_ok=True)

    # Створити візуалізатор
    visualizer = BalanceScaleVisualizer(width=800, height=600)

    print(f"Генерація візуальних порівнянь у папку {output_dir}/\n")

    # Згенерувати зображення для кожного рівня
    for impact_name, data in IMPACT_LEVELS.items():
        filename = data["filename"]
        value = data["value"]

        print(f"  Генерація: {filename} ({impact_name}, значення={value})")

        # Створити зображення
        img = visualizer.create_visual(impact_name, value)

        # Зберегти
        output_path = os.path.join(output_dir, filename)
        img.save(output_path, "PNG")

        print(f"    ✓ Збережено: {output_path}")

    print(f"\n✓ Готово! Згенеровано {len(IMPACT_LEVELS)} зображень у {output_dir}/")


if __name__ == "__main__":
    # Запустити пакетну генерацію
    export_all_visuals()
