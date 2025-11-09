"""
Example: Using the Modern Dynamic Scale Interface

This demonstrates the modern, professionally-designed pairwise comparison interface.
All functionality is identical to the original Delphi implementation.

The interface provides:
- Progressive scale refinement (Less/More → coarse → medium → fine)
- Multiple scale transformations (Integer, Balanced, Power, Ma-Zheng, Dodd)
- Visual feedback with balance scale hints
- Mouse wheel gradation adjustment
- Modern, clean UI design
"""

import tkinter as tk
from dynamic_scale_interface_modern import DynamicScaleInterface


def compare_alternatives():
    """
    Example 1: Compare two alternatives using the modern interface.
    """
    root = tk.Tk()

    interface = DynamicScaleInterface(
        root,
        object_a="High-Quality Option: Expensive but durable",
        object_b="Budget Option: Affordable but limited warranty"
    )

    root.mainloop()

    # Get results
    result, reliability, scale_type = interface.get_result()

    scale_names = ['None', 'Integer', 'Balanced', 'Power', 'Ma-Zheng', 'Dodd']

    print("\n" + "="*70)
    print(" COMPARISON RESULTS")
    print("="*70)
    print(f"  Result Ratio:     {result:.4f}")
    print(f"  Reliability:      {reliability} (0=unsure, 8=very confident)")
    print(f"  Scale Type:       {scale_names[scale_type]}")
    print("="*70)

    if reliability == 0:
        print("  Status: User indicated uncertainty")
    elif result > 1:
        print(f"  Conclusion: Alternative A preferred {result:.2f}x more than B")
    elif result < 1:
        print(f"  Conclusion: Alternative B preferred {1/result:.2f}x more than A")
    else:
        print(f"  Conclusion: Alternatives are equally preferred")

    print("="*70 + "\n")

    return result, reliability, scale_type


def compare_criteria():
    """
    Example 2: Compare importance of decision criteria.
    """
    root = tk.Tk()

    interface = DynamicScaleInterface(
        root,
        object_a="Cost - Total price including maintenance",
        object_b="Quality - Durability and performance metrics"
    )

    root.mainloop()

    result, reliability, scale_type = interface.get_result()

    print("\n" + "="*70)
    print(" CRITERIA IMPORTANCE COMPARISON")
    print("="*70)

    if reliability > 0:
        if result > 1:
            print(f"  Cost is {result:.2f}x more important than Quality")
        elif result < 1:
            print(f"  Quality is {1/result:.2f}x more important than Cost")
        else:
            print(f"  Cost and Quality are equally important")
    else:
        print(f"  User was unsure about relative importance")

    print("="*70 + "\n")

    return result, reliability, scale_type


def batch_comparisons():
    """
    Example 3: Perform multiple comparisons in sequence.
    """
    alternatives = [
        ("Option A", "Option B"),
        ("Option A", "Option C"),
        ("Option B", "Option C")
    ]

    results = []

    print("\n" + "="*70)
    print(" BATCH PAIRWISE COMPARISONS")
    print("="*70)

    for i, (obj_a, obj_b) in enumerate(alternatives, 1):
        print(f"\n  Comparison {i}: {obj_a} vs {obj_b}")
        print("  " + "-"*66)

        root = tk.Tk()
        interface = DynamicScaleInterface(root, obj_a, obj_b)
        root.mainloop()

        result, reliability, scale_type = interface.get_result()
        results.append((obj_a, obj_b, result, reliability, scale_type))

        if reliability > 0:
            if result > 1:
                print(f"  → {obj_a} preferred (ratio: {result:.2f})")
            elif result < 1:
                print(f"  → {obj_b} preferred (ratio: {1/result:.2f})")
            else:
                print(f"  → Equal preference")
        else:
            print(f"  → Unsure")

    print("\n" + "="*70)
    print(" SUMMARY OF ALL COMPARISONS")
    print("="*70)

    for obj_a, obj_b, result, reliability, scale_type in results:
        status = "Confident" if reliability >= 5 else "Moderate" if reliability >= 3 else "Low confidence"
        print(f"  {obj_a} vs {obj_b}: {result:.3f} ({status})")

    print("="*70 + "\n")

    return results


def demonstrate_scale_types():
    """
    Example 4: Demonstrate different scale transformation types.
    """
    print("\n" + "="*70)
    print(" SCALE TRANSFORMATION DEMONSTRATION")
    print("="*70)
    print("\n  The interface supports 5 scale transformation types:")
    print("\n  1. Integer Scale - Linear (1, 2, 3, ..., 9)")
    print("  2. Balanced Scale - Ratio-balanced transformation")
    print("  3. Power Scale - Exponential (9^((grade-1)/8))")
    print("  4. Ma-Zheng Scale - Reciprocal (9/(10-grade))")
    print("  5. Dodd-McMasters - Hyperbolic tangent-based")
    print("\n  Each scale type affects how preference intensities are interpreted.")
    print("  Select the scale type that best fits your decision context.")
    print("\n" + "="*70)

    root = tk.Tk()
    interface = DynamicScaleInterface(
        root,
        object_a="Project Alpha: High risk, high reward",
        object_b="Project Beta: Low risk, moderate reward"
    )
    root.mainloop()

    result, reliability, scale_type = interface.get_result()
    scale_names = ['None', 'Integer', 'Balanced', 'Power', 'Ma-Zheng', 'Dodd']

    print(f"\n  You used: {scale_names[scale_type]} scale")
    print(f"  Result: {result:.4f}")
    print("="*70 + "\n")

    return result, reliability, scale_type


if __name__ == "__main__":
    print("\n" + "="*70)
    print(" MODERN DYNAMIC SCALE INTERFACE - EXAMPLES")
    print("="*70)
    print("\n  This script demonstrates various use cases for the modern")
    print("  pairwise comparison interface.")
    print("\n  Features:")
    print("    ✓ Clean, professional design")
    print("    ✓ Progressive refinement workflow")
    print("    ✓ Multiple scale transformations")
    print("    ✓ Visual balance hints")
    print("    ✓ Mouse wheel support")
    print("    ✓ Identical logic to original Delphi version")
    print("\n" + "="*70)

    print("\n  Select an example to run:")
    print("\n    1. Simple alternative comparison")
    print("    2. Criteria importance comparison")
    print("    3. Batch comparisons (multiple pairs)")
    print("    4. Scale type demonstration")
    print("    5. Exit")

    while True:
        try:
            choice = input("\n  Enter choice (1-5): ").strip()

            if choice == '1':
                compare_alternatives()
            elif choice == '2':
                compare_criteria()
            elif choice == '3':
                batch_comparisons()
            elif choice == '4':
                demonstrate_scale_types()
            elif choice == '5':
                print("\n  Goodbye!\n")
                break
            else:
                print("\n  Invalid choice. Please enter 1-5.")
        except KeyboardInterrupt:
            print("\n\n  Interrupted. Goodbye!\n")
            break
        except Exception as e:
            print(f"\n  Error: {e}")
            print("  Please try again.\n")
