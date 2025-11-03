"""
Example usage of the Dynamic Scale Interface for pairwise comparisons.

This script demonstrates how to use the dynamic_scale_interface module
for conducting pairwise comparisons with various scale types.
"""

import tkinter as tk
from dynamic_scale_interface import DynamicScaleInterface, ScaleType


def example_single_comparison():
    """Example: Single pairwise comparison"""
    print("=" * 60)
    print("Example 1: Single Pairwise Comparison")
    print("=" * 60)
    print("\nComparing: Project A vs Project B")
    print("Instructions:")
    print("  1. First choose Less/More preferred")
    print("  2. Then refine your choice through progressive gradations")
    print("  3. You can change scale type using the left panel")
    print("  4. Use mouse wheel or buttons to adjust gradation levels")
    print("  5. Click 'No idea' if uncertain\n")

    root = tk.Tk()
    interface = DynamicScaleInterface(
        root,
        object_a="Project A: High risk, high reward",
        object_b="Project B: Low risk, steady returns"
    )

    root.mainloop()

    result, reliability, scale_type = interface.get_result()

    print("\n" + "=" * 60)
    print("Comparison Results:")
    print("=" * 60)
    print(f"Result Ratio: {result:.6f}")
    print(f"Reliability Level: {reliability}")
    print(f"Scale Type Used: {ScaleType(scale_type).name}")

    if result > 1:
        print(f"\nConclusion: Project A is preferred by a factor of {result:.3f}")
    elif result < 1:
        print(f"\nConclusion: Project B is preferred by a factor of {1/result:.3f}")
    else:
        print(f"\nConclusion: Both projects are equally preferred")

    print("\nInterpretation:")
    if reliability == 0:
        print("  - User was uncertain (No idea)")
    elif reliability == 1:
        print("  - Low confidence (only Less/More selected)")
    elif reliability == 3:
        print("  - Medium confidence (coarse gradation)")
    elif reliability >= 5:
        print("  - High confidence (fine gradation)")

    print()


def example_multiple_comparisons():
    """Example: Multiple pairwise comparisons"""
    print("=" * 60)
    print("Example 2: Multiple Pairwise Comparisons")
    print("=" * 60)
    print("\nComparing three alternatives: A, B, C")
    print("We need 3 comparisons: A-B, A-C, B-C\n")

    alternatives = ["Alternative A", "Alternative B", "Alternative C"]
    results = {}

    # Perform pairwise comparisons
    pairs = [
        (0, 1),  # A vs B
        (0, 2),  # A vs C
        (1, 2)   # B vs C
    ]

    for idx, (i, j) in enumerate(pairs, 1):
        print(f"\nComparison {idx}/3: {alternatives[i]} vs {alternatives[j]}")
        print("-" * 60)

        root = tk.Tk()
        interface = DynamicScaleInterface(
            root,
            object_a=alternatives[i],
            object_b=alternatives[j]
        )

        root.mainloop()

        result, reliability, scale_type = interface.get_result()
        results[(i, j)] = {
            'result': result,
            'reliability': reliability,
            'scale_type': scale_type
        }

        print(f"  Result: {result:.4f}, Reliability: {reliability}")

    # Display summary
    print("\n" + "=" * 60)
    print("Comparison Matrix Summary:")
    print("=" * 60)

    for (i, j), data in results.items():
        result = data['result']
        print(f"{alternatives[i]} vs {alternatives[j]}: {result:.4f}")

    print("\nNote: Values >1 mean first alternative is preferred")
    print("      Values <1 mean second alternative is preferred")
    print()


