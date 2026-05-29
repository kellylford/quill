from pathlib import Path

TEXT_EXTENSIONS = {
    ".txt",
    ".md",
    ".markdown",
    ".rst",
    ".json",
    ".toml",
    ".yaml",
    ".yml",
    ".xml",
    ".csv",
    ".tsv",
    ".ini",
    ".cfg",
    ".log",
    ".py",
    ".html",
    ".htm",
    ".css",
    ".js",
    ".ts",
}


def looks_like_text(path: Path) -> bool:
    return path.suffix.lower() in TEXT_EXTENSIONS
