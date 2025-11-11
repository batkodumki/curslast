"""
Головний модуль GUI для системи експертного оцінювання
"""

import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import os
from PIL import Image, ImageTk

from gui.scales import get_scale, get_all_scale_names, ScaleType
from gui.calculations import (
    calculate_weights_eigenvector,
    calculate_weights_geometric_mean,
    build_comparison_matrix,
    check_consistency
)


# Mapping of scale labels to image filenames
LABEL_TO_IMAGE = {
    "Слабко або незначно": "slabko-abo-neznachno.png",
    "Середнє": "serednie.png",
    "Більше ніж середнє": "bil-she-nizh-serednie.png",
    "Сильно": "sylno.png",
    "Більше ніж сильно": "bil-she-nizh-sylno.png",
    "Дуже сильно": "duzhe-sylno.png",
    "Дуже-дуже сильно": "duzhe-duzhe-sylno.png",
    "Абсолютно": "absolutno.png",
    "Абсолютна перевага": "absolutna-perevaha.png"
}


class InputPanel(ttk.Frame):
    """Панель введення альтернатив"""

    def __init__(self, parent, on_next):
        super().__init__(parent)
        self.on_next = on_next
        self.entries = []

        self._create_widgets()

    def _create_widgets(self):
        # Заголовок
        title = ttk.Label(self, text="Введення альтернатив", font=('Arial', 16, 'bold'))
        title.pack(pady=20)

        # Інструкція
        instruction = ttk.Label(
            self,
            text="Введіть назви об'єктів для порівняння (мінімум 2):",
            font=('Arial', 10)
        )
        instruction.pack(pady=10)

        # Фрейм для полів введення
        self.entries_frame = ttk.Frame(self)
        self.entries_frame.pack(pady=10, padx=20, fill='both', expand=True)

        # Початкові поля
        for i in range(3):
            self._add_entry_field(i)

        # Кнопка додати поле
        add_btn = ttk.Button(
            self,
            text="+ Додати альтернативу",
            command=self._add_field
        )
        add_btn.pack(pady=10)

        # Кнопка далі
        next_btn = ttk.Button(
            self,
            text="Далі →",
            command=self._validate_and_next,
            style='Accent.TButton'
        )
        next_btn.pack(pady=20)

    def _add_entry_field(self, index):
        """Додати поле для введення альтернативи"""
        frame = ttk.Frame(self.entries_frame)
        frame.pack(fill='x', pady=5)

        label = ttk.Label(frame, text=f"Альтернатива {index + 1}:", width=15)
        label.pack(side='left', padx=5)

        entry = ttk.Entry(frame, width=40)
        entry.pack(side='left', padx=5, fill='x', expand=True)

        self.entries.append(entry)

    def _add_field(self):
        """Додати нове поле введення"""
        index = len(self.entries)
        self._add_entry_field(index)

    def _validate_and_next(self):
        """Перевірити введені дані та перейти далі"""
        alternatives = self.get_alternatives()

        if len(alternatives) < 2:
            messagebox.showerror(
                "Помилка",
                "Потрібно ввести мінімум 2 альтернативи"
            )
            return

        # Перевірка унікальності
        if len(alternatives) != len(set(alternatives)):
            messagebox.showerror(
                "Помилка",
                "Назви альтернатив повинні бути унікальними"
            )
            return

        self.on_next(alternatives)

    def get_alternatives(self):
        """Отримати список введених альтернатив"""
        alternatives = []
        for entry in self.entries:
            text = entry.get().strip()
            if text:
                alternatives.append(text)
        return alternatives


