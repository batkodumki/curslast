"""
Example usage of the Complete Dynamic Scale Interface

This demonstrates the faithful Python recreation of the Delphi DynamicScaleInterface.
"""

import tkinter as tk
from dynamic_scale_interface_complete import DynamicScaleInterface, PREF


def example_single_comparison():
    """Example 1: Single pairwise comparison"""
    print("\n" + "="*60)
    print("Example 1: Single Pairwise Comparison")
    print("="*60)

    root = tk.Tk()

    interface = DynamicScaleInterface(
        root,
        object_a="Alternative A: High cost, excellent quality",
        object_b="Alternative B: Low cost, good quality"
    )

    print("\nPlease use the interface to compare the two alternatives.")
    print("Follow the progressive refinement:")
    print("  1. Choose Less or More preferred")
    print("  2. Select coarse gradation (Weakly/Strongly/Extremely)")
    print("  3. Optionally adjust gradations with mouse wheel or buttons")
    print("  4. Make final selection or click 'No idea' if unsure")

    root.mainloop()

    # Get results
    result, reliability, scale_type = interface.get_result()

    scale_names = ['None', 'Integer', 'Balanced', 'Power', 'Ma-Zheng', 'Dodd']

    print("\nResults:")
    print(f"  Comparison Ratio: {result:.4f}")
    print(f"  Reliability: {reliability}")
    print(f"  Scale Type: {scale_names[scale_type]}")

    if reliability == 0:
        print(f"\n  → User was unsure (clicked 'No idea')")
    elif result > 1:
        print(f"\n  → Alternative A is {result:.2f}x preferred over Alternative B")
    elif result < 1:
        print(f"\n  → Alternative B is {1/result:.2f}x preferred over Alternative A")
    else:
        print(f"\n  → Alternatives are equally preferred")


def example_ahp_matrix():
    """Example 2: Build AHP pairwise comparison matrix"""
    print("\n" + "="*60)
    print("Example 2: AHP Pairwise Comparison Matrix")
    print("="*60)

    criteria = ["Cost", "Quality", "Delivery Time"]
    n = len(criteria)

    # Initialize matrix
    matrix = [[1.0 for _ in range(n)] for _ in range(n)]
    reliability_matrix = [[0.0 for _ in range(n)] for _ in range(n)]

    print(f"\nBuilding {n}x{n} pairwise comparison matrix")
    print(f"Criteria: {', '.join(criteria)}")
    print(f"\nYou will be asked to compare each pair of criteria.")

    # Compare each pair
    for i in range(n):
        for j in range(i + 1, n):
            print(f"\n--- Comparing: {criteria[i]} vs {criteria[j]} ---")

            root = tk.Tk()

            interface = DynamicScaleInterface(
                root,
                object_a=criteria[i],
                object_b=criteria[j]
            )

            root.mainloop()

            result, reliability, scale_type = interface.get_result()

            # Fill matrix (symmetric)
            matrix[i][j] = result
            matrix[j][i] = 1 / result if result != 0 else 1.0

            reliability_matrix[i][j] = reliability
            reliability_matrix[j][i] = reliability

            print(f"Result: {criteria[i]}/{criteria[j]} = {result:.4f} (reliability: {reliability})")

    # Display matrix
    print("\n" + "="*60)
    print("Pairwise Comparison Matrix:")
    print("="*60)

    # Header
    print(f"{'':20}", end='')
    for criterion in criteria:
        print(f"{criterion:15}", end='')
    print()

    # Rows
    for i, criterion in enumerate(criteria):
        print(f"{criterion:20}", end='')
        for j in range(n):
            print(f"{matrix[i][j]:15.4f}", end='')
        print()

    # Display reliability
    print("\n" + "="*60)
    print("Reliability Matrix:")
    print("="*60)

    print(f"{'':20}", end='')
    for criterion in criteria:
        print(f"{criterion:15}", end='')
    print()

    for i, criterion in enumerate(criteria):
        print(f"{criterion:20}", end='')
        for j in range(n):
            if i == j:
                print(f"{'N/A':15}", end='')
            else:
                print(f"{reliability_matrix[i][j]:15.1f}", end='')
        print()

    # Calculate average reliability
    total_reliability = 0
    count = 0
    for i in range(n):
        for j in range(i + 1, n):
            total_reliability += reliability_matrix[i][j]
            count += 1

    avg_reliability = total_reliability / count if count > 0 else 0
    print(f"\nAverage Reliability: {avg_reliability:.2f}")

    if avg_reliability >= 5:
        print("→ High confidence in comparisons (fine gradations used)")
    elif avg_reliability >= 3:
        print("→ Medium confidence in comparisons (coarse gradations used)")
    elif avg_reliability >= 1:
        print("→ Low confidence in comparisons (only Less/More selected)")
    else:
        print("→ Very low confidence (many 'No idea' responses)")


