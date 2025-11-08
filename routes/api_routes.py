"""
API路由模块
处理HTTP请求
"""
from flask import Blueprint, render_template, jsonify, request
from config import app_state
import constants
from core import lcu
from core.lcu.enrichment import enrich_game_with_augments
from utils.game_data_formatter import format_game_data
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# OP.GG integration has been removed from this build.
OPGG_AVAILABLE = False

# 创建蓝图
api_bp = Blueprint('api', __name__)

# 向后兼容的别名
api = api_bp


@api_bp.route('/')
def index():
    """渲染主页面"""
    return render_template('index.html')


@api_bp.route('/summoner/<path:summoner_name>')
def summoner_detail(summoner_name):
    """
    渲染召唤师详细战绩页面
    
    Args:
        summoner_name: 召唤师名称 (格式: 名称#TAG)
    
    Returns:
        HTML: 详细战绩页面
    """
    import urllib.parse
    
    # URL 解码召唤师名称
    decoded_summoner_name = urllib.parse.unquote(summoner_name)
    
    # allow optional puuid query param to bypass name->puuid lookup in the client
    puuid = request.args.get('puuid')
    
    # 获取召唤师头像 ID、等级和段位信息
    profile_icon_id = 29  # 默认头像
    summoner_level = 0  # 默认等级
    ranked_solo_tier = ""  # 单排段位
    ranked_solo_rank = ""  # 单排小段位
    ranked_solo_lp = 0  # 单排胜点
    ranked_flex_tier = ""  # 灵活组排段位
    ranked_flex_rank = ""  # 灵活组排小段位
    ranked_flex_lp = 0  # 灵活组排胜点
    ranked_solo_summary = None
    ranked_flex_summary = None

    SOLO_QUEUE_TYPES = {
        "RANKED_SOLO_5X5",
        "RANKED_SOLO",
        "SOLO",
    }
    FLEX_QUEUE_TYPES = {
        "RANKED_FLEX_SR",
        "RANKED_FLEX",
        "FLEX",
        "RANKED_FLEX_5X5",
    }

    def _safe_int(value):
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def _summarize_queue(queue: dict | None, label: str):
        if not isinstance(queue, dict):
            return None

        tier_raw = queue.get('tier') or queue.get('tierName') or queue.get('tierNameShort') or ""
        tier = str(tier_raw).strip().upper()
        if tier in {"NA", "NONE", "UNRANKED", "N/A"}:
            tier = ""

        division_raw = queue.get('division') or queue.get('divisionName') or queue.get('rank') or ""
        division = str(division_raw).strip().upper()
        if division in {"NA", "NONE", "UNRANKED", "UNSPECIFIED", "N/A"}:
            division = ""

        lp_candidates = [
            queue.get('leaguePoints'),
            queue.get('leaguePointsEarned'),
            queue.get('lp'),
            queue.get('league_points'),
        ]
        lp_val = next((val for val in lp_candidates if val is not None), 0)
        lp = _safe_int(lp_val)
        if lp is None:
            lp = 0

        wins = _safe_int(queue.get('wins'))
        losses = _safe_int(queue.get('losses'))

        queue_type = queue.get('queueType') or queue.get('queue') or queue.get('type') or ""

        return {
            "label": label,
            "tier": tier,
            "division": division,
            "lp": lp,
            "wins": wins,
            "losses": losses,
            "queueType": str(queue_type).upper(),
            "leagueName": queue.get('leagueName') or queue.get('leagueId') or "",
        }

    if app_state.is_lcu_connected():
        token = app_state.lcu_credentials["auth_token"]
        port = app_state.lcu_credentials["app_port"]

        summoner_data = None
        if puuid:
            summoner_data = lcu.get_summoner_by_puuid(token, port, puuid)
        else:
            summoner_data = lcu.get_summoner_by_name(token, port, decoded_summoner_name)

        if summoner_data:
            profile_icon_id = summoner_data.get('profileIconId', 29)
            summoner_level = summoner_data.get('summonerLevel', 0)
            if not puuid:
                puuid = summoner_data.get('puuid') or puuid

            summoner_id = summoner_data.get('id') or summoner_data.get('summonerId')
            ranked_stats = {}
            if summoner_id or puuid:
                ranked_stats = lcu.get_ranked_stats(
                    token,
                    port,
                    summoner_id=summoner_id,
                    puuid=puuid
                ) or {}

            if isinstance(ranked_stats, dict):
                queues = ranked_stats.get('queues', [])
                if isinstance(queues, list):
                    solo_queue = None
                    flex_queue = None
                    for queue in queues:
                        queue_type = str(queue.get('queueType') or queue.get('queue') or queue.get('type') or "").upper()
                        if not solo_queue and queue_type in SOLO_QUEUE_TYPES:
                            solo_queue = queue
                        elif not flex_queue and queue_type in FLEX_QUEUE_TYPES:
                            flex_queue = queue

                    ranked_solo_summary = _summarize_queue(solo_queue, "单双排 (Solo/Duo)")
                    ranked_flex_summary = _summarize_queue(flex_queue, "灵活排位 (Flex)")

                    if ranked_solo_summary:
                        ranked_solo_tier = ranked_solo_summary.get('tier', '')
                        ranked_solo_rank = ranked_solo_summary.get('division', '')
                        ranked_solo_lp = ranked_solo_summary.get('lp', 0)

                    if ranked_flex_summary:
                        ranked_flex_tier = ranked_flex_summary.get('tier', '')
                        ranked_flex_rank = ranked_flex_summary.get('division', '')
                        ranked_flex_lp = ranked_flex_summary.get('lp', 0)
    
    # pass champion map so templates can resolve championId -> champion key for ddragon
    return render_template(
        'summoner_detail.html', 
        summoner_name=decoded_summoner_name,
        champion_map=constants._get_champion_map(), 
        puuid=puuid,
        profile_icon_id=profile_icon_id,
        summoner_level=summoner_level,
        ranked_solo_tier=ranked_solo_tier,
        ranked_solo_rank=ranked_solo_rank,
        ranked_solo_lp=ranked_solo_lp,
        ranked_flex_tier=ranked_flex_tier,
        ranked_flex_rank=ranked_flex_rank,
        ranked_flex_lp=ranked_flex_lp,
        ranked_solo_summary=ranked_solo_summary,
        ranked_flex_summary=ranked_flex_summary
    )


