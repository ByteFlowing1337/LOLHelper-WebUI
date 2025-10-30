"""
游戏内实时数据 API
通过游戏客户端本地 API (端口 2999) 获取实时对局信息
注意：此 API 仅在游戏进行中可用，不需要 LCU 认证
"""
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_live_game_data():
    """
    通过游戏客户端本地API获取当前对局的实时数据（端口2999）。
    
    此API仅在游戏进行中可用，不需要认证。
    
    Returns:
        dict: 包含所有玩家信息的完整游戏数据
        None: 如果游戏未开始或请求失败
    
    返回数据结构:
    {
        'activePlayer': {...},  # 当前玩家信息
        'allPlayers': [...],    # 所有玩家列表
        'events': {...},        # 游戏事件
        'gameData': {...}       # 游戏元数据
    }
    """
    try:
        url = "https://127.0.0.1:2999/liveclientdata/allgamedata"
        response = requests.get(url, verify=False, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"获取游戏内数据失败（可能游戏未开始）: {e}")
        return None


def get_enemy_players_from_game():
    """
    从游戏内API获取敌方队伍的所有玩家信息。
    
    支持多种游戏模式:
    - 传统模式 (5v5): 返回对方5人
    - cherry模式 (2v2v2v2v2v2v2v2): 返回其他14人
    
    Returns:
        list: 敌方玩家列表，每个玩家包含 summonerName、championName、team 等信息
        []: 如果游戏未开始或解析失败
    """
    game_data = get_live_game_data()
    if not game_data:
        return []
    
    try:
        all_players = game_data.get('allPlayers', [])
        active_player = game_data.get('activePlayer', {})
        my_summoner_name = active_player.get('summonerName', '')
        game_mode = game_data.get('gameData', {}).get('gameMode', 'CLASSIC')
        
        # 找到当前玩家的队伍
        my_team = None
        for player in all_players:
            if player.get('summonerName') == my_summoner_name:
                my_team = player.get('team', '')
                break
        
        if not my_team:
            print("⚠️ 无法确定当前玩家的队伍")
            return []
        
        is_cherry_mode = game_mode.upper() == 'CHERRY'
        if is_cherry_mode:
            print(f"🍒 CHERRY 模式 (2v2v2v2v2v2v2v2)：当前队伍 {my_team}，查找其他队伍")
        
        # 筛选出敌方玩家（队伍不同的玩家）
        enemy_players = [
            player for player in all_players 
            if player.get('team', '') != my_team
        ]
        
        mode_suffix = " (CHERRY 模式 - 16人)" if is_cherry_mode else ""
        print(f"找到 {len(enemy_players)} 名敌方玩家{mode_suffix}")
        return enemy_players
        
    except Exception as e:
        print(f"解析敌方玩家数据失败: {e}")
        return []