def example_scale_comparison():
    """Example 3: Compare different scale types"""
    print("\n" + "="*60)
    print("Example 3: Comparing Different Scale Types")
    print("="*60)

    print("\nThis example demonstrates how different scale types")
    print("transform the same integer judgments.")

    # Simulate a comparison for each scale type
    test_values = [2, 5, 9]  # Weakly, Strongly, Extremely

    print(f"\nGrade values: {test_values}")
    print(f"Grade labels: {[PREF[v] for v in test_values]}")

    print("\nTransformed values by scale type:")
    print(f"{'Grade':<10} {'Integer':<12} {'Balanced':<12} {'Power':<12} {'Ma-Zheng':<12} {'Dodd':<12}")
    print("-" * 70)

    # Integer scale
    for grade in test_values:
        integer_val = float(grade)

        # Balanced
        balanced_val = (0.5 + (grade - 1) * 0.05) / (0.5 - (grade - 1) * 0.05)

        # Power
        import math
        power_val = 9 ** ((grade - 1) / 8)

        # Ma-Zheng
        mazheng_val = 9 / (9 + 1 - grade)

        # Dodd
        dodd_val = math.exp(math.atanh((grade - 1) / 14 * math.sqrt(3)))

        print(f"{PREF[grade]:<10} {integer_val:<12.4f} {balanced_val:<12.4f} {power_val:<12.4f} {mazheng_val:<12.4f} {dodd_val:<12.4f}")

    print("\nObservations:")
    print("- Integer: Linear scale (1.0 to 9.0)")
    print("- Balanced: Moderate growth, emphasizes middle values")
    print("- Power: Exponential growth, emphasizes extreme values")
    print("- Ma-Zheng: Special AHP scale (reciprocal properties)")
    print("- Dodd: Psychological preference modeling")


def example_progressive_refinement():
    """Example 4: Understanding progressive refinement"""
    print("\n" + "="*60)
    print("Example 4: Progressive Refinement Process")
    print("="*60)

    print("\nThe Dynamic Scale Interface uses a 4-level progressive approach:")
    print("\nLevel 0: Initial Choice")
    print("  - Choose: [Less] or [More] preferred")
    print("  - ScaleStr: '0' → '259'")
    print("  - Reliability: 0 → 1")

    print("\nLevel 1: Coarse Gradation (3 options)")
    print("  - Grades: 2 (Weakly), 5 (Strongly), 9 (Extremely)")
    print("  - Clicking 2 → ScaleStr: '23459'")
    print("  - Clicking 5 → ScaleStr: '25679'")
    print("  - Clicking 9 → ScaleStr: '2589'")
    print("  - Reliability: 1 → 3")

    print("\nLevel 2: Medium Gradation (5 options)")
    print("  - Depending on previous choice:")
    print("    • '23459': Grades 2,3,4,5,9 (weak to strong range)")
    print("    • '25679': Grades 2,5,6,7,9 (strong range)")
    print("    • '2589': Grades 2,5,8,9 (very strong range)")
    print("  - Gray panels = grouped values (clickable to return)")
    print("  - Red panels = active selection options")

    print("\nLevel 3+: Fine Gradation (2-8 adjustable)")
    print("  - Use mouse wheel or ▲▼ buttons to adjust")
    print("  - More gradations = higher reliability (5-8)")
    print("  - Available: '25', '259', '3579', '23579', etc.")

    print("\nTry it now:")

    root = tk.Tk()

    interface = DynamicScaleInterface(
        root,
        object_a="Option A",
        object_b="Option B"
    )

    print("\nPay attention to how the scale changes at each step!")

    root.mainloop()

    result, reliability, scale_type = interface.get_result()

    print(f"\nFinal State:")
    print(f"  Result: {result:.4f}")
    print(f"  Reliability: {reliability}")

    if reliability == 0:
        print("  → You clicked 'No idea' (Level 0)")
    elif reliability == 1:
        print("  → You only chose Less/More (Level 0)")
    elif reliability == 3:
        print("  → You chose coarse gradation (Level 1)")
    elif reliability >= 5:
        print(f"  → You chose fine gradation with {int(reliability)} levels (Level 3)")


def main():
    """Main menu for examples"""
    print("\n" + "="*60)
    print("Dynamic Scale Interface - Complete Python Implementation")
    print("Faithful Recreation of Delphi Source Code")
    print("="*60)

    examples = [
        ("Single Pairwise Comparison", example_single_comparison),
        ("AHP Matrix Construction", example_ahp_matrix),
        ("Scale Type Comparison", example_scale_comparison),
        ("Progressive Refinement Demo", example_progressive_refinement),
    ]

    while True:
        print("\nAvailable Examples:")
        for i, (name, _) in enumerate(examples, 1):
            print(f"  {i}. {name}")
        print(f"  0. Exit")

        try:
            choice = input("\nEnter your choice (0-4): ").strip()

            if choice == '0':
                print("\nGoodbye!")
                break

            choice_num = int(choice)
            if 1 <= choice_num <= len(examples):
                _, func = examples[choice_num - 1]
                func()
            else:
                print("Invalid choice. Please try again.")

        except ValueError:
            print("Invalid input. Please enter a number.")
        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except Exception as e:
            print(f"\nError: {e}")
            import traceback
            traceback.print_exc()


if __name__ == '__main__':
    # Check if running in interactive mode
    import sys

    if len(sys.argv) > 1:
        # Run specific example
        example_map = {
            '1': example_single_comparison,
            'single': example_single_comparison,
            '2': example_ahp_matrix,
            'ahp': example_ahp_matrix,
            '3': example_scale_comparison,
            'scale': example_scale_comparison,
            '4': example_progressive_refinement,
            'progressive': example_progressive_refinement,
        }

        arg = sys.argv[1].lower()
        if arg in example_map:
            example_map[arg]()
        else:
            print(f"Unknown example: {arg}")
            print("Available: single, ahp, scale, progressive")
    else:
        # Interactive menu
        main()
