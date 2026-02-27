import json
import random
import sys
import time
from pathlib import Path

try:
    from colorama import Fore, Style, init as colorama_init

    colorama_init(autoreset=True)
    COLOR_ENABLED = True
except ImportError:
    COLOR_ENABLED = False


if COLOR_ENABLED:
    COLOR_TITLE = Fore.CYAN + Style.BRIGHT
    COLOR_INFO = Fore.BLUE
    COLOR_SUCCESS = Fore.GREEN
    COLOR_WARN = Fore.YELLOW
    COLOR_ERROR = Fore.RED + Style.BRIGHT
    COLOR_RESET = Style.RESET_ALL
else:
    COLOR_TITLE = ""
    COLOR_INFO = ""
    COLOR_SUCCESS = ""
    COLOR_WARN = ""
    COLOR_ERROR = ""
    COLOR_RESET = ""


def tint(text, color_code):
    return f"{color_code}{text}{COLOR_RESET}"


def load_habitats():
    data_path = Path(__file__).with_name("habitats.json")

    try:
        with data_path.open(encoding="utf-8") as file:
            payload = json.load(file)
    except FileNotFoundError:
        raise SystemExit("Could not find habitats.json in the project directory.")
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in habitats.json: {exc}")

    if not isinstance(payload, list) or not payload:
        raise SystemExit("habitats.json must contain a non-empty list of habitats.")

    names = []
    texts = []

    for index, habitat in enumerate(payload):
        if not isinstance(habitat, dict):
            raise SystemExit(f"Habitat at index {index} must be an object.")

        name = habitat.get("name")
        text = habitat.get("text")
        if not isinstance(name, str) or not name.strip():
            raise SystemExit(f"Habitat at index {index} has an invalid 'name'.")
        if not isinstance(text, str) or not text:
            raise SystemExit(f"Habitat '{name}' has an invalid 'text'.")

        cleaned_name = name.strip().lower()
        if cleaned_name in names:
            raise SystemExit(f"Duplicate habitat name found: '{cleaned_name}'.")

        names.append(cleaned_name)
        texts.append(text)

    return names, texts


def default_save_path():
    return Path(__file__).with_name("zoo_progress.json")


animal_names, animals = load_habitats()
ENABLE_ANIMATION = sys.stdin.isatty() and sys.stdout.isatty()


def print_help():
    print(tint("Available commands:", COLOR_TITLE))
    print("  list                      - show all habitats")
    print("  show <id|name>            - open a habitat camera by index or name")
    print("  random                    - open a random habitat camera")
    print("  mode <watcher|zookeeper>  - switch app mode")
    print("  status [id|name]          - show stats for one/all habitats")
    print("  feed <id|name>            - raise fullness (zookeeper mode)")
    print("  clean <id|name>           - raise cleanliness (zookeeper mode)")
    print("  play <id|name>            - raise mood (uses some fullness)")
    print("  save [file]               - save progress (default: zoo_progress.json)")
    print("  load [file]               - load progress (default: zoo_progress.json)")
    print("  help                      - show this help message")
    print("  exit                      - quit the program")


def resolve_habitat(selection):
    value = selection.strip().lower()
    if not value:
        return None, "Please provide a habitat index or name."

    if value.isdigit():
        habitat_index = int(value)
        if 0 <= habitat_index < len(animals):
            return habitat_index, None
        return None, f"Habitat index must be between 0 and {len(animals) - 1}."

    if value in animal_names:
        return animal_names.index(value), None

    return None, f"Unknown habitat '{selection}'. Use 'list' to see options."


def play_loading_animation(habitat_name):
    if not ENABLE_ANIMATION:
        return

    frames = ["[      ]", "[=     ]", "[===   ]", "[===== ]", "[======]"]
    print(tint(f"Loading camera feed for {habitat_name}...", COLOR_INFO))
    for frame in frames:
        print(f"\r{tint(frame, COLOR_INFO)}", end="", flush=True)
        time.sleep(0.1)
    print("\r" + tint("Camera online.      ", COLOR_SUCCESS))


def show_habitat_by_index(habitat_index, habitat_stats=None, current_mode="watcher"):
    play_loading_animation(animal_names[habitat_index])
    print(animals[habitat_index])
    if current_mode == "zookeeper" and habitat_stats is not None:
        print("  " + format_status_line(habitat_index, habitat_stats[habitat_index]))


def list_habitats():
    print(tint("Habitats:", COLOR_TITLE))
    for i, name in enumerate(animal_names):
        print(f"  {i}: {name}")


