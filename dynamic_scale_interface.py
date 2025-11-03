"""
Dynamic Scale Interface for Pairwise Comparisons

This module implements a progressive pairwise comparison interface with multiple scale types,
based on the Delphi implementation from DynamicScaleInterface/*.txt files.

Key Features:
- Progressive scale refinement (starting broad, getting more precise)
- Multiple scale transformation types (Integer, Balanced, Power, Ma-Zheng, Dodd)
- Visual feedback and tooltips
- Mouse wheel support for changing gradation levels
"""

import tkinter as tk
from tkinter import ttk
import math
from typing import Optional, Tuple
from enum import IntEnum


class ScaleType(IntEnum):
    """Available scale transformation types"""
    NONE = 0
    INTEGER = 1
    BALANCED = 2
    POWER = 3
    MA_ZHENG = 4
    DODD = 5


class Reverse(IntEnum):
    """Direction of comparison"""
    NOT_SET = -1
    LESS = 0
    MORE = 1


class DynamicScaleInterface:
    """
    Main class implementing the dynamic scale interface for pairwise comparisons.

    The interface uses a progressive approach where users first choose Less/More,
    then progressively refine their choice through multiple levels of granularity.
    """

    # Preference labels for scale values 1-9
    PREF = [
        "Confirm",  # placeholder for index 0
        "Equally",
        "Weakly or slightly",
        "Moderately",
        "Moderately plus",
        "Strongly",
        "Strongly plus",
        "Very strongly",
        "Very, very strongly",
        "Extremely"
    ]

    # Less/More/NotSure labels
    LESS_MORE = ["Less", "More", "Not sure"]

    # Progressive scale gradations (key = length, value = scale string)
    GRADUAL_SCALE = {
        2: "25",
        3: "259",
        4: "3579",
        5: "23579",
        6: "234579",
        7: "2345679",
        8: "23456789"
    }

    def __init__(self, root: tk.Tk, object_a: str = "Object A", object_b: str = "Object B"):
        """
        Initialize the dynamic scale interface.

        Args:
            root: Tkinter root window
            object_a: Label for first comparison object
            object_b: Label for second comparison object
        """
        self.root = root
        self.object_a = object_a
        self.object_b = object_b

        # State variables
        self.reverse: int = Reverse.NOT_SET
        self.result: float = 1.0  # Result estimate
        self.reliability: float = 0.0  # Reliability/confidence level
        self.scale_type: int = ScaleType.INTEGER
        self.scale_str: str = "0"
        self.delay_wheel: int = 0

        # GUI elements
        self.panels: list = []
        self.scale_choice_visible: bool = False

        self._setup_ui()

    def _setup_ui(self):
        """Setup the user interface"""
        self.root.title("Dynamic Scale Interface - Pairwise Comparison")
        self.root.geometry("800x300")

        # Configure window
        self.root.configure(bg='#F0F0F0')

        # Top frame for labels
        top_frame = tk.Frame(self.root, bg='#F0F0F0')
        top_frame.pack(fill=tk.BOTH, expand=False, pady=10)

        # Object A label
        self.label_a = tk.Label(
            top_frame,
            text=self.object_a,
            fg='red',
            font=('Arial', 11),
            bg='#F0F0F0',
            wraplength=150,
            justify=tk.LEFT,
            width=20
        )
        self.label_a.pack(side=tk.LEFT, padx=(10, 5))

        # "is" label
        self.label_is = tk.Label(
            top_frame,
            text="is",
            fg='red',
            font=('Arial', 14, 'bold'),
            bg='#F0F0F0'
        )
        self.label_is.pack(side=tk.LEFT, padx=5)

        # Spacer
        spacer = tk.Frame(top_frame, bg='#F0F0F0')
        spacer.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # "than" label
        self.label_than = tk.Label(
            top_frame,
            text="than",
            fg='red',
            font=('Arial', 14, 'bold'),
            bg='#F0F0F0'
        )
        self.label_than.pack(side=tk.LEFT, padx=5)

        # Object B label
        self.label_b = tk.Label(
            top_frame,
            text=self.object_b,
            fg='red',
            font=('Arial', 11),
            bg='#F0F0F0',
            wraplength=150,
            justify=tk.LEFT,
            width=20
        )
        self.label_b.pack(side=tk.LEFT, padx=(5, 10))

        # Main content frame
        content_frame = tk.Frame(self.root, bg='#F0F0F0')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10)

        # Left side - Scale type selection
        left_frame = tk.Frame(content_frame, bg='#F0F0F0', width=160)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_frame.pack_propagate(False)

        # Scale type choice panel
        self.panel_scale_button = tk.Button(
            left_frame,
            text="Scale Type Choice",
            relief=tk.SUNKEN,
            cursor='hand2',
            command=self._toggle_scale_choice
        )
        self.panel_scale_button.pack(fill=tk.X)

        # Gradation change buttons
        grad_frame = tk.Frame(left_frame, bg='#F0F0F0')
        grad_frame.pack(fill=tk.X)

        btn_frame = tk.Frame(grad_frame, bg='#F0F0F0')
        btn_frame.pack(side=tk.RIGHT)

        self.btn_grad_up = tk.Button(
            btn_frame,
            text="▲",
            width=2,
            command=self._increase_gradations
        )
        self.btn_grad_up.pack(side=tk.TOP)

        self.btn_grad_down = tk.Button(
            btn_frame,
            text="▼",
            width=2,
            command=self._decrease_gradations
        )
        self.btn_grad_down.pack(side=tk.TOP)

        # Scale choice frame (initially hidden)
        self.scale_choice_frame = tk.Frame(left_frame, bg='#F0F0F0')

        self.scale_var = tk.IntVar(value=ScaleType.INTEGER)

        self.rb_integer = tk.Radiobutton(
            self.scale_choice_frame,
            text="Integer",
            variable=self.scale_var,
            value=ScaleType.INTEGER,
            cursor='hand2',
            command=self._on_scale_type_change
        )
        self.rb_integer.pack(anchor=tk.W, pady=2)

        self.rb_power = tk.Radiobutton(
            self.scale_choice_frame,
            text="Power",
            variable=self.scale_var,
            value=ScaleType.POWER,
            cursor='hand2',
            command=self._on_scale_type_change
        )
        self.rb_power.pack(anchor=tk.W, pady=2)

        self.rb_balanced = tk.Radiobutton(
            self.scale_choice_frame,
            text="Balanced",
            variable=self.scale_var,
            value=ScaleType.BALANCED,
            cursor='hand2',
            command=self._on_scale_type_change
        )
        self.rb_balanced.pack(anchor=tk.W, pady=2)

        self.rb_mazheng = tk.Radiobutton(
            self.scale_choice_frame,
            text="Ma-Zheng (9/9-9/1)",
            variable=self.scale_var,
            value=ScaleType.MA_ZHENG,
            cursor='hand2',
            command=self._on_scale_type_change
        )
        self.rb_mazheng.pack(anchor=tk.W, pady=2)

        self.rb_dodd = tk.Radiobutton(
            self.scale_choice_frame,
            text="Donegan-Dodd-McMasters",
            variable=self.scale_var,
            value=ScaleType.DODD,
            cursor='hand2',
            command=self._on_scale_type_change
        )
        self.rb_dodd.pack(anchor=tk.W, pady=2)

        # Center - Scale panel
        center_frame = tk.Frame(content_frame, bg='#F0F0F0')
        center_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.scale_panel = tk.Frame(center_frame, bg='white', height=30)
        self.scale_panel.pack(fill=tk.X, pady=(5, 0))

        # Image/visualization area
        self.canvas = tk.Canvas(center_frame, bg='white', height=150)
        self.canvas.pack(fill=tk.BOTH, expand=True, pady=(5, 0))

        # Right side - No idea button
        right_frame = tk.Frame(content_frame, bg='#F0F0F0', width=150)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y)
        right_frame.pack_propagate(False)

        self.panel_no_idea = tk.Button(
            right_frame,
            text="No idea",
            height=2,
            cursor='hand2',
            command=self._on_no_idea_click
        )
        self.panel_no_idea.pack(side=tk.BOTTOM, fill=tk.X, pady=(0, 10))

        # Build initial scale
        self._build_scale()

        # Bind keyboard events
        self.root.bind('<Return>', lambda e: self._on_no_idea_click())
        self.root.bind('<MouseWheel>', self._on_mouse_wheel)

    def _toggle_scale_choice(self):
        """Toggle visibility of scale type choice panel"""
        if self.scale_choice_visible:
            self.scale_choice_frame.pack_forget()
            self.panel_scale_button.config(relief=tk.SUNKEN)
            self.scale_choice_visible = False
        else:
            self.scale_choice_frame.pack(fill=tk.BOTH, expand=True, pady=5)
            self.panel_scale_button.config(relief=tk.RAISED)
            self.scale_choice_visible = True

    def _on_scale_type_change(self):
        """Handle scale type radio button changes"""
        self.scale_type = self.scale_var.get()
        self._build_scale()
        self._update_canvas()

    def _increase_gradations(self):
        """Increase the number of scale gradations"""
        if self.reverse != Reverse.NOT_SET and len(self.scale_str) < 8:
            self.scale_str = self.GRADUAL_SCALE[len(self.scale_str) + 1]
            self.reliability = 1
            self.result = 5.5
            self._build_scale()
            self._update_canvas()

    def _decrease_gradations(self):
        """Decrease the number of scale gradations"""
        if self.reverse != Reverse.NOT_SET and len(self.scale_str) > 2:
            self.scale_str = self.GRADUAL_SCALE[len(self.scale_str) - 1]
            self.reliability = 1
            self.result = 5.5
            self._build_scale()
            self._update_canvas()

    def _on_mouse_wheel(self, event):
        """Handle mouse wheel events"""
        if event.delta > 0:
            self._increase_gradations()
        else:
            self._decrease_gradations()

    def _integer_by_scale(self, data: float) -> float:
        """
        Transform integer scale value according to selected scale type.

        Args:
            data: Input value (typically 1-9)

        Returns:
            Transformed value according to current scale type
        """
        result = data

        if self.scale_type == ScaleType.BALANCED:
            # Balanced scale: (0.5+(data-1)*0.05)/(0.5-(data-1)*0.05)
            result = (0.5 + (data - 1) * 0.05) / (0.5 - (data - 1) * 0.05)
        elif self.scale_type == ScaleType.POWER:
            # Power scale: 9^((data-1)/8)
            result = math.pow(9, (data - 1) / 8)
        elif self.scale_type == ScaleType.MA_ZHENG:
            # Ma-Zheng scale: 9/(9+1-data)
            result = 9 / (9 + 1 - data)
        elif self.scale_type == ScaleType.DODD:
            # Donegan-Dodd-McMasters scale: exp(arctanh((data-1)/14*sqrt(3)))
            result = math.exp(math.atanh((data - 1) / 14 * math.sqrt(3)))

        return result

    def _build_scale(self):
        """Build or rebuild the scale panel with appropriate buttons"""
        # Clear existing panels
        for widget in self.scale_panel.winfo_children():
            widget.destroy()
        self.panels = []

        if self.scale_str == "0":
            # Initial state: Less/More choice
            panel_less = tk.Button(
                self.scale_panel,
                text=self.LESS_MORE[0],
                bg='red',
                fg='white',
                cursor='hand2',
                relief=tk.RAISED
            )
            panel_less.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=1)
            panel_less.config(command=lambda: self._on_scale_click(self.LESS_MORE[0], panel_less))
            self.panels.append((panel_less, self.LESS_MORE[0]))

            panel_more = tk.Button(
                self.scale_panel,
                text=self.LESS_MORE[1],
                bg='red',
                fg='white',
                cursor='hand2',
                relief=tk.RAISED
            )
            panel_more.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=1)
            panel_more.config(command=lambda: self._on_scale_click(self.LESS_MORE[1], panel_more))
            self.panels.append((panel_more, self.LESS_MORE[1]))
        else:
            # Progressive scale with gradations
            li = len(self.scale_str)

            # Calculate widths based on scale type
            if self.scale_type == ScaleType.INTEGER:
                # Equal widths for integer scale
                for i, char in enumerate(self.scale_str):
                    grade = int(char)
                    label = self.PREF[grade]

                    panel = tk.Button(
                        self.scale_panel,
                        text="",
                        bg='red',
                        cursor='hand2',
                        relief=tk.RAISED
                    )
                    panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=1)
                    panel.config(command=lambda l=label, p=panel: self._on_scale_click(l, p))
                    self.panels.append((panel, label))
            else:
                # Weighted widths for non-integer scales
                for i, char in enumerate(self.scale_str):
                    grade = int(char)
                    label = self.PREF[grade]

                    panel = tk.Button(
                        self.scale_panel,
                        text="",
                        bg='red',
                        cursor='hand2',
                        relief=tk.RAISED
                    )
                    # Width proportional to scale value
                    weight = self._integer_by_scale(grade)
                    panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=1)
                    panel.config(command=lambda l=label, p=panel: self._on_scale_click(l, p))
                    self.panels.append((panel, label))

            # Add end panel (Less or More depending on reverse)
            if self.reverse != Reverse.NOT_SET:
                end_label = self.LESS_MORE[1 - self.reverse]
                end_panel = tk.Button(
                    self.scale_panel,
                    text=end_label,
                    bg='#F0F0F0',
                    cursor='hand2',
                    relief=tk.RAISED
                )
                if self.reverse == Reverse.LESS:
                    end_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=1)
                else:
                    end_panel.pack(side=tk.LEFT, fill=tk.Y, padx=1)
                end_panel.config(command=lambda l=end_label, p=end_panel: self._on_scale_click(l, p))

    def _on_scale_click(self, label: str, panel: tk.Button):
        """
        Handle click on scale button.

        Args:
            label: Label of clicked button
            panel: Button widget that was clicked
        """
        # Check if Less/More was clicked
        if label in [self.LESS_MORE[0], self.LESS_MORE[1]]:
            self.panel_no_idea.config(text=self.PREF[1])  # "Equally"

            if label == self.LESS_MORE[0]:
                self.reverse = Reverse.LESS
            else:
                self.reverse = Reverse.MORE

            # Update label_is to show direction
            self.label_is.config(text=f"is {label}")

        # Progress through scale levels
        if self.scale_str == "0":
            self.reliability = 1
            self.result = 5.5
            self.scale_str = "259"  # First level: 3 gradations
        elif self.scale_str == "259":
            # Find which grade was clicked
            grad = 0
            for i, char in enumerate(self.scale_str):
                grade = int(char)
                if label == self.PREF[grade]:
                    grad = i + 1
                    break

            if grad == 1:
                self.scale_str = "23459"
                self.result = 1.5 + (1 - 0.5) * (9.5 - 1.5) / 3
            elif grad == 2:
                self.scale_str = "25679"
                self.result = 1.5 + (2 - 0.5) * (9.5 - 1.5) / 3
            elif grad == 3:
                self.scale_str = "2589"
                self.result = 1.5 + (3 - 0.5) * (9.5 - 1.5) / 3

            self.reliability = 3
        else:
            # Final selection
            grad = 0
            for i, char in enumerate(self.scale_str):
                grade = int(char)
                if label == self.PREF[grade]:
                    grad = i + 1
                    break

            if grad > 0:
                self.reliability = len(self.scale_str)
                self.result = 1.5 + (grad - 0.5) * (9.5 - 1.5) / self.reliability
                self._finalize_comparison()
                return

        # Rebuild scale for next level
        self._build_scale()
        self._update_canvas()

    def _update_canvas(self):
        """Update the visualization canvas"""
        self.canvas.delete('all')

        # Draw scale visualization
        if self.reverse != Reverse.NOT_SET and len(self.panels) > 0:
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()

            if canvas_width > 1:  # Canvas is initialized
                # Draw scale labels
                num_gradations = len(self.scale_str)
                x_step = canvas_width / (num_gradations + 1)

                for i, char in enumerate(self.scale_str):
                    grade = int(char)
                    label = self.PREF[grade]
                    x = x_step * (i + 1)

                    # Draw tick mark
                    self.canvas.create_line(x, 20, x, 30, width=2)

                    # Draw label (rotated)
                    self.canvas.create_text(
                        x, 40,
                        text=label,
                        angle=90,
                        anchor='w',
                        font=('Arial', 8)
                    )

                # Draw scale line
                self.canvas.create_line(
                    x_step, 25,
                    canvas_width - x_step, 25,
                    width=2
                )

    def _on_no_idea_click(self):
        """Handle 'No idea' button click"""
        self._finalize_comparison()

    def _finalize_comparison(self):
        """Finalize the comparison and close the window"""
        # Apply scale transformation
        if self.reverse != Reverse.NOT_SET:
            self.result = self._integer_by_scale(self.result)

            # Apply reverse if less was selected
            if self.reverse == Reverse.LESS:
                self.result = 1 / self.result
        else:
            self.reliability = 0
            self.result = 1.0  # Equal/no preference

        # Set scale type
        if self.reverse == Reverse.NOT_SET:
            self.scale_type = ScaleType.NONE
        else:
            self.scale_type = self.scale_var.get()

        # Close window
        self.root.quit()

    def get_result(self) -> Tuple[float, float, int]:
        """
        Get the comparison result.

        Returns:
            Tuple of (result, reliability, scale_type)
            - result: Comparison ratio (>1 means A preferred over B)
            - reliability: Confidence level (0=not sure, higher=more confident)
            - scale_type: Type of scale used
        """
        return (self.result, self.reliability, self.scale_type)


def main():
    """Example usage of the Dynamic Scale Interface"""
    root = tk.Tk()

    interface = DynamicScaleInterface(
        root,
        object_a="Alternative A",
        object_b="Alternative B"
    )

    root.mainloop()

    # Get results
    result, reliability, scale_type = interface.get_result()

    print(f"\nComparison Result:")
    print(f"  Ratio: {result:.4f}")
    print(f"  Reliability: {reliability}")
    print(f"  Scale Type: {ScaleType(scale_type).name}")

    if result > 1:
        print(f"  Conclusion: A is preferred over B by a factor of {result:.4f}")
    elif result < 1:
        print(f"  Conclusion: B is preferred over A by a factor of {1/result:.4f}")
    else:
        print(f"  Conclusion: A and B are equally preferred")


if __name__ == "__main__":
    main()