@api_bp.route('/tft_summoner/<path:summoner_name>')
def tft_summoner_detail(summoner_name):
    """
    渲染 TFT 专用的召唤师战绩页面
    """
    import urllib.parse
    
    # URL 解码召唤师名称
    decoded_summoner_name = urllib.parse.unquote(summoner_name)
    
    puuid = request.args.get('puuid')
    
    # 获取召唤师头像 ID
    profile_icon_id = 29  # 默认头像
    if app_state.is_lcu_connected():
        token = app_state.lcu_credentials["auth_token"]
        port = app_state.lcu_credentials["app_port"]
        if puuid:
            summoner_data = lcu.get_summoner_by_puuid(token, port, puuid)
            if summoner_data:
                profile_icon_id = summoner_data.get('profileIconId', 29)
        else:
            # 如果没有 puuid，尝试通过名称获取（使用解码后的名称）
            s_data = lcu.get_summoner_by_name(token, port, decoded_summoner_name)
            if s_data:
                profile_icon_id = s_data.get('profileIconId', 29)
                # 同时获取 puuid 用于后续查询
                puuid = s_data.get('puuid')

    return render_template(
        'tft_summoner.html', 
        summoner_name=decoded_summoner_name,  # 传递解码后的名称给模板
        puuid=puuid,
        profile_icon_id=profile_icon_id
    )


@api_bp.route('/match/<path:summoner_name>/<int:game_index>')
def match_detail_page(summoner_name, game_index):
    """
    渲染单场对局详情页面
    
    支持两种访问方式：
    1. /match/召唤师名/索引 - 通过战绩列表索引访问
    2. /match/召唤师名/索引?match_id=xxx - 通过对局ID直接访问（更快）
    """
    # 获取可选的 match_id 参数（如果提供，可以直接查询对局，无需先查战绩）
    match_id = request.args.get('match_id')
    
    # pass champion map so the template can resolve championId -> champion key
    return render_template(
        'match_detail.html', 
        summoner_name=summoner_name, 
        game_index=game_index, 
        match_id=match_id,
        champion_map=constants._get_champion_map()
    )


@api_bp.route('/live_game')
def live_game():
    """
    渲染实时游戏监控页面
    
    Returns:
        HTML: 实时游戏详情页面
    """
    return render_template('live_game.html')