def clamp_stat(value):
    return max(0, min(100, value))


def build_initial_stats():
    return [{"fullness": 55, "cleanliness": 70, "mood": 65} for _ in animals]


def format_status_line(habitat_index, stats):
    return (
        f"{habitat_index}: {animal_names[habitat_index]:<7} | "
        f"fullness={stats['fullness']:>3} | "
        f"cleanliness={stats['cleanliness']:>3} | "
        f"mood={stats['mood']:>3}"
    )


def print_status(habitat_stats, habitat_index=None):
    print(tint("Habitat status:", COLOR_TITLE))
    if habitat_index is None:
        for i, stats in enumerate(habitat_stats):
            print("  " + format_status_line(i, stats))
        return

    print("  " + format_status_line(habitat_index, habitat_stats[habitat_index]))


def apply_action(action_name, habitat_index, habitat_stats):
    stats = habitat_stats[habitat_index]

    if action_name == "feed":
        stats["fullness"] = clamp_stat(stats["fullness"] + 30)
        stats["mood"] = clamp_stat(stats["mood"] + 8)
        print(tint(f"You fed the {animal_names[habitat_index]}.", COLOR_SUCCESS))
    elif action_name == "clean":
        stats["cleanliness"] = clamp_stat(stats["cleanliness"] + 35)
        stats["mood"] = clamp_stat(stats["mood"] + 4)
        print(tint(f"You cleaned the {animal_names[habitat_index]} habitat.", COLOR_SUCCESS))
    elif action_name == "play":
        stats["mood"] = clamp_stat(stats["mood"] + 22)
        stats["fullness"] = clamp_stat(stats["fullness"] - 8)
        stats["cleanliness"] = clamp_stat(stats["cleanliness"] - 6)
        print(tint(f"You played with the {animal_names[habitat_index]}.", COLOR_SUCCESS))

    print("  " + format_status_line(habitat_index, stats))


def advance_turn(habitat_stats):
    for stats in habitat_stats:
        stats["fullness"] = clamp_stat(stats["fullness"] - random.randint(2, 6))
        stats["cleanliness"] = clamp_stat(stats["cleanliness"] - random.randint(1, 4))

        mood_delta = random.randint(-1, 1)
        if stats["fullness"] < 30:
            mood_delta -= 2
        if stats["cleanliness"] < 35:
            mood_delta -= 2

        stats["mood"] = clamp_stat(stats["mood"] + mood_delta)


def resolve_save_path(argument):
    raw = argument.strip()
    if not raw:
        return default_save_path()

    path = Path(raw).expanduser()
    if not path.suffix:
        path = path.with_suffix(".json")
    return path


def save_progress(path, habitat_stats, current_mode, turn_counter):
    payload = {
        "version": 1,
        "animal_names": animal_names,
        "habitat_stats": habitat_stats,
        "current_mode": current_mode,
        "turn_counter": turn_counter,
    }

    try:
        with path.open("w", encoding="utf-8") as file:
            json.dump(payload, file, indent=2)
    except OSError as exc:
        print(tint(f"Could not save progress: {exc}", COLOR_ERROR))
        return

    print(tint(f"Progress saved to {path}.", COLOR_SUCCESS))


def normalize_loaded_stats(raw_stats):
    if not isinstance(raw_stats, list) or len(raw_stats) != len(animals):
        return None

    normalized = []
    for raw_item in raw_stats:
        if not isinstance(raw_item, dict):
            return None

        try:
            if "fullness" in raw_item:
                fullness = clamp_stat(int(raw_item["fullness"]))
            else:
                # Backward compatibility with older saves that used "hunger".
                hunger = clamp_stat(int(raw_item["hunger"]))
                fullness = clamp_stat(100 - hunger)
            cleanliness = clamp_stat(int(raw_item["cleanliness"]))
            mood = clamp_stat(int(raw_item["mood"]))
        except (KeyError, TypeError, ValueError):
            return None

        normalized.append(
            {"fullness": fullness, "cleanliness": cleanliness, "mood": mood}
        )
    return normalized