class ComparisonPanel(ttk.Frame):
    """Панель парних порівнянь"""

    def __init__(self, parent, alternatives, on_complete, on_back):
        super().__init__(parent)
        self.alternatives = alternatives
        self.on_complete = on_complete
        self.on_back = on_back

        self.n = len(alternatives)
        self.total_pairs = (self.n * (self.n - 1)) // 2
        self.current_pair = 0
        self.comparisons = []
        self.pairs = self._generate_pairs()

        # Поточна вибрана шкала та градації
        self.scale_var = tk.StringVar(value=ScaleType.INTEGER)
        self.gradations_var = tk.IntVar(value=3)  # Початкова кількість градацій - 3
        self.selected_section = None

        # Image display
        self.current_image = None
        self.image_label = None

        self._create_widgets()
        self._update_gradations_label()  # Ініціалізувати стан кнопок градацій
        self._update_display()

    def _generate_pairs(self):
        """Генерувати всі пари для порівняння"""
        pairs = []
        for i in range(self.n):
            for j in range(i + 1, self.n):
                pairs.append((i, j))
        return pairs

    def _create_widgets(self):
        # Головний контейнер - горизонтальне розділення
        main_container = ttk.Frame(self)
        main_container.pack(fill='both', expand=True, padx=10, pady=10)

        # ===== ЛІВА ПАНЕЛЬ - Підбір шкали =====
        left_panel = ttk.LabelFrame(main_container, text="Підбір шкали", width=200)
        left_panel.pack(side='left', fill='y', padx=(0, 10))
        left_panel.pack_propagate(False)

        # Radio buttons для вибору шкали
        scales = get_all_scale_names()
        for scale_name in scales:
            rb = ttk.Radiobutton(
                left_panel,
                text=scale_name,
                variable=self.scale_var,
                value=scale_name,
                command=self._on_scale_changed
            )
            rb.pack(anchor='w', padx=10, pady=5)

        # Кнопки для зміни градацій
        self.gradations_frame = ttk.Frame(left_panel)
        self.gradations_frame.pack(anchor='w', padx=10, pady=10, fill='x')

        ttk.Label(self.gradations_frame, text="Градації:").pack(anchor='w', pady=5)

        # Кнопки +/-
        buttons_frame = ttk.Frame(self.gradations_frame)
        buttons_frame.pack(anchor='w', pady=5)

        self.minus_btn = ttk.Button(
            buttons_frame,
            text="− Прибрати градацію",
            command=self._decrease_gradations,
            width=20
        )
        self.minus_btn.pack(pady=2, fill='x')

        self.plus_btn = ttk.Button(
            buttons_frame,
            text="+ Додати градацію",
            command=self._increase_gradations,
            width=20
        )
        self.plus_btn.pack(pady=2, fill='x')

        # Лейбл для відображення поточної кількості
        self.gradations_label = ttk.Label(
            self.gradations_frame,
            text=f"Поточно: {self.gradations_var.get()} з 9",
            font=('Arial', 9)
        )
        self.gradations_label.pack(anchor='w', pady=5)

        # ===== ПРАВА ПАНЕЛЬ - Бар та кнопки =====
        right_panel = ttk.Frame(main_container)
        right_panel.pack(side='left', fill='both', expand=True)

        # Прогрес
        self.progress_label = ttk.Label(right_panel, text="", font=('Arial', 10))
        self.progress_label.pack(pady=5)

        # Заголовок з назвами альтернатив та "впливає Більше"
        header_frame = ttk.Frame(right_panel)
        header_frame.pack(fill='x', pady=10)

        self.obj_a_label = ttk.Label(header_frame, text="Object A", font=('Arial', 11))
        self.obj_a_label.pack(side='left')

        center_label = ttk.Label(header_frame, text="впливає Більше", font=('Arial', 11, 'bold'))
        center_label.pack(side='left', expand=True)

        self.obj_b_label = ttk.Label(header_frame, text="Object B", font=('Arial', 11))
        self.obj_b_label.pack(side='right')

        # Canvas для горизонтального бара
        self.bar_canvas = tk.Canvas(right_panel, height=80, bg='white')
        self.bar_canvas.pack(fill='x', pady=10)
        self.bar_canvas.bind('<Configure>', self._on_canvas_resize)
        self.bar_canvas.bind('<Button-1>', self._on_bar_click)
        self.bar_canvas.bind('<Motion>', self._on_bar_hover)

        # Image display area for balance scale visualization
        image_frame = ttk.LabelFrame(right_panel, text="Візуалізація порівняння", padding=10)
        image_frame.pack(fill='both', expand=True, pady=10)

        self.image_label = tk.Label(image_frame, bg='white')
        self.image_label.pack(fill='both', expand=True)

        # Кнопка "Підтверджую"
        confirm_btn = ttk.Button(
            right_panel,
            text="Підтверджую",
            command=self._confirm_comparison,
            style='Accent.TButton'
        )
        confirm_btn.pack(pady=20)

        # Кнопки навігації внизу
        nav_frame = ttk.Frame(right_panel)
        nav_frame.pack(pady=10)

        back_btn = ttk.Button(
            nav_frame,
            text="← Попередня пара",
            command=self._go_back
        )
        back_btn.pack(side='left', padx=5)

        return_btn = ttk.Button(
            nav_frame,
            text="Повернутися до введення",
            command=self.on_back
        )
        return_btn.pack(side='left', padx=5)

    def _on_scale_changed(self, event=None):
        """Обробник зміни шкали"""
        # Скинути градації до 3
        self.gradations_var.set(3)

        # Скинути вибір секції
        self.selected_section = None

        # Скинути зображення
        if self.image_label:
            self.image_label.config(image='', text='Виберіть рівень впливу')
            self.current_image = None

        # Оновити лейбл градацій
        self._update_gradations_label()

        # Перемалювати бар
        self._draw_bar()

    def _increase_gradations(self):
        """Збільшити кількість градацій на 1"""
        current = self.gradations_var.get()
        if current < 9:
            self.gradations_var.set(current + 1)
            self._update_gradations_label()
            self.selected_section = None
            # Скинути зображення
            if self.image_label:
                self.image_label.config(image='', text='Виберіть рівень впливу')
                self.current_image = None
            self._draw_bar()

    def _decrease_gradations(self):
        """Зменшити кількість градацій на 1"""
        current = self.gradations_var.get()
        if current > 3:
            self.gradations_var.set(current - 1)
            self._update_gradations_label()
            self.selected_section = None
            # Скинути зображення
            if self.image_label:
                self.image_label.config(image='', text='Виберіть рівень впливу')
                self.current_image = None
            self._draw_bar()

    def _update_gradations_label(self):
        """Оновити лейбл з поточною кількістю градацій"""
        current = self.gradations_var.get()
        self.gradations_label.config(text=f"Поточно: {current} з 9")

        # Оновити стан кнопок
        if current <= 3:
            self.minus_btn.config(state='disabled')
        else:
            self.minus_btn.config(state='normal')

        if current >= 9:
            self.plus_btn.config(state='disabled')
        else:
            self.plus_btn.config(state='normal')

    def _on_canvas_resize(self, event=None):
        """Обробник зміни розміру canvas"""
        self._draw_bar()

    def _on_bar_click(self, event):
        """Обробник кліку по бару"""
        # Визначити на яку секцію клікнули
        gradations = self.gradations_var.get()

        canvas_width = self.bar_canvas.winfo_width()
        section_width = canvas_width / gradations

        section_index = int(event.x / section_width)
        if 0 <= section_index < gradations:
            self.selected_section = section_index
            self._draw_bar()
            self._update_image_display(section_index)

    def _on_bar_hover(self, event):
        """Обробник наведення миші на бар (preview image)"""
        if self.selected_section is not None:
            # Якщо вже вибрано секцію, не оновлювати при наведенні
            return

        gradations = self.gradations_var.get()
        canvas_width = self.bar_canvas.winfo_width()
        section_width = canvas_width / gradations

        section_index = int(event.x / section_width)
        if 0 <= section_index < gradations:
            self._update_image_display(section_index)

    def _update_image_display(self, section_index):
        """Оновити відображення зображення для вибраної секції"""
        scale_name = self.scale_var.get()
        gradations = self.gradations_var.get()
        scale = get_scale(scale_name, gradations)

        # Отримати підпис для секції
        if hasattr(scale, 'labels') and section_index < len(scale.labels):
            label = scale.labels[section_index]

            # Знайти відповідне зображення
            if label in LABEL_TO_IMAGE:
                image_filename = LABEL_TO_IMAGE[label]
                image_path = os.path.join('exported_visuals', image_filename)

                if os.path.exists(image_path):
                    try:
                        # Завантажити зображення
                        img = Image.open(image_path)

                        # Масштабувати зображення для відображення (зберігаючи пропорції)
                        display_width = 600
                        display_height = 400
                        img.thumbnail((display_width, display_height), Image.Resampling.LANCZOS)

                        # Конвертувати для Tkinter
                        self.current_image = ImageTk.PhotoImage(img)

                        # Оновити label
                        self.image_label.config(image=self.current_image)
                    except Exception as e:
                        # Якщо помилка завантаження, показати повідомлення
                        self.image_label.config(image='', text=f'Помилка завантаження зображення:\n{label}')
                else:
                    self.image_label.config(image='', text=f'Зображення не знайдено:\n{label}')
            else:
                self.image_label.config(image='', text=f'Візуалізація:\n{label}')
        else:
            self.image_label.config(image='', text='Виберіть рівень впливу')

    def _draw_bar(self):
        """Намалювати горизонтальний бар з секціями"""
        # Очистити canvas
        self.bar_canvas.delete('all')

        scale_name = self.scale_var.get()
        gradations = self.gradations_var.get()

        scale = get_scale(scale_name, gradations)

        canvas_width = self.bar_canvas.winfo_width()
        canvas_height = self.bar_canvas.winfo_height()

        if canvas_width < 10:  # canvas ще не ініціалізовано
            return

        bar_height = 40
        bar_y = 30
        section_width = canvas_width / gradations

        # Намалювати секції
        for i in range(gradations):
            x1 = i * section_width
            x2 = (i + 1) * section_width

            # Колір секції - червоний, але темніший для вибраної
            if self.selected_section == i:
                fill_color = '#cc0000'
            else:
                fill_color = '#ff4444'

            # Намалювати прямокутник секції
            self.bar_canvas.create_rectangle(
                x1, bar_y, x2, bar_y + bar_height,
                fill=fill_color,
                outline='#880000',
                width=2
            )

            # Підпис секції
            if hasattr(scale, 'labels') and i < len(scale.labels):
                label = scale.labels[i]
                # Розмістити текст над секцією
                text_x = x1 + section_width / 2
                self.bar_canvas.create_text(
                    text_x, bar_y - 10,
                    text=label,
                    font=('Arial', 8),
                    anchor='s'
                )

    def _update_display(self):
        """Оновити відображення поточної пари"""
        if self.current_pair >= len(self.pairs):
            self._finish_comparisons()
            return

        i, j = self.pairs[self.current_pair]

        # Оновити прогрес
        self.progress_label.config(
            text=f"Порівняння {self.current_pair + 1} з {self.total_pairs}"
        )

        # Оновити назви альтернатив
        self.obj_a_label.config(text=self.alternatives[i])
        self.obj_b_label.config(text=self.alternatives[j])

        # Скинути вибір
        self.selected_section = None

        # Скинути зображення
        if self.image_label:
            self.image_label.config(image='', text='Виберіть рівень впливу')
            self.current_image = None

        # Перемалювати бар
        self._draw_bar()

    def _confirm_comparison(self):
        """Підтвердити поточне порівняння"""
        # Перевірити чи вибрано секцію
        if self.selected_section is None:
            messagebox.showwarning(
                "Попередження",
                "Будь ласка, виберіть рівень впливу, клікнувши на секції бара"
            )
            return

        i, j = self.pairs[self.current_pair]

        scale_name = self.scale_var.get()
        gradations = self.gradations_var.get()

        scale = get_scale(scale_name, gradations)

        # Отримати уніфіковане значення
        unified_value = scale.unify(self.selected_section)

        # Зберегти порівняння
        self.comparisons.append((i, j, unified_value))

        # Наступна пара
        self.current_pair += 1
        self._update_display()

    def _go_back(self):
        """Повернутися до попередньої пари"""
        if self.current_pair > 0:
            self.current_pair -= 1
            if self.comparisons:
                self.comparisons.pop()
            self._update_display()

    def _finish_comparisons(self):
        """Завершити порівняння"""
        self.on_complete(self.comparisons)


