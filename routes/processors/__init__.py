"""
游戏数据处理器模块
提供 LOL 和 TFT 游戏数据处理功能
"""
from .lol_processor import (
    process_lol_match_history,
    process_single_lol_game,
    format_game_mode,
    calculate_time_ago
)
from .tft_processor import process_single_tft_game

__all__ = [
    'process_lol_match_history',
    'process_single_lol_game',
    'process_single_tft_game',
    'format_game_mode',
    'calculate_time_ago'
]
