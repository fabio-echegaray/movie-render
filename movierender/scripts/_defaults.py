from pathlib import Path

DEFAULT_DEFAULTS_FILE = "defaults.cfg"


def find_default_files(cfg_path: Path, root_defaults: Path | None) -> list[Path] | Path | None:
    """Find defaults.cfg files from the config file's directory up to CWD.

    Returns a list of paths ordered closest to the config file first
    (closest = highest priority), a single Path if only one is found,
    or None if nothing exists.  *root_defaults* (if provided) is
    appended as the lowest-priority entry when not already present.
    """
    cwd = Path('.').absolute()
    cfg_dir = cfg_path.absolute().parent

    # collect directories from cfg_dir up to cwd (inclusive)
    dirs: list[Path] = []
    current = cfg_dir
    while True:
        dirs.append(current)
        if current == cwd:
            break
        if current == current.parent:
            break
        current = current.parent

    # dirs is [cfg_dir, ..., cwd] — closest to the config file first
    found: list[Path] = []
    seen: set[Path] = set()
    for d in dirs:
        df = d / DEFAULT_DEFAULTS_FILE
        abs_df = df.absolute()
        if abs_df not in seen and abs_df.is_file():
            found.append(abs_df)
            seen.add(abs_df)

    # also search ancestors above CWD (up to filesystem root) in case
    # defaults.cfg lives in a parent directory of the working directory
    current = cwd.parent
    while current != current.parent:
        df = current / DEFAULT_DEFAULTS_FILE
        abs_df = df.absolute()
        if abs_df not in seen and abs_df.is_file():
            found.append(abs_df)
            seen.add(abs_df)
        current = current.parent

    if root_defaults is not None:
        abs_root = root_defaults.absolute()
        if abs_root not in seen and abs_root.is_file():
            found.append(abs_root)
            seen.add(abs_root)

    if len(found) == 0:
        return None
    if len(found) == 1:
        return found[0]
    return found