def example_scale_types():
    """Example: Demonstrating different scale types"""
    print("=" * 60)
    print("Example 3: Comparing Scale Types")
    print("=" * 60)
    print("\nThis example shows how different scale transformations")
    print("affect the result for the same qualitative judgment.\n")

    # Show transformation for a moderately strong preference (grade 6)
    from dynamic_scale_interface import DynamicScaleInterface
    import math

    grade = 6  # "Strongly plus"

    print(f"For grade {grade} ('{DynamicScaleInterface.PREF[grade]}'):\n")

    # Integer scale
    integer_val = grade
    print(f"  Integer Scale:     {integer_val:.4f}")

    # Balanced scale
    balanced_val = (0.5 + (grade - 1) * 0.05) / (0.5 - (grade - 1) * 0.05)
    print(f"  Balanced Scale:    {balanced_val:.4f}")

    # Power scale
    power_val = math.pow(9, (grade - 1) / 8)
    print(f"  Power Scale:       {power_val:.4f}")

    # Ma-Zheng scale
    mazheng_val = 9 / (9 + 1 - grade)
    print(f"  Ma-Zheng Scale:    {mazheng_val:.4f}")

    # Dodd scale
    dodd_val = math.exp(math.atanh((grade - 1) / 14 * math.sqrt(3)))
    print(f"  Dodd Scale:        {dodd_val:.4f}")

    print("\nObservation: Different scales give different numerical values")
    print("for the same qualitative judgment. Choose the scale that best")
    print("matches your decision-making context.\n")


def example_ahp_integration():
    """Example: Integration with AHP (Analytic Hierarchy Process)"""
    print("=" * 60)
    print("Example 4: AHP Matrix Construction")
    print("=" * 60)
    print("\nThis example shows how to build a pairwise comparison matrix")
    print("suitable for use in the Analytic Hierarchy Process (AHP).\n")

    n = 3  # Number of criteria
    criteria = ["Cost", "Quality", "Time"]

    # Initialize comparison matrix
    matrix = [[1.0] * n for _ in range(n)]

    print(f"Building comparison matrix for {n} criteria: {', '.join(criteria)}\n")

    # Collect pairwise comparisons
    for i in range(n):
        for j in range(i + 1, n):
            print(f"\nComparing: {criteria[i]} vs {criteria[j]}")

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

            print(f"  Result: {result:.4f}")

    # Display matrix
    print("\n" + "=" * 60)
    print("Pairwise Comparison Matrix:")
    print("=" * 60)

    # Header
    print(f"{'':12}", end='')
    for c in criteria:
        print(f"{c:>12}", end='')
    print()

    # Rows
    for i, c in enumerate(criteria):
        print(f"{c:12}", end='')
        for j in range(n):
            print(f"{matrix[i][j]:12.4f}", end='')
        print()

    print("\nThis matrix can now be used for AHP priority calculation.")
    print("(Priority calculation requires eigenvalue computation, not shown here)\n")


def main():
    """Run all examples"""
    examples = [
        ("Single Comparison", example_single_comparison),
        ("Multiple Comparisons", example_multiple_comparisons),
        ("Scale Types Comparison", example_scale_types),
        ("AHP Integration", example_ahp_integration),
    ]

    print("\n")
    print("=" * 60)
    print("Dynamic Scale Interface - Examples")
    print("=" * 60)
    print("\nAvailable examples:")

    for idx, (name, _) in enumerate(examples, 1):
        print(f"  {idx}. {name}")

    print(f"  {len(examples) + 1}. Run all examples")
    print(f"  0. Exit")

    while True:
        try:
            choice = input(f"\nSelect example (0-{len(examples) + 1}): ").strip()

            if choice == '0':
                print("Goodbye!")
                break

            choice = int(choice)

            if choice == len(examples) + 1:
                # Run all
                for name, func in examples:
                    func()
                    input("\nPress Enter to continue to next example...")
                break
            elif 1 <= choice <= len(examples):
                examples[choice - 1][1]()
                break
            else:
                print(f"Please enter a number between 0 and {len(examples) + 1}")

        except ValueError:
            print("Invalid input. Please enter a number.")
        except KeyboardInterrupt:
            print("\n\nInterrupted. Goodbye!")
            break


if __name__ == "__main__":
    main()
