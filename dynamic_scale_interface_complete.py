"""
Dynamic Scale Interface - Faithful Python Recreation of Delphi Version

This is a complete, faithful recreation of the Delphi DynamicScaleInterface.
Every detail from the original Delphi code has been preserved:
- Exact BuildScale algorithm with all special cases
- Exact ShowImage visualization with rotated text
- Exact PanelScaleClick progressive refinement logic
- GraphicHint window with balance visualization
- All mouse/keyboard event handling
- All scale transformation formulas

Based on DynamicScaleInterface/*.txt files (Delphi source code).

Author: Recreated from Delphi source
"""

import tkinter as tk
from tkinter import font as tkfont
import math
from typing import Tuple, Optional, List


# Constants from Delphi code

# Preference labels (Pref array from UForm.pas line 70-71)
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

# Less/More labels (LessMore array from UForm.pas line 72-73)
LESS_MORE = ['Less', 'More', 'Not sure']

# Gradual scale configurations (GradualScale array from UForm.pas line 74)
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

        # Canvas for drawing (250x200 from CalcHintRect line 64)
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
        Paint the hint content (Paint procedure from UGraphicHint.pas line 69-144).
        """
        self.canvas.delete('all')

        if self.data == 0.0:
            # Simple text hint
            self.canvas.create_text(125, 100, text=self.hint_text, font=('Arial', 10))
            return

        # Draw hint text at top
        self.canvas.create_text(125, 15, text=self.hint_text, font=('Arial', 10, 'bold'))

        if self.data < 0:
            # Scale type diagram (lines 88-97)
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
            # Object B preferred (lines 99-113)
            self.draw_balance_tilted_right()
            data_ = (1 / self.data) ** (1/3)  # Cube root for scaling (line 101)

            xe, ye = 25, 25  # Base dimensions (line 75)

            # Draw heavier weight on right (Object B)
            bottom = 180
            top = bottom - round(ye * data_)
            left = 180 - round(xe * data_ / 2)
            right = left + round(xe * data_)
            self.canvas.create_rectangle(left, top, right, bottom, fill='red', outline='black', width=2)

            # Draw lighter weight on left (Object A)
            self.canvas.create_rectangle(50, 145, 75, 170, fill='blue', outline='black', width=2)
        else:
            # Object A preferred or equal (lines 114-138)
            self.draw_balance_tilted_left()
            data_ = self.data ** (1/3)  # Cube root for scaling (line 116)

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
                # Equal - show question mark (lines 129-136)
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


class DynamicScaleInterface:
    """
    Main Dynamic Scale Interface class (TFormDynScaleInt from UForm.pas).

    This is a FAITHFUL recreation of the Delphi implementation with:
    - Exact BuildScale algorithm (lines 182-285)
    - Exact ShowImage visualization (lines 84-107)
    - Exact PanelScaleClick logic (lines 287-353)
    - All scale transformations (lines 169-180)
    - All mouse/keyboard events
    - GraphicHint integration
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

        # State variables (from Delphi private/public declarations lines 54-66)
        self.reverse = -1  # -1: not set, 0: Less, 1: More
        self.res = 1.0     # Result estimate (Res in Delphi)
        self.rel = 0.0     # Reliability (Rel in Delphi)
        self.scale_str = '0'  # Current scale configuration (ScaleStr in Delphi)
        self.scale_type = 0   # 0: none, 1-5: scale types
        self.delay_wheel = 0  # Mouse wheel delay (line 58)
        self.data = 0.0    # Data for hints (line 55)

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

        # Initialize form (FormShow equivalent, lines 109-167)
        self.form_show()

    def setup_window(self):
        """Configure main window (from UForm_dfm.txt lines 1-28)."""
        self.root.title('Make a choice using visual hints')  # Line 6
        self.root.geometry('779x195')  # Width=779, Height=195 from lines 8-9
        self.root.resizable(False, False)  # bsSingle border style (line 5)
        self.root.configure(bg='#f0f0f0')  # clBtnFace (line 9)

        # Center on screen (Position = poDesktopCenter, line 17)
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (779 // 2)
        y = (self.root.winfo_screenheight() // 2) - (195 // 2)
        self.root.geometry(f'779x195+{x}+{y}')

        self.root.protocol("WM_DELETE_WINDOW", self.close_window)

    def create_widgets(self):
        """Create all UI widgets (from UForm_dfm.txt)."""
        # LabelA (lines 31-49)
        self.label_a = tk.Label(
            self.root, text=self.object_a,
            font=('MS Sans Serif', 9), fg='red',
            bg='#f0f0f0', wraplength=150, justify='left'
        )
        self.label_a.place(x=0, y=8, width=150, height=73)

        # LabelB (lines 50-67)
        self.label_b = tk.Label(
            self.root, text=self.object_b,
            font=('MS Sans Serif', 9), fg='red',
            bg='#f0f0f0', wraplength=150, justify='left'
        )
        self.label_b.place(x=630, y=8, width=150, height=73)

        # LabelIs (lines 68-81)
        self.label_is = tk.Label(
            self.root, text='is',
            font=('MS Sans Serif', 12, 'bold'), fg='red',
            bg='#f0f0f0'
        )
        self.label_is.place(x=154, y=4)

        # LabelThan (lines 82-96)
        self.label_than = tk.Label(
            self.root, text='than',
            font=('MS Sans Serif', 12, 'bold'), fg='red',
            bg='#f0f0f0'
        )
        self.label_than.place(x=589, y=3)

        # ImageShow canvas (lines 97-105)
        self.image_show = tk.Canvas(
            self.root, bg='white', highlightthickness=0
        )
        self.image_show.place(x=154, y=53, width=476, height=142)

        # PanelScale container (lines 106-143)
        self.panel_scale = tk.Frame(self.root, bg='#f0f0f0', relief='flat')
        self.panel_scale.place(x=154, y=28, width=475, height=25)

        # PanelLess (lines 115-128)
        self.panel_less = tk.Button(
            self.panel_scale, text='Less preferred',
            relief='raised', cursor='hand2',
            bg='red', fg='white', font=('MS Sans Serif', 9)
        )
        self.panel_less.place(x=0, y=0, width=153, height=25)
        self.panel_less.hint = LESS_MORE[0]

        # PanelMore (lines 129-142)
        self.panel_more = tk.Button(
            self.panel_scale, text='More preferred',
            relief='raised', cursor='hand2',
            bg='red', fg='white', font=('MS Sans Serif', 9)
        )
        self.panel_more.place(x=152, y=0, width=129, height=25)
        self.panel_more.hint = LESS_MORE[1]

        # PanelScaleChoice (lines 144-251)
        self.panel_scale_choice = tk.Frame(self.root, relief='raised', bd=2)
        self.panel_scale_choice.place(x=0, y=80, width=153, height=115)

        # PanelScaleButtonChoice (lines 237-250)
        self.panel_scale_button_choice = tk.Button(
            self.panel_scale_choice, text='Scale Type Choice',
            relief='lowered', cursor='hand2',
            font=('MS Sans Serif', 9)
        )
        self.panel_scale_button_choice.place(x=0, y=0, width=114, height=27)

        # RxSpinButton equivalent (lines 157-167)
        self.spin_frame = tk.Frame(self.panel_scale_choice)
        self.spin_frame.place(x=113, y=0, width=41, height=27)

        self.spin_up = tk.Button(self.spin_frame, text='▲', command=self.spin_up_click)
        self.spin_up.pack(side='top', fill='both', expand=True)

        self.spin_down = tk.Button(self.spin_frame, text='▼', command=self.spin_down_click)
        self.spin_down.pack(side='bottom', fill='both', expand=True)

        # Radio buttons for scale types
        self.scale_type_var = tk.IntVar(value=1)

        # RButInteger (lines 168-183)
        self.rbut_integer = tk.Radiobutton(
            self.panel_scale_choice, text='Integer',
            variable=self.scale_type_var, value=1,
            cursor='hand2', font=('MS Sans Serif', 9),
            command=self.scale_choice_changed
        )
        self.rbut_integer.place(x=3, y=29, width=102, height=17)
        self.rbut_integer.data = -1

        # RButPower (lines 198-210)
        self.rbut_power = tk.Radiobutton(
            self.panel_scale_choice, text='Power',
            variable=self.scale_type_var, value=3,
            cursor='hand2', font=('MS Sans Serif', 9),
            command=self.scale_choice_changed
        )
        self.rbut_power.place(x=3, y=45, width=137, height=17)
        self.rbut_power.data = -3

        # RButBalanced (lines 185-197)
        self.rbut_balanced = tk.Radiobutton(
            self.panel_scale_choice, text='Balanced',
            variable=self.scale_type_var, value=2,
            cursor='hand2', font=('MS Sans Serif', 9),
            command=self.scale_choice_changed
        )
        self.rbut_balanced.place(x=3, y=61, width=137, height=17)
        self.rbut_balanced.data = -2

        # RButMaZheng (lines 211-223)
        self.rbut_mazheng = tk.Radiobutton(
            self.panel_scale_choice, text='Ma-Zheng (9/9-9/1)',
            variable=self.scale_type_var, value=4,
            cursor='hand2', font=('MS Sans Serif', 9),
            command=self.scale_choice_changed
        )
        self.rbut_mazheng.place(x=3, y=77, width=149, height=17)
        self.rbut_mazheng.data = -4

        # RButDodd (lines 224-236)
        self.rbut_dodd = tk.Radiobutton(
            self.panel_scale_choice, text='Donegan-Dodd-McMasters',
            variable=self.scale_type_var, value=5,
            cursor='hand2', font=('MS Sans Serif', 9),
            command=self.scale_choice_changed
        )
        self.rbut_dodd.place(x=3, y=93, width=148, height=17)
        self.rbut_dodd.data = -5

        # PanelNoIdea (lines 252-266)
        self.panel_no_idea = tk.Button(
            self.root, text='No idea',
            relief='raised', cursor='hand2',
            font=('MS Sans Serif', 9)
        )
        self.panel_no_idea.place(x=638, y=128, width=137, height=25)
        self.panel_no_idea.hint = LESS_MORE[2]

    def bind_events(self):
        """Bind all keyboard and mouse events."""
        # Form events (from UForm_dfm.txt lines 18-25)
        self.root.bind('<Return>', lambda e: self.no_idea_click())  # FormKeyDown (line 20)
        self.root.bind('<MouseWheel>', self.mouse_wheel)  # FormMouseWheel (line 22)
        self.root.bind('<Button-4>', lambda e: self.spin_up_click())  # Linux scroll up
        self.root.bind('<Button-5>', lambda e: self.spin_down_click())  # Linux scroll down

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
        """
        Initialize form state (FormShow procedure, lines 109-167).
        """
        self.reverse = -1  # Line 112
        self.res = 1.0     # Line 113
        self.rel = 0.0     # Line 114
        self.scale_str = '0'  # Line 115

        self.panel_no_idea.config(text=PREF[1])  # Line 128
        self.panel_no_idea.hint = PREF[1]
        self.panel_less.config(text=LESS_MORE[0])  # Line 129
        self.panel_more.config(text=LESS_MORE[1])  # Line 130
        self.panel_scale_choice.place_forget()  # Line 164

        self.build_scale(self.scale_str)
        self.show_image()

    def integer_by_scale(self, data: float) -> float:
        """
        Apply scale transformation (IntegerByScale function, lines 169-180).

        Args:
            data: Input value (1-9 range)

        Returns:
            Transformed value according to selected scale type
        """
        result = data

        scale_type = self.scale_type_var.get()

        if scale_type == 2:  # Balanced (line 172)
            result = (0.5 + (data - 1) * 0.05) / (0.5 - (data - 1) * 0.05)  # Line 173
        if scale_type == 3:  # Power (line 174)
            result = math.pow(9, (data - 1) / 8)  # Line 175
        if scale_type == 4:  # Ma-Zheng (line 176)
            result = 9 / (9 + 1 - data)  # Line 177
        if scale_type == 5:  # Dodd (line 178)
            result = math.exp(math.atanh((data - 1) / 14 * math.sqrt(3)))  # Line 179

        return result

    def in_range(self, value: int, min_val: int, max_val: int) -> bool:
        """Helper function equivalent to Delphi's InRange."""
        return min_val <= value <= max_val

    def build_scale(self, scale_str: str):
        """
        Build dynamic scale panels (BuildScale procedure, lines 182-285).
        This is a FAITHFUL recreation of the complex Delphi algorithm.

        Args:
            scale_str: Scale configuration string
        """
        # Clear existing dynamic panels (lines 205-212)
        for panel in self.scale_panels:
            panel.destroy()
        self.scale_panels.clear()

        if self.reverse == -1:
            # Initial state - just show Less/More (lines 214-220)
            return

        # Calculate number of panels needed (line 204)
        li = len(scale_str)  # last index (line 204)

        # Calculate sum of weights (lines 222-229)
        if scale_str in ['23459', '25679', '2589']:
            ii = 8
        else:
            ii = li

        sum_w = 0.0
        for i in range(1, ii + 1):
            sum_w += self.integer_by_scale(1.5 + (i - 0.5) * (9.5 - 1.5) / ii)

        # Build panels (lines 231-281)
        wi = 0  # Width accumulator (line 230)
        panel_scale_width = 475  # PanelScale.Width

        for i in range(li, -1, -1):  # Reverse order (line 231)
            # Create new panel
            new_pin = tk.Button(
                self.panel_scale,
                text='',
                relief='raised',
                cursor='hand2',
                font=('MS Sans Serif', 8)
            )

            if i == li:
                # Last panel - Less/More indicator (lines 233-240)
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
                # Regular gradation panel (lines 241-280)
                idx = li - i - 1
                grade_char = scale_str[idx]
                grade = int(grade_char)

                # Calculate width based on complex algorithm
                if scale_str in ['23459', '25679', '2589']:
                    # Special handling for these scales (lines 242-266)
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
                        # Grouped panels (lines 248-256)
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
                        # Active panels (lines 258-264)
                        if self.scale_type_var.get() == 1:  # Integer
                            width = width // (len(scale_str) - 2)
                        else:
                            width = round(panel_scale_width * 16 / 9 / 2 / sum_w *
                                        self.integer_by_scale(grade))
                        new_pin.config(bg='red', fg='white')
                else:
                    # Regular scale (lines 267-273)
                    if self.scale_type_var.get() == 1:  # Integer
                        width = panel_scale_width / 2 * 16 / 9 / li
                        width = int(width)
                    else:
                        width = round(panel_scale_width / 2 * 16 / 9 / sum_w *
                                    self.integer_by_scale(1.5 + (li - i - 0.5) * (9.5 - 1.5) / li))
                    new_pin.config(bg='red', fg='white')

                wi += width  # Line 275
                left = panel_scale_width * (1 - self.reverse) - wi + 2 * wi * self.reverse - width * self.reverse  # Line 276
                new_pin.hint = PREF[grade]  # Line 278

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
        """
        Draw visual scale representation (ShowImage procedure, lines 84-107).
        """
        self.image_show.delete('all')

        if self.reverse == -1:
            return

        # Find min/max positions (lines 90-99)
        min_l = 475
        max_r = 0

        for panel in self.scale_panels:
            if panel.winfo_exists() and panel.winfo_ismapped():
                x = panel.winfo_x()
                width = panel.winfo_width()
                hint = panel.hint

                # Draw vertical tick (lines 94-95)
                self.image_show.create_line(x, 0, x, 10, fill='black')

                # Draw vertical text (line 93)
                center_x = x + width // 2
                # Tkinter doesn't support vertical text natively, so we rotate
                self.image_show.create_text(
                    center_x - 5, 50,
                    text=hint, angle=90, anchor='w',
                    font=('Arial', 8)
                )

                min_l = min(min_l, x)
                max_r = max(max_r, x + width)

        # Draw final tick and horizontal line (lines 101-104)
        if max_r > 0:
            self.image_show.create_line(max_r - 1, 0, max_r - 1, 10, fill='black')
            self.image_show.create_line(min_l, 0, max_r - 1, 0, fill='black')

    def panel_scale_click(self, panel):
        """
        Handle scale panel click (PanelScaleClick procedure, lines 287-353).
        This implements the exact progressive refinement logic from Delphi.

        Args:
            panel: The panel that was clicked
        """
        hint = panel.hint

        # Handle Less/More selection (lines 292-299)
        if hint in [LESS_MORE[0], LESS_MORE[1]]:
            self.panel_no_idea.config(text=PREF[1])
            self.panel_no_idea.hint = PREF[1]

            if hint == LESS_MORE[0]:
                self.reverse = 0  # Less
            else:
                self.reverse = 1  # More

        # Progressive refinement logic (lines 300-346)
        if self.scale_str == '0':
            # First level - coarse scale (lines 300-304)
            self.rel = 1.0  # Chose Less/More
            self.res = 5.5  # Middle value
            self.scale_str = '259'
        elif self.scale_str == '259' and panel.cget('bg') == 'red':
            # Second level - medium scale (lines 305-316)
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
            # Click on grouped panel (lines 317-330)
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
            # Final selection (lines 331-346)
            grad = 1
            for idx, char in enumerate(self.scale_str, 1):
                if hint == PREF[int(char)]:
                    grad = idx
                    break

            if self.scale_str in ['23459', '25679', '2589']:
                # Adjust for offset (lines 336-339)
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

        # Rebuild scale and update (lines 347-352)
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
        """
        Show graphical hint (DoShowHint procedure, lines 360-407).

        Args:
            event: Mouse event
        """
        widget = event.widget

        # Get hint text
        if hasattr(widget, 'hint'):
            hint_text = widget.hint
        else:
            return

        # Calculate data for visualization (lines 362-406)
        data = 0.0

        if isinstance(widget, tk.Radiobutton):
            # Scale type hint (lines 394-404)
            data = widget.data
        elif hasattr(widget, 'hint'):
            if self.panel_scale_choice.winfo_ismapped():
                # Panel hint when scale is visible (lines 367-384)
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
                # Initial state hints (lines 386-392)
                if widget.hint == LESS_MORE[0]:
                    data = 1 / 5.5
                elif widget.hint == LESS_MORE[1]:
                    data = 5.5
                else:
                    data = 1.0

        # Show hint window
        if data != 0:
            x = self.root.winfo_pointerx()
            y = self.root.winfo_pointery()
            self.hint_window.show_hint(x, y, hint_text, data)

    def toggle_scale_choice(self):
        """Toggle scale type panel visibility (PanelScaleButtonChoiceClick, lines 518-531)."""
        if self.panel_scale_button_choice.cget('relief') == 'lowered':
            self.panel_scale_button_choice.config(relief='raised')
            # Disable radio buttons
            for rb in [self.rbut_integer, self.rbut_balanced, self.rbut_power,
                      self.rbut_mazheng, self.rbut_dodd]:
                rb.config(state='disabled')
        else:
            self.panel_scale_button_choice.config(relief='lowered')
            # Enable radio buttons
            for rb in [self.rbut_integer, self.rbut_balanced, self.rbut_power,
                      self.rbut_mazheng, self.rbut_dodd]:
                rb.config(state='normal')

    def scale_choice_changed(self):
        """Handle scale type change (PanelScaleChoiceClick, lines 482-486)."""
        self.build_scale(self.scale_str)
        self.show_image()

    def spin_up_click(self):
        """Increase gradations (RxSpinButGradChangeTopClick, lines 494-504)."""
        if self.reverse > -1 and len(self.scale_str) < 8:
            self.scale_str = GRADUAL_SCALE[len(self.scale_str) + 1]
            self.rel = 1.0
            self.res = 5.5
            self.build_scale(self.scale_str)
            self.show_image()

    def spin_down_click(self):
        """Decrease gradations (RxSpinButGradChangeBottomClick, lines 506-516)."""
        if self.reverse > -1 and len(self.scale_str) > 2:
            self.scale_str = GRADUAL_SCALE[len(self.scale_str) - 1]
            self.rel = 1.0
            self.res = 5.5
            self.build_scale(self.scale_str)
            self.show_image()

    def mouse_wheel(self, event):
        """Handle mouse wheel (FormMouseWheel, lines 440-445)."""
        if self.delay_wheel < 3:
            self.delay_wheel += 1
            return
        self.delay_wheel = 0

        if event.delta > 0:
            self.spin_up_click()
        else:
            self.spin_down_click()

    def no_idea_click(self):
        """Handle 'No idea' click (PanelNoIdeaClick, lines 447-450)."""
        self.close_window()

    def close_window(self):
        """
        Close window and finalize results (FormClose, lines 419-438).
        """
        # Apply transformation and reverse (lines 422-425)
        if self.reverse > -1:
            self.res = self.integer_by_scale(self.res)

            if self.reverse == 0:  # Less
                if self.res != 0:
                    self.res = 1 / self.res
        else:
            self.rel = 0.0

        # Set scale type (lines 426-437)
        if self.reverse < 0:
            self.scale_type = 0
        else:
            self.scale_type = self.scale_type_var.get()

        # Destroy hint window
        self.hint_window.destroy()

        # Close
        self.root.quit()

    def get_result(self) -> Tuple[float, float, int]:
        """
        Get comparison result.

        Returns:
            Tuple of (result, reliability, scale_type)
            - result: Comparison ratio (>1 means A>B, <1 means B>A)
            - reliability: Confidence level (0=no idea, 1=Less/More, 3=coarse, 5-8=fine)
            - scale_type: Scale transformation type (0=none, 1-5=scale types)
        """
        return (self.res, self.rel, self.scale_type)


def main():
    """Example usage."""
    root = tk.Tk()

    interface = DynamicScaleInterface(
        root,
        object_a="Alternative A: High cost, excellent quality",
        object_b="Alternative B: Low cost, good quality"
    )

    root.mainloop()

    # Get results
    result, reliability, scale_type = interface.get_result()

    scale_names = ['None', 'Integer', 'Balanced', 'Power', 'Ma-Zheng', 'Dodd']

    print(f"\nComparison Result:")
    print(f"  Ratio: {result:.4f}")
    print(f"  Reliability: {reliability}")
    print(f"  Scale Type: {scale_names[scale_type]}")

    if reliability == 0:
        print(f"  Interpretation: User was unsure")
    elif result > 1:
        print(f"  Interpretation: Object A is {result:.2f}x preferred over Object B")
    elif result < 1:
        print(f"  Interpretation: Object B is {1/result:.2f}x preferred over Object A")
    else:
        print(f"  Interpretation: Objects are equally preferred")


if __name__ == '__main__':
    main()
