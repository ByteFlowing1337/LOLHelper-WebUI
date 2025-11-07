"""
配置文件
包含应用的全局配置和共享状态
"""

# Flask 配置
HOST = '0.0.0.0'
PORT = 5000

# 全局状态变量
class AppState:
    """应用全局状态管理"""
    def __init__(self):
        from typing import Any
        from threading import Thread

        # 功能开关
        self.auto_accept_enabled: bool = False
        self.auto_analyze_enabled: bool = False

        # 分析状态
        self.teammate_analysis_done: bool = False
        self.enemy_analysis_done: bool = False
        self.current_teammates: set = set()

        # LCU凭证 (auth_token may be str or None; app_port may be int or None)
        self.lcu_credentials: dict[str, Any] = {
            "auth_token": None,
            "app_port": None
        }

        # 线程引用
        self.auto_accept_thread: 'Thread | None' = None
        self.auto_analyze_thread: 'Thread | None' = None
    
    def reset_analysis_state(self):
        """重置分析状态"""
        self.teammate_analysis_done = False
        self.enemy_analysis_done = False
        self.current_teammates.clear()
    
    def is_lcu_connected(self):
        """检查LCU是否连接"""
        return self.lcu_credentials["auth_token"] is not None

# 创建全局状态实例
app_state = AppState()