@api_bp.route('/get_history', methods=['GET'])
def get_history():
    """
    获取指定召唤师的战绩
    
    查询参数:
        name: 召唤师名称 (格式: 名称#TAG)
        puuid: 或直接使用 puuid
        count: 每页数量 (默认20，最大200)
        page: 页码 (默认1，表示第1-20场；page=2表示第21-40场)
    
    Returns:
        JSON: 包含战绩数据的响应
    """
    # support either name OR puuid to speed up lookups from client
    summoner_name = request.args.get('name')
    puuid = request.args.get('puuid')

    if not summoner_name and not puuid:
        return jsonify({
            "success": False,
            "message": "请求缺少召唤师名称 (name) 或 puuid 查询参数"
        })

    if not app_state.is_lcu_connected():
        return jsonify({
            "success": False,
            "message": "未连接到客户端"
        })

    # 获取PUUID（若客户端未直接提供）
    token = app_state.lcu_credentials["auth_token"]
    port = app_state.lcu_credentials["app_port"]
    if not puuid:
        puuid = lcu.get_puuid(token, port, summoner_name)
        if not puuid:
            return jsonify({
                "success": False,
                "message": f"找不到召唤师 '{summoner_name}' 或 LCU API 失败"
            })

    # 🚀 优化：默认只查询 20 场，支持分页查询
    count = request.args.get('count', 20, type=int)  # 每页数量
    count = min(max(count, 1), 200)  # 限制在1-200之间
    
    page = request.args.get('page', 1, type=int)  # 页码，从1开始
    page = max(page, 1)  # 确保页码至少为1
    
    # 计算beginIndex: page=1 -> beginIndex=0; page=2 -> beginIndex=20
    begin_index = (page - 1) * count
    
    # 获取战绩
    history = lcu.get_match_history(token, port, puuid, count=count, begin_index=begin_index)
    if not history:
        return jsonify({
            "success": False,
            "message": "获取战绩失败"
        })
    
    # 处理数据
    processed_games = _process_lol_match_history(history, puuid)
    
    # OP.GG integration removed: processed_games contains core match info only.
    
    return jsonify({
        "success": True, 
        "games": processed_games,
        "page": page,
        "count": count
    })


@api_bp.route('/get_tft_history', methods=['GET'])
def get_tft_history():
    """
    获取指定召唤师的 TFT 战绩（调用 LCU 的 TFT 产品端点）

    查询参数:
        name: 召唤师名称 (格式: 名称#TAG) 或
        puuid: 直接使用 puuid
        count: 可选，查询数量（默认20）
    """
    summoner_name = request.args.get('name')
    puuid = request.args.get('puuid')

    if not summoner_name and not puuid:
        return jsonify({
            "success": False,
            "message": "请求缺少召唤师名称 (name) 或 puuid 查询参数"
        })

    if not app_state.is_lcu_connected():
        return jsonify({
            "success": False,
            "message": "未连接到客户端"
        })

    token = app_state.lcu_credentials["auth_token"]
    port = app_state.lcu_credentials["app_port"]
    if not puuid:
        puuid = lcu.get_puuid(token, port, summoner_name)
        if not puuid:
            return jsonify({
                "success": False,
                "message": f"找不到召唤师 '{summoner_name}' 或 LCU API 失败"
            })

    count = request.args.get('count', 20, type=int)
    count = min(max(count, 1), 200)

    history = lcu.get_tft_match_history(token, port, puuid, count=count)
    if not history:
        return jsonify({
            "success": False,
            "message": "获取 TFT 战绩失败"
        })

    # 只返回摘要字段供前端快速显示，不返回完整游戏数据
    games = history.get('games', {}).get('games', [])[:20]
    
    # 为每场比赛提取摘要字段
    summary_games = []
    for idx, game in enumerate(games):
        # 只添加摘要字段（快速显示在卡片上）
        summary = _process_single_tft_game(game, puuid)
        summary['match_index'] = idx
        
        summary_games.append(summary)

    return jsonify({
        "success": True,
        "games": summary_games
    })


