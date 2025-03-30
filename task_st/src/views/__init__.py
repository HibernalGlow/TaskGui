"""视图模块"""
from ..views.table_view import render_table_view
from ..views.card_view import render_card_view
from ..views.group_view import render_group_view

__all__ = [
    'render_table_view',
    'render_card_view',
    'render_group_view'
] 