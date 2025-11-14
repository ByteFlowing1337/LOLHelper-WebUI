"""
自动 Ban/Pick 服务
在英雄选择阶段自动执行 ban 和 pick 操作
"""
import time
from config import app_state
from core import lcu


def auto_banpick_task(socketio, ban_champion_id=None, pick_champion_id=None):
    """
    自动 Ban/Pick 的后台任务
    
    Args:
        socketio: Flask-SocketIO实例，用于发送消息到前端
        ban_champion_id: 要禁用的英雄ID（可选）
        pick_champion_id: 要选择的英雄ID（可选）
    """
    try:
        last_phase = None
        ban_done = False
        pick_done = False
        
        while app_state.auto_banpick_enabled:
            if not app_state.is_lcu_connected():
                time.sleep(0.5)
                continue

            try:
                token = app_state.lcu_credentials["auth_token"]
                port = app_state.lcu_credentials["app_port"]

                phase = lcu.get_gameflow_phase(token, port)

                # ChampSelect 阶段：自动 ban/pick
                if phase == "ChampSelect":
                    if phase != last_phase:
                        print("🎮 进入英雄选择阶段")
                        socketio.emit('status_update', {
                            'type': 'biz', 
                            'message': '🎮 进入英雄选择阶段，准备自动 Ban/Pick'
                        })
                        last_phase = phase
                        ban_done = False
                        pick_done = False
                    
                    # 获取选人会话数据
                    session = lcu.get_champ_select_session(token, port)
                    if not session:
                        time.sleep(0.5)
                        continue
                    
                    # 获取本地玩家的 cellId
                    local_player_cell_id = session.get('localPlayerCellId')
                    if local_player_cell_id is None:
                        time.sleep(0.5)
                        continue
                    
                    # 处理 actions
                    actions = session.get('actions', [])
                    for action_group in actions:
                        if not isinstance(action_group, list):
                            continue
                        
                        for action in action_group:
                            if action.get('actorCellId') != local_player_cell_id:
                                continue
                            
                            action_id = action.get('id')
                            action_type = action.get('type', '').lower()
                            is_in_progress = action.get('isInProgress', False)
                            completed = action.get('completed', False)
                            
                            # 跳过已完成的动作
                            if completed:
                                continue
                            
                            # 只处理正在进行中的动作
                            if not is_in_progress:
                                continue
                            
                            # 自动 Ban
                            if action_type == 'ban' and not ban_done and ban_champion_id:
                                try:
                                    success = complete_action(
                                        token, port, action_id, ban_champion_id, 
                                        action_type='ban'
                                    )
                                    if success:
                                        ban_done = True
                                        socketio.emit('status_update', {
                                            'type': 'success',
                                            'message': f'✅ 已自动禁用英雄 (ID: {ban_champion_id})'
                                        })
                                        print(f"✅ 自动禁用英雄成功: {ban_champion_id}")
                                except Exception as e:
                                    print(f"⚠️ 自动禁用英雄失败: {e}")
                                    socketio.emit('status_update', {
                                        'type': 'warning',
                                        'message': f'⚠️ 自动禁用失败: {e}'
                                    })
                            
                            # 自动 Pick
                            elif action_type == 'pick' and not pick_done and pick_champion_id:
                                try:
                                    success = complete_action(
                                        token, port, action_id, pick_champion_id,
                                        action_type='pick'
                                    )
                                    if success:
                                        pick_done = True
                                        socketio.emit('status_update', {
                                            'type': 'success',
                                            'message': f'✅ 已自动选择英雄 (ID: {pick_champion_id})'
                                        })
                                        print(f"✅ 自动选择英雄成功: {pick_champion_id}")
                                except Exception as e:
                                    print(f"⚠️ 自动选择英雄失败: {e}")
                                    socketio.emit('status_update', {
                                        'type': 'warning',
                                        'message': f'⚠️ 自动选择失败: {e}'
                                    })
                
                elif phase != "ChampSelect" and last_phase == "ChampSelect":
                    print("🏁 离开英雄选择阶段")
                    last_phase = phase
                    ban_done = False
                    pick_done = False

            except Exception as e:
                print(f"❌ 自动 Ban/Pick 任务异常: {e}")

            time.sleep(0.5)  # 更快的轮询以确保及时响应
            
    finally:
        app_state.auto_banpick_thread = None
        app_state.auto_banpick_enabled = False
        print("🛑 自动 Ban/Pick 任务已退出")


def complete_action(token, port, action_id, champion_id, action_type='pick'):
    """
    完成一个选人/禁用动作
    
    Args:
        token: LCU认证令牌
        port: LCU端口
        action_id: 动作ID
        champion_id: 英雄ID
        action_type: 动作类型 ('ban' 或 'pick')
    
    Returns:
        bool: 是否成功
    """
    endpoint = f"/lol-champ-select/v1/session/actions/{action_id}"
    
    payload = {
        "championId": champion_id,
        "completed": True,
        "type": action_type
    }
    
    response = lcu.make_request("PATCH", endpoint, token, port, json_data=payload)
    
    # 如果响应不为空且没有错误，认为成功
    return response is not None


def hover_champion(token, port, action_id, champion_id):
    """
    悬停（预选）一个英雄
    
    Args:
        token: LCU认证令牌
        port: LCU端口
        action_id: 动作ID
        champion_id: 英雄ID
    
    Returns:
        dict: 响应数据
    """
    endpoint = f"/lol-champ-select/v1/session/actions/1"
    
    payload = {
        "championId": champion_id,
        "completed": False
    }
    
    return lcu.make_request("PATCH", endpoint, token, port, json_data=payload)
