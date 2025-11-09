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


# Modern Design Color Palette
COLORS = {
    'primary': '#4A90E2',        # Soft blue
    'primary_dark': '#357ABD',   # Darker blue
    'secondary': '#50C878',      # Soft emerald green
    'accent': '#FF6B6B',         # Soft coral red
    'accent_light': '#FF8E8E',   # Lighter coral
    'background': '#F7F9FC',     # Light gray-blue background
    'surface': '#FFFFFF',        # White surface
    'text_primary': '#2C3E50',   # Dark blue-gray
    'text_secondary': '#7F8C8D', # Medium gray
    'border': '#E0E6ED',         # Light border
    'hover': '#5BA3F5',          # Lighter blue for hover
    'success': '#27AE60',        # Green
    'warning': '#F39C12',        # Orange
}

# Constants from Delphi implementation
PREF = [
    '',  # Index 0 not used
    'Однаково',               # 1 - Equally
    'Слабко',                 # 2 - Weakly or slightly
    'Помірно',                # 3 - Moderately
    'Помірно плюс',           # 4 - Moderately plus
    'Сильно',                 # 5 - Strongly
    'Сильно плюс',            # 6 - Strongly plus
    'Дуже сильно',            # 7 - Very strongly
    'Дуже-дуже сильно',       # 8 - Very, very strongly
    'Надзвичайно'             # 9 - Extremely
]

LESS_MORE = ['Менше', 'Більше', 'Не впевнений']

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
        self.configure(bg=COLORS['surface'], relief='solid', borderwidth=2, highlightbackground=COLORS['border'])

        self.data = 0.0
        self.hint_text = ""

        # Canvas for drawing with modern styling
        self.canvas = tk.Canvas(self, width=250, height=200, bg=COLORS['surface'], highlightthickness=0)
        self.canvas.pack(padx=5, pady=5)

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
            self.canvas.create_text(125, 100, text=self.hint_text, font=('Segoe UI', 10), fill=COLORS['text_primary'])
            return

        # Draw hint text at top
        self.canvas.create_text(125, 15, text=self.hint_text, font=('Segoe UI', 10, 'bold'), fill=COLORS['text_primary'])

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
            self.canvas.create_text(125, 110, text=text, font=('Segoe UI', 9), justify='center', fill=COLORS['text_secondary'])
        elif self.data < 1:
            # Object B preferred
            self.draw_balance_tilted_right()
            data_ = (1 / self.data) ** (1/3)  # Cube root for scaling

            xe, ye = 25, 25

            # Draw heavier weight on right (Object B) - modern coral color
            bottom = 180
            top = bottom - round(ye * data_)
            left = 180 - round(xe * data_ / 2)
            right = left + round(xe * data_)
            self.canvas.create_rectangle(left, top, right, bottom, fill=COLORS['accent'], outline=COLORS['text_primary'], width=2)

            # Draw lighter weight on left (Object A) - modern blue color
            self.canvas.create_rectangle(50, 145, 75, 170, fill=COLORS['primary'], outline=COLORS['text_primary'], width=2)
        else:
            # Object A preferred or equal
            self.draw_balance_tilted_left()
            data_ = self.data ** (1/3)  # Cube root for scaling

            xe, ye = 25, 25

            # Draw heavier weight on left (Object A) - modern blue color
            bottom = 180
            top = bottom - round(ye * data_)
            left = 70 - round(xe * data_ / 2)
            right = left + round(xe * data_)
            self.canvas.create_rectangle(left, top, right, bottom, fill=COLORS['primary'], outline=COLORS['text_primary'], width=2)

            # Draw lighter weight on right (Object B) - modern coral color
            self.canvas.create_rectangle(180, 145, 205, 170, fill=COLORS['accent'], outline=COLORS['text_primary'], width=2)

            if self.data == 1:
                # Equal - show question mark
                self.canvas.create_text(125, 100, text='?', font=('Segoe UI', 60), fill=COLORS['accent'])

    def draw_balance_tilted_right(self):
        """Draw balance scale tilted to the right (B heavier)."""
        # Fulcrum (triangle) - modern gray
        self.canvas.create_polygon(125, 110, 110, 140, 140, 140, fill=COLORS['text_secondary'], outline=COLORS['text_primary'], width=2)
        # Beam tilted right - modern dark color
        self.canvas.create_line(40, 125, 210, 105, width=4, fill=COLORS['text_primary'])

    def draw_balance_tilted_left(self):
        """Draw balance scale tilted to the left (A heavier)."""
        # Fulcrum (triangle) - modern gray
        self.canvas.create_polygon(125, 110, 110, 140, 140, 140, fill=COLORS['text_secondary'], outline=COLORS['text_primary'], width=2)
        # Beam tilted left - modern dark color
        self.canvas.create_line(40, 105, 210, 125, width=4, fill=COLORS['text_primary'])


