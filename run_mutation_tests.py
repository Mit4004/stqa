"""
Automated Mutation Testing Framework for Calc.py
------------------------------------------------
This script introduces small changes (mutations) into the source code of Calc.py
and runs the test suite (test_calc.py) against each mutant to evaluate test suite effectiveness.
"""

import sys
import subprocess
import os

# Define the set of mutations (Operator replacement, condition change, constant change, etc.)
MUTANTS = [
    {
        "id": "Mutant_1",
        "description": "AOR: In add(), replace '+' with '-' (return a - b)",
        "original": "def add(a,b):\n    return a+b",
        "mutation": "def add(a,b):\n    return a-b"
    },
    {
        "id": "Mutant_2",
        "description": "AOR: In subs(), replace '-' with '+' (return a + b)",
        "original": "def subs(a,b):\n    return a-b",
        "mutation": "def subs(a,b):\n    return a+b"
    },
    {
        "id": "Mutant_3",
        "description": "AOR: In mult(), replace '*' with '/' (return a / b)",
        "original": "def mult(a,b):\n    return a*b",
        "mutation": "def mult(a,b):\n    return a/b"
    },
    {
        "id": "Mutant_4",
        "description": "AOR: In divide(), replace '/' with '*' (return a * b)",
        "original": "return a/b",
        "mutation": "return a*b"
    },
    {
        "id": "Mutant_5",
        "description": "ROR: In divide(), replace '==' with '!=' (if b != 0:)",
        "original": "if b == 0:",
        "mutation": "if b != 0:"
    },
    {
        "id": "Mutant_6",
        "description": "CR: In divide(), replace constant '0' with '1' (if b == 1:)",
        "original": "if b == 0:",
        "mutation": "if b == 1:"
    },
    {
        "id": "Mutant_7",
        "description": "ERR: In divide(), replace 'ValueError' with 'TypeError'",
        "original": "raise ValueError(\"Cannot divide by zero\")",
        "mutation": "raise TypeError(\"Cannot divide by zero\")"
    },
    {
        "id": "Mutant_8",
        "description": "VR: In add(), return fixed constant 5",
        "original": "return a+b",
        "mutation": "return 5"
    }
]

def run_pytest():
    """Runs pytest as a subprocess and returns True if tests pass, False if tests fail."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "test_calc.py", "--quiet", "--no-header"],
        capture_output=True,
        text=True
    )
    return result.returncode == 0

def main():
    original_code_path = "Calc.py"
    with open(original_code_path, "r") as f:
        original_source = f.read()

    print("=" * 80)
    print("                    PYTHON MUTATION TESTING EXECUTION                    ")
    print("=" * 80)
    print(f"Target Module : {original_code_path}")
    print(f"Test Suite    : test_calc.py")
    print(f"Total Mutants : {len(MUTANTS)}")
    print("-" * 80)

    # First, verify baseline passes
    print("[+] Baseline Check: Running tests on ORIGINAL (unmutated) source code...")
    if not run_pytest():
        print("[-] ERROR: Baseline tests failed on unmutated code! Fix tests before running mutation testing.")
        sys.exit(1)
    print("[+] Baseline PASSED! Beginning mutation execution...\n")

    killed_count = 0
    survived_count = 0
    results = []

    for mutant in MUTANTS:
        m_id = mutant["id"]
        desc = mutant["description"]
        orig_str = mutant["original"]
        mut_str = mutant["mutation"]

        if orig_str not in original_source:
            print(f"[!] WARNING: Target pattern for {m_id} not found in source code. Skipping.")
            continue

        # Inject mutation into Calc.py
        mutated_source = original_source.replace(orig_str, mut_str, 1)
        with open(original_code_path, "w") as f:
            f.write(mutated_source)

        # Run test suite against mutated source code
        passed = run_pytest()

        # If tests pass on mutated code, the mutant SURVIVED (test suite failed to catch change).
        # If tests fail on mutated code, the mutant was KILLED (test suite successfully caught change).
        if passed:
            status = "[SURVIVED]"
            survived_count += 1
        else:
            status = "[KILLED]"
            killed_count += 1

        results.append((m_id, desc, status))

        # Restore original code immediately
        with open(original_code_path, "w") as f:
            f.write(original_source)

    # Re-verify original code restored properly
    with open(original_code_path, "w") as f:
        f.write(original_source)

    print("\n" + "=" * 80)
    print("                         MUTATION TEST SUMMARY LOG                        ")
    print("=" * 80)
    print(f"{'Mutant ID':<12} | {'Description':<50} | {'Status':<12}")
    print("-" * 80)
    for m_id, desc, status in results:
        print(f"{m_id:<12} | {desc:<50} | {status:<12}")

    total_mutants = killed_count + survived_count
    mutation_score = (killed_count / total_mutants * 100) if total_mutants > 0 else 0

    print("-" * 80)
    print(f"Total Mutants Evaluated : {total_mutants}")
    print(f"Killed Mutants (Caught)  : {killed_count}")
    print(f"Survived Mutants (Missed): {survived_count}")
    print(f"MUTATION SCORE           : {mutation_score:.2f}%")
    print("=" * 80)

if __name__ == "__main__":
    main()
