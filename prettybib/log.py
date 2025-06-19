def color_wrap(text, color):
    """Wrap text in ANSI color codes."""
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "magenta": "\033[95m",
        "cyan": "\033[96m",
        "white": "\033[97m",
        "reset": "\033[0m"
    }
    start = colors.get(color, colors['reset'])
    end = colors['reset']
    return f"{start}{text}{end}"


def log_warn(x):
    print(color_wrap(f"WARN: {x}", "yellow"))


def log_debug(x):
    print(color_wrap(f"DEBUG: {x}", "cyan"))


def log_success(x):
    print(color_wrap(f"SUCCESS: {x}", "green"))


def log_info(x):
    print(f"INFO: {x}")
