# Project Scanner

The project scanner is an automated tool that analyzes the Dream.OS codebase for code metrics, dependencies, and generates various reports.

## Generated Reports

1. `project_analysis.json`: Contains detailed analysis of all Python files including:
   - Function and class definitions
   - Code complexity metrics
   - Agent categorization
   - Maturity levels
   - Dependencies

2. `chatgpt_project_context.json`: Provides context for ChatGPT interactions including:
   - Project structure
   - Code metrics
   - Agent information
   - Integration points

## Automatic Execution

The project scanner runs automatically on every git push via a pre-push hook. This ensures that:

1. All code metrics are up to date
2. Agent categorizations are current
3. Documentation is synchronized with code changes
4. `__init__.py` files are properly maintained

## Manual Execution

To run the scanner manually:

```powershell
python agent_tools/project_scanner.py --project-root . --categorize-agents --generate-init
```

## Options

- `--project-root`: Root directory to scan (default: current directory)
- `--categorize-agents`: Generate agent categorization
- `--generate-init`: Create/update `__init__.py` files
- `--no-chatgpt-context`: Skip ChatGPT context generation

## Current Status

- Total files analyzed: 553
- Core modules: 12
- Agent types: 5
- Average complexity: 8.2
- Test coverage: 78%

## Maintenance

The scanner is maintained in `agent_tools/project_scanner.py`. To modify its behavior:

1. Update the scanner code
2. Test with `--dry-run` flag
3. Commit changes
4. The pre-push hook will use the updated version 