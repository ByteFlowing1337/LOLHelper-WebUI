"""
游戏内实时数据 API
通过游戏客户端本地 API (端口 2999) 获取实时对局信息
注意：此 API 仅在游戏进行中可用，不需要 LCU 认证
"""
import requests
import urllib3

from utils.game_data_formatter import format_game_data
from utils.logger import logger

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
        logger.debug(f"获取游戏内数据失败（可能游戏未开始）: {e}")
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
        snapshot = format_game_data(game_data)
        formatted_enemies = snapshot.get('enemies', []) if isinstance(snapshot, dict) else []
        formatted_lookup = {
            entry.get('summonerName'): entry
            for entry in formatted_enemies
            if isinstance(entry, dict)
        }
        
        # 找到当前玩家的队伍
        my_team = None
        for player in all_players:
            if player.get('summonerName') == my_summoner_name:
                my_team = player.get('team', '')
                break
        
        if not my_team:
            logger.warning("⚠️ 无法确定当前玩家的队伍")
            return []
        
        is_cherry_mode = game_mode.upper() == 'CHERRY'
        if is_cherry_mode:
            logger.debug(f"🍒 CHERRY 模式 (2v2v2v2v2v2v2v2)：当前队伍 {my_team}，查找其他队伍")
        
        # 筛选出敌方玩家（队伍不同的玩家）
        if is_cherry_mode and formatted_lookup:
            enemy_players = [
                player for player in all_players
                if player.get('summonerName') in formatted_lookup
            ]
        else:
            enemy_players = [
                player for player in all_players 
                if player.get('team', '') != my_team
            ]
        
        mode_suffix = " (CHERRY 模式 - 16人)" if is_cherry_mode else ""
        logger.debug(f"找到 {len(enemy_players)} 名敌方玩家{mode_suffix}")
        return enemy_players
        
    except Exception as e:
        logger.error(f"解析敌方玩家数据失败: {e}")
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
        logger.debug("❌ 无法获取游戏数据（游戏可能未开始）")
        return None
    
    try:
        all_players = game_data.get('allPlayers', [])
        active_player = game_data.get('activePlayer', {})
        game_mode = game_data.get('gameData', {}).get('gameMode', 'CLASSIC')
        
        # 检测游戏模式并确定最小玩家数
        is_cherry_mode = game_mode.upper() == 'CHERRY'
        min_players = 16 if is_cherry_mode else 10
        
        if len(all_players) < min_players:
            logger.warning(f"⚠️ 玩家数据不完整，当前只有 {len(all_players)} 人（{game_mode} 模式需要至少 {min_players} 人）")
            return None
        
        if is_cherry_mode:
            logger.info("🍒 检测到斗魂竞技场模式 (CHERRY)，8个队伍每队2人，共16人")
        
        # 获取当前玩家的召唤师名和队伍
        my_summoner_name = active_player.get('summonerName', '')
        my_team_side = None
        
        # 从 allPlayers 中找到当前玩家，确定队伍
        for player in all_players:
            if player.get('summonerName') == my_summoner_name:
                my_team_side = player.get('team', '')
                break
        
        if not my_team_side:
            logger.warning("⚠️ 无法确定当前玩家的队伍")
            return None
        
        logger.debug(f"🎮 当前玩家队伍: {my_team_side} (模式: {game_mode})")
        
        snapshot = format_game_data(game_data)
        formatted_teammates = snapshot.get('teammates', []) if isinstance(snapshot, dict) else []
        formatted_enemies = snapshot.get('enemies', []) if isinstance(snapshot, dict) else []
        active_player_team = snapshot.get('activePlayerTeam', my_team_side)
        active_player_subteam = snapshot.get('activePlayerSubteam')

        my_team_side = active_player_team or my_team_side

        formatted_lookup = {
            entry.get('summonerName'): entry
            for entry in (formatted_teammates + formatted_enemies)
            if isinstance(entry, dict)
        }

        use_subteams = (
            is_cherry_mode
            and active_player_subteam not in (None, -1)
            and formatted_enemies
        )

        if is_cherry_mode:
            subteam_counts = {}
            for entry in formatted_lookup.values():
                sub_id = entry.get('subteamId')
                if sub_id in (None, -1):
                    continue
                subteam_counts[sub_id] = subteam_counts.get(sub_id, 0) + 1
            if not formatted_enemies:
                logger.warning("⚠️ CHERRY 子队分类失败，尝试使用传统队伍字段作为回退逻辑")

            if subteam_counts:
                formatted_counts = ", ".join(
                    [f"S{sub_id}:{count}" for sub_id, count in sorted(subteam_counts.items())]
                )
                logger.debug(f"🍒 子队统计: {formatted_counts}")

        teammate_list = []
        enemy_list = []

        def build_player_info(entry, default_team):
            summoner_name = entry.get('summonerName', '未知')
            raw_game_name = entry.get('gameName')
            raw_tag = entry.get('tagLine')

            if raw_game_name and raw_tag:
                game_name = raw_game_name
                tag_line = raw_tag
            elif '#' in summoner_name:
                parts = summoner_name.split('#', 1)
                game_name = parts[0]
                tag_line = parts[1] if len(parts) > 1 else 'NA'
            else:
                game_name = summoner_name
                tag_line = 'NA'

            puuid = get_puuid(token, port, summoner_name)
            champion = (
                entry.get('champion')
                or entry.get('championName')
                or entry.get('championRaw')
                or '未知'
            )
            team_label = entry.get('team') or default_team or 'UNKNOWN'
            subteam_id = entry.get('subteamId')

            return {
                'summonerName': summoner_name,
                'gameName': game_name,
                'tagLine': tag_line,
                'puuid': puuid,
                'championName': champion,
                'level': entry.get('level', 0),
                'team': team_label,
                'subteamId': subteam_id
            }

        if formatted_teammates or formatted_enemies:
            for entry in formatted_teammates:
                info = build_player_info(entry, my_team_side)
                teammate_list.append(info)
                team_desc = (
                    f"小队 {info['subteamId']}"
                    if use_subteams and info.get('subteamId') not in (None, -1)
                    else info['team']
                )
                logger.debug(f"👥 队友: {info['summonerName']} ({info['championName']}) [队伍: {team_desc}]")

            for entry in formatted_enemies:
                info = build_player_info(entry, None)
                enemy_list.append(info)
                team_desc = (
                    f"小队 {info['subteamId']}"
                    if info.get('subteamId') not in (None, -1)
                    else info['team']
                )
                logger.debug(f"💥 敌人: {info['summonerName']} ({info['championName']}) [队伍: {team_desc}]")

        if is_cherry_mode and not enemy_list:
            logger.warning("⚠️ 使用回退逻辑重新分类 CHERRY 模式玩家")
            for player in all_players:
                summoner_name = player.get('summonerName', '未知')
                player_team = player.get('team', '')
                formatted_entry = formatted_lookup.get(summoner_name, {})

                merged_entry = {
                    'summonerName': summoner_name,
                    'gameName': formatted_entry.get('gameName'),
                    'tagLine': formatted_entry.get('tagLine'),
                    'champion': formatted_entry.get('champion') or player.get('championName'),
                    'level': formatted_entry.get('level') or player.get('level', 0),
                    'team': formatted_entry.get('team') or player_team,
                    'subteamId': formatted_entry.get('subteamId')
                }

                info = build_player_info(merged_entry, player_team)

                if player_team == my_team_side:
                    teammate_list.append(info)
                    team_desc = (
                        f"小队 {info['subteamId']}"
                        if info.get('subteamId') not in (None, -1)
                        else info['team']
                    )
                    logger.debug(f"👥 队友: {info['summonerName']} ({info['championName']}) [队伍: {team_desc}]")
                else:
                    enemy_list.append(info)
                    team_desc = (
                        f"小队 {info['subteamId']}"
                        if info.get('subteamId') not in (None, -1)
                        else info['team']
                    )
                    logger.debug(f"💥 敌人: {info['summonerName']} ({info['championName']}) [队伍: {team_desc}]")
        
        mode_info = f"({game_mode})" if is_cherry_mode else f"({my_team_side})"
        logger.info(f"✅ 成功获取 {len(teammate_list)} 名队友和 {len(enemy_list)} 名敌人 {mode_info}")
        
        return {
            'teammates': teammate_list,
            'enemies': enemy_list
        }
        
    except Exception as e:
        logger.error(f"❌ 解析玩家数据失败: {e}")
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
        logger.warning("❌ 无法获取敌方玩家信息（可能游戏未开始）")
        return []
    
    enemy_stats = []
    
    for player in enemy_players:
        summoner_name = player.get('summonerName', '未知')
        logger.debug(f"正在查询敌方玩家: {summoner_name}")
        
        # 步骤1: 获取PUUID（前端可以用来查询战绩）
        puuid = get_puuid(token, port, summoner_name)
        if not puuid:
            logger.warning(f"  ⚠️ 无法获取 {summoner_name} 的PUUID")
            enemy_stats.append({
                'summonerName': summoner_name,
                'puuid': None,
                'championId': player.get('championName', '未知'),
                'level': player.get('level', 0),
                'error': '无法获取PUUID'
            })
            continue
        
        logger.debug(f"  ✅ PUUID: {puuid[:20]}...")
        
        # 返回基本信息，战绩由前端异步查询（避免后端阻塞）
        enemy_stats.append({
            'summonerName': summoner_name,
            'puuid': puuid,
            'championId': player.get('championName', '未知'),
            'level': player.get('level', 0)
        })
    
    return enemy_stats
