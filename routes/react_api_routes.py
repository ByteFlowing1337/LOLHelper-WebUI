"""
React 前端 REST API 适配层
"""
from flask import Blueprint, jsonify, request

from config import app_state
from core import lcu
from constants import CHAMPION_MAP
from routes.processors import process_lol_match_history, process_single_tft_game

react_api_bp = Blueprint('react_api', __name__, url_prefix='/api')


def _require_lcu_connected():
  if not app_state.is_lcu_connected():
    return jsonify({'success': False, 'error': '未连接到客户端'}), 503
  return None


@react_api_bp.route('/lcu-status', methods=['GET'])
def lcu_status():
  return jsonify({
    'connected': app_state.is_lcu_connected(),
    'message': '已连接' if app_state.is_lcu_connected() else '未连接',
  })


@react_api_bp.route('/summoner/<path:summoner_name>', methods=['GET'])
def get_summoner(summoner_name):
  error = _require_lcu_connected()
  if error:
    return error

  token = app_state.lcu_credentials.get('auth_token')
  port = app_state.lcu_credentials.get('app_port')

  puuid = lcu.get_puuid(token, port, summoner_name)
  if not puuid:
    return jsonify({'success': False, 'error': f"找不到召唤师 '{summoner_name}'"}), 404

  summoner = lcu.get_summoner_by_puuid(token, port, puuid) or {}
  summoner_id = summoner.get('summonerId') or summoner.get('id')
  ranked = lcu.get_ranked_stats(token, port, summoner_id=summoner_id, puuid=puuid) or {}

  return jsonify({
    'success': True,
    'data': {
      'name': summoner.get('displayName') or summoner_name,
      'puuid': puuid,
      'summonerId': summoner_id,
      'profileIconId': summoner.get('profileIconId', 0),
      'level': summoner.get('summonerLevel', 0),
      'ranked': ranked,
    },
  })


@react_api_bp.route('/match-history/<path:summoner_name>', methods=['GET'])
def get_match_history(summoner_name):
  error = _require_lcu_connected()
  if error:
    return error

  token = app_state.lcu_credentials.get('auth_token')
  port = app_state.lcu_credentials.get('app_port')

  count = request.args.get('count', 20, type=int)
  count = min(max(count, 1), 50)

  puuid = lcu.get_puuid(token, port, summoner_name)
  if not puuid:
    return jsonify({'success': False, 'error': f"找不到召唤师 '{summoner_name}'"}), 404

  history = lcu.get_match_history(token, port, puuid, count=count, begin_index=0)
  if not history:
    return jsonify({'success': False, 'error': '获取战绩失败'}), 500

  processed = process_lol_match_history(history, puuid)
  matches = []
  for item in processed[:count]:
    kills = deaths = assists = 0
    kda = item.get('kda', '0/0/0')
    if isinstance(kda, str):
      try:
        kills, deaths, assists = [int(part) for part in kda.split('/')]
      except ValueError:
        kills = deaths = assists = 0
    game_id = item.get('match_id') or item.get('matchId') or item.get('gameId')
    matches.append({
      'gameId': game_id,
      'championName': item.get('champion_en'),
      'kills': kills,
      'deaths': deaths,
      'assists': assists,
      'win': bool(item.get('win')),
      'gameMode': item.get('mode') or item.get('gameMode'),
      'duration': item.get('duration'),
      'timeAgo': item.get('time_ago'),
    })

  return jsonify({'success': True, 'matches': matches})


