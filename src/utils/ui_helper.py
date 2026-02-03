from rich.console import Console
from contextlib import contextmanager

console = Console()

@contextmanager
def progress_spinner(message="Working..."):
    with console.status(f"[bold blue]⏳ {message}", spinner="dots"):
        yield