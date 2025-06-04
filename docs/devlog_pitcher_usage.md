# Devlog Pitcher CLI

`tools/devlog_pitcher.py` turns a `devlog.md` file into short product pitches using the ChatGPT bridge.

## Usage

```bash
python tools/devlog_pitcher.py path/to/devlog.md --limit 5 --out pitch.md
```

- **`devlog`**: path to the markdown log
- **`--limit`**: number of recent entries to convert (default: 3)
- **`--out`**: optional file to save the generated pitch. If omitted, the pitch is printed to stdout.

The script parses headings in the devlog and asks ChatGPT to create a brief marketing snippet for each entry. The result is returned in simple Markdown format.