def get_all_players_from_game(token, port):
    """
    从游戏内API获取所有玩家信息，并分类为队友和敌人。
    
    规则：
    - 通过 activePlayer 的 team 字段确定己方队伍
    - 根据 allPlayers 中每个玩家的 team 字段进行分类
      * team 相同 → 队友
      * team 不同 → 敌人
    - 特殊模式支持:
      * cherry (斗魂竞技场): 2v2v2v2v2v2v2v2 (16人，8个队伍)
      * 传统模式: 5v5 (10人)
    
    Args:
        token: LCU认证令牌（用于查询PUUID）
        port: LCU端口
    
    Returns:
        dict: 包含队友和敌人信息的字典
        None: 如果游戏未开始或数据不完整
    
    返回格式:
    {
        'teammates': [
            {
                'summonerName': '玩家名',
                'gameName': '游戏名',
                'tagLine': 'TAG',
                'puuid': 'xxx-xxx-xxx',
                'championName': '英雄名',
                'level': 等级,
                'team': 'ORDER' 或 'CHAOS'
            },
            ...
        ],
        'enemies': [ 同上格式 ]
    }
    """
    # 延迟导入以避免循环依赖
    from .summoner import get_puuid
    
    game_data = get_live_game_data()
    if not game_data:
        print("❌ 无法获取游戏数据（游戏可能未开始）")
        return None
    
    try:
        all_players = game_data.get('allPlayers', [])
        active_player = game_data.get('activePlayer', {})
        game_mode = game_data.get('gameData', {}).get('gameMode', 'CLASSIC')
        
        # 检测游戏模式并确定最小玩家数
        is_cherry_mode = game_mode.upper() == 'CHERRY'
        min_players = 16 if is_cherry_mode else 10
        
        if len(all_players) < min_players:
            print(f"⚠️ 玩家数据不完整，当前只有 {len(all_players)} 人（{game_mode} 模式需要至少 {min_players} 人）")
            return None
        
        if is_cherry_mode:
            print("🍒 检测到斗魂竞技场模式 (CHERRY)，8个队伍每队2人，共16人")
        
        # 获取当前玩家的召唤师名和队伍
        my_summoner_name = active_player.get('summonerName', '')
        my_team_side = None
        
        # 从 allPlayers 中找到当前玩家，确定队伍
        for player in all_players:
            if player.get('summonerName') == my_summoner_name:
                my_team_side = player.get('team', '')
                break
        
        if not my_team_side:
            print("⚠️ 无法确定当前玩家的队伍")
            return None
        
        print(f"🎮 当前玩家队伍: {my_team_side} (模式: {game_mode})")
        
        # 根据队伍分类玩家
        teammate_list = []
        enemy_list = []
        
        for player in all_players:
            summoner_name = player.get('summonerName', '未知')
            player_team = player.get('team', '')
            
            # 获取PUUID
            puuid = get_puuid(token, port, summoner_name)
            
            # 解析游戏名和标签
            if '#' in summoner_name:
                parts = summoner_name.split('#', 1)
                game_name = parts[0]
                tag_line = parts[1] if len(parts) > 1 else 'NA'
            else:
                game_name = summoner_name
                tag_line = 'NA'
            
            player_info = {
                'summonerName': summoner_name,
                'gameName': game_name,
                'tagLine': tag_line,
                'puuid': puuid,
                'championName': player.get('championName', '未知'),
                'level': player.get('level', 0),
                'team': player_team
            }
            
            # 根据队伍字段分类
            if player_team == my_team_side:
                teammate_list.append(player_info)
                print(f"👥 队友: {summoner_name} ({player.get('championName', '未知')}) [队伍: {player_team}]")
            else:
                enemy_list.append(player_info)
                print(f"💥 敌人: {summoner_name} ({player.get('championName', '未知')}) [队伍: {player_team}]")
        
        mode_info = f"({game_mode})" if is_cherry_mode else f"({my_team_side})"
        print(f"✅ 成功获取 {len(teammate_list)} 名队友和 {len(enemy_list)} 名敌人 {mode_info}")
        
        return {
            'teammates': teammate_list,
            'enemies': enemy_list
        }
        
    except Exception as e:
        print(f"❌ 解析玩家数据失败: {e}")
        return None


def get_enemy_stats(token, port):
    """
    【完整流程】获取敌方玩家的战绩信息。
    
    工作流程:
    1. 从游戏内API（端口2999）获取敌方召唤师名
    2. 通过LCU API将召唤师名转换为PUUID
    3. 返回基本信息（PUUID由前端用于异步查询战绩）
    
    Args:
        token: LCU认证令牌
        port: LCU端口
    
    Returns:
        list: 敌方玩家信息列表
    
    返回格式:
    [
        {
            'summonerName': '玩家名',
            'puuid': 'xxx-xxx-xxx',
            'championId': '英雄名',
            'level': 等级,
            'error': '错误信息'  # 可选，仅在失败时存在
        },
        ...
    ]
    """
    # 延迟导入以避免循环依赖
    from .summoner import get_puuid
    
    enemy_players = get_enemy_players_from_game()
    if not enemy_players:
        print("❌ 无法获取敌方玩家信息（可能游戏未开始）")
        return []
    
    enemy_stats = []
    
    for player in enemy_players:
        summoner_name = player.get('summonerName', '未知')
        print(f"正在查询敌方玩家: {summoner_name}")
        
        # 步骤1: 获取PUUID（前端可以用来查询战绩）
        puuid = get_puuid(token, port, summoner_name)
        if not puuid:
            print(f"  ⚠️ 无法获取 {summoner_name} 的PUUID")
            enemy_stats.append({
                'summonerName': summoner_name,
                'puuid': None,
                'championId': player.get('championName', '未知'),
                'level': player.get('level', 0),
                'error': '无法获取PUUID'
            })
            continue
        
        print(f"  ✅ PUUID: {puuid[:20]}...")
        
        # 返回基本信息，战绩由前端异步查询（避免后端阻塞）
        enemy_stats.append({
            'summonerName': summoner_name,
            'puuid': puuid,
            'championId': player.get('championName', '未知'),
            'level': player.get('level', 0)
        })
    
    return enemy_stats