@api_bp.route('/get_match', methods=['GET'])
def get_match():
    """
    返回指定召唤师历史列表中某一场的完整对局信息（包含所有参赛者）
    
    支持 LOL 和 TFT 两种游戏类型

    查询参数:
        name: 召唤师名称 (格式: 名称#TAG)
        index: 在 /get_history 返回的 games 列表中的索引 (整数，0 表示最近一场)
        match_id: 对局 ID（可选，直接通过对局ID查询）
        is_tft: 是否为 TFT 对局（true/false）
    """
    summoner_name = request.args.get('name')
    index = request.args.get('index', type=int)
    match_id = request.args.get('match_id')
    is_tft = request.args.get('is_tft', 'false').lower() == 'true'

    if not app_state.is_lcu_connected():
        return jsonify({"success": False, "message": "未连接到客户端"}), 400

    token = app_state.lcu_credentials["auth_token"]
    port = app_state.lcu_credentials["app_port"]

    # 如果有 match_id，直接通过 match_id 查询（仅支持 LOL）
    if match_id:
        match_obj = lcu.get_match_by_id(token, port, match_id)
        if match_obj:
            game = match_obj.get('game') if (isinstance(match_obj, dict) and 'game' in match_obj) else match_obj
            try:
                lcu.enrich_game_with_summoner_info(token, port, game)
                enrich_game_with_augments(game)  # 添加 augment 图标 URL
            except Exception as e:
                print(f"召唤师信息补全失败 (match_id path): {e}")
            return jsonify({"success": True, "game": game})
        else:
            return jsonify({"success": False, "message": "通过 match_id 获取对局失败"}), 404

    if not summoner_name or index is None:
        return jsonify({"success": False, "message": "缺少参数 name 或 index"}), 400

    puuid = lcu.get_puuid(token, port, summoner_name)
    if not puuid:
        return jsonify({"success": False, "message": f"找不到召唤师 '{summoner_name}' 或 LCU API 失败"}), 404

    if is_tft:
        # TFT 战绩查询
        fetch_count = min(index + 20, 200)
        history = lcu.get_tft_match_history(token, port, puuid, count=fetch_count)
        if not history:
            return jsonify({"success": False, "message": "获取 TFT 战绩失败"}), 500

        games = history.get('games', {}).get('games', [])
        if index < 0 or index >= len(games):
            return jsonify({"success": False, "message": "索引越界"}), 400

        game_summary = games[index]
        
        # TFT 的 match_id 通常在 metadata.match_id 中
        metadata = game_summary.get('metadata', {})
        game_match_id = metadata.get('match_id') if isinstance(metadata, dict) else None
        
        # 如果 metadata 中没有，尝试从顶层获取
        if not game_match_id:
            game_match_id = game_summary.get('matchId') or game_summary.get('gameId') or game_summary.get('match_id')
        
        if game_match_id:
            # 通过 match_id 获取完整 TFT 对局数据（包含所有8名玩家的完整信息）
            print(f"🔍 [TFT] 通过 match_id={game_match_id} 获取完整对局详情")
            full_game = lcu.get_match_by_id(token, port, game_match_id)
            if full_game:
                # 有些端点返回 {'game': {...}}，有些直接返回 game 对象
                game = full_game.get('game') if (isinstance(full_game, dict) and 'game' in full_game) else full_game
                if isinstance(game, dict):
                    # TFT 参与者在 json.participants 中
                    game_json = game.get('json', game)
                    participants = game_json.get('participants', []) if isinstance(game_json, dict) else []
                    participants_count = len(participants)
                    print(f"✅ [TFT] 获取到完整对局数据，参与者数量: {participants_count}")
            else:
                # 如果通过 match_id 获取失败，降级使用 history 中的数据
                print("⚠️ [TFT] 通过 match_id 获取失败，使用历史记录中的数据")
                game = game_summary
        else:
            # 如果没有 match_id，使用 history 中的数据
            print("⚠️ [TFT] 无 match_id，使用历史记录中的数据")
            game = game_summary
        
        # 尝试使用 LCU API 补全 TFT 参与者的召唤师信息（如果返回数据缺失）
        try:
            # 在 enrichment 之前打印数据结构样本
            game_json = game.get('json', game) if isinstance(game, dict) else {}
            participants = game_json.get('participants', []) if isinstance(game_json, dict) else []
            if participants and len(participants) > 0:
                print(f"🔍 [TFT] enrichment 前第一个参与者数据样本: {list(participants[0].keys())}")
            
            lcu.enrich_tft_game_with_summoner_info(token, port, game)
            
            # enrichment 后再次检查
            game_json = game.get('json', game) if isinstance(game, dict) else {}
            participants = game_json.get('participants', []) if isinstance(game_json, dict) else []
            if participants and len(participants) > 0:
                print(f"✅ [TFT] enrichment 后第一个参与者数据: summonerName={participants[0].get('summonerName')}, units={len(participants[0].get('units', []))}")
            print("✅ [TFT] 召唤师信息补全完成")
        except Exception as e:
            # enrichment 是 best-effort，不应阻塞主响应
            print(f"⚠️ [TFT] 召唤师信息补全失败: {e}")
            import traceback
            traceback.print_exc()
        # 额外尝试：对仍然缺少头像的参与者，使用 puuid 调用 LCU /lol-summoner 接口获取 profileIcon
        try:
            game_json = game.get('json', game) if isinstance(game, dict) else {}
            participants = game_json.get('participants', []) if isinstance(game_json, dict) else []
            
            # 统计头像填充情况
            participants_with_icons = sum(1 for p in participants if p.get('profileIcon') or p.get('profileIconId'))
            print(f"🔍 [TFT] 当前 {participants_with_icons}/{len(participants)} 个参与者有头像")
            
            for idx, p in enumerate(participants):
                try:
                    # 如果已经有头像则跳过
                    if p.get('profileIcon') or p.get('profileIconId'):
                        continue

                    summoner_name = p.get('summonerName') or f"Player{idx+1}"
                    print(f"🔍 [TFT] 尝试为 {summoner_name} 获取头像...")

                    puuid = p.get('puuid') or (p.get('player') or {}).get('puuid')
                    if not puuid:
                        # 备用：participantIdentities 中寻找
                        pid = p.get('participantId')
                        if pid:
                            idents = {ident.get('participantId'): ident.get('player') for ident in (game_json.get('participantIdentities') or [])}
                            player = idents.get(pid) or {}
                            puuid = player.get('puuid')

                    info = None
                    # 方法1: 通过 puuid 查询
                    if puuid:
                        print(f"  📞 使用 puuid 查询: {puuid[:8]}...")
                        info = lcu.get_summoner_by_puuid(token, port, puuid)
                        if info:
                            print("  ✅ puuid 查询成功")
                        else:
                            print("  ❌ puuid 查询失败")
                    
                    # 方法2: 如果 puuid 查询失败，尝试通过名称查询
                    if not info and summoner_name and summoner_name != f"Player{idx+1}":
                        print(f"  📞 使用名称查询: {summoner_name}")
                        info = lcu.get_summoner_by_name(token, port, summoner_name)
                        if info:
                            print("  ✅ 名称查询成功")
                        else:
                            print("  ❌ 名称查询失败")

                    # 填充头像信息
                    if info and isinstance(info, dict):
                        if 'profileIconId' in info and info.get('profileIconId') is not None:
                            p['profileIcon'] = info.get('profileIconId')
                            print(f"  ✅ 设置头像 ID: {p['profileIcon']}")
                        elif 'profileIcon' in info and info.get('profileIcon') is not None:
                            p['profileIcon'] = info.get('profileIcon')
                            print(f"  ✅ 设置头像 ID: {p['profileIcon']}")
                        else:
                            print("  ⚠️ 查询成功但无头像字段")
                    else:
                        print(f"  ❌ 无法获取 {summoner_name} 的头像")
                        
                except Exception as inner_e:
                    print(f"  💥 处理参与者 {idx} 失败: {inner_e}")
                    continue
                    
            # 最终统计
            participants_with_icons_final = sum(1 for p in participants if p.get('profileIcon') or p.get('profileIconId'))
            print(f"✅ [TFT] 最终 {participants_with_icons_final}/{len(participants)} 个参与者有头像")
            
        except Exception as e:
            print(f"⚠️ [TFT] 批量头像查询失败: {e}")
            pass
        
        return jsonify({"success": True, "game": game})
    else:
        # LOL 战绩查询
        fetch_count = min(index + 20, 200)
        history = lcu.get_match_history(token, port, puuid, count=fetch_count)
        if not history:
            return jsonify({"success": False, "message": "获取战绩失败"}), 500

        games = history.get('games', {}).get('games', [])
        if index < 0 or index >= len(games):
            return jsonify({"success": False, "message": "索引越界"}), 400

        game_summary = games[index]
        
        # 尝试从 game_summary 中获取 match_id，然后通过 match_id 获取完整对局数据
        game_match_id = game_summary.get('matchId') or game_summary.get('gameId') or game_summary.get('match_id')
        
        if game_match_id:
            # 通过 match_id 获取完整对局数据（包含所有10名玩家）
            print(f"🔍 通过 match_id={game_match_id} 获取完整对局详情")
            full_game = lcu.get_match_by_id(token, port, game_match_id)
            if full_game:
                # 有些端点返回 {'game': {...}}，有些直接返回 game 对象
                game = full_game.get('game') if (isinstance(full_game, dict) and 'game' in full_game) else full_game
                if isinstance(game, dict):
                    participants_count = len(game.get('participants', []))
                    print(f"✅ 获取到完整对局数据，参与者数量: {participants_count}")
            else:
                # 如果通过 match_id 获取失败，降级使用 history 中的数据
                print("⚠️ 通过 match_id 获取失败，使用历史记录中的数据")
                game = game_summary
        else:
            # 如果没有 match_id，使用 history 中的数据
            print("⚠️ 无 match_id，使用历史记录中的数据")
            game = game_summary

        # 尝试使用 LCU API 补全参与者的召唤师名和头像（如果返回数据缺失）
        try:
            lcu.enrich_game_with_summoner_info(token, port, game)
            enrich_game_with_augments(game)  # 添加 augment 图标 URL
        except Exception as e:
            # enrichment 是 best-effort，不应阻塞主响应
            print(f"召唤师信息补全失败: {e}")

        # 返回完整对局对象（尽量保持原始结构，前端负责格式化展示）
        return jsonify({"success": True, "game": game})


