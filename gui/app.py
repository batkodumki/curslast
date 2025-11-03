"""
Головний модуль GUI для системи експертного оцінювання
Інтегрований з динамічним інтерфейсом шкалування з Delphi
"""

import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import math
from typing import List, Optional, Tuple

from gui.scales import get_scale, get_all_scale_names, ScaleType
from gui.calculations import (
    calculate_weights_eigenvector,
    calculate_weights_geometric_mean,
    build_comparison_matrix,
    check_consistency
)


# Constants from Delphi implementation
PREF = [
    '',  # Index 0 not used
    'Equally',                # 1
    'Weakly or slightly',     # 2
    'Moderately',             # 3
    'Moderately plus',        # 4
    'Strongly',               # 5
    'Strongly plus',          # 6
    'Very strongly',          # 7
    'Very, very strongly',    # 8
    'Extremely'               # 9
]

LESS_MORE = ['Less', 'More', 'Not sure']

GRADUAL_SCALE = {
    2: '25',
    3: '259',
    4: '3579',
    5: '23579',
    6: '234579',
    7: '2345679',
    8: '23456789'
}


class GraphicHintWindow(tk.Toplevel):
    """
    Custom graphical hint window (TGraphicHint from UGraphicHint.pas).
    Shows balance scale visualization for comparison values.
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.withdraw()
        self.overrideredirect(True)
        self.configure(bg='white', relief='solid', borderwidth=1)

        self.data = 0.0
        self.hint_text = ""

        # Canvas for drawing
        self.canvas = tk.Canvas(self, width=250, height=200, bg='white', highlightthickness=0)
        self.canvas.pack()

    def show_hint(self, x: int, y: int, text: str, data: float):
        """Display hint at position with graphical visualization."""
        self.hint_text = text
        self.data = data

        # Position window
        self.geometry(f'+{x+10}+{y+10}')

        # Draw content
        self.paint()

        # Show
        self.deiconify()
        self.lift()

    def hide_hint(self):
        """Hide the hint window."""
        self.withdraw()

    def paint(self):
        """Paint the hint content."""
        self.canvas.delete('all')

        if self.data == 0.0:
            # Simple text hint
            self.canvas.create_text(125, 100, text=self.hint_text, font=('Arial', 10))
            return

        # Draw hint text at top
        self.canvas.create_text(125, 15, text=self.hint_text, font=('Arial', 10, 'bold'))

        if self.data < 0:
            # Scale type diagram
            scale_info = {
                -1: 'Integer Scale\n\nLinear: value = grade\n(1 to 9)',
                -2: 'Balanced Scale\n\nFormula:\n(0.5+(g-1)*0.05)/\n(0.5-(g-1)*0.05)',
                -3: 'Power Scale\n\nFormula:\n9^((grade-1)/8)',
                -4: 'Ma-Zheng Scale\n\nFormula:\n9/(9+1-grade)',
                -5: 'Donegan-Dodd-McMasters\n\nFormula:\nexp(arctanh((g-1)/14*√3))'
            }
            text = scale_info.get(self.data, '')
            self.canvas.create_text(125, 110, text=text, font=('Arial', 9), justify='center')
        elif self.data < 1:
            # Object B preferred
            self.draw_balance_tilted_right()
            data_ = (1 / self.data) ** (1/3)  # Cube root for scaling

            xe, ye = 25, 25

            # Draw heavier weight on right (Object B)
            bottom = 180
            top = bottom - round(ye * data_)
            left = 180 - round(xe * data_ / 2)
            right = left + round(xe * data_)
            self.canvas.create_rectangle(left, top, right, bottom, fill='red', outline='black', width=2)

            # Draw lighter weight on left (Object A)
            self.canvas.create_rectangle(50, 145, 75, 170, fill='blue', outline='black', width=2)
        else:
            # Object A preferred or equal
            self.draw_balance_tilted_left()
            data_ = self.data ** (1/3)  # Cube root for scaling

            xe, ye = 25, 25

            # Draw heavier weight on left (Object A)
            bottom = 180
            top = bottom - round(ye * data_)
            left = 70 - round(xe * data_ / 2)
            right = left + round(xe * data_)
            self.canvas.create_rectangle(left, top, right, bottom, fill='blue', outline='black', width=2)

            # Draw lighter weight on right (Object B)
            self.canvas.create_rectangle(180, 145, 205, 170, fill='red', outline='black', width=2)

            if self.data == 1:
                # Equal - show question mark
                self.canvas.create_text(125, 100, text='?', font=('Arial', 60), fill='red')

    def draw_balance_tilted_right(self):
        """Draw balance scale tilted to the right (B heavier)."""
        # Fulcrum (triangle)
        self.canvas.create_polygon(125, 110, 110, 140, 140, 140, fill='gray', outline='black', width=2)
        # Beam tilted right
        self.canvas.create_line(40, 125, 210, 105, width=4, fill='brown')

    def draw_balance_tilted_left(self):
        """Draw balance scale tilted to the left (A heavier)."""
        # Fulcrum (triangle)
        self.canvas.create_polygon(125, 110, 110, 140, 140, 140, fill='gray', outline='black', width=2)
        # Beam tilted left
        self.canvas.create_line(40, 105, 210, 125, width=4, fill='brown')


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
    """Панель парних порівнянь з динамічним інтерфейсом шкалування"""

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

        # Dynamic scale interface state
        self.reverse = -1  # -1: not set, 0: Less, 1: More
        self.res = 1.0     # Result estimate
        self.rel = 0.0     # Reliability
        self.scale_str = '0'  # Current scale configuration
        self.scale_type_id = 1  # 1-5: scale types
        self.delay_wheel = 0  # Mouse wheel delay

        # UI component references
        self.scale_panels: List[tk.Button] = []
        self.panel_less: Optional[tk.Button] = None
        self.panel_more: Optional[tk.Button] = None

        self._create_widgets()
        self._reset_comparison()

    def _generate_pairs(self):
        """Генерувати всі пари для порівняння"""
        pairs = []
        for i in range(self.n):
            for j in range(i + 1, self.n):
                pairs.append((i, j))
        return pairs

    def _create_widgets(self):
        # Контейнер для всього вмісту - горизонтальне розділення
        main_container = ttk.Frame(self)
        main_container.pack(fill='both', expand=True, padx=10, pady=10)

        # ===== ЛІВА ПАНЕЛЬ - Налаштування шкали =====
        left_panel = ttk.LabelFrame(main_container, text="Налаштування шкали", width=250)
        left_panel.pack(side='left', fill='y', padx=(0, 10))
        left_panel.pack_propagate(False)

        # Scale type choice panel
        self.panel_scale_choice = tk.Frame(left_panel, relief='raised', bd=2)
        self.panel_scale_choice.pack(padx=5, pady=5, fill='both')

        # Button and spin
        button_spin_frame = tk.Frame(self.panel_scale_choice)
        button_spin_frame.pack(fill='x')

        self.panel_scale_button_choice = tk.Button(
            button_spin_frame,
            text='Тип шкали',
            relief='sunken',
            cursor='hand2',
            font=('Arial', 9),
            command=self.toggle_scale_choice
        )
        self.panel_scale_button_choice.pack(side='left', fill='x', expand=True)

        # Spin buttons
        spin_frame = tk.Frame(button_spin_frame)
        spin_frame.pack(side='right')

        self.spin_up = tk.Button(
            spin_frame,
            text='▲',
            command=self.spin_up_click,
            width=2
        )
        self.spin_up.pack(side='top')

        self.spin_down = tk.Button(
            spin_frame,
            text='▼',
            command=self.spin_down_click,
            width=2
        )
        self.spin_down.pack(side='bottom')

        # Radio buttons for scale types
        self.scale_type_var = tk.IntVar(value=1)

        self.rbut_integer = tk.Radiobutton(
            self.panel_scale_choice,
            text='Integer',
            variable=self.scale_type_var,
            value=1,
            cursor='hand2',
            font=('Arial', 9),
            command=self.scale_choice_changed
        )
        self.rbut_integer.pack(anchor='w', padx=5, pady=2)
        self.rbut_integer.data = -1

        self.rbut_balanced = tk.Radiobutton(
            self.panel_scale_choice,
            text='Balanced',
            variable=self.scale_type_var,
            value=2,
            cursor='hand2',
            font=('Arial', 9),
            command=self.scale_choice_changed
        )
        self.rbut_balanced.pack(anchor='w', padx=5, pady=2)
        self.rbut_balanced.data = -2

        self.rbut_power = tk.Radiobutton(
            self.panel_scale_choice,
            text='Power',
            variable=self.scale_type_var,
            value=3,
            cursor='hand2',
            font=('Arial', 9),
            command=self.scale_choice_changed
        )
        self.rbut_power.pack(anchor='w', padx=5, pady=2)
        self.rbut_power.data = -3

        self.rbut_mazheng = tk.Radiobutton(
            self.panel_scale_choice,
            text='Ma-Zheng (9/9-9/1)',
            variable=self.scale_type_var,
            value=4,
            cursor='hand2',
            font=('Arial', 9),
            command=self.scale_choice_changed
        )
        self.rbut_mazheng.pack(anchor='w', padx=5, pady=2)
        self.rbut_mazheng.data = -4

        self.rbut_dodd = tk.Radiobutton(
            self.panel_scale_choice,
            text='Donegan-Dodd-McMasters',
            variable=self.scale_type_var,
            value=5,
            cursor='hand2',
            font=('Arial', 9),
            command=self.scale_choice_changed
        )
        self.rbut_dodd.pack(anchor='w', padx=5, pady=2)
        self.rbut_dodd.data = -5

        # No idea button
        self.panel_no_idea = tk.Button(
            left_panel,
            text='Не впевнений',
            relief='raised',
            cursor='hand2',
            font=('Arial', 9, 'bold'),
            bg='#ffcc00',
            command=self.no_idea_click
        )
        self.panel_no_idea.pack(padx=5, pady=10, fill='x')
        self.panel_no_idea.hint = LESS_MORE[2]

        # ===== ПРАВА ПАНЕЛЬ - Область порівняння =====
        right_panel = ttk.Frame(main_container)
        right_panel.pack(side='left', fill='both', expand=True)

        # Прогрес
        self.progress_label = ttk.Label(
            right_panel,
            text="",
            font=('Arial', 12, 'bold')
        )
        self.progress_label.pack(pady=5)

        # Заголовок з назвами об'єктів
        header_frame = tk.Frame(right_panel, bg='white', relief='solid', bd=1)
        header_frame.pack(fill='x', pady=10)

        # Label A (зліва)
        self.label_a = tk.Label(
            header_frame,
            text="Object A",
            font=('Arial', 12, 'bold'),
            fg='#0066cc',
            bg='white',
            wraplength=200,
            justify='left'
        )
        self.label_a.pack(side='left', padx=20, pady=10)

        # Center labels
        center_frame = tk.Frame(header_frame, bg='white')
        center_frame.pack(side='left', expand=True)

        self.label_is = tk.Label(
            center_frame,
            text='впливає',
            font=('Arial', 11),
            fg='#666666',
            bg='white'
        )
        self.label_is.pack(pady=2)

        self.label_than = tk.Label(
            center_frame,
            text='',
            font=('Arial', 11, 'bold'),
            fg='red',
            bg='white'
        )
        self.label_than.pack(pady=2)

        # Label B (справа)
        self.label_b = tk.Label(
            header_frame,
            text="Object B",
            font=('Arial', 12, 'bold'),
            fg='#cc0066',
            bg='white',
            wraplength=200,
            justify='right'
        )
        self.label_b.pack(side='right', padx=20, pady=10)

        # Середня частина - панель шкали
        middle_frame = tk.Frame(right_panel, bg='white', relief='solid', bd=1)
        middle_frame.pack(fill='x', pady=10)

        # Інструкція
        instruction_label = ttk.Label(
            middle_frame,
            text="Оберіть рівень впливу:",
            font=('Arial', 10)
        )
        instruction_label.pack(pady=5)

        # Контейнер для динамічних панелей
        scale_container = tk.Frame(middle_frame, bg='white')
        scale_container.pack(fill='x', padx=20, pady=10)

        self.panel_scale = tk.Frame(scale_container, bg='#f0f0f0', relief='flat', height=40)
        self.panel_scale.pack(fill='x')
        self.panel_scale.pack_propagate(False)

        # Початкові кнопки Less/More
        self.panel_less = tk.Button(
            self.panel_scale,
            text='Менше впливає',
            relief='raised',
            cursor='hand2',
            bg='#cc0000',
            fg='white',
            font=('Arial', 10, 'bold')
        )
        self.panel_less.place(x=0, y=5, relwidth=0.48, height=30)
        self.panel_less.hint = LESS_MORE[0]
        self.panel_less.config(command=lambda: self.panel_scale_click(self.panel_less))

        self.panel_more = tk.Button(
            self.panel_scale,
            text='Більше впливає',
            relief='raised',
            cursor='hand2',
            bg='#cc0000',
            fg='white',
            font=('Arial', 10, 'bold')
        )
        self.panel_more.place(relx=0.52, y=5, relwidth=0.48, height=30)
        self.panel_more.hint = LESS_MORE[1]
        self.panel_more.config(command=lambda: self.panel_scale_click(self.panel_more))

        # Візуалізація шкали
        self.image_show = tk.Canvas(
            middle_frame,
            bg='white',
            highlightthickness=1,
            highlightbackground='gray'
        )
        self.image_show.pack(fill='both', expand=True, padx=20, pady=5)
        self.image_show.configure(height=100)

        # ===== КНОПКИ НАВІГАЦІЇ =====
        nav_frame = ttk.Frame(right_panel)
        nav_frame.pack(pady=15)

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

        # Create graphic hint window
        self.hint_window = GraphicHintWindow(self.winfo_toplevel())

        # Bind hint events
        for widget in [self.panel_less, self.panel_more, self.panel_no_idea,
                      self.rbut_integer, self.rbut_balanced, self.rbut_power,
                      self.rbut_mazheng, self.rbut_dodd]:
            widget.bind('<Enter>', self.show_hint_event)
            widget.bind('<Leave>', lambda e: self.hint_window.hide_hint())

        # Bind mouse wheel
        self.bind_all('<MouseWheel>', self.mouse_wheel)
        self.bind_all('<Button-4>', lambda e: self.spin_up_click())
        self.bind_all('<Button-5>', lambda e: self.spin_down_click())

    def _reset_comparison(self):
        """Reset state for new comparison"""
        self.reverse = -1
        self.res = 1.0
        self.rel = 0.0
        self.scale_str = '0'
        self.scale_type_id = 1

        self.panel_no_idea.config(text=PREF[1])
        self.panel_no_idea.hint = PREF[1]
        self.panel_less.config(text=LESS_MORE[0])
        self.panel_more.config(text=LESS_MORE[1])
        self.panel_scale_choice.pack_forget()

        # Clear dynamic panels
        for panel in self.scale_panels:
            panel.destroy()
        self.scale_panels.clear()

        # Reset button positions
        self.panel_less.place(x=0, y=5, relwidth=0.48, height=30)
        self.panel_more.place(relx=0.52, y=5, relwidth=0.48, height=30)

        self._update_display()

    def _update_display(self):
        """Оновити відображення поточної пари"""
        if self.current_pair >= len(self.pairs):
            return

        i, j = self.pairs[self.current_pair]

        # Оновити прогрес
        self.progress_label.config(
            text=f"Порівняння {self.current_pair + 1} з {self.total_pairs}"
        )

        # Оновити назви альтернатив
        self.label_a.config(text=self.alternatives[i])
        self.label_b.config(text=self.alternatives[j])

        # Reset center label
        self.label_than.config(text='')

        # Clear visualization
        self.image_show.delete('all')

    # ===== DYNAMIC SCALE INTERFACE METHODS =====

    def integer_by_scale(self, data: float) -> float:
        """Apply scale transformation"""
        result = data
        scale_type = self.scale_type_var.get()

        if scale_type == 2:  # Balanced
            result = (0.5 + (data - 1) * 0.05) / (0.5 - (data - 1) * 0.05)
        elif scale_type == 3:  # Power
            result = math.pow(9, (data - 1) / 8)
        elif scale_type == 4:  # Ma-Zheng
            result = 9 / (9 + 1 - data)
        elif scale_type == 5:  # Dodd
            result = math.exp(math.atanh((data - 1) / 14 * math.sqrt(3)))

        return result

    def in_range(self, value: int, min_val: int, max_val: int) -> bool:
        """Helper function equivalent to Delphi's InRange"""
        return min_val <= value <= max_val

    def build_scale(self, scale_str: str):
        """Build dynamic scale panels (faithful Delphi recreation)"""
        # Clear existing dynamic panels
        for panel in self.scale_panels:
            panel.destroy()
        self.scale_panels.clear()

        if self.reverse == -1:
            # Initial state - just show Less/More
            return

        # Calculate number of panels needed
        li = len(scale_str)

        # Calculate sum of weights
        if scale_str in ['23459', '25679', '2589']:
            ii = 8
        else:
            ii = li

        sum_w = 0.0
        for i in range(1, ii + 1):
            sum_w += self.integer_by_scale(1.5 + (i - 0.5) * (9.5 - 1.5) / ii)

        # Build panels
        wi = 0  # Width accumulator
        panel_scale_width = 475

        for i in range(li, -1, -1):  # Reverse order
            # Create new panel
            new_pin = tk.Button(
                self.panel_scale,
                text='',
                relief='raised',
                cursor='hand2',
                font=('MS Sans Serif', 8)
            )

            if i == li:
                # Last panel - Less/More indicator
                width = panel_scale_width // 9
                wi = width
                caption = LESS_MORE[1 - self.reverse]
                new_pin.config(text=caption, bg='#f0f0f0', fg='black')
                new_pin.hint = caption

                if self.reverse == 1:  # More
                    left = 0
                else:  # Less
                    left = panel_scale_width - width
            else:
                # Regular gradation panel
                idx = li - i - 1
                grade_char = scale_str[idx]
                grade = int(grade_char)

                # Calculate width based on complex algorithm
                if scale_str in ['23459', '25679', '2589']:
                    # Special handling for these scales
                    if self.scale_type_var.get() == 1:  # Integer
                        width = panel_scale_width * 16 // 9 // 6

                    pos = scale_str.index(grade_char) + 1  # 1-based position

                    # Check if grouped panel
                    is_grouped = False
                    if scale_str == '23459' and pos > 3:
                        is_grouped = True
                    elif scale_str == '25679' and not self.in_range(pos, 2, 4):
                        is_grouped = True
                    elif scale_str == '2589' and pos < 3:
                        is_grouped = True

                    if is_grouped and self.scale_type_var.get() != 1:
                        # Grouped panels
                        if (scale_str in ['25679', '2589']) and grade_char == '2':
                            width = round(panel_scale_width / 2 * 16 / 9 / sum_w *
                                        (self.integer_by_scale(2) + self.integer_by_scale(3) +
                                         self.integer_by_scale(4)))
                        elif (scale_str in ['23459', '2589']) and grade_char == '5':
                            width = round(panel_scale_width / 2 * 16 / 9 / sum_w *
                                        (self.integer_by_scale(5) + self.integer_by_scale(6) +
                                         self.integer_by_scale(7)))
                        elif (scale_str in ['23459', '25679']) and grade_char == '9':
                            width = round(panel_scale_width / 2 * 16 / 9 / sum_w *
                                        (self.integer_by_scale(8) + self.integer_by_scale(9)))
                        new_pin.config(bg='#f0f0f0', fg='black')
                    else:
                        # Active panels
                        if self.scale_type_var.get() == 1:  # Integer
                            width = width // (len(scale_str) - 2)
                        else:
                            width = round(panel_scale_width * 16 / 9 / 2 / sum_w *
                                        self.integer_by_scale(grade))
                        new_pin.config(bg='red', fg='white')
                else:
                    # Regular scale
                    if self.scale_type_var.get() == 1:  # Integer
                        width = panel_scale_width / 2 * 16 / 9 / li
                        width = int(width)
                    else:
                        width = round(panel_scale_width / 2 * 16 / 9 / sum_w *
                                    self.integer_by_scale(1.5 + (li - i - 0.5) * (9.5 - 1.5) / li))
                    new_pin.config(bg='red', fg='white')

                wi += width
                left = panel_scale_width * (1 - self.reverse) - wi + 2 * wi * self.reverse - width * self.reverse
                new_pin.hint = PREF[grade]

            # Position panel
            new_pin.place(x=int(left), y=0, width=int(width), height=30)

            # Bind events
            new_pin.config(command=lambda p=new_pin: self.panel_scale_click(p))
            new_pin.bind('<Enter>', self.show_hint_event)
            new_pin.bind('<Leave>', lambda e: self.hint_window.hide_hint())

            if i < li:
                self.scale_panels.append(new_pin)

        # Update visualization
        self.show_image()

    def show_image(self):
        """Draw visual scale representation"""
        self.image_show.delete('all')

        if self.reverse == -1:
            return

        # Find min/max positions
        min_l = 475
        max_r = 0

        for panel in self.scale_panels:
            if panel.winfo_exists() and panel.winfo_ismapped():
                x = panel.winfo_x()
                width = panel.winfo_width()
                hint = panel.hint

                # Draw vertical tick
                self.image_show.create_line(x, 0, x, 10, fill='black')

                # Draw vertical text
                center_x = x + width // 2
                self.image_show.create_text(
                    center_x - 5, 50,
                    text=hint, angle=90, anchor='w',
                    font=('Arial', 8)
                )

                min_l = min(min_l, x)
                max_r = max(max_r, x + width)

        # Draw final tick and horizontal line
        if max_r > 0:
            self.image_show.create_line(max_r - 1, 0, max_r - 1, 10, fill='black')
            self.image_show.create_line(min_l, 0, max_r - 1, 0, fill='black')

    def panel_scale_click(self, panel):
        """Handle scale panel click (progressive refinement logic)"""
        hint = panel.hint

        # Handle Less/More selection
        if hint in [LESS_MORE[0], LESS_MORE[1]]:
            self.panel_no_idea.config(text=PREF[1])
            self.panel_no_idea.hint = PREF[1]

            if hint == LESS_MORE[0]:
                self.reverse = 0  # Less
            else:
                self.reverse = 1  # More

        # Progressive refinement logic
        if self.scale_str == '0':
            # First level - coarse scale
            self.rel = 1.0  # Chose Less/More
            self.res = 5.5  # Middle value
            self.scale_str = '259'
        elif self.scale_str == '259' and panel.cget('bg') == 'red':
            # Second level - medium scale
            grad = 1
            for idx, char in enumerate(self.scale_str, 1):
                if hint == PREF[int(char)]:
                    grad = idx
                    break

            if grad == 1:
                self.scale_str = '23459'
            elif grad == 2:
                self.scale_str = '25679'
            elif grad == 3:
                self.scale_str = '2589'

            self.rel = 3.0  # Chose from 3 options
            self.res = 1.5 + (grad - 0.5) * (9.5 - 1.5) / 3
        elif panel.cget('bg') == '#f0f0f0':
            # Click on grouped panel
            if hint == PREF[2]:
                self.scale_str = '23459'
                self.res = 1.5 + (1 - 0.5) * (9.5 - 1.5) / 3
            elif hint == PREF[5]:
                self.scale_str = '25679'
                self.res = 1.5 + (2 - 0.5) * (9.5 - 1.5) / 3
            elif hint == PREF[9]:
                self.scale_str = '2589'
                self.res = 1.5 + (3 - 0.5) * (9.5 - 1.5) / 3
        else:
            # Final selection
            grad = 1
            for idx, char in enumerate(self.scale_str, 1):
                if hint == PREF[int(char)]:
                    grad = idx
                    break

            if self.scale_str in ['23459', '25679', '2589']:
                # Adjust for offset
                if self.scale_str == '25679':
                    grad += 2
                elif self.scale_str == '2589':
                    grad += 4
                self.rel = 8.0
            else:
                self.rel = len(self.scale_str)

            self.res = 1.5 + (grad - 0.5) * (9.5 - 1.5) / self.rel
            self._confirm_comparison()
            return

        # Rebuild scale and update
        self.build_scale(self.scale_str)
        self.panel_scale_choice.pack(padx=5, pady=5, fill='both')

        # Update center label
        if self.reverse == 0:
            self.label_than.config(text='МЕНШЕ')
        else:
            self.label_than.config(text='БІЛЬШЕ')

    def show_hint_event(self, event):
        """Show graphical hint"""
        widget = event.widget

        # Get hint text
        if hasattr(widget, 'hint'):
            hint_text = widget.hint
        else:
            return

        # Calculate data for visualization
        data = 0.0

        if isinstance(widget, tk.Radiobutton):
            # Scale type hint
            data = widget.data
        elif hasattr(widget, 'hint'):
            if self.panel_scale_choice.winfo_ismapped():
                # Panel hint when scale is visible
                if widget.hint in [PREF[1], LESS_MORE[0], LESS_MORE[1]]:
                    data = self.res
                else:
                    # Find grade
                    data = 1.0
                    for i in range(1, 10):
                        if widget.hint == PREF[i]:
                            data = float(i)
                            break

                    # Apply transformation
                    data = self.integer_by_scale(data)

                    # Invert if Less
                    if ((self.reverse == 0 and widget.hint != LESS_MORE[1]) or
                        (self.reverse != 0 and widget.hint == LESS_MORE[0])):
                        if data != 0:
                            data = 1 / data
            else:
                # Initial state hints
                if widget.hint == LESS_MORE[0]:
                    data = 1 / 5.5
                elif widget.hint == LESS_MORE[1]:
                    data = 5.5
                else:
                    data = 1.0

        # Show hint window
        if data != 0:
            x = self.winfo_toplevel().winfo_pointerx()
            y = self.winfo_toplevel().winfo_pointery()
            self.hint_window.show_hint(x, y, hint_text, data)

    def toggle_scale_choice(self):
        """Toggle scale type panel visibility"""
        if self.panel_scale_button_choice.cget('relief') == 'sunken':
            self.panel_scale_button_choice.config(relief='raised')
            # Disable radio buttons
            for rb in [self.rbut_integer, self.rbut_balanced, self.rbut_power,
                      self.rbut_mazheng, self.rbut_dodd]:
                rb.config(state='disabled')
        else:
            self.panel_scale_button_choice.config(relief='sunken')
            # Enable radio buttons
            for rb in [self.rbut_integer, self.rbut_balanced, self.rbut_power,
                      self.rbut_mazheng, self.rbut_dodd]:
                rb.config(state='normal')

    def scale_choice_changed(self):
        """Handle scale type change"""
        self.build_scale(self.scale_str)

    def spin_up_click(self):
        """Increase gradations"""
        if self.reverse > -1 and len(self.scale_str) < 8:
            self.scale_str = GRADUAL_SCALE[len(self.scale_str) + 1]
            self.rel = 1.0
            self.res = 5.5
            self.build_scale(self.scale_str)

    def spin_down_click(self):
        """Decrease gradations"""
        if self.reverse > -1 and len(self.scale_str) > 2:
            self.scale_str = GRADUAL_SCALE[len(self.scale_str) - 1]
            self.rel = 1.0
            self.res = 5.5
            self.build_scale(self.scale_str)

    def mouse_wheel(self, event):
        """Handle mouse wheel"""
        if self.delay_wheel < 3:
            self.delay_wheel += 1
            return
        self.delay_wheel = 0

        # Handle different platforms (Windows uses delta, Linux doesn't)
        if hasattr(event, 'delta'):
            if event.delta > 0:
                self.spin_up_click()
            else:
                self.spin_down_click()

    def no_idea_click(self):
        """Handle 'No idea' click"""
        # Set result to 1 (equal) with zero reliability
        self.res = 1.0
        self.rel = 0.0
        self.reverse = -1
        self._confirm_comparison()

    def _confirm_comparison(self):
        """Confirm current comparison and move to next"""
        i, j = self.pairs[self.current_pair]

        # Apply transformation and reverse
        if self.reverse > -1:
            final_res = self.integer_by_scale(self.res)

            if self.reverse == 0:  # Less
                if final_res != 0:
                    final_res = 1 / final_res
        else:
            final_res = 1.0

        # Save scale type
        self.scale_type_id = self.scale_type_var.get()

        # Store comparison
        self.comparisons.append((i, j, final_res))

        # Move to next pair
        self.current_pair += 1

        if self.current_pair >= len(self.pairs):
            self._finish_comparisons()
        else:
            self._reset_comparison()

    def _go_back(self):
        """Повернутися до попередньої пари"""
        if self.current_pair > 0:
            self.current_pair -= 1
            if self.comparisons:
                self.comparisons.pop()
            self._reset_comparison()

    def _finish_comparisons(self):
        """Завершити порівняння"""
        self.hint_window.destroy()
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
            text="Почати заново",
            command=self.on_restart
        )
        restart_btn.pack(pady=20)


class MainApplication(tk.Tk):
    """Головне вікно застосунку"""

    def __init__(self):
        super().__init__()

        self.title("Експертне оцінювання - Динамічний інтерфейс шкалування")
        self.geometry("1000x700")

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
