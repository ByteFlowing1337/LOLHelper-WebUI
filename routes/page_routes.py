"""
页面渲染路由模块
负责返回 HTML 页面
"""
from flask import Blueprint, render_template, request
from config import app_state
from constants import CHAMPION_MAP
from core import lcu
import urllib.parse

page_bp = Blueprint('pages', __name__)


@page_bp.route('/')
def index():
    """渲染主页面"""
    return render_template('index.html')


@page_bp.route('/summoner/<path:summoner_name>')
def summoner_detail(summoner_name):
    """
    渲染召唤师详细战绩页面
    
    Args:
        summoner_name: 召唤师名称 (格式: 名称#TAG)
    
    Returns:
        HTML: 详细战绩页面
    """
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
    
    if app_state.is_lcu_connected():
        token = app_state.lcu_credentials["auth_token"]
        port = app_state.lcu_credentials["app_port"]
        if puuid:
            summoner_data = lcu.get_summoner_by_puuid(token, port, puuid)
            if summoner_data:
                profile_icon_id = summoner_data.get('profileIconId', 29)
                summoner_level = summoner_data.get('summonerLevel', 0)
                # 获取段位信息
                summoner_id = summoner_data.get('id')
                if summoner_id:
                    ranked_stats = lcu.get_ranked_stats(token, port, summoner_id)
                    if ranked_stats and isinstance(ranked_stats, dict):
                        queues = ranked_stats.get('queues', [])
                        for queue in queues:
                            if queue.get('queueType') == 'RANKED_SOLO_5x5':
                                ranked_solo_tier = queue.get('tier', '')
                                ranked_solo_rank = queue.get('division', '')
                                ranked_solo_lp = queue.get('leaguePoints', 0)
                            elif queue.get('queueType') == 'RANKED_FLEX_SR':
                                ranked_flex_tier = queue.get('tier', '')
                                ranked_flex_rank = queue.get('division', '')
                                ranked_flex_lp = queue.get('leaguePoints', 0)
        else:
            # 如果没有 puuid，尝试通过名称获取（使用解码后的名称）
            s_data = lcu.get_summoner_by_name(token, port, decoded_summoner_name)
            if s_data:
                profile_icon_id = s_data.get('profileIconId', 29)
                summoner_level = s_data.get('summonerLevel', 0)
                # 同时获取 puuid 用于后续查询
                puuid = s_data.get('puuid')
                # 获取段位信息
                summoner_id = s_data.get('id')
                if summoner_id:
                    ranked_stats = lcu.get_ranked_stats(token, port, summoner_id)
                    if ranked_stats and isinstance(ranked_stats, dict):
                        queues = ranked_stats.get('queues', [])
                        for queue in queues:
                            if queue.get('queueType') == 'RANKED_SOLO_5x5':
                                ranked_solo_tier = queue.get('tier', '')
                                ranked_solo_rank = queue.get('division', '')
                                ranked_solo_lp = queue.get('leaguePoints', 0)
                            elif queue.get('queueType') == 'RANKED_FLEX_SR':
                                ranked_flex_tier = queue.get('tier', '')
                                ranked_flex_rank = queue.get('division', '')
                                ranked_flex_lp = queue.get('leaguePoints', 0)
    
    # pass champion map so templates can resolve championId -> champion key for ddragon
    return render_template(
        'summoner_detail.html', 
        summoner_name=decoded_summoner_name,
        champion_map=CHAMPION_MAP, 
        puuid=puuid,
        profile_icon_id=profile_icon_id,
        summoner_level=summoner_level,
        ranked_solo_tier=ranked_solo_tier,
        ranked_solo_rank=ranked_solo_rank,
        ranked_solo_lp=ranked_solo_lp,
        ranked_flex_tier=ranked_flex_tier,
        ranked_flex_rank=ranked_flex_rank,
        ranked_flex_lp=ranked_flex_lp
    )


@page_bp.route('/tft_summoner/<path:summoner_name>')
def tft_summoner_detail(summoner_name):
    """
    渲染 TFT 专用的召唤师战绩页面
    """
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


@page_bp.route('/match/<path:summoner_name>/<int:game_index>')
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
        champion_map=CHAMPION_MAP
    )


@page_bp.route('/live_game')
def live_game():
    """
    渲染实时游戏监控页面
    
    Returns:
        HTML: 实时游戏详情页面
    """
    return render_template('live_game.html')