# OP.GG helper removed.


@api_bp.route('/get_live_game_data', methods=['GET'])
def get_live_game_data():
    """
    获取实时游戏数据（从游戏API 2999端口）
    
    Returns:
        JSON: 格式化后的游戏数据（队友、敌人、游戏信息等）
    """
    try:
        # 尝试连接游戏客户端API（端口2999，减少timeout）
        response = requests.get('https://127.0.0.1:2999/liveclientdata/allgamedata', 
                               verify=False, timeout=2)
        
        if response.status_code == 200:
            all_game_data = response.json()
            formatted_data = format_game_data(all_game_data)
            
            # OP.GG integration removed: returning formatted game data without external stats.
            
            return jsonify({
                "success": True,
                "inGame": True,
                "data": formatted_data
            })
        else:
            return jsonify({
                "success": False,
                "inGame": False,
                "message": "无法连接到游戏客户端"
            })
            
    except requests.exceptions.RequestException:
        return jsonify({
            "success": False,
            "inGame": False,
            "message": "未在游戏中或游戏API不可用"
        })


def _process_single_tft_game(game, puuid=None):
    """
    从单个 TFT 游戏对象中提取摘要字段（用于卡片快速显示）
    不修改原始游戏数据，只添加快速显示需要的摘要字段
    
    Args:
        game: 单个游戏对象
        puuid: 召唤师 PUUID（用于匹配玩家数据）
    
    Returns:
        dict: 包含摘要字段的字典，这些字段会合并到原始游戏对象中
    """
    if not isinstance(game, dict):
        return {}
    
    # TFT 数据在 json 字段中
    game_json = game.get('json')
    if not isinstance(game_json, dict):
        game_json = game
    
    metadata = game.get('metadata', {})
    
    # 定位玩家数据（用户的数据）
    participant = None
    participants_data = game_json.get('participants') if isinstance(game_json, dict) else None
    participants_list = participants_data if isinstance(participants_data, list) else []
    
    # 从 participants 中找到用户的数据
    if isinstance(participants_list, list) and len(participants_list) > 0:
        if puuid:
            for p in participants_list:
                if not isinstance(p, dict):
                    continue
                if p.get('puuid') == puuid:
                    participant = p
                    break
        
        # 如果没找到则用第一个（通常是查询用户）
        if participant is None:
            participant = participants_list[0] if len(participants_list) > 0 else None
    
    # 提取摘要字段
    summary = {}
    
    # 胜负标志（placement == 1 为赢）
    win_flag = False
    if isinstance(participant, dict):
        placement = participant.get('placement')
        if placement is not None:
            try:
                win_flag = int(placement) == 1
            except Exception:
                pass
    summary['win'] = win_flag
    
    # 排名
    placement = 8  # 默认值
    if isinstance(participant, dict):
        p = participant.get('placement')
        if p is not None:
            try:
                placement = int(p)
            except Exception:
                pass
    summary['placement'] = placement
    
    # 最后一轮
    last_round = 0
    if isinstance(participant, dict):
        lr = participant.get('last_round')
        if lr is not None:
            try:
                last_round = int(lr)
            except Exception:
                pass
    summary['last_round'] = last_round
    
    # 玩家等级
    level = 0
    if isinstance(participant, dict):
        lv = participant.get('level')
        if lv is not None:
            try:
                level = int(lv)
            except Exception:
                pass
    summary['level'] = level
    
    # 总伤害
    total_damage = 0
    if isinstance(participant, dict):
        dmg = participant.get('total_damage_to_players')
        if dmg is not None:
            try:
                total_damage = int(dmg)
            except Exception:
                pass
    summary['total_damage'] = total_damage
    
    # 剩余金币
    gold_left = 0
    if isinstance(participant, dict):
        gold = participant.get('gold_left')
        if gold is not None:
            try:
                gold_left = int(gold)
            except Exception:
                pass
    summary['gold_left'] = gold_left
    
    # 提取最高 Style 的 Traits（Style >= 2）
    top_traits = []
    if isinstance(participant, dict):
        traits = participant.get('traits', [])
        if isinstance(traits, list):
            # 过滤 style >= 2 的 traits
            high_style_traits = [t for t in traits if isinstance(t, dict) and t.get('style', 0) >= 2]
            # 按 style 降序排序
            high_style_traits.sort(key=lambda t: t.get('style', 0), reverse=True)
            # 取前 3 个
            for trait in high_style_traits[:3]:
                if isinstance(trait, dict):
                    name = trait.get('name', 'Unknown')
                    num_units = trait.get('num_units', 0)
                    style = trait.get('style', 0)
                    top_traits.append({
                        'name': name,
                        'num_units': num_units,
                        'style': style
                    })
    summary['top_traits'] = top_traits
    
    # 游戏模式
    game_mode = (game_json.get('gameMode') or game_json.get('tft_game_type') or 'UNKNOWN') if isinstance(game_json, dict) else 'UNKNOWN'
    summary['gameMode'] = game_mode
    summary['mode'] = _format_game_mode(game_mode)
    
    # 时间差（使用 gameCreation）
    game_creation = (game_json.get('gameCreation', 0) if isinstance(game_json, dict) else 0)
    summary['time_ago'] = _calculate_time_ago(game_creation)
    summary['game_creation'] = game_creation
    
    # 对局时长
    game_length = (game_json.get('game_length', 0) if isinstance(game_json, dict) else 0)
    summary['duration'] = int(game_length) if game_length else 0
    
    # Match ID
    match_id = metadata.get('match_id') if isinstance(metadata, dict) else None
    summary['match_id'] = match_id
    
    return summary


