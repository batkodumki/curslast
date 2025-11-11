"""
Dynamic Scale Interface with Fixed Cube Placement

This module provides a visual interface for pairwise comparisons using a balance scale metaphor.
The cubes now sit correctly on the tilted balance pans.
"""

import tkinter as tk
from tkinter import font as tkfont
import math
from typing import Tuple, Optional, List


# Constants

# Preference labels
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

# Less/More labels
LESS_MORE = ['Less', 'More', 'Not sure']

# Gradual scale configurations
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
    Custom graphical hint window showing balance scale visualization.
    FIXED: Cubes now sit correctly on the tilted balance pans.
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
        """
        Paint the hint content with balance scale visualization.
        FIXED: Cubes are now positioned correctly on the balance beam pans.
        """
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
            # Object B preferred (tilted right - right side lower)
            # Beam positions: left at (40, 125), right at (210, 105)
            self.draw_balance_tilted_right()
            data_ = (1 / self.data) ** (1/3)  # Cube root for scaling

            xe, ye = 25, 25  # Base dimensions

            # Draw heavier weight on right (Object B) - ON the right pan at (210, 105)
            bottom_right = 105
            top_right = bottom_right - round(ye * data_)
            left_right = 210 - round(xe * data_ / 2)
            right_right = left_right + round(xe * data_)
            self.canvas.create_rectangle(left_right, top_right, right_right, bottom_right,
                                        fill='red', outline='black', width=2)

            # Draw lighter weight on left (Object A) - ON the left pan at (40, 125)
            bottom_left = 125
            top_left = bottom_left - ye
            left_left = 40 - xe // 2
            right_left = left_left + xe
            self.canvas.create_rectangle(left_left, top_left, right_left, bottom_left,
                                        fill='blue', outline='black', width=2)
        else:
            # Object A preferred or equal (tilted left - left side lower)
            # Beam positions: left at (40, 105), right at (210, 125)
            self.draw_balance_tilted_left()
            data_ = self.data ** (1/3)  # Cube root for scaling

            xe, ye = 25, 25

            # Draw heavier weight on left (Object A) - ON the left pan at (40, 105)
            bottom_left = 105
            top_left = bottom_left - round(ye * data_)
            left_left = 40 - round(xe * data_ / 2)
            right_left = left_left + round(xe * data_)
            self.canvas.create_rectangle(left_left, top_left, right_left, bottom_left,
                                        fill='blue', outline='black', width=2)

            # Draw lighter weight on right (Object B) - ON the right pan at (210, 125)
            bottom_right = 125
            top_right = bottom_right - ye
            left_right = 210 - xe // 2
            right_right = left_right + xe
            self.canvas.create_rectangle(left_right, top_right, right_right, bottom_right,
                                        fill='red', outline='black', width=2)

            if self.data == 1:
                # Equal - show question mark
                self.canvas.create_text(125, 100, text='?', font=('Arial', 60), fill='red')

    def draw_balance_tilted_right(self):
        """Draw balance scale tilted to the right (B heavier).
        Beam: left at (40, 125), right at (210, 105)
        """
        # Fulcrum (triangle)
        self.canvas.create_polygon(125, 110, 110, 140, 140, 140, fill='gray', outline='black', width=2)
        # Beam tilted right: left higher, right lower
        self.canvas.create_line(40, 125, 210, 105, width=4, fill='brown')

    def draw_balance_tilted_left(self):
        """Draw balance scale tilted to the left (A heavier).
        Beam: left at (40, 105), right at (210, 125)
        """
        # Fulcrum (triangle)
        self.canvas.create_polygon(125, 110, 110, 140, 140, 140, fill='gray', outline='black', width=2)
        # Beam tilted left: left lower, right higher
        self.canvas.create_line(40, 105, 210, 125, width=4, fill='brown')


