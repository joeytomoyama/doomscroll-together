from pathlib import Path


OBS_DIR = Path(__file__).parent


def _set_after_colon(filename: str, value: str) -> None:
	path = OBS_DIR / filename
	existing = ""
	if path.exists():
		existing = path.read_text(encoding="utf-8")
	prefix, sep, _ = existing.partition(":")
	if sep:
		new_text = f"{prefix}{sep} {value}"
	else:
		new_text = value
	path.write_text(new_text, encoding="utf-8")


def write_chatter_down(content: str) -> None:
	print("[DEBUG] Writing to chatter_down.txt")
	_set_after_colon("chatter_down.txt", content)


def write_chatter_up(content: str) -> None:
	print("[DEBUG] Writing to chatter_up.txt")
	_set_after_colon("chatter_up.txt", content)


def write_chatter(content: str) -> None:
	print("[DEBUG] Writing to chatter.txt")
	_set_after_colon("chatter.txt", content)


def write_link_down(content: str) -> None:
	print("[DEBUG] Writing to link_down.txt")
	_set_after_colon("link_down.txt", content)


def write_link_up(content: str) -> None:
	print("[DEBUG] Writing to link_up.txt")
	_set_after_colon("link_up.txt", content)