@react_api_bp.route('/match/<int:game_id>', methods=['GET'])
def get_match_detail(game_id):
  error = _require_lcu_connected()
  if error:
    return error

  token = app_state.lcu_credentials.get('auth_token')
  port = app_state.lcu_credentials.get('app_port')

  detail = lcu.get_match_by_id(token, port, game_id)
  if not detail:
    return jsonify({'success': False, 'error': '获取对局详情失败'}), 500

  participants_raw = detail.get('participants') or []
  identities = {
    identity.get('participantId'): identity.get('player', {})
    for identity in detail.get('participantIdentities', [])
    if isinstance(identity, dict)
  }

  participants = []
  for participant in participants_raw:
    if not isinstance(participant, dict):
      continue
    pid = participant.get('participantId')
    stats = participant.get('stats', {}) if isinstance(participant.get('stats'), dict) else {}
    player_info = identities.get(pid, {})
    champion_id = participant.get('championId', 0)
    participants.append({
      'participantId': pid,
      'summonerName': player_info.get('summonerName') or player_info.get('gameName') or f'Player {pid}',
      'championId': champion_id,
      'championName': CHAMPION_MAP.get(champion_id, f'Champion{champion_id}'),
      'teamId': participant.get('teamId'),
      'kills': stats.get('kills', 0),
      'deaths': stats.get('deaths', 0),
      'assists': stats.get('assists', 0),
      'totalDamageDealtToChampions': stats.get('totalDamageDealtToChampions', 0),
      'totalDamageTaken': stats.get('totalDamageTaken', 0),
      'goldEarned': stats.get('goldEarned', 0),
      'totalMinionsKilled': stats.get('totalMinionsKilled', 0) + stats.get('neutralMinionsKilled', 0),
      'visionScore': stats.get('visionScore', 0),
      'win': bool(stats.get('win', False) or participant.get('win')),
    })

  return jsonify({
    'success': True,
    'gameInfo': {
      'gameId': game_id,
      'gameMode': detail.get('queueId'),
      'duration': (detail.get('gameDuration') or 0) // 60,
      'version': detail.get('gameVersion'),
    },
    'participants': participants,
  })


@react_api_bp.route('/tft/summoner/<path:summoner_name>', methods=['GET'])
def get_tft_history(summoner_name):
  error = _require_lcu_connected()
  if error:
    return error

  token = app_state.lcu_credentials.get('auth_token')
  port = app_state.lcu_credentials.get('app_port')

  puuid = lcu.get_puuid(token, port, summoner_name)
  if not puuid:
    return jsonify({'success': False, 'error': f"找不到召唤师 '{summoner_name}'"}), 404

  history = lcu.get_tft_match_history(token, port, puuid, count=20)
  if not history:
    return jsonify({'success': False, 'error': '获取 TFT 战绩失败'}), 500

  games = history.get('games', {}).get('games', [])
  matches = []
  for idx, game in enumerate(games[:20]):
    summary = process_single_tft_game(game, puuid) or {}
    matches.append({
      'id': game.get('id') or game.get('gameId') or idx,
      'placement': summary.get('placement') or summary.get('subteamPlacement'),
      'level': summary.get('level'),
      'gameDuration': summary.get('gameLength') or summary.get('duration'),
      'traits': summary.get('traits'),
    })

  return jsonify({'success': True, 'matches': matches})


@react_api_bp.route('/live-game', methods=['GET'])
def live_game():
  error = _require_lcu_connected()
  if error:
    return error

  data = lcu.get_live_game_data()
  if not data:
    return jsonify({'success': False, 'error': '当前没有正在进行的游戏'}), 404

  players = []
  for player in data.get('allPlayers', []):
    if not isinstance(player, dict):
      continue
    players.append({
      'summonerName': player.get('summonerName'),
      'championName': player.get('championName'),
      'teamId': player.get('team'),
      'championLevel': player.get('level'),
    })

  return jsonify({
    'success': True,
    'data': {
      'gameMode': data.get('gameData', {}).get('gameMode'),
      'gameTime': data.get('gameData', {}).get('gameTime'),
      'players': players,
    },
  })


@react_api_bp.route('/auto-accept', methods=['POST'])
def auto_accept():
  error = _require_lcu_connected()
  if error:
    return error

  app_state.auto_accept_enabled = True
  return jsonify({'success': True, 'message': '自动接受对局已启用'})


@react_api_bp.route('/auto-analyze', methods=['POST'])
def auto_analyze():
  error = _require_lcu_connected()
  if error:
    return error

  app_state.auto_analyze_enabled = True
  return jsonify({'success': True, 'message': '敌我分析已启用'})
