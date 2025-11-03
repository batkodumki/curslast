# Dynamic Scale Interface

A Python implementation of a progressive pairwise comparison interface with multiple scale transformations.

## Overview

This implementation is based on the Delphi source code found in the `DynamicScaleInterface/*.txt` files. It provides an intuitive GUI for conducting pairwise comparisons using a progressive refinement approach.

### Key Features

1. **Progressive Gradation**: Users start with a broad Less/More choice and progressively refine their judgment through multiple levels
2. **Multiple Scale Types**: Five different scale transformations are supported:
   - Integer (linear 1-9)
   - Balanced (non-linear balanced scale)
   - Power (exponential scale)
   - Ma-Zheng (9/9-9/1 scale)
   - Donegan-Dodd-McMasters (hyperbolic tangent scale)
3. **Visual Feedback**: Real-time visual representation of scale gradations
4. **Mouse Wheel Support**: Quick adjustment of gradation levels
5. **Keyboard Shortcuts**: Enter key to confirm "No idea"

## Files

- **`_DynScaInt.txt`**: Program entry point (Delphi project file)
- **`UForm_Pas.txt`**: Main form implementation with scale logic
- **`UForm_dfm.txt`**: Form layout and UI components
- **`UFrame_pas.txt`**: Frame for embedded images/resources
- **`UFrame_dfm.txt`**: Frame layout with embedded metafiles
- **`UGraphicHint_pas.txt`**: Custom hint window with graphical visualization

## Python Implementation

The Python implementation (`../dynamic_scale_interface.py`) replicates the core functionality:

### Main Class: `DynamicScaleInterface`

```python
from dynamic_scale_interface import DynamicScaleInterface
import tkinter as tk

root = tk.Tk()
interface = DynamicScaleInterface(
    root,
    object_a="Alternative A",
    object_b="Alternative B"
)

root.mainloop()

# Get results
result, reliability, scale_type = interface.get_result()
```

### Return Values

- **result** (float): Comparison ratio
  - `> 1`: Object A is preferred over Object B
  - `< 1`: Object B is preferred over Object A
  - `= 1`: Objects are equally preferred or user unsure

- **reliability** (float): Confidence level
  - `0`: User clicked "No idea" (no preference)
  - `1`: Only Less/More selected (low confidence)
  - `3`: Coarse gradation level (medium confidence)
  - `5-8`: Fine gradation level (high confidence)

- **scale_type** (int): Scale transformation used
  - `0`: None (no selection made)
  - `1`: Integer scale
  - `2`: Balanced scale
  - `3`: Power scale
  - `4`: Ma-Zheng scale
  - `5`: Donegan-Dodd-McMasters scale

## Scale Transformations

### 1. Integer Scale
Linear scale: `value = grade` (1-9)

**Use case**: Simple, intuitive comparisons

### 2. Balanced Scale
Formula: `value = (0.5 + (grade-1)*0.05) / (0.5 - (grade-1)*0.05)`

**Use case**: Balanced emphasis on both extremes

### 3. Power Scale
Formula: `value = 9^((grade-1)/8)`

**Use case**: Exponential growth in preference strength

### 4. Ma-Zheng Scale
Formula: `value = 9 / (9 + 1 - grade)`

**Use case**: Specific mathematical properties for AHP

### 5. Donegan-Dodd-McMasters Scale
Formula: `value = exp(arctanh((grade-1)/14*sqrt(3)))`

**Use case**: Psychological preference modeling

## Progressive Gradation Levels

The interface uses a progressive refinement approach:

### Level 0: Initial Choice
- **Less** or **More** preferred

### Level 1: Coarse Gradation (3 levels)
- Grades: 2, 5, 9
- Labels: "Weakly", "Strongly", "Extremely"

### Level 2: Medium Gradation (5 levels)
Depending on Level 1 choice:
- If grade 2: "23459" (2,3,4,5,9)
- If grade 5: "25679" (2,5,6,7,9)
- If grade 9: "2589" (2,5,8,9)

### Level 3+: Fine Gradation (up to 8 levels)
- Can be adjusted using mouse wheel or buttons
- Available: 2-8 gradation levels
- More gradations = higher confidence/reliability

## Usage Examples

### Example 1: Single Comparison

