# NiceGUI re-executes by path; relative import can fail.
try:
    from .app import main
except ImportError:
    import sys
    from pathlib import Path
    _root = Path(__file__).resolve().parent.parent
    if str(_root) not in sys.path:
        sys.path.insert(0, str(_root))
    from grid_editor.app import main

if __name__ == "__main__":
    main()