class InputPanel(ttk.Frame):
    """Панель введення альтернатив"""

    def __init__(self, parent, on_next):
        super().__init__(parent)
        self.on_next = on_next
        self.entries = []

        self._create_widgets()

    def _create_widgets(self):
        # Add top spacing
        ttk.Frame(self, height=30).pack()

        # Заголовок з більш виразним стилем
        title = ttk.Label(self, text="Введення альтернатив", font=('Segoe UI', 24, 'bold'), foreground=COLORS['text_primary'])
        title.pack(pady=(10, 5))

        # Інструкція з кращою читабельністю
        instruction = ttk.Label(
            self,
            text="Введіть назви об'єктів для порівняння (мінімум 2):",
            font=('Segoe UI', 11),
            foreground=COLORS['text_secondary']
        )
        instruction.pack(pady=(5, 25))

        # Фрейм для полів введення з кращим відступом
        self.entries_frame = ttk.Frame(self)
        self.entries_frame.pack(pady=10, padx=40, fill='both', expand=True)

        # Початкові поля
        for i in range(3):
            self._add_entry_field(i)

        # Кнопка додати поле з кращим стилем
        add_btn = ttk.Button(
            self,
            text="+ Додати альтернативу",
            command=self._add_field
        )
        add_btn.pack(pady=15)

        # Кнопка далі з більшим акцентом
        next_btn = ttk.Button(
            self,
            text="Далі →",
            command=self._validate_and_next,
            style='Accent.TButton'
        )
        next_btn.pack(pady=(10, 30))

    def _add_entry_field(self, index):
        """Додати поле для введення альтернативи"""
        frame = ttk.Frame(self.entries_frame)
        frame.pack(fill='x', pady=8)

        label = ttk.Label(frame, text=f"Альтернатива {index + 1}:", width=18, font=('Segoe UI', 10), foreground=COLORS['text_primary'])
        label.pack(side='left', padx=(5, 10))

        entry = ttk.Entry(frame, width=40, font=('Segoe UI', 10))
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
        self.scale_dividers: List[tk.Frame] = []  # Track divider lines between buttons
        self.directional_indicator: Optional[tk.Button] = None  # Track the gray Less/More box
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
        # Контейнер для всього вмісту - горизонтальне розділення з кращими відступами
        main_container = ttk.Frame(self)
        main_container.pack(fill='both', expand=True, padx=20, pady=15)

        # ===== ЛІВА ПАНЕЛЬ - Налаштування шкали =====
        left_panel = ttk.LabelFrame(main_container, text="Налаштування шкали", width=270)
        left_panel.pack(side='left', fill='y', padx=(0, 15))
        left_panel.pack_propagate(False)

        # Scale type choice panel з сучасним дизайном
        self.panel_scale_choice = tk.Frame(left_panel, relief='flat', bd=0, bg=COLORS['background'])
        self.panel_scale_choice.pack(padx=8, pady=8, fill='both')

        # Button and spin
        button_spin_frame = tk.Frame(self.panel_scale_choice, bg=COLORS['background'])
        button_spin_frame.pack(fill='x')

        self.panel_scale_button_choice = tk.Button(
            button_spin_frame,
            text='Тип шкали',
            relief='flat',
            cursor='hand2',
            font=('Segoe UI', 10),
            bg=COLORS['primary'],
            fg='white',
            activebackground=COLORS['primary_dark'],
            activeforeground='white',
            command=self.toggle_scale_choice,
            padx=10,
            pady=5
        )
        self.panel_scale_button_choice.pack(side='left', fill='x', expand=True)

        # Spin buttons з кращим дизайном
        spin_frame = tk.Frame(button_spin_frame, bg=COLORS['background'])
        spin_frame.pack(side='right', padx=(5, 0))

        self.spin_up = tk.Button(
            spin_frame,
            text='▲',
            command=self.spin_up_click,
            width=2,
            relief='flat',
            bg=COLORS['surface'],
            fg=COLORS['text_primary'],
            activebackground=COLORS['hover'],
            font=('Segoe UI', 8)
        )
        self.spin_up.pack(side='top', pady=(0, 2))

        self.spin_down = tk.Button(
            spin_frame,
            text='▼',
            command=self.spin_down_click,
            width=2,
            relief='flat',
            bg=COLORS['surface'],
            fg=COLORS['text_primary'],
            activebackground=COLORS['hover'],
            font=('Segoe UI', 8)
        )
        self.spin_down.pack(side='bottom')

        # Radio buttons for scale types з сучасним дизайном
        self.scale_type_var = tk.IntVar(value=1)

        self.rbut_integer = tk.Radiobutton(
            self.panel_scale_choice,
            text='Integer',
            variable=self.scale_type_var,
            value=1,
            cursor='hand2',
            font=('Segoe UI', 10),
            bg=COLORS['background'],
            fg=COLORS['text_primary'],
            activebackground=COLORS['background'],
            selectcolor=COLORS['primary'],
            command=self.scale_choice_changed
        )
        self.rbut_integer.pack(anchor='w', padx=8, pady=4)
        self.rbut_integer.data = -1

        self.rbut_balanced = tk.Radiobutton(
            self.panel_scale_choice,
            text='Balanced',
            variable=self.scale_type_var,
            value=2,
            cursor='hand2',
            font=('Segoe UI', 10),
            bg=COLORS['background'],
            fg=COLORS['text_primary'],
            activebackground=COLORS['background'],
            selectcolor=COLORS['primary'],
            command=self.scale_choice_changed
        )
        self.rbut_balanced.pack(anchor='w', padx=8, pady=4)
        self.rbut_balanced.data = -2

        self.rbut_power = tk.Radiobutton(
            self.panel_scale_choice,
            text='Power',
            variable=self.scale_type_var,
            value=3,
            cursor='hand2',
            font=('Segoe UI', 10),
            bg=COLORS['background'],
            fg=COLORS['text_primary'],
            activebackground=COLORS['background'],
            selectcolor=COLORS['primary'],
            command=self.scale_choice_changed
        )
        self.rbut_power.pack(anchor='w', padx=8, pady=4)
        self.rbut_power.data = -3

        self.rbut_mazheng = tk.Radiobutton(
            self.panel_scale_choice,
            text='Ma-Zheng (9/9-9/1)',
            variable=self.scale_type_var,
            value=4,
            cursor='hand2',
            font=('Segoe UI', 10),
            bg=COLORS['background'],
            fg=COLORS['text_primary'],
            activebackground=COLORS['background'],
            selectcolor=COLORS['primary'],
            command=self.scale_choice_changed
        )
        self.rbut_mazheng.pack(anchor='w', padx=8, pady=4)
        self.rbut_mazheng.data = -4

        self.rbut_dodd = tk.Radiobutton(
            self.panel_scale_choice,
            text='Donegan-Dodd-McMasters',
            variable=self.scale_type_var,
            value=5,
            cursor='hand2',
            font=('Segoe UI', 9),
            bg=COLORS['background'],
            fg=COLORS['text_primary'],
            activebackground=COLORS['background'],
            selectcolor=COLORS['primary'],
            command=self.scale_choice_changed
        )
        self.rbut_dodd.pack(anchor='w', padx=8, pady=4)
        self.rbut_dodd.data = -5

        # ===== ПРАВА ПАНЕЛЬ - Область порівняння =====
        right_panel = ttk.Frame(main_container)
        right_panel.pack(side='left', fill='both', expand=True)

        # Прогрес з кращою типографікою
        self.progress_label = ttk.Label(
            right_panel,
            text="",
            font=('Segoe UI', 13, 'bold'),
            foreground=COLORS['text_secondary']
        )
        self.progress_label.pack(pady=(5, 10))

        # Кнопка підтвердження (Confirm button to skip/confirm current comparison) з сучасним дизайном
        self.confirm_button = tk.Button(
            right_panel,
            text='Підтверджую',
            relief='flat',
            cursor='hand2',
            bg=COLORS['secondary'],
            fg='white',
            font=('Segoe UI', 11, 'bold'),
            state='normal',
            activebackground=COLORS['success'],
            activeforeground='white',
            command=self._confirm_current_selection,
            padx=20,
            pady=8,
            borderwidth=0
        )
        self.confirm_button.pack(pady=12)

        # Заголовок з назвами об'єктів - сучасний card-стиль
        header_frame = tk.Frame(right_panel, bg=COLORS['surface'], relief='flat', bd=0, highlightthickness=1, highlightbackground=COLORS['border'])
        header_frame.pack(fill='x', pady=10)

        # Label A (зліва) з сучасними кольорами
        self.label_a = tk.Label(
            header_frame,
            text="Object A",
            font=('Segoe UI', 13, 'bold'),
            fg=COLORS['primary'],
            bg=COLORS['surface'],
            wraplength=200,
            justify='left'
        )
        self.label_a.pack(side='left', padx=25, pady=15)

        # Center labels з кращим дизайном
        center_frame = tk.Frame(header_frame, bg=COLORS['surface'])
        center_frame.pack(side='left', expand=True)

        self.label_is = tk.Label(
            center_frame,
            text='впливає',
            font=('Segoe UI', 11),
            fg=COLORS['text_secondary'],
            bg=COLORS['surface']
        )
        self.label_is.pack(pady=2)

        self.label_than = tk.Label(
            center_frame,
            text='',
            font=('Segoe UI', 12, 'bold'),
            fg=COLORS['accent'],
            bg=COLORS['surface']
        )
        self.label_than.pack(pady=2)

        # Label B (справа) з сучасними кольорами
        self.label_b = tk.Label(
            header_frame,
            text="Object B",
            font=('Segoe UI', 13, 'bold'),
            fg=COLORS['accent'],
            bg=COLORS['surface'],
            wraplength=200,
            justify='right'
        )
        self.label_b.pack(side='right', padx=25, pady=15)

        # Середня частина - панель шкали з сучасним дизайном
        middle_frame = tk.Frame(right_panel, bg=COLORS['surface'], relief='flat', bd=0, highlightthickness=1, highlightbackground=COLORS['border'])
        middle_frame.pack(fill='x', pady=10)

        # Інструкція з кращим дизайном
        instruction_label = ttk.Label(
            middle_frame,
            text="Оберіть рівень впливу:",
            font=('Segoe UI', 11),
            foreground=COLORS['text_secondary']
        )
        instruction_label.pack(pady=(10, 5))

        # Контейнер для динамічних панелей (centered with more padding)
        scale_container = tk.Frame(middle_frame, bg=COLORS['surface'])
        scale_container.pack(fill='x', padx=50, pady=15)

        self.panel_scale = tk.Frame(scale_container, bg=COLORS['background'], relief='flat', height=45, width=800)
        self.panel_scale.pack(anchor='center')
        self.panel_scale.pack_propagate(False)

        # Початкові кнопки Less/More з сучасним дизайном
        self.panel_less = tk.Button(
            self.panel_scale,
            text='Менше впливає',
            relief='flat',
            cursor='hand2',
            bg=COLORS['accent'],
            fg='white',
            font=('Segoe UI', 11, 'bold'),
            activebackground=COLORS['accent_light'],
            activeforeground='white',
            borderwidth=0
        )
        self.panel_less.place(x=0, y=7, relwidth=0.48, height=32)
        self.panel_less.hint = LESS_MORE[0]
        self.panel_less.config(command=lambda: self.panel_scale_click(self.panel_less))

        self.panel_more = tk.Button(
            self.panel_scale,
            text='Більше впливає',
            relief='flat',
            cursor='hand2',
            bg=COLORS['accent'],
            fg='white',
            font=('Segoe UI', 11, 'bold'),
            activebackground=COLORS['accent_light'],
            activeforeground='white',
            borderwidth=0
        )
        self.panel_more.place(relx=0.52, y=7, relwidth=0.48, height=32)
        self.panel_more.hint = LESS_MORE[1]
        self.panel_more.config(command=lambda: self.panel_scale_click(self.panel_more))

        # Візуалізація шкали з сучасним дизайном
        self.image_show = tk.Canvas(
            middle_frame,
            bg=COLORS['surface'],
            highlightthickness=1,
            highlightbackground=COLORS['border']
        )
        self.image_show.pack(fill='both', expand=True, padx=25, pady=(10, 15))
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
        for widget in [self.panel_less, self.panel_more,
                      self.rbut_integer, self.rbut_balanced, self.rbut_power,
                      self.rbut_mazheng, self.rbut_dodd]:
            widget.bind('<Enter>', self.show_hint_event)
            widget.bind('<Leave>', lambda e: self.hint_window.hide_hint())

        # Bind mouse wheel
        self.bind_all('<MouseWheel>', self.mouse_wheel)
        self.bind_all('<Button-4>', lambda e: self.spin_up_click())
        self.bind_all('<Button-5>', lambda e: self.spin_down_click())

        # Bind Enter key to confirm current selection (like in original Delphi)
        self.bind_all('<Return>', lambda e: self._confirm_current_selection())

    def _reset_comparison(self):
        """Reset state for new comparison"""
        self.reverse = -1
        self.res = 1.0
        self.rel = 0.0
        self.scale_str = '0'
        self.scale_type_id = 1

        self.panel_less.config(text=LESS_MORE[0])
        self.panel_more.config(text=LESS_MORE[1])
        self.panel_scale_choice.pack_forget()

        # Clear dynamic panels
        for panel in self.scale_panels:
            panel.destroy()
        self.scale_panels.clear()

        # Clear dividers
        for divider in self.scale_dividers:
            divider.destroy()
        self.scale_dividers.clear()

        # Clear directional indicator if it exists
        if self.directional_indicator:
            self.directional_indicator.destroy()
            self.directional_indicator = None

        # Reset button positions (updated for new design)
        self.panel_less.place(x=0, y=7, relwidth=0.48, height=32)
        self.panel_more.place(relx=0.52, y=7, relwidth=0.48, height=32)

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

        # Clear existing dividers
        for divider in self.scale_dividers:
            divider.destroy()
        self.scale_dividers.clear()

        # IMPORTANT: Clear directional indicator (gray Less/More button) if it exists
        # This prevents the old indicator from staying visible when rebuilding the scale
        if self.directional_indicator:
            self.directional_indicator.destroy()
            self.directional_indicator = None

        if self.reverse == -1:
            # Initial state - just show Less/More
            # Make sure Less/More buttons are visible (updated for new design)
            self.panel_less.place(x=0, y=7, relwidth=0.48, height=32)
            self.panel_more.place(relx=0.52, y=7, relwidth=0.48, height=32)
            return

        # Hide the original Less/More buttons when showing progressive scale
        self.panel_less.place_forget()
        self.panel_more.place_forget()

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
        panel_scale_width = 800  # Increased for better visual clarity

        for i in range(li, -1, -1):  # Reverse order
            # Create new panel з сучасним дизайном
            new_pin = tk.Button(
                self.panel_scale,
                text='',
                relief='flat',
                cursor='hand2',
                font=('Segoe UI', 9),
                borderwidth=0
            )

            if i == li:
                # Last panel - Less/More indicator з сучасним дизайном
                width = panel_scale_width // 9
                wi = width
                caption = LESS_MORE[1 - self.reverse]
                new_pin.config(text=caption, bg=COLORS['border'], fg=COLORS['text_primary'])
                new_pin.hint = caption

                if self.reverse == 1:  # More
                    left = 0
                else:  # Less
                    left = panel_scale_width - width

                # Track this directional indicator for cleanup
                self.directional_indicator = new_pin
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
                        # Grouped panels з сучасним дизайном
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
                        new_pin.config(bg=COLORS['border'], fg=COLORS['text_primary'])
                    else:
                        # Active panels з сучасним дизайном
                        if self.scale_type_var.get() == 1:  # Integer
                            width = width // (len(scale_str) - 2)
                        else:
                            width = round(panel_scale_width * 16 / 9 / 2 / sum_w *
                                        self.integer_by_scale(grade))
                        new_pin.config(bg=COLORS['accent'], fg='white', activebackground=COLORS['accent_light'])
                else:
                    # Regular scale з сучасним дизайном
                    if self.scale_type_var.get() == 1:  # Integer
                        width = panel_scale_width / 2 * 16 / 9 / li
                        width = int(width)
                    else:
                        width = round(panel_scale_width / 2 * 16 / 9 / sum_w *
                                    self.integer_by_scale(1.5 + (li - i - 0.5) * (9.5 - 1.5) / li))
                    new_pin.config(bg=COLORS['accent'], fg='white', activebackground=COLORS['accent_light'])

                wi += width
                left = panel_scale_width * (1 - self.reverse) - wi + 2 * wi * self.reverse - width * self.reverse
                new_pin.hint = PREF[grade]
                new_pin.config(text=PREF[grade])  # Add text label to panel

            # Position panel (updated height for modern design)
            new_pin.place(x=int(left), y=0, width=int(width), height=32)

            # Add thin black divider line to the right of this button (except for last button)
            if i < li:
                divider_x = int(left + width)
                divider = tk.Frame(
                    self.panel_scale,
                    bg='black',
                    width=1,
                    height=32
                )
                divider.place(x=divider_x, y=0, width=1, height=32)
                self.scale_dividers.append(divider)

            # Bind events
            new_pin.config(command=lambda p=new_pin: self.panel_scale_click(p))
            new_pin.bind('<Enter>', self.show_hint_event)
            new_pin.bind('<Leave>', lambda e: self.hint_window.hide_hint())

            if i < li:
                self.scale_panels.append(new_pin)

        # Update visualization
        self.show_image()

    def show_image(self):
        """Draw visual scale representation з сучасним дизайном"""
        self.image_show.delete('all')

        if self.reverse == -1:
            return

        # Find min/max positions
        min_l = 800  # Updated to match panel_scale_width
        max_r = 0

        for panel in self.scale_panels:
            if panel.winfo_exists() and panel.winfo_ismapped():
                x = panel.winfo_x()
                width = panel.winfo_width()
                hint = panel.hint

                # Draw vertical tick з сучасним кольором
                self.image_show.create_line(x, 0, x, 10, fill=COLORS['text_secondary'], width=2)

                # Draw vertical text з кращою типографікою
                center_x = x + width // 2
                self.image_show.create_text(
                    center_x - 5, 50,
                    text=hint, angle=90, anchor='w',
                    font=('Segoe UI', 9),
                    fill=COLORS['text_primary']
                )

                min_l = min(min_l, x)
                max_r = max(max_r, x + width)

        # Draw final tick and horizontal line з сучасним дизайном
        if max_r > 0:
            self.image_show.create_line(max_r - 1, 0, max_r - 1, 10, fill=COLORS['text_secondary'], width=2)
            self.image_show.create_line(min_l, 0, max_r - 1, 0, fill=COLORS['text_secondary'], width=2)

    def panel_scale_click(self, panel):
        """Handle scale panel click (progressive refinement logic)"""
        hint = panel.hint

        # Handle Less/More selection
        if hint in [LESS_MORE[0], LESS_MORE[1]]:
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
        elif self.scale_str == '259' and panel.cget('bg') == COLORS['accent']:
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
        elif panel.cget('bg') == COLORS['border']:
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

    def _confirm_current_selection(self):
        """Confirm current selection (even if partial) and move to next comparison"""
        # This allows users to skip/confirm at any stage of the progressive refinement
        # Similar to pressing Enter in the original Delphi implementation
        if self.reverse > -1:
            # User has made at least a Less/More selection
            # Confirm with current res/rel values
            self._confirm_comparison()
        else:
            # No selection made yet - treat as "not sure" (equal with zero reliability)
            self.res = 1.0
            self.rel = 0.0
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
        # Clean up any remaining UI elements
        for panel in self.scale_panels:
            panel.destroy()
        self.scale_panels.clear()

        for divider in self.scale_dividers:
            divider.destroy()
        self.scale_dividers.clear()

        if self.directional_indicator:
            self.directional_indicator.destroy()
            self.directional_indicator = None

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
        # Add top spacing
        ttk.Frame(self, height=20).pack()

        # Заголовок з сучасним дизайном
        title = ttk.Label(self, text="Результати", font=('Segoe UI', 26, 'bold'), foreground=COLORS['text_primary'])
        title.pack(pady=(10, 25))

        # Таблиця результатів з кращими відступами
        table_frame = ttk.Frame(self)
        table_frame.pack(pady=15, padx=40, fill='both', expand=True)

        # Заголовки таблиці з сучасним дизайном
        headers = ['Альтернатива', 'Вага', 'Ранг']
        for col, header in enumerate(headers):
            label = tk.Label(
                table_frame,
                text=header,
                font=('Segoe UI', 12, 'bold'),
                bg=COLORS['primary'],
                fg='white',
                relief='flat',
                borderwidth=0,
                padx=15,
                pady=10
            )
            label.grid(row=0, column=col, sticky='nsew', padx=1, pady=1)

        # Дані таблиці з сучасним дизайном
        for i, alternative in enumerate(self.alternatives):
            row_bg = COLORS['surface'] if i % 2 == 0 else COLORS['background']

            # Альтернатива
            label = tk.Label(
                table_frame,
                text=alternative,
                font=('Segoe UI', 10),
                bg=row_bg,
                fg=COLORS['text_primary'],
                relief='flat',
                borderwidth=0,
                padx=15,
                pady=8,
                anchor='w'
            )
            label.grid(row=i + 1, column=0, sticky='nsew', padx=1, pady=1)

            # Вага
            label = tk.Label(
                table_frame,
                text=f"{self.weights[i]:.4f}",
                font=('Segoe UI', 10),
                bg=row_bg,
                fg=COLORS['text_primary'],
                relief='flat',
                borderwidth=0,
                padx=15,
                pady=8
            )
            label.grid(row=i + 1, column=1, sticky='nsew', padx=1, pady=1)

            # Ранг
            label = tk.Label(
                table_frame,
                text=str(self.ranks[i]),
                font=('Segoe UI', 10, 'bold'),
                bg=row_bg,
                fg=COLORS['primary'],
                relief='flat',
                borderwidth=0,
                padx=15,
                pady=8
            )
            label.grid(row=i + 1, column=2, sticky='nsew', padx=1, pady=1)

        # Налаштувати розтягування колонок
        for col in range(3):
            table_frame.columnconfigure(col, weight=1)

        # Показники узгодженості з сучасним дизайном
        consistency_frame = ttk.LabelFrame(self, text="Показники узгодженості", padding=25)
        consistency_frame.pack(pady=20, padx=40, fill='x')

        lambda_max = self.consistency['lambda_max']
        ci = self.consistency['CI']
        cr = self.consistency['CR']
        is_consistent = self.consistency['is_consistent']

        ttk.Label(
            consistency_frame,
            text=f"λ_max = {lambda_max:.4f}",
            font=('Segoe UI', 11),
            foreground=COLORS['text_primary']
        ).pack(anchor='w', pady=3)

        ttk.Label(
            consistency_frame,
            text=f"Індекс узгодженості (CI) = {ci:.4f}",
            font=('Segoe UI', 11),
            foreground=COLORS['text_primary']
        ).pack(anchor='w', pady=3)

        cr_color = COLORS['success'] if is_consistent else COLORS['accent']
        cr_label = ttk.Label(
            consistency_frame,
            text=f"Коефіцієнт узгодженості (CR) = {cr:.4f}",
            font=('Segoe UI', 11, 'bold'),
            foreground=cr_color
        )
        cr_label.pack(anchor='w', pady=3)

        # Рекомендації з сучасним дизайном
        recommendations_frame = ttk.LabelFrame(self, text="Рекомендації", padding=25)
        recommendations_frame.pack(pady=(10, 15), padx=40, fill='both', expand=True)

        for recommendation in self.consistency['recommendations']:
            ttk.Label(
                recommendations_frame,
                text=f"• {recommendation}",
                font=('Segoe UI', 10),
                foreground=COLORS['text_secondary'],
                wraplength=700
            ).pack(anchor='w', pady=3)

        # Кнопка почати заново з кращим дизайном
        restart_btn = tk.Button(
            self,
            text="Почати заново",
            command=self.on_restart,
            relief='flat',
            cursor='hand2',
            bg=COLORS['primary'],
            fg='white',
            font=('Segoe UI', 11, 'bold'),
            activebackground=COLORS['primary_dark'],
            activeforeground='white',
            padx=30,
            pady=10,
            borderwidth=0
        )
        restart_btn.pack(pady=(10, 25))