class DynamicScaleInterface:
    """
    Main Dynamic Scale Interface for pairwise comparisons.
    """

    def __init__(self, root: tk.Tk, object_a: str = "Object A", object_b: str = "Object B"):
        """
        Initialize the interface.

        Args:
            root: Tkinter root window
            object_a: Name of first comparison object
            object_b: Name of second comparison object
        """
        self.root = root
        self.object_a = object_a
        self.object_b = object_b

        # State variables
        self.reverse = -1  # -1: not set, 0: Less, 1: More
        self.res = 1.0     # Result estimate
        self.rel = 0.0     # Reliability
        self.scale_str = '0'  # Current scale configuration
        self.scale_type = 0   # 0: none, 1-5: scale types
        self.delay_wheel = 0  # Mouse wheel delay
        self.data = 0.0    # Data for hints

        # UI component references
        self.scale_panels: List[tk.Button] = []
        self.panel_less: Optional[tk.Button] = None
        self.panel_more: Optional[tk.Button] = None

        # Setup window and create all widgets
        self.setup_window()
        self.create_widgets()
        self.bind_events()

        # Create graphic hint window
        self.hint_window = GraphicHintWindow(self.root)

        # Initialize form
        self.form_show()

    def setup_window(self):
        """Configure main window."""
        self.root.title('Make a choice using visual hints')
        self.root.geometry('779x195')
        self.root.resizable(False, False)
        self.root.configure(bg='#f0f0f0')

        # Center on screen
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (779 // 2)
        y = (self.root.winfo_screenheight() // 2) - (195 // 2)
        self.root.geometry(f'779x195+{x}+{y}')

        self.root.protocol("WM_DELETE_WINDOW", self.close_window)

    def create_widgets(self):
        """Create all UI widgets."""
        # LabelA
        self.label_a = tk.Label(
            self.root, text=self.object_a,
            font=('MS Sans Serif', 9), fg='red',
            bg='#f0f0f0', wraplength=150, justify='left'
        )
        self.label_a.place(x=0, y=8, width=150, height=73)

        # LabelB
        self.label_b = tk.Label(
            self.root, text=self.object_b,
            font=('MS Sans Serif', 9), fg='red',
            bg='#f0f0f0', wraplength=150, justify='left'
        )
        self.label_b.place(x=630, y=8, width=150, height=73)

        # LabelIs
        self.label_is = tk.Label(
            self.root, text='is',
            font=('MS Sans Serif', 12, 'bold'), fg='red',
            bg='#f0f0f0'
        )
        self.label_is.place(x=154, y=4)

        # LabelThan
        self.label_than = tk.Label(
            self.root, text='than',
            font=('MS Sans Serif', 12, 'bold'), fg='red',
            bg='#f0f0f0'
        )
        self.label_than.place(x=589, y=3)

        # ImageShow canvas
        self.image_show = tk.Canvas(
            self.root, bg='white', highlightthickness=0
        )
        self.image_show.place(x=154, y=53, width=476, height=142)

        # PanelScale container
        self.panel_scale = tk.Frame(self.root, bg='#f0f0f0', relief='flat')
        self.panel_scale.place(x=154, y=28, width=475, height=25)

        # PanelLess
        self.panel_less = tk.Button(
            self.panel_scale, text='Less preferred',
            relief='raised', cursor='hand2',
            bg='red', fg='white', font=('MS Sans Serif', 9)
        )
        self.panel_less.place(x=0, y=0, width=153, height=25)
        self.panel_less.hint = LESS_MORE[0]

        # PanelMore
        self.panel_more = tk.Button(
            self.panel_scale, text='More preferred',
            relief='raised', cursor='hand2',
            bg='red', fg='white', font=('MS Sans Serif', 9)
        )
        self.panel_more.place(x=152, y=0, width=129, height=25)
        self.panel_more.hint = LESS_MORE[1]

        # PanelScaleChoice
        self.panel_scale_choice = tk.Frame(self.root, relief='raised', bd=2)
        self.panel_scale_choice.place(x=0, y=80, width=153, height=115)

        # PanelScaleButtonChoice
        self.panel_scale_button_choice = tk.Button(
            self.panel_scale_choice, text='Scale Type Choice',
            relief='sunken', cursor='hand2',
            font=('MS Sans Serif', 9)
        )
        self.panel_scale_button_choice.place(x=0, y=0, width=114, height=27)

        # Spin buttons
        self.spin_frame = tk.Frame(self.panel_scale_choice)
        self.spin_frame.place(x=113, y=0, width=41, height=27)

        self.spin_up = tk.Button(self.spin_frame, text='▲', command=self.spin_up_click)
        self.spin_up.pack(side='top', fill='both', expand=True)

        self.spin_down = tk.Button(self.spin_frame, text='▼', command=self.spin_down_click)
        self.spin_down.pack(side='bottom', fill='both', expand=True)

        # Radio buttons for scale types
        self.scale_type_var = tk.IntVar(value=1)

        # RButInteger
        self.rbut_integer = tk.Radiobutton(
            self.panel_scale_choice, text='Integer',
            variable=self.scale_type_var, value=1,
            cursor='hand2', font=('MS Sans Serif', 9),
            command=self.scale_choice_changed
        )
        self.rbut_integer.place(x=3, y=29, width=102, height=17)
        self.rbut_integer.data = -1

        # RButPower
        self.rbut_power = tk.Radiobutton(
            self.panel_scale_choice, text='Power',
            variable=self.scale_type_var, value=3,
            cursor='hand2', font=('MS Sans Serif', 9),
            command=self.scale_choice_changed
        )
        self.rbut_power.place(x=3, y=45, width=137, height=17)
        self.rbut_power.data = -3

        # RButBalanced
        self.rbut_balanced = tk.Radiobutton(
            self.panel_scale_choice, text='Balanced',
            variable=self.scale_type_var, value=2,
            cursor='hand2', font=('MS Sans Serif', 9),
            command=self.scale_choice_changed
        )
        self.rbut_balanced.place(x=3, y=61, width=137, height=17)
        self.rbut_balanced.data = -2

        # RButMaZheng
        self.rbut_mazheng = tk.Radiobutton(
            self.panel_scale_choice, text='Ma-Zheng (9/9-9/1)',
            variable=self.scale_type_var, value=4,
            cursor='hand2', font=('MS Sans Serif', 9),
            command=self.scale_choice_changed
        )
        self.rbut_mazheng.place(x=3, y=77, width=149, height=17)
        self.rbut_mazheng.data = -4

        # RButDodd
        self.rbut_dodd = tk.Radiobutton(
            self.panel_scale_choice, text='Donegan-Dodd-McMasters',
            variable=self.scale_type_var, value=5,
            cursor='hand2', font=('MS Sans Serif', 9),
            command=self.scale_choice_changed
        )
        self.rbut_dodd.place(x=3, y=93, width=148, height=17)
        self.rbut_dodd.data = -5

        # PanelNoIdea
        self.panel_no_idea = tk.Button(
            self.root, text='No idea',
            relief='raised', cursor='hand2',
            font=('MS Sans Serif', 9)
        )
        self.panel_no_idea.place(x=638, y=128, width=137, height=25)
        self.panel_no_idea.hint = LESS_MORE[2]

    def bind_events(self):
        """Bind all keyboard and mouse events."""
        self.root.bind('<Return>', lambda e: self.no_idea_click())
        self.root.bind('<MouseWheel>', self.mouse_wheel)
        self.root.bind('<Button-4>', lambda e: self.spin_up_click())
        self.root.bind('<Button-5>', lambda e: self.spin_down_click())

        # Panel click events
        self.panel_less.config(command=lambda: self.panel_scale_click(self.panel_less))
        self.panel_more.config(command=lambda: self.panel_scale_click(self.panel_more))
        self.panel_no_idea.config(command=self.no_idea_click)
        self.panel_scale_button_choice.config(command=self.toggle_scale_choice)

        # Mouse move events for visual feedback
        self.panel_less.bind('<Enter>', lambda e: self.panel_mouse_enter(self.panel_less))
        self.panel_more.bind('<Enter>', lambda e: self.panel_mouse_enter(self.panel_more))
        self.panel_no_idea.bind('<Enter>', lambda e: self.panel_mouse_enter(self.panel_no_idea))

        # Hint events
        for widget in [self.panel_less, self.panel_more, self.panel_no_idea,
                      self.rbut_integer, self.rbut_balanced, self.rbut_power,
                      self.rbut_mazheng, self.rbut_dodd]:
            widget.bind('<Enter>', self.show_hint_event)
            widget.bind('<Leave>', lambda e: self.hint_window.hide_hint())

    def form_show(self):
        """Initialize form state."""
        self.reverse = -1
        self.res = 1.0
        self.rel = 0.0
        self.scale_str = '0'

        self.panel_no_idea.config(text=PREF[1])
        self.panel_no_idea.hint = PREF[1]
        self.panel_less.config(text=LESS_MORE[0])
        self.panel_more.config(text=LESS_MORE[1])
        self.panel_scale_choice.place_forget()

        self.build_scale(self.scale_str)
        self.show_image()

    def integer_by_scale(self, data: float) -> float:
        """Apply scale transformation."""
        result = data

        scale_type = self.scale_type_var.get()

        if scale_type == 2:  # Balanced
            result = (0.5 + (data - 1) * 0.05) / (0.5 - (data - 1) * 0.05)
        if scale_type == 3:  # Power
            result = math.pow(9, (data - 1) / 8)
        if scale_type == 4:  # Ma-Zheng
            result = 9 / (9 + 1 - data)
        if scale_type == 5:  # Dodd
            result = math.exp(math.atanh((data - 1) / 14 * math.sqrt(3)))

        return result

    def in_range(self, value: int, min_val: int, max_val: int) -> bool:
        """Helper function for range checking."""
        return min_val <= value <= max_val

    def build_scale(self, scale_str: str):
        """Build dynamic scale panels."""
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
        wi = 0
        panel_scale_width = 475

        for i in range(li, -1, -1):
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

                # Calculate width based on algorithm
                if scale_str in ['23459', '25679', '2589']:
                    # Special handling for these scales
                    if self.scale_type_var.get() == 1:  # Integer
                        width = panel_scale_width * 16 // 9 // 6

                    pos = scale_str.index(grade_char) + 1

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
            new_pin.place(x=int(left), y=0, width=int(width), height=25)

            # Bind events
            new_pin.config(command=lambda p=new_pin: self.panel_scale_click(p))
            new_pin.bind('<Enter>', lambda e, p=new_pin: self.panel_mouse_enter(p))
            new_pin.bind('<Enter>', self.show_hint_event)
            new_pin.bind('<Leave>', lambda e: self.hint_window.hide_hint())

            if i < li:
                self.scale_panels.append(new_pin)

    def show_image(self):
        """Draw visual scale representation."""
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
        """Handle scale panel click."""
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
            self.rel = 1.0
            self.res = 5.5
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

            self.rel = 3.0
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
            self.close_window()
            return

        # Rebuild scale and update
        self.build_scale(self.scale_str)
        self.panel_scale_choice.place(x=0, y=80, width=153, height=115)

        st = LESS_MORE[self.reverse]
        self.label_is.config(text=f'{self.label_is.cget("text").split()[0]} {st}')

        self.show_image()

    def panel_mouse_enter(self, panel):
        """Handle mouse enter on panel (visual feedback)."""
        if panel.cget('bg') == 'red':
            panel.config(relief='sunken')

    def show_hint_event(self, event):
        """Show graphical hint."""
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
                    # Find grade for hint
                    for i, pref in enumerate(PREF):
                        if widget.hint == pref:
                            grade = i
                            data = self.integer_by_scale(grade)
                            break

                    if self.reverse == 0:  # Less
                        data = 1 / data if data != 0 else 1

        # Show hint window
        x = widget.winfo_rootx()
        y = widget.winfo_rooty()
        self.hint_window.show_hint(x, y, hint_text, data)

    def no_idea_click(self):
        """Handle 'No idea' button click."""
        self.res = 1.0
        self.rel = 0.0
        self.close_window()

    def toggle_scale_choice(self):
        """Toggle scale choice panel visibility."""
        if self.panel_scale_choice.winfo_ismapped():
            self.panel_scale_choice.place_forget()
        else:
            self.panel_scale_choice.place(x=0, y=80, width=153, height=115)

    def scale_choice_changed(self):
        """Handle scale type selection change."""
        # Rebuild scale with new type
        self.build_scale(self.scale_str)
        self.show_image()

    def spin_up_click(self):
        """Handle spin up button click."""
        # Implement gradation increase logic if needed
        pass

    def spin_down_click(self):
        """Handle spin down button click."""
        # Implement gradation decrease logic if needed
        pass

    def mouse_wheel(self, event):
        """Handle mouse wheel scrolling."""
        # Implement mouse wheel logic if needed
        pass

    def close_window(self):
        """Close the window and return result."""
        self.root.quit()
        self.root.destroy()

    def get_result(self):
        """Get the comparison result."""
        return self.res, self.rel


def main():
    """Main entry point for the application."""
    root = tk.Tk()
    app = DynamicScaleInterface(root, "Alternative A", "Alternative B")
    root.mainloop()

    # Get and print result
    result, reliability = app.get_result()
    print(f"Result: {result:.4f}, Reliability: {reliability:.4f}")


if __name__ == '__main__':
    main()