```python
import tkinter as tk
from dynamic_scale_interface import DynamicScaleInterface

root = tk.Tk()
interface = DynamicScaleInterface(
    root,
    object_a="Project A",
    object_b="Project B"
)

root.mainloop()

result, reliability, scale_type = interface.get_result()
print(f"Comparison result: {result:.4f} (reliability: {reliability})")
```

### Example 2: AHP Matrix Construction

```python
import tkinter as tk
from dynamic_scale_interface import DynamicScaleInterface

n = 3
criteria = ["Cost", "Quality", "Time"]
matrix = [[1.0] * n for _ in range(n)]

for i in range(n):
    for j in range(i + 1, n):
        root = tk.Tk()
        interface = DynamicScaleInterface(
            root,
            object_a=criteria[i],
            object_b=criteria[j]
        )
        root.mainloop()

        result, _, _ = interface.get_result()
        matrix[i][j] = result
        matrix[j][i] = 1 / result if result != 0 else 1.0

# Use matrix for AHP calculation
```

### Example 3: Running Examples

```bash
python example_dynamic_scale.py
```

This runs an interactive menu with multiple examples:
1. Single Comparison
2. Multiple Comparisons
3. Scale Types Comparison
4. AHP Integration

## Preference Labels

The interface uses 9 standard preference levels:

1. **Equally** - No preference
2. **Weakly or slightly** - Slight preference
3. **Moderately** - Moderate preference
4. **Moderately plus** - Moderate to strong
5. **Strongly** - Strong preference
6. **Strongly plus** - Strong to very strong
7. **Very strongly** - Very strong preference
8. **Very, very strongly** - Extremely strong (almost)
9. **Extremely** - Absolute preference

## Integration with AHP (Analytic Hierarchy Process)

The dynamic scale interface is particularly useful for AHP:

1. **Consistent Scale**: Uses standard 1-9 AHP scale
2. **Multiple Transformations**: Choose appropriate scale for context
3. **Reliability Metric**: Track confidence in judgments
4. **Reciprocal Relationships**: Automatically maintained (if A/B = x, then B/A = 1/x)

### AHP Consistency

The pairwise comparison matrix should satisfy:
- Reciprocal: `matrix[i][j] = 1 / matrix[j][i]`
- Transitive (ideally): `matrix[i][j] * matrix[j][k] ≈ matrix[i][k]`

The reliability metric helps identify uncertain comparisons that may affect consistency.

## Technical Notes

### Architecture Mapping (Delphi → Python)

| Delphi Component | Python Equivalent |
|-----------------|-------------------|
| TForm | tkinter.Tk |
| TPanel | tkinter.Button/Frame |
| TRadioButton | tkinter.Radiobutton |
| TLabel | tkinter.Label |
| TImage/TCanvas | tkinter.Canvas |
| TGraphicHint | (simplified, no metafiles) |

### Key Differences

1. **Graphics**: Delphi uses metafiles for hints; Python implementation uses simplified canvas drawing
2. **Font Rotation**: Delphi uses Windows API for rotated text; Python uses canvas text rotation
3. **Events**: Event handling adapted to tkinter's event model

### Dependencies

- **Python 3.6+**
- **tkinter** (included in standard Python distribution)
- **math** (standard library)

No external packages required!

## References

### Original Delphi Implementation

The original implementation includes:
- Progressive scale refinement
- Five scale transformation types
- Graphical hints with balance metaphor
- Mouse wheel support for gradation changes
- Full Windows GUI with all visual effects

### Related Concepts

- **AHP (Analytic Hierarchy Process)**: Decision-making method using pairwise comparisons
- **Saaty Scale**: Standard 1-9 scale for pairwise comparisons
- **Judgment Matrix**: Square matrix of pairwise comparison results
- **Consistency Ratio**: Measure of logical consistency in AHP judgments

## Future Enhancements

Possible improvements for the Python implementation:

1. **Graphical Hints**: Add visual balance scale representation (like Delphi version)
2. **Image Resources**: Load and display scale diagrams
3. **Consistency Check**: Calculate and display consistency ratio for AHP matrices
4. **Export**: Save comparison matrices to CSV/JSON
5. **Batch Mode**: Run multiple comparisons in sequence
6. **Localization**: Support for multiple languages (Delphi version has Ukrainian comments)

## License

Based on the Delphi source code from `DynamicScaleInterface/` directory.
Python implementation follows the same logic and structure.

## Author

Python implementation created from Delphi source analysis.

Original Delphi implementation: See source file headers in `.txt` files.
