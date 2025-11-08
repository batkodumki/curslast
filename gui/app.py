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

    # Modern Color Scheme
    COLORS = {
        'primary': '#4A90E2',
        'primary_dark': '#357ABD',
        'primary_light': '#6FA8E8',
        'secondary': '#7B68EE',
        'success': '#50C878',
        'warning': '#FFA500',
        'danger': '#E74C3C',
        'background': '#F8F9FA',
        'card': '#FFFFFF',
        'card_shadow': '#E8E9EA',
        'text': '#2C3E50',
        'text_secondary': '#7F8C8D',
        'text_light': '#95A5A6',
        'border': '#DFE4EA',
        'scale_active': '#5C7CFA',
        'scale_inactive': '#E9ECEF',
        'less_color': '#FA5252',
        'more_color': '#20C997',
        'equal_color': '#868E96'
    }

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
        """Create modernized UI with professional styling"""
        # Set background color
        self.configure(style='Card.TFrame')

        # Main container with better padding
        main_container = tk.Frame(self, bg=self.COLORS['background'])
        main_container.pack(fill='both', expand=True, padx=20, pady=20)

        # ===== LEFT PANEL - Scale Settings =====
        left_panel = tk.Frame(main_container, bg=self.COLORS['card'],
                             relief='flat', bd=0, width=280)
        left_panel.pack(side='left', fill='y', padx=(0, 16))
        left_panel.pack_propagate(False)

        # Add subtle shadow effect with border
        left_panel.configure(highlightbackground=self.COLORS['border'],
                           highlightthickness=1)

        # Left panel header
        header_left = tk.Frame(left_panel, bg=self.COLORS['primary'], height=50)
        header_left.pack(fill='x')
        header_left.pack_propagate(False)

        tk.Label(
            header_left,
            text="⚙ Налаштування",
            font=('Segoe UI', 11, 'bold'),
            bg=self.COLORS['primary'],
            fg='white'
        ).pack(pady=12)

        # Scale type choice panel
        self.panel_scale_choice = tk.Frame(left_panel, bg=self.COLORS['card'])
        self.panel_scale_choice.pack(padx=12, pady=12, fill='both')

        # Scale type selector with modern styling
        selector_frame = tk.Frame(self.panel_scale_choice, bg=self.COLORS['card'])
        selector_frame.pack(fill='x', pady=(0, 8))

        tk.Label(
            selector_frame,
            text="Тип шкали:",
            font=('Segoe UI', 9),
            bg=self.COLORS['card'],
            fg=self.COLORS['text_secondary']
        ).pack(anchor='w', pady=(0, 4))

        button_spin_frame = tk.Frame(selector_frame, bg=self.COLORS['card'])
        button_spin_frame.pack(fill='x')

        self.panel_scale_button_choice = tk.Button(
            button_spin_frame,
            text='▼ Оберіть тип',
            relief='solid',
            cursor='hand2',
            font=('Segoe UI', 9),
            bg=self.COLORS['card'],
            fg=self.COLORS['text'],
            activebackground=self.COLORS['primary_light'],
            bd=1,
            command=self.toggle_scale_choice
        )
        self.panel_scale_button_choice.pack(side='left', fill='x', expand=True, ipady=6)

        # Spin buttons with modern style
        spin_frame = tk.Frame(button_spin_frame, bg=self.COLORS['card'])
        spin_frame.pack(side='right', padx=(4, 0))

        self.spin_up = tk.Button(
            spin_frame,
            text='▲',
            command=self.spin_up_click,
            width=3,
            font=('Segoe UI', 8),
            bg=self.COLORS['scale_inactive'],
            fg=self.COLORS['text'],
            activebackground=self.COLORS['primary_light'],
            relief='solid',
            bd=1,
            cursor='hand2'
        )
        self.spin_up.pack(side='top', pady=(0, 2))

        self.spin_down = tk.Button(
            spin_frame,
            text='▼',
            command=self.spin_down_click,
            width=3,
            font=('Segoe UI', 8),
            bg=self.COLORS['scale_inactive'],
            fg=self.COLORS['text'],
            activebackground=self.COLORS['primary_light'],
            relief='solid',
            bd=1,
            cursor='hand2'
        )
        self.spin_down.pack(side='bottom')

        # Radio buttons for scale types with modern styling
        self.scale_type_var = tk.IntVar(value=1)

        # Separator
        tk.Frame(
            self.panel_scale_choice,
            height=1,
            bg=self.COLORS['border']
        ).pack(fill='x', pady=8)

        # Radio buttons container
        radio_container = tk.Frame(self.panel_scale_choice, bg=self.COLORS['card'])
        radio_container.pack(fill='x')

        self.rbut_integer = tk.Radiobutton(
            radio_container,
            text='⬤ Integer Scale',
            variable=self.scale_type_var,
            value=1,
            cursor='hand2',
            font=('Segoe UI', 9),
            bg=self.COLORS['card'],
            fg=self.COLORS['text'],
            selectcolor=self.COLORS['primary_light'],
            activebackground=self.COLORS['card'],
            command=self.scale_choice_changed
        )
        self.rbut_integer.pack(anchor='w', padx=4, pady=3)
        self.rbut_integer.data = -1

        self.rbut_balanced = tk.Radiobutton(
            radio_container,
            text='⬤ Balanced Scale',
            variable=self.scale_type_var,
            value=2,
            cursor='hand2',
            font=('Segoe UI', 9),
            bg=self.COLORS['card'],
            fg=self.COLORS['text'],
            selectcolor=self.COLORS['primary_light'],
            activebackground=self.COLORS['card'],
            command=self.scale_choice_changed
        )
        self.rbut_balanced.pack(anchor='w', padx=4, pady=3)
        self.rbut_balanced.data = -2

        self.rbut_power = tk.Radiobutton(
            radio_container,
            text='⬤ Power Scale',
            variable=self.scale_type_var,
            value=3,
            cursor='hand2',
            font=('Segoe UI', 9),
            bg=self.COLORS['card'],
            fg=self.COLORS['text'],
            selectcolor=self.COLORS['primary_light'],
            activebackground=self.COLORS['card'],
            command=self.scale_choice_changed
        )
        self.rbut_power.pack(anchor='w', padx=4, pady=3)
        self.rbut_power.data = -3

        self.rbut_mazheng = tk.Radiobutton(
            radio_container,
            text='⬤ Ma-Zheng (9/9-9/1)',
            variable=self.scale_type_var,
            value=4,
            cursor='hand2',
            font=('Segoe UI', 9),
            bg=self.COLORS['card'],
            fg=self.COLORS['text'],
            selectcolor=self.COLORS['primary_light'],
            activebackground=self.COLORS['card'],
            command=self.scale_choice_changed
        )
        self.rbut_mazheng.pack(anchor='w', padx=4, pady=3)
        self.rbut_mazheng.data = -4

        self.rbut_dodd = tk.Radiobutton(
            radio_container,
            text='⬤ Donegan-Dodd-McMasters',
            variable=self.scale_type_var,
            value=5,
            cursor='hand2',
            font=('Segoe UI', 9),
            bg=self.COLORS['card'],
            fg=self.COLORS['text'],
            selectcolor=self.COLORS['primary_light'],
            activebackground=self.COLORS['card'],
            command=self.scale_choice_changed
        )
        self.rbut_dodd.pack(anchor='w', padx=4, pady=3)
        self.rbut_dodd.data = -5

        # Spacer to push button to bottom
        tk.Frame(left_panel, bg=self.COLORS['card']).pack(fill='both', expand=True)

        # Separator above button
        tk.Frame(left_panel, height=1, bg=self.COLORS['border']).pack(fill='x')

        # No idea button with modern styling
        self.panel_no_idea = tk.Button(
            left_panel,
            text='❓ Не впевнений\n(Рівноцінно)',
            relief='flat',
            cursor='hand2',
            font=('Segoe UI', 10, 'bold'),
            bg=self.COLORS['warning'],
            fg='white',
            activebackground=self.COLORS['warning'],
            activeforeground='white',
            command=self.no_idea_click,
            height=3
        )
        self.panel_no_idea.pack(fill='x')
        self.panel_no_idea.hint = LESS_MORE[2]

        # ===== RIGHT PANEL - Comparison Area =====
        right_panel = tk.Frame(main_container, bg=self.COLORS['card'],
                              relief='flat', bd=0)
        right_panel.pack(side='left', fill='both', expand=True)

        # Add subtle border
        right_panel.configure(highlightbackground=self.COLORS['border'],
                            highlightthickness=1)

        # Right panel header with gradient-like effect
        header_right = tk.Frame(right_panel, bg=self.COLORS['primary'], height=50)
        header_right.pack(fill='x')
        header_right.pack_propagate(False)

        # Progress label inside header
        self.progress_label = tk.Label(
            header_right,
            text="",
            font=('Segoe UI', 11, 'bold'),
            bg=self.COLORS['primary'],
            fg='white'
        )
        self.progress_label.pack(pady=12)

        # Content area inside right panel
        content_area = tk.Frame(right_panel, bg=self.COLORS['card'])
        content_area.pack(fill='both', expand=True, padx=16, pady=16)

        # Comparison header with object names
        header_frame = tk.Frame(content_area, bg=self.COLORS['background'],
                               relief='flat', bd=0, height=80)
        header_frame.pack(fill='x', pady=(0, 12))
        header_frame.pack_propagate(False)

        # Add border to header
        header_frame.configure(highlightbackground=self.COLORS['border'],
                              highlightthickness=1)

        # Label A (left)
        self.label_a = tk.Label(
            header_frame,
            text="Object A",
            font=('Segoe UI', 13, 'bold'),
            fg=self.COLORS['primary'],
            bg=self.COLORS['background'],
            wraplength=220,
            justify='left'
        )
        self.label_a.pack(side='left', padx=16, pady=12)

        # Center section with comparison text
        center_frame = tk.Frame(header_frame, bg=self.COLORS['background'])
        center_frame.pack(side='left', expand=True, fill='both')

        self.label_is = tk.Label(
            center_frame,
            text='впливає',
            font=('Segoe UI', 10),
            fg=self.COLORS['text_secondary'],
            bg=self.COLORS['background']
        )
        self.label_is.pack(expand=True)

        self.label_than = tk.Label(
            center_frame,
            text='',
            font=('Segoe UI', 12, 'bold'),
            fg=self.COLORS['danger'],
            bg=self.COLORS['background']
        )
        self.label_than.pack(expand=True)

        # Label B (right)
        self.label_b = tk.Label(
            header_frame,
            text="Object B",
            font=('Segoe UI', 13, 'bold'),
            fg=self.COLORS['secondary'],
            bg=self.COLORS['background'],
            wraplength=220,
            justify='right'
        )
        self.label_b.pack(side='right', padx=16, pady=12)

        # Scale selection area
        scale_section = tk.Frame(content_area, bg=self.COLORS['background'],
                                relief='flat', bd=0)
        scale_section.pack(fill='x', pady=(0, 12))

        # Add border
        scale_section.configure(highlightbackground=self.COLORS['border'],
                               highlightthickness=1)

        # Instruction with icon
        instruction_header = tk.Frame(scale_section, bg=self.COLORS['primary_light'],
                                     height=36)
        instruction_header.pack(fill='x')
        instruction_header.pack_propagate(False)

        tk.Label(
            instruction_header,
            text="👆 Оберіть рівень впливу",
            font=('Segoe UI', 10, 'bold'),
            bg=self.COLORS['primary_light'],
            fg='white'
        ).pack(pady=8)

        # Container for dynamic scale panels
        scale_container = tk.Frame(scale_section, bg=self.COLORS['card'])
        scale_container.pack(fill='x', padx=16, pady=16)

        self.panel_scale = tk.Frame(scale_container, bg=self.COLORS['background'],
                                    relief='flat', height=50)
        self.panel_scale.pack(fill='x')
        self.panel_scale.pack_propagate(False)

        # Initial Less/More buttons with modern styling
        self.panel_less = tk.Button(
            self.panel_scale,
            text='◀ Менше впливає',
            relief='flat',
            cursor='hand2',
            bg=self.COLORS['less_color'],
            fg='white',
            font=('Segoe UI', 11, 'bold'),
            activebackground='#E03131',
            activeforeground='white'
        )
        self.panel_less.place(x=0, y=5, relwidth=0.48, height=40)
        self.panel_less.hint = LESS_MORE[0]
        self.panel_less.config(command=lambda: self.panel_scale_click(self.panel_less))

        self.panel_more = tk.Button(
            self.panel_scale,
            text='Більше впливає ▶',
            relief='flat',
            cursor='hand2',
            bg=self.COLORS['more_color'],
            fg='white',
            font=('Segoe UI', 11, 'bold'),
            activebackground='#12B886',
            activeforeground='white'
        )
        self.panel_more.place(relx=0.52, y=5, relwidth=0.48, height=40)
        self.panel_more.hint = LESS_MORE[1]
        self.panel_more.config(command=lambda: self.panel_scale_click(self.panel_more))

        # Visualization area with improved styling
        viz_frame = tk.Frame(content_area, bg=self.COLORS['background'],
                            relief='flat', bd=0)
        viz_frame.pack(fill='both', expand=True)

        # Add border
        viz_frame.configure(highlightbackground=self.COLORS['border'],
                           highlightthickness=1)

        # Visualization header
        viz_header = tk.Frame(viz_frame, bg=self.COLORS['scale_inactive'],
                             height=32)
        viz_header.pack(fill='x')
        viz_header.pack_propagate(False)

        tk.Label(
            viz_header,
            text="📊 Візуалізація шкали",
            font=('Segoe UI', 9, 'bold'),
            bg=self.COLORS['scale_inactive'],
            fg=self.COLORS['text']
        ).pack(pady=6)

        self.image_show = tk.Canvas(
            viz_frame,
            bg=self.COLORS['card'],
            highlightthickness=0
        )
        self.image_show.pack(fill='both', expand=True, padx=8, pady=8)
        self.image_show.configure(height=120)

        # ===== NAVIGATION BUTTONS =====
        nav_frame = tk.Frame(content_area, bg=self.COLORS['card'])
        nav_frame.pack(pady=(12, 0))

        # Back button
        back_btn = tk.Button(
            nav_frame,
            text="← Попередня пара",
            command=self._go_back,
            font=('Segoe UI', 9),
            bg=self.COLORS['scale_inactive'],
            fg=self.COLORS['text'],
            activebackground=self.COLORS['border'],
            cursor='hand2',
            relief='flat',
            padx=16,
            pady=8
        )
        back_btn.pack(side='left', padx=(0, 8))

        # Return button
        return_btn = tk.Button(
            nav_frame,
            text="⏎ Повернутися до введення",
            command=self.on_back,
            font=('Segoe UI', 9),
            bg=self.COLORS['scale_inactive'],
            fg=self.COLORS['text'],
            activebackground=self.COLORS['border'],
            cursor='hand2',
            relief='flat',
            padx=16,
            pady=8
        )
        return_btn.pack(side='left')

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

        self.panel_no_idea.config(text='❓ Не впевнений\n(Рівноцінно)')
        self.panel_no_idea.hint = PREF[1]
        self.panel_less.config(text='◀ Менше впливає')
        self.panel_more.config(text='Більше впливає ▶')
        self.panel_scale_choice.pack_forget()

        # Clear dynamic panels
        for panel in self.scale_panels:
            panel.destroy()
        self.scale_panels.clear()

        # Reset button positions and styling
        self.panel_less.place(x=0, y=5, relwidth=0.48, height=40)
        self.panel_more.place(relx=0.52, y=5, relwidth=0.48, height=40)

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
            # Make sure Less/More buttons are visible
            self.panel_less.place(x=0, y=5, relwidth=0.48, height=40)
            self.panel_more.place(relx=0.52, y=5, relwidth=0.48, height=40)
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
        panel_scale_width = 475

        for i in range(li, -1, -1):  # Reverse order
            # Create new panel with modern styling
            new_pin = tk.Button(
                self.panel_scale,
                text='',
                relief='flat',
                cursor='hand2',
                font=('Segoe UI', 9, 'bold'),
                bd=0
            )

            if i == li:
                # Last panel - Less/More indicator
                width = panel_scale_width // 9
                wi = width
                caption = LESS_MORE[1 - self.reverse]
                new_pin.config(
                    text=caption,
                    bg=self.COLORS['scale_inactive'],
                    fg=self.COLORS['text'],
                    activebackground=self.COLORS['border']
                )
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
                        # Grouped panels with modern styling
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
                        new_pin.config(
                            bg=self.COLORS['scale_inactive'],
                            fg=self.COLORS['text'],
                            activebackground=self.COLORS['border']
                        )
                    else:
                        # Active panels with modern styling
                        if self.scale_type_var.get() == 1:  # Integer
                            width = width // (len(scale_str) - 2)
                        else:
                            width = round(panel_scale_width * 16 / 9 / 2 / sum_w *
                                        self.integer_by_scale(grade))
                        new_pin.config(
                            bg=self.COLORS['scale_active'],
                            fg='white',
                            activebackground=self.COLORS['primary_dark']
                        )
                else:
                    # Regular scale with modern styling
                    if self.scale_type_var.get() == 1:  # Integer
                        width = panel_scale_width / 2 * 16 / 9 / li
                        width = int(width)
                    else:
                        width = round(panel_scale_width / 2 * 16 / 9 / sum_w *
                                    self.integer_by_scale(1.5 + (li - i - 0.5) * (9.5 - 1.5) / li))
                    new_pin.config(
                        bg=self.COLORS['scale_active'],
                        fg='white',
                        activebackground=self.COLORS['primary_dark']
                    )

                wi += width
                left = panel_scale_width * (1 - self.reverse) - wi + 2 * wi * self.reverse - width * self.reverse
                new_pin.hint = PREF[grade]

            # Position panel with modern height
            new_pin.place(x=int(left), y=5, width=int(width), height=40)

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
