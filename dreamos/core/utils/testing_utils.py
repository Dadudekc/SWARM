from typing import Dict


def parse_test_failures(output: str) -> Dict[str, str]:
    """Parse pytest output and return a mapping of test names to errors."""
    failures: Dict[str, str] = {}
    current_test = None
    error_lines = []

    for line in output.splitlines():
        if line.startswith("FAILED"):
            if current_test:
                failures[current_test] = "\n".join(error_lines)
            parts = line.split()
            if len(parts) >= 2:
                current_test = parts[1].split("::")[-1]
            else:
                current_test = line.split("::")[-1].strip()
            error_lines = []
        elif current_test and line.strip():
            error_lines.append(line)
            if line.startswith("AssertionError") or line.startswith("Error"):
                failures[current_test] = "\n".join(error_lines)
                current_test = None
                error_lines = []

    if current_test:
        failures[current_test] = "\n".join(error_lines)

    return failures
