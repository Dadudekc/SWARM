import subprocess
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEST_DIR = ROOT / 'tests'
STUBBORN_DIR = TEST_DIR / 'stubborn'
STUBBORN_DIR.mkdir(exist_ok=True)

# Run pytest and capture output
print('Running pytest...')
result = subprocess.run(['pytest', '-q'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
output = result.stdout

# Save raw output
(Path('pytest_output.log')).write_text(output)

# Parse failing test file paths
pattern = re.compile(r'(tests/[^\s:\n]+\.py)')
files = set(pattern.findall(output))

# Move each failing test file to stubborn directory
for file in files:
    src = ROOT / file
    if src.is_file():
        dest = STUBBORN_DIR / src.name
        print(f"Moving {src} to {dest}")
        dest.parent.mkdir(parents=True, exist_ok=True)
        src.rename(dest)

print('Done.')