class ResultsPanel(ttk.Frame):
    """Панель результатів"""

    def __init__(self, parent, alternatives, comparisons, on_restart):
        super().__init__(parent)
        self.alternatives = alternatives
        self.comparisons = comparisons
        self.on_restart = on_restart

        self._calculate_results()
        self._create_widgets()

    def _calculate_results(self):
        """Розрахувати результати"""
        n = len(self.alternatives)

        # Побудувати матрицю порівнянь
        self.matrix = build_comparison_matrix(n, self.comparisons)

        # Розрахувати ваги
        self.weights = calculate_weights_eigenvector(self.matrix)

        # Розрахувати ранги
        self.ranks = np.argsort(-self.weights) + 1

        # Перевірити узгодженість
        self.consistency = check_consistency(self.matrix, self.weights)

    def _create_widgets(self):
        # Заголовок
        title = ttk.Label(self, text="Результати", font=('Arial', 16, 'bold'))
        title.pack(pady=20)

        # Таблиця результатів
        table_frame = ttk.Frame(self)
        table_frame.pack(pady=10, padx=20, fill='both', expand=True)

        # Заголовки таблиці
        headers = ['Альтернатива', 'Вага', 'Ранг']
        for col, header in enumerate(headers):
            label = ttk.Label(
                table_frame,
                text=header,
                font=('Arial', 11, 'bold'),
                relief='solid',
                borderwidth=1,
                width=20
            )
            label.grid(row=0, column=col, sticky='nsew', padx=1, pady=1)

        # Дані таблиці
        for i, alternative in enumerate(self.alternatives):
            # Альтернатива
            label = ttk.Label(
                table_frame,
                text=alternative,
                relief='solid',
                borderwidth=1
            )
            label.grid(row=i + 1, column=0, sticky='nsew', padx=1, pady=1)

            # Вага
            label = ttk.Label(
                table_frame,
                text=f"{self.weights[i]:.4f}",
                relief='solid',
                borderwidth=1
            )
            label.grid(row=i + 1, column=1, sticky='nsew', padx=1, pady=1)

            # Ранг
            label = ttk.Label(
                table_frame,
                text=str(self.ranks[i]),
                relief='solid',
                borderwidth=1
            )
            label.grid(row=i + 1, column=2, sticky='nsew', padx=1, pady=1)

        # Налаштувати розтягування колонок
        for col in range(3):
            table_frame.columnconfigure(col, weight=1)

        # Показники узгодженості
        consistency_frame = ttk.LabelFrame(self, text="Показники узгодженості", padding=20)
        consistency_frame.pack(pady=20, padx=20, fill='x')

        lambda_max = self.consistency['lambda_max']
        ci = self.consistency['CI']
        cr = self.consistency['CR']
        is_consistent = self.consistency['is_consistent']

        ttk.Label(
            consistency_frame,
            text=f"λ_max = {lambda_max:.4f}",
            font=('Arial', 10)
        ).pack(anchor='w', pady=2)

        ttk.Label(
            consistency_frame,
            text=f"Індекс узгодженості (CI) = {ci:.4f}",
            font=('Arial', 10)
        ).pack(anchor='w', pady=2)

        cr_color = 'green' if is_consistent else 'red'
        cr_label = ttk.Label(
            consistency_frame,
            text=f"Коефіцієнт узгодженості (CR) = {cr:.4f}",
            font=('Arial', 10, 'bold'),
            foreground=cr_color
        )
        cr_label.pack(anchor='w', pady=2)

        # Рекомендації
        recommendations_frame = ttk.LabelFrame(self, text="Рекомендації", padding=20)
        recommendations_frame.pack(pady=10, padx=20, fill='both', expand=True)

        for recommendation in self.consistency['recommendations']:
            ttk.Label(
                recommendations_frame,
                text=f"• {recommendation}",
                font=('Arial', 10),
                wraplength=600
            ).pack(anchor='w', pady=2)

        # Кнопка почати заново
        restart_btn = ttk.Button(
            self,
            text="🔄 Почати заново",
            command=self.on_restart
        )
        restart_btn.pack(pady=20)