def _process_lol_match_history(history, puuid=None):
    """
    处理 LOL 战绩数据，提取关键信息
    
    Args:
        history: LCU API返回的原始战绩数据
        puuid: 召唤师 PUUID
    
    Returns:
        list: 处理后的战绩列表
    """
    processed_games = []
    # 不再限制为前20场，因为分页已经在API层面处理
    games = history.get('games', {}).get('games', [])

    for idx, game in enumerate(games):
        summary = _process_single_lol_game(game, puuid)
        summary['match_index'] = idx
        processed_games.append(summary)
    
    return processed_games


def _process_single_lol_game(game, puuid=None):
    """
    从单个 LOL 游戏对象中提取摘要字段（用于卡片快速显示）
    
    Args:
        game: 单个游戏对象
        puuid: 召唤师 PUUID（用于匹配玩家数据）
    
    Returns:
        dict: 包含摘要字段的字典
    """
    if not isinstance(game, dict):
        return {}
    
    summary = {}
    
    # 获取参与者列表
    participants = game.get('participants', [])
    if not isinstance(participants, list):
        participants = []
    
    # 查找用户的参与者数据
    participant = None
    for p in participants:
        if not isinstance(p, dict):
            continue
        if puuid and p.get('puuid') == puuid:
            participant = p
            break
    
    # 如果没找到则用第一个（通常是查询用户）
    if participant is None and len(participants) > 0:
        participant = participants[0]
    
    # 提取胜负：从队伍信息中获取
    # LCU API 的 participant 可能没有 win 字段，需要通过 teamId 匹配队伍的胜负
    win = False
    if isinstance(participant, dict):
        # 先尝试从参与者直接获取
        participant_win = participant.get('win')
        if participant_win is not None:
            win = bool(participant_win)
        else:
            # 如果参与者没有 win 字段，从队伍信息中获取
            team_id = participant.get('teamId', 0)
            teams = game.get('teams', [])
            for team in teams:
                if team.get('teamId') == team_id:
                    team_win = team.get('win', 'Fail')
                    # team.win 可能是 "Win" 或 "Fail" 字符串，也可能是布尔值
                    if isinstance(team_win, str):
                        win = team_win == 'Win'
                    else:
                        win = bool(team_win)
                    break
    summary['win'] = win
    
    # 提取英雄名称
    champion_id = 0
    champion_en = "Unknown"
    if isinstance(participant, dict):
        champion_id = participant.get('championId', 0)
        champion_en = constants._get_champion_map().get(champion_id, f"Champion{champion_id}")
    summary['champion_id'] = champion_id
    summary['champion_en'] = champion_en
    
    # 提取 KDA
    kda = "0/0/0"
    if isinstance(participant, dict):
        stats = participant.get('stats', {})
        if isinstance(stats, dict):
            kills = stats.get('kills', 0)
            deaths = stats.get('deaths', 0)
            assists = stats.get('assists', 0)
            kda = f"{kills}/{deaths}/{assists}"
    summary['kda'] = kda
    
    # 提取金币
    gold = 0
    if isinstance(participant, dict):
        stats = participant.get('stats', {})
        if isinstance(stats, dict):
            gold_earned = stats.get('goldEarned', 0)
            try:
                gold = int(gold_earned / 1000)  # 转换为 k 格式（千）
            except Exception:
                gold = 0
    summary['gold'] = gold
    
    # 提取 CS
    cs = 0
    if isinstance(participant, dict):
        stats = participant.get('stats', {})
        if isinstance(stats, dict):
            minions = stats.get('totalMinionsKilled', 0)
            neutral = stats.get('neutralMinionsKilled', 0)
            try:
                cs = int(minions) + int(neutral)
            except Exception:
                cs = 0
    summary['cs'] = cs
    
    # 提取英雄等级
    champion_level = 0
    if isinstance(participant, dict):
        stats = participant.get('stats', {})
        if isinstance(stats, dict):
            champion_level = stats.get('champLevel', 0)
    summary['champion_level'] = champion_level
    
    # 游戏模式
    game_mode = game.get('gameMode', 'CLASSIC')
    summary['gameMode'] = game_mode
    summary['mode'] = _format_game_mode(game_mode)
    
    # CHERRY 模式的排名信息
    if game_mode == 'CHERRY' and isinstance(participant, dict):
        stats = participant.get('stats', {})
        if isinstance(stats, dict):
            # 尝试多个可能的字段名
            placement = (
                stats.get('subteamPlacement') or 
                stats.get('placement') or 
                participant.get('subteamPlacement') or 
                participant.get('placement') or 
                0
            )
            if placement:
                summary['placement'] = int(placement)
                summary['subteamPlacement'] = int(placement)
    
    # 时间差（使用 gameCreation）
    game_creation = game.get('gameCreation', 0)
    summary['time_ago'] = _calculate_time_ago(game_creation)
    summary['game_creation'] = game_creation
    
    # 对局时长（秒）
    game_length = game.get('gameDuration', 0)
    summary['duration'] = int(game_length) if game_length else 0
    
    # Match ID
    match_id = game.get('matchId', '')
    summary['match_id'] = match_id
    
    return summary


