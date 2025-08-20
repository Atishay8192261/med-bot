def trim(s: str, n: int = 1200) -> str:
    if not s:
        return s
    return s if len(s) <= n else s[:n] + "..."
