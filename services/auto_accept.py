"""
自动接受对局服务
"""
import time
from config import app_state
from core import lcu


def auto_accept_task(socketio):
    """
    自动接受对局的后台任务
    
    Args:
        socketio: Flask-SocketIO实例，用于发送消息到前端
    """
    while True:
        if app_state.auto_accept_enabled and app_state.is_lcu_connected():
            try:
                token = app_state.lcu_credentials["auth_token"]
                port = app_state.lcu_credentials["app_port"]
                
                phase = lcu.get_gameflow_phase(token, port)
                
                # ReadyCheck 阶段：自动接受对局
                if phase == "ReadyCheck":
                    try:
                        lcu.accept_ready_check(token, port)
                        socketio.emit('status_update', {'type': 'biz', 'message': '✅ 已自动接受对局!'})
                        print("✅ 自动接受对局成功")
                    except Exception as accept_error:
                        print(f"⚠️ 自动接受对局失败: {accept_error}")
                        socketio.emit('status_update', {'type': 'biz', 'message': f'⚠️ 自动接受失败: {accept_error}'})
                
            except Exception as e:
                print(f"❌ 自动接受任务异常: {e}")
            
            time.sleep(1)  # 快速轮询
        else:
            time.sleep(2)
