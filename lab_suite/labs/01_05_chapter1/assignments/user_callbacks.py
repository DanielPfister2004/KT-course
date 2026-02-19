"""
User callbacks: logic for the GUI. Not overwritten by the skeleton generator.
Add new callbacks after layout changes and run 'Generate skeleton' again.

Use gui_binding.get(key) / gui_binding.set(key, value) for semantic keys (user_id in layout).
"""
from __future__ import annotations

from typing import Any

from .._core.assignment_registry import get_assignment

# widget: user_id=header-text
def on_header_text_change(value: Any) -> None:
    """Path-ID: row_1.widget_2. Widget: 'markdown', label: 'widget_2'. Callback args: value: Any"""
#begin user code
    # value = value
    pass
#end user code

# widget: path_id:row_1.widget_5
def on_row_1_widget_5_change(value: Any) -> None:
    """Path-ID: row_1.widget_5. Widget: 'slider', label: 'Slider'. Callback args: value: float"""
#begin user code
    # value = value
    pass
#end user code

# widget: user_id=my_text
def on_my_text_change(value: Any) -> None:
    """Path-ID: row_2.widget_3. Widget: 'markdown', label: 'widget_3'. Callback args: value: Any"""
#begin user code
    assignment = get_assignment()
    if assignment is not None and hasattr(assignment, "solve_task"):
        assignment.solve_task()
#end user code

# widget: user_id=code_table
def on_code_table_change(value: Any) -> None:
    """Path-ID: row_2.widget_4. Widget: 'markdown', label: 'widget_4'. Callback args: value: Any"""
#begin user code
    # value = value
    pass
#end user code

# widget: user_id=code_tree
def on_code_tree_change(value: Any) -> None:
    """Path-ID: row_2.widget_6. Widget: 'markdown', label: 'widget_6'. Callback args: value: Any"""
#begin user code
    # value = value
    pass
#end user code
