"""
Callback-Skeleton: generated from layout.json by App-Builder.
Logic lives in assignments.user_callbacks.py (not overwritten).
State defaults: model_schema.STATE_DEFAULTS (single source).
"""
from __future__ import annotations

from typing import Callable

# ---- Callbacks from assignments.user_callbacks.py (user edits this file only) ----
from ..assignments.user_callbacks import on_header_text_change, on_row_1_widget_5_change, on_my_text_change, on_code_table_change, on_code_tree_change

# ---- Callback-Registry (für GUI-Schicht) ----
def get_callback_registry() -> dict[str, Callable]:
    return {
        'row_1.widget_2': on_header_text_change,
        'row_1.widget_5': on_row_1_widget_5_change,
        'row_2.widget_3': on_my_text_change,
        'row_2.widget_4': on_code_table_change,
        'row_2.widget_6': on_code_tree_change,
    }
