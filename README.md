# Zoo Security Camera System

My first Python project from Hyperskill, now upgraded into an interactive CLI app.

## Run

```bash
python zookeeper.py
```

Optional for colorized output:

```bash
pip install colorama
```

## Data file

All habitats are loaded from `habitats.json`.
To add a new animal, add a new object with `name` and `text` fields to that file.
No Python changes are needed.

## Commands

- `list` - show all habitats
- `show <id|name>` - open a habitat camera by number or animal name
- `random` - open a random habitat camera
- `mode <watcher|zookeeper>` - switch between camera mode and management mode
- `status [id|name]` - show fullness, cleanliness, and mood
- `feed <id|name>` - raise fullness (zookeeper mode)
- `clean <id|name>` - raise cleanliness (zookeeper mode)
- `play <id|name>` - raise mood (uses some fullness)
- `save [file]` - save progress (default: `zoo_progress.json`)
- `load [file]` - load progress (default: `zoo_progress.json`)
- `help` - show command help
- `exit` - quit

You can also type a habitat name or index directly (for example `lion` or `3`).

## Zookeeper mode

Switch to zookeeper mode with:

```bash
mode zookeeper
```

In this mode, habitat stats change over time every turn, so you need to keep animals happy and healthy.

When viewing habitats (`show`/`random`) you'll see a small camera loading animation in interactive terminals.
