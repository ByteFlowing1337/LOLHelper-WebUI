"""
数据 API 路由模块
处理所有数据获取的 API 端点
"""
from flask import Blueprint, request, jsonify
import requests

from config import app_state
from core import lcu
from core.lcu.enrichment import enrich_game_with_augments
from utils.game_data_formatter import format_game_data
from .processors import process_lol_match_history, process_single_tft_game

# 创建数据 API 蓝图
data_bp = Blueprint('data', __name__)


@data_bp.route('/get_history', methods=['GET'])
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
    processed_games = process_lol_match_history(history, puuid)
    
    # OP.GG integration removed: processed_games contains core match info only.
    
    return jsonify({
        "success": True, 
        "games": processed_games,
        "page": page,
        "count": count
    })


@data_bp.route('/get_tft_history', methods=['GET'])
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
        summary = process_single_tft_game(game, puuid)
        summary['match_index'] = idx
        
        summary_games.append(summary)

    return jsonify({
        "success": True,
        "games": summary_games
    })


@data_bp.route('/get_summoner_rank', methods=['GET'])
def get_summoner_rank():
    """
    返回召唤师的头像、等级与段位信息（用于客户端在页面加载后异步获取）。

    查询参数：
        name: 召唤师名称（可选）
        puuid: PUUID（可选，优先）

    返回：
        { success: bool, profile_icon_id, summoner_level, ranked: { queues: [...] } }
    """
    summoner_name = request.args.get('name')
    puuid = request.args.get('puuid')

    if not summoner_name and not puuid:
        return jsonify({"success": False, "message": "缺少 name 或 puuid 参数"}), 400

    if not app_state.is_lcu_connected():
        return jsonify({"success": False, "message": "未连接到客户端"}), 400

    token = app_state.lcu_credentials["auth_token"]
    port = app_state.lcu_credentials["app_port"]

    # 获取基础召唤师信息
    summoner_data = None
    if puuid:
        summoner_data = lcu.get_summoner_by_puuid(token, port, puuid)
    else:
        summoner_data = lcu.get_summoner_by_name(token, port, summoner_name)

    if not summoner_data:
        return jsonify({"success": False, "message": "无法获取召唤师信息"}), 404

    profile_icon_id = summoner_data.get('profileIconId', 29)
    summoner_level = summoner_data.get('summonerLevel', 0)
    summoner_id = summoner_data.get('id')
    puuid = summoner_data.get('puuid') or puuid

    ranked = {}
    if summoner_id or puuid:
        ranked = lcu.get_ranked_stats(token, port, summoner_id=summoner_id, puuid=puuid) or {}

    return jsonify({
        "success": True,
        "profile_icon_id": profile_icon_id,
        "summoner_level": summoner_level,
        "ranked": ranked,
    })


@data_bp.route('/get_match', methods=['GET'])
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


@data_bp.route('/get_live_game_data', methods=['GET'])
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