class MainApplication(tk.Tk):
    """Головне вікно застосунку"""

    def __init__(self):
        super().__init__()

        self.title("Експертне оцінювання - Динамічний інтерфейс шкалування")
        self.geometry("1100x750")

        # Сучасний дизайн вікна
        self.configure(bg=COLORS['background'])

        # Стиль з сучасними налаштуваннями
        self.style = ttk.Style()
        self.style.theme_use('clam')

        # Налаштування кольорів для ttk компонентів
        self.style.configure('TFrame', background=COLORS['background'])
        self.style.configure('TLabel', background=COLORS['background'], foreground=COLORS['text_primary'], font=('Segoe UI', 10))
        self.style.configure('TButton', background=COLORS['primary'], foreground='white', borderwidth=0, focuscolor='none', font=('Segoe UI', 10))
        self.style.map('TButton', background=[('active', COLORS['hover'])])
        self.style.configure('Accent.TButton', background=COLORS['secondary'], foreground='white', font=('Segoe UI', 11, 'bold'))
        self.style.map('Accent.TButton', background=[('active', COLORS['success'])])
        self.style.configure('TLabelframe', background=COLORS['background'], foreground=COLORS['text_primary'], borderwidth=1, relief='flat')
        self.style.configure('TLabelframe.Label', background=COLORS['background'], foreground=COLORS['text_primary'], font=('Segoe UI', 11, 'bold'))
        self.style.configure('TEntry', fieldbackground=COLORS['surface'], foreground=COLORS['text_primary'], borderwidth=1)

        # Створити контейнер для панелей з сучасним фоном
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