class MainApplication(tk.Tk):
    """Головне вікно застосунку"""

    def __init__(self):
        super().__init__()

        self.title("Експертне оцінювання - Метод парних порівнянь")
        self.geometry("800x700")

        # Стиль
        self.style = ttk.Style()
        self.style.theme_use('clam')

        # Створити контейнер для панелей
        self.container = ttk.Frame(self)
        self.container.pack(fill='both', expand=True)

        # Показати панель введення
        self.show_input_panel()

    def show_input_panel(self):
        """Показати панель введення альтернатив"""
        self._clear_container()

        panel = InputPanel(self.container, on_next=self.show_comparison_panel)
        panel.pack(fill='both', expand=True)

    def show_comparison_panel(self, alternatives):
        """Показати панель парних порівнянь"""
        self._clear_container()

        self.alternatives = alternatives
        panel = ComparisonPanel(
            self.container,
            alternatives,
            on_complete=self.show_results_panel,
            on_back=self.show_input_panel
        )
        panel.pack(fill='both', expand=True)

    def show_results_panel(self, comparisons):
        """Показати панель результатів"""
        self._clear_container()

        panel = ResultsPanel(
            self.container,
            self.alternatives,
            comparisons,
            on_restart=self.show_input_panel
        )
        panel.pack(fill='both', expand=True)

    def _clear_container(self):
        """Очистити контейнер від попередніх панелей"""
        for widget in self.container.winfo_children():
            widget.destroy()


def main():
    """Запустити застосунок"""
    app = MainApplication()
    app.mainloop()


if __name__ == '__main__':
    main()
