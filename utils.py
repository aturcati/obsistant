from pathlib import Path
from rich.console import Console

console = Console()

def log_change(file: Path, added: set[str], removed: set[str], dry: bool):
    console.print(f"[bold cyan]{file}[/]: +{len(added)} tags, "
                  f"-{len(removed)} tags {'[dry-run]' if dry else ''}")