def load_progress(path, habitat_stats, current_mode, turn_counter):
    try:
        with path.open(encoding="utf-8") as file:
            payload = json.load(file)
    except FileNotFoundError:
        print(tint(f"Save file not found: {path}", COLOR_ERROR))
        return habitat_stats, current_mode, turn_counter
    except json.JSONDecodeError as exc:
        print(tint(f"Invalid save JSON: {exc}", COLOR_ERROR))
        return habitat_stats, current_mode, turn_counter
    except OSError as exc:
        print(tint(f"Could not load progress: {exc}", COLOR_ERROR))
        return habitat_stats, current_mode, turn_counter

    if not isinstance(payload, dict):
        print(tint("Save file format is invalid.", COLOR_ERROR))
        return habitat_stats, current_mode, turn_counter

    saved_names = payload.get("animal_names")
    if saved_names != animal_names:
        print(
            tint(
                "Save file does not match the current habitats.json data.",
                COLOR_ERROR,
            )
        )
        return habitat_stats, current_mode, turn_counter

    normalized_stats = normalize_loaded_stats(payload.get("habitat_stats"))
    if normalized_stats is None:
        print(tint("Save file has invalid habitat stats.", COLOR_ERROR))
        return habitat_stats, current_mode, turn_counter

    loaded_mode = payload.get("current_mode")
    if loaded_mode not in {"watcher", "zookeeper"}:
        loaded_mode = "watcher"

    try:
        loaded_turn = max(0, int(payload.get("turn_counter", 0)))
    except (TypeError, ValueError):
        loaded_turn = 0

    print(tint(f"Progress loaded from {path}.", COLOR_SUCCESS))
    return normalized_stats, loaded_mode, loaded_turn


habitat_stats = build_initial_stats()
current_mode = "watcher"
turn_counter = 0

print(tint("Zoo Security Camera System", COLOR_TITLE))
print(tint("Type 'help' to see commands. Current mode: watcher", COLOR_INFO))

while True:
    raw_command = input(tint("zoo> ", COLOR_INFO)).strip()
    if not raw_command:
        continue

    parts = raw_command.split(maxsplit=1)
    command = parts[0].lower()
    argument = parts[1] if len(parts) > 1 else ""
    should_advance_turn = False

    if command in {"exit", "quit"}:
        break

    if command == "help":
        print_help()
        continue

    if command == "list":
        list_habitats()
        should_advance_turn = True
    elif command == "mode":
        mode = argument.strip().lower()
        if mode not in {"watcher", "zookeeper"}:
            print(tint("Mode must be 'watcher' or 'zookeeper'.", COLOR_ERROR))
            continue
        current_mode = mode
        print(tint(f"Switched to {current_mode} mode.", COLOR_SUCCESS))
    elif command == "status":
        if argument.strip():
            habitat_index, error = resolve_habitat(argument)
            if error:
                print(tint(error, COLOR_ERROR))
                continue
            print_status(habitat_stats, habitat_index)
        else:
            print_status(habitat_stats)
        should_advance_turn = True
    elif command in {"feed", "clean", "play"}:
        if current_mode != "zookeeper":
            print(
                tint(
                    "Action unavailable in watcher mode. Use 'mode zookeeper' first.",
                    COLOR_WARN,
                )
            )
            continue
        habitat_index, error = resolve_habitat(argument)
        if error:
            print(tint(error, COLOR_ERROR))
            continue
        apply_action(command, habitat_index, habitat_stats)
        should_advance_turn = True
    elif command == "save":
        save_path = resolve_save_path(argument)
        save_progress(save_path, habitat_stats, current_mode, turn_counter)
    elif command == "load":
        load_path = resolve_save_path(argument)
        habitat_stats, current_mode, turn_counter = load_progress(
            load_path, habitat_stats, current_mode, turn_counter
        )
    elif command == "random":
        random_index = random.randint(0, len(animals) - 1)
        print(tint(f"Randomly selected: {animal_names[random_index]}", COLOR_INFO))
        show_habitat_by_index(random_index, habitat_stats, current_mode)
        should_advance_turn = True
    elif command == "show":
        habitat_index, error = resolve_habitat(argument)
        if error:
            print(tint(error, COLOR_ERROR))
            continue
        show_habitat_by_index(habitat_index, habitat_stats, current_mode)
        should_advance_turn = True
    else:
        habitat_index, error = resolve_habitat(raw_command)
        if error:
            print(tint("Unknown command. Type 'help' for available commands.", COLOR_ERROR))
            continue
        show_habitat_by_index(habitat_index, habitat_stats, current_mode)
        should_advance_turn = True

    if should_advance_turn and current_mode == "zookeeper":
        advance_turn(habitat_stats)
        turn_counter += 1
        print(tint(f"[Turn {turn_counter}] Time passes in the zoo.", COLOR_WARN))
        continue

print(tint("---", COLOR_INFO))
print(tint("You've reached the end of the program. See you next time at the zoo!", COLOR_INFO))