def _process_match_history(history, puuid=None):
    """
    处理战绩数据，提取关键信息（保持向后兼容）
    
    Args:
        history: LCU API返回的原始战绩数据
        puuid: 召唤师 PUUID
    
    Returns:
        list: 处理后的战绩列表
    """
    processed_games = []
    games = history.get('games', {}).get('games', [])[:20]

    for idx, game in enumerate(games):
        summary = _process_single_tft_game(game, puuid)
        summary['match_index'] = idx
        processed_games.append(summary)
    
    return processed_games


def _format_game_mode(mode):
    """格式化游戏模式名称"""
    mode_map = {
        'CLASSIC': '经典模式',
        'ARAM': '极地大乱斗',
        'KIWI': '海克斯大乱斗',
        'CHERRY': '斗魂竞技场',
        'URF': '无限火力',
        'ONEFORALL': '克隆模式',
        'NEXUSBLITZ': '激斗峡谷',
        'TUTORIAL': '教程',
        'PRACTICETOOL': '训练模式'
    }
    return mode_map.get(mode, mode)


def _calculate_time_ago(timestamp_ms):
    """计算时间差"""
    from datetime import datetime
    
    if not timestamp_ms:
        return '未知时间'
    
    game_time = datetime.fromtimestamp(timestamp_ms / 1000)
    now = datetime.now()
    diff = now - game_time
    
    if diff.days > 0:
        return f"{diff.days}天前"
    elif diff.seconds >= 3600:
        hours = diff.seconds // 3600
        return f"{hours}小时前"
    elif diff.seconds >= 60:
        minutes = diff.seconds // 60
        return f"{minutes}分钟前"
    else:
        return "刚刚"
