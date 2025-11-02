"""
Головний модуль GUI для системи експертного оцінювання
"""

import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np

from gui.scales import get_scale, get_all_scale_names, ScaleType
from gui.calculations import (
    calculate_weights_eigenvector,
    calculate_weights_geometric_mean,
    build_comparison_matrix,
    check_consistency
)


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

        self._create_widgets()
        self._update_display()

    def _generate_pairs(self):
        """Генерувати всі пари для порівняння"""
        pairs = []
        for i in range(self.n):
            for j in range(i + 1, self.n):
                pairs.append((i, j))
        return pairs

    def _create_widgets(self):
        # Заголовок
        title = ttk.Label(self, text="Парні порівняння", font=('Arial', 16, 'bold'))
        title.pack(pady=20)

        # Прогрес
        self.progress_label = ttk.Label(self, text="", font=('Arial', 10))
        self.progress_label.pack(pady=5)

        self.progress_bar = ttk.Progressbar(
            self,
            length=400,
            mode='determinate'
        )
        self.progress_bar.pack(pady=10)

        # Питання
        self.question_label = ttk.Label(
            self,
            text="",
            font=('Arial', 12),
            wraplength=500
        )
        self.question_label.pack(pady=20)

        # Вибір шкали
        scale_frame = ttk.Frame(self)
        scale_frame.pack(pady=10)

        ttk.Label(scale_frame, text="Оберіть шкалу оцінювання:").pack(side='left', padx=5)

        self.scale_var = tk.StringVar(value=ScaleType.INTEGER)
        self.scale_combo = ttk.Combobox(
            scale_frame,
            textvariable=self.scale_var,
            values=get_all_scale_names(),
            state='readonly',
            width=30
        )
        self.scale_combo.pack(side='left', padx=5)
        self.scale_combo.bind('<<ComboboxSelected>>', self._on_scale_changed)

        # Вибір градації
        gradation_frame = ttk.Frame(self)
        gradation_frame.pack(pady=20, fill='x', padx=50)

        self.gradation_label = ttk.Label(gradation_frame, text="Оберіть ступінь переваги:")
        self.gradation_label.pack(pady=5)

        # Слайдер
        slider_frame = ttk.Frame(gradation_frame)
        slider_frame.pack(fill='x', pady=10)

        self.gradation_var = tk.IntVar(value=0)
        self.gradation_scale = ttk.Scale(
            slider_frame,
            from_=0,
            to=8,
            orient='horizontal',
            variable=self.gradation_var,
            command=self._on_gradation_changed
        )
        self.gradation_scale.pack(fill='x', pady=5)

        self.gradation_value_label = ttk.Label(
            slider_frame,
            text="",
            font=('Arial', 10)
        )
        self.gradation_value_label.pack(pady=5)

        # Візуалізація (текстова)
        self.visualization_label = ttk.Label(
            self,
            text="⚖️",
            font=('Arial', 48)
        )
        self.visualization_label.pack(pady=20)

        # Кнопки навігації
        button_frame = ttk.Frame(self)
        button_frame.pack(pady=20)

        back_btn = ttk.Button(
            button_frame,
            text="← Назад",
            command=self._go_back
        )
        back_btn.pack(side='left', padx=10)

        skip_btn = ttk.Button(
            button_frame,
            text="Пропустити",
            command=self._skip_pair
        )
        skip_btn.pack(side='left', padx=10)

        confirm_btn = ttk.Button(
            button_frame,
            text="Підтвердити →",
            command=self._confirm_comparison,
            style='Accent.TButton'
        )
        confirm_btn.pack(side='left', padx=10)

        # Кнопка повернення до введення
        return_btn = ttk.Button(
            self,
            text="⬅ Повернутися до введення альтернатив",
            command=self.on_back
        )
        return_btn.pack(pady=10)

    def _on_scale_changed(self, event=None):
        """Обробник зміни шкали"""
        scale_name = self.scale_var.get()
        scale = get_scale(scale_name)

        # Оновити діапазон слайдера
        self.gradation_scale.config(to=scale.gradations - 1)

        # Скинути значення
        self.gradation_var.set(0)

        self._update_gradation_display()

    def _on_gradation_changed(self, value=None):
        """Обробник зміни градації"""
        self._update_gradation_display()

    def _update_gradation_display(self):
        """Оновити відображення поточної градації"""
        scale_name = self.scale_var.get()
        scale = get_scale(scale_name)
        gradation = int(self.gradation_var.get())

        value = scale.get_value(gradation)
        unified_value = scale.unify(gradation)

        # Показати мітку (якщо є)
        label_text = ""
        if hasattr(scale, 'labels') and gradation < len(scale.labels):
            label_text = f"{scale.labels[gradation]} "

        self.gradation_value_label.config(
            text=f"{label_text}(значення: {value:.2f}, уніфіковане: {unified_value:.2f})"
        )

        # Оновити візуалізацію
        self._update_visualization(unified_value)

    def _update_visualization(self, value):
        """Оновити візуалізацію ваг"""
        if value > 5:
            symbol = "⚖️➡️"  # сильно вправо
        elif value > 2:
            symbol = "⚖️→"   # вправо
        elif value > 1.5:
            symbol = "⚖️"    # збалансовано
        else:
            symbol = "⚖️"

        self.visualization_label.config(text=symbol)

    def _update_display(self):
        """Оновити відображення поточної пари"""
        if self.current_pair >= len(self.pairs):
            self._finish_comparisons()
            return

        i, j = self.pairs[self.current_pair]

        # Оновити прогрес
        progress = (self.current_pair / self.total_pairs) * 100
        self.progress_bar['value'] = progress
        self.progress_label.config(
            text=f"Порівняння {self.current_pair + 1} з {self.total_pairs}"
        )

        # Оновити питання
        question = f"Наскільки '{self.alternatives[i]}' краще ніж '{self.alternatives[j]}'?"
        self.question_label.config(text=question)

        # Оновити градацію
        self._on_scale_changed()

    def _confirm_comparison(self):
        """Підтвердити поточне порівняння"""
        i, j = self.pairs[self.current_pair]

        scale_name = self.scale_var.get()
        scale = get_scale(scale_name)
        gradation = int(self.gradation_var.get())

        # Отримати уніфіковане значення
        unified_value = scale.unify(gradation)

        # Зберегти порівняння
        self.comparisons.append((i, j, unified_value))

        # Наступна пара
        self.current_pair += 1
        self._update_display()

    def _skip_pair(self):
        """Пропустити поточну пару (використати нейтральне значення)"""
        i, j = self.pairs[self.current_pair]
        self.comparisons.append((i, j, 1.0))  # нейтральне значення

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
