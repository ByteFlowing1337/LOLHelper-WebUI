"""
敌我分析服务
"""
import time
from config import app_state
from core import lcu


def auto_analyze_task(socketio):
    """
    敌我分析的后台任务
    
    Args:
        socketio: Flask-SocketIO实例，用于发送消息到前端
    """
    enemy_retry_count = 0
    MAX_ENEMY_RETRIES = 10
    last_phase = None
    
    while True:
        if app_state.auto_analyze_enabled and app_state.is_lcu_connected():
            try:
                token = app_state.lcu_credentials["auth_token"]
                port = app_state.lcu_credentials["app_port"]
                
                phase = lcu.get_gameflow_phase(token, port)
                
                # 检测到新的游戏流程开始，重置状态
                if last_phase in ["Lobby", "None", None] and phase not in ["Lobby", "None"]:
                    app_state.reset_analysis_state()
                    enemy_retry_count = 0
                    print(f"🔄 检测到新游戏流程开始 ({last_phase} -> {phase})，重置分析状态")
                
                # ChampSelect 阶段：分析队友战绩
                elif phase == "ChampSelect" and not app_state.teammate_analysis_done:
                    _analyze_teammates(token, port, socketio)
                
                # InProgress/GameStart 阶段：分析敌人战绩
                elif phase in ["InProgress", "GameStart"] and not app_state.enemy_analysis_done:
                    if enemy_retry_count < MAX_ENEMY_RETRIES:
                        enemy_retry_count += 1
                        success = _analyze_enemies(token, port, socketio, enemy_retry_count, MAX_ENEMY_RETRIES)
                        if not success:
                            time.sleep(3)  # 失败后等待3秒重试
                    else:
                        # 达到最大重试次数
                        socketio.emit('status_update', {'type': 'biz', 'message': '❌ 无法获取敌方信息，已停止重试'})
                        app_state.enemy_analysis_done = True
                        print(f"❌ 达到最大重试次数 ({MAX_ENEMY_RETRIES})，停止尝试")
                
                # EndOfGame 阶段：显示提示
                elif phase == "EndOfGame":
                    if app_state.teammate_analysis_done or app_state.enemy_analysis_done:
                        socketio.emit('status_update', {'type': 'biz', 'message': '🏁 比赛结束，等待下一局...'})
                        print("🏁 游戏结束")
                
                # 更新上一次的阶段
                last_phase = phase

            except Exception as e:
                error_msg = f'敌我分析任务出错: {str(e)}'
                socketio.emit('status_update', {'type': 'biz', 'message': f'❌ {error_msg}'})
                print(f"❌ 异常: {error_msg}")
                time.sleep(5)
            
            # 循环等待时间
            if phase in ["InProgress", "GameStart"] and not app_state.enemy_analysis_done:
                time.sleep(1)
            else:
                time.sleep(2)
        else:
            time.sleep(2)


def _analyze_teammates(token, port, socketio):
    """
    分析队友战绩（ChampSelect阶段）
    
    Args:
        token: LCU认证令牌
        port: LCU端口
        socketio: SocketIO实例
    """
    session = lcu.get_champ_select_session(token, port)
    if session:
        teammates = []
        for team_member in session.get('myTeam', []):
            puuid = team_member.get('puuid')
            if puuid:
                app_state.current_teammates.add(puuid)  # 记录队友PUUID
                teammates.append({
                    'gameName': team_member.get('gameName', '未知'),
                    'tagLine': team_member.get('tagLine', ''),
                    'puuid': puuid
                })
        
        if teammates:
            socketio.emit('teammates_found', {'teammates': teammates})
            socketio.emit('status_update', {'type': 'biz', 'message': f'👥 发现 {len(teammates)} 名队友，开始分析战绩...'})
            app_state.teammate_analysis_done = True
            print(f"✅ 队友分析完成，共 {len(teammates)} 人")
            print(f"📝 记录队友PUUID集合: {len(app_state.current_teammates)} 人")


def _analyze_enemies(token, port, socketio, retry_count, max_retries):
    """
    分析敌人战绩（InProgress阶段）
    
    Args:
        token: LCU认证令牌
        port: LCU端口
        socketio: SocketIO实例
        retry_count: 当前重试次数
        max_retries: 最大重试次数
    
    Returns:
        bool: 是否成功
    """
    socketio.emit('status_update', {'type': 'biz', 'message': f'🔍 正在获取敌方信息... (尝试 {retry_count}/{max_retries})'})
    print(f"开始第 {retry_count} 次尝试获取敌方信息")
    
    # 调用API获取所有玩家（通过team字段区分敌我：ORDER vs CHAOS）
    players_data = lcu.get_all_players_from_game(token, port)
    
    if players_data:
        enemies = players_data.get('enemies', [])
        
        # 双重过滤：排除队友PUUID
        if app_state.current_teammates:
            filtered_enemies = []
            for enemy in enemies:
                if enemy.get('puuid') and enemy['puuid'] not in app_state.current_teammates:
                    filtered_enemies.append(enemy)
                elif enemy.get('puuid') in app_state.current_teammates:
                    print(f"🚫 过滤队友: {enemy.get('summonerName', '未知')}")
            enemies = filtered_enemies
        
        if len(enemies) > 0:
            socketio.emit('enemies_found', {'enemies': enemies})
            socketio.emit('status_update', {'type': 'biz', 'message': f'💥 发现 {len(enemies)} 名敌人，开始分析战绩...'})
            app_state.enemy_analysis_done = True
            print(f"✅ 敌人分析完成，共 {len(enemies)} 人")
            return True
        else:
            print(f"⚠️ 第 {retry_count} 次尝试：过滤后无敌人数据")
            return False
    else:
        print(f"⚠️ 第 {retry_count} 次尝试：未获取到游戏数据")
        return False
