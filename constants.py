import winreg
import os

# --- LCU 根路径查找函数 ---

# 日志目录路径
def find_league_client_root_static():
    """
    尝试通过注册表查找英雄联盟客户端的安装根目录 (LeagueClient 文件夹)。
    查找失败时，尝试通用路径作为后备。
    """
    # 注册表路径（适用于 Riot Client 安装）
    REG_KEY_PATH = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Riot Game league_of_legends.live"
    
    # 尝试从注册表读取路径
    try:
        # 使用 KEY_WOW64_64KEY 确保在 64 位系统上找到 64 位应用程序的键
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, REG_KEY_PATH, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY)
        # 查找名为 'InstallLocation' 的值，例如: C:\Riot Games\League of Legends
        install_location, _ = winreg.QueryValueEx(key, "InstallLocation")
        winreg.CloseKey(key)
        
        # 检查路径是否有效
        if os.path.isdir(install_location):
            # LCU 日志位于此根目录的 Logs/LeagueClient Logs 子目录中
            # 但 Riot Games 的根目录通常是 LOL 文件夹。我们需要找到最终的 LeagueClient 文件夹。
            # 对于 Riot Games 安装，根目录可能已经是 C:\Riot Games\League of Legends，
            # WeGame 安装则可能是 C:\WeGameApps\英雄联盟\LeagueClient
            
            # 简单返回注册表中的路径，通常是客户端的根目录
            return install_location 
            
    except FileNotFoundError:
        pass 
    except Exception:
        pass 

    # 2. 后备方案：尝试常见的默认路径
    common_paths = [
        r"C:\Riot Games\League of Legends", # Riot Games 默认路径
        r"D:\Riot Games\League of Legends",
        r"C:\WeGameApps\英雄联盟\LeagueClient" # WeGame 默认路径
    ]
    
    for path in common_paths:
        if os.path.isdir(path):
            return path
            
    # 3. 彻底失败
    return None

# ----------------------------------------------------
# 2. 定义两个全局常量
# ----------------------------------------------------

# CLIENT_ROOT_PATH: LeagueClient 的根目录 (你想要的结果)
CLIENT_ROOT_PATH = find_league_client_root_static()

if CLIENT_ROOT_PATH:
    # LOG_DIR: LCU 日志文件的精确目录 (lcu_api.py 需要的结果)
    LOG_DIR = os.path.join(CLIENT_ROOT_PATH)
else:
    # 如果找不到根目录，将 LOG_DIR 设置为 None
    LOG_DIR = "C:\\WeGameApps\\英雄联盟\\LeagueClient"

# 英雄ID到名称的映射 (基于 Data Dragon CDN 15.21.1)
CHAMPION_MAP = {
    1: "Annie", 2: "Olaf", 3: "Galio", 4: "TwistedFate", 5: "XinZhao", 6: "Urgot", 7: "Leblanc", 8: "Vladimir", 9: "Fiddlesticks", 10: "Kayle",
    11: "MasterYi", 12: "Alistar", 13: "Ryze", 14: "Sion", 15: "Sivir", 16: "Soraka", 17: "Teemo", 18: "Tristana", 19: "Warwick", 20: "Nunu",
    21: "MissFortune", 22: "Ashe", 23: "Tryndamere", 24: "Jax", 25: "Morgana", 26: "Zilean", 27: "Singed", 28: "Evelynn", 29: "Twitch", 30: "Karthus",
    31: "Chogath", 32: "Amumu", 33: "Rammus", 34: "Anivia", 35: "Shaco", 36: "DrMundo", 37: "Sona", 38: "Kassadin", 39: "Irelia", 40: "Janna",
    41: "Gangplank", 42: "Corki", 43: "Karma", 44: "Taric", 45: "Veigar", 48: "Trundle", 50: "Swain", 51: "Caitlyn", 53: "Blitzcrank", 54: "Malphite",
    55: "Katarina", 56: "Nocturne", 57: "Maokai", 58: "Renekton", 59: "JarvanIV", 60: "Elise", 61: "Orianna", 62: "MonkeyKing", 63: "Brand", 64: "LeeSin",
    67: "Vayne", 68: "Rumble", 69: "Cassiopeia", 72: "Skarner", 74: "Heimerdinger", 75: "Nasus", 76: "Nidalee", 77: "Udyr", 78: "Poppy", 79: "Gragas",
    80: "Pantheon", 81: "Ezreal", 82: "Mordekaiser", 83: "Yorick", 84: "Akali", 85: "Kennen", 86: "Garen", 89: "Leona", 90: "Malzahar", 91: "Talon",
    92: "Riven", 96: "KogMaw", 98: "Shen", 99: "Lux", 101: "Xerath", 102: "Shyvana", 103: "Ahri", 104: "Graves", 105: "Fizz", 106: "Volibear",
    107: "Rengar", 110: "Varus", 111: "Nautilus", 112: "Viktor", 113: "Sejuani", 114: "Fiora", 115: "Ziggs", 117: "Lulu", 119: "Draven", 120: "Hecarim",
    121: "Khazix", 122: "Darius", 126: "Jayce", 127: "Lissandra", 131: "Diana", 133: "Quinn", 134: "Syndra", 136: "AurelionSol", 141: "Kayn", 142: "Zoe",
    143: "Zyra", 145: "Kaisa", 147: "Seraphine", 150: "Gnar", 154: "Zac", 157: "Yasuo", 161: "Velkoz", 163: "Taliyah", 164: "Camille", 166: "Akshan",
    200: "Belveth", 201: "Braum", 202: "Jhin", 203: "Kindred", 221: "Zeri", 222: "Jinx", 223: "TahmKench", 233: "Briar", 234: "Viego", 235: "Senna",
    236: "Lucian", 238: "Zed", 240: "Kled", 245: "Ekko", 246: "Qiyana", 254: "Vi", 266: "Aatrox", 267: "Nami", 268: "Azir", 350: "Yuumi",
    360: "Samira", 412: "Thresh", 420: "Illaoi", 421: "RekSai", 427: "Ivern", 429: "Kalista", 432: "Bard", 497: "Rakan", 498: "Xayah", 516: "Ornn",
    517: "Sylas", 518: "Neeko", 523: "Aphelios", 526: "Rell", 555: "Pyke", 711: "Vex", 777: "Yone", 799: "Ambessa", 800: "Mel", 804: "Yunara",
    875: "Sett", 876: "Lillia", 887: "Gwen", 888: "Renata", 893: "Aurora", 895: "Nilah", 897: "KSante", 901: "Smolder", 902: "Milio", 910: "Hwei", 950: "Naafiri"
}

# CHAMPION_ZH_MAP = {
#     "Aatrox": "亚托克斯", "Ahri": "阿狸", "Akali": "阿卡丽", "Akshan": "阿克尚", "Alistar": "阿利斯塔",
#     "Ambessa": "安蓓萨", "Amumu": "阿木木", "Anivia": "艾尼维亚", "Annie": "安妮", "Aphelios": "厄斐琉斯",
#     "Ashe": "艾希", "Aurelion Sol": "奥瑞利安·索尔", "Aurora": "奥罗拉", "Azir": "阿兹尔", "Bard": "巴德",
#     "Bel'Veth": "卑尔维斯", "Blitzcrank": "布里茨", "Brand": "布兰德", "Braum": "布隆", "Briar": "百裂冥犬",
#     "Caitlyn": "凯特琳", "Camille": "卡蜜尔", "Cassiopeia": "卡西奥佩娅", "Cho'Gath": "科加斯", "Corki": "库奇",
#     "Darius": "德莱厄斯", "Diana": "黛安娜", "Draven": "德莱文", "Dr. Mundo": "蒙多医生", "Ekko": "艾克",
#     "Elise": "伊莉丝", "Evelynn": "伊芙琳", "Ezreal": "伊泽瑞尔", "Fiddlesticks": "费德提克", "Fiora": "菲奥娜",
#     "Fizz": "菲兹", "Galio": "加里奥", "Gangplank": "普朗克", "Garen": "盖伦", "Gnar": "纳尔", "Gragas": "古拉加斯",
#     "Graves": "格雷福斯", "Gwen": "格温", "Hecarim": "赫卡里姆", "Heimerdinger": "黑默丁格", "Hwei": "彗",
#     "Illaoi": "俄洛伊", "Irelia": "艾瑞莉娅", "Ivern": "艾翁", "Janna": "迦娜", "Jarvan IV": "嘉文四世",
#     "Jax": "贾克斯", "Jayce": "杰斯", "Jhin": "烬", "Jinx": "金克丝", "Kai'Sa": "卡莎", "Kalista": "卡莉丝塔",
#     "Karma": "卡尔玛", "Karthus": "卡尔萨斯", "Kassadin": "卡萨丁", "Katarina": "卡特琳娜", "Kayle": "凯尔",
#     "Kayn": "凯隐", "Kennen": "凯南", "Kha'Zix": "卡兹克", "Kindred": "千珏", "Kled": "克烈", "Kog'Maw": "克格莫",
#     "K'Sante": "奎桑提", "LeBlanc": "乐芙兰", "Lee Sin": "李青", "Leona": "蕾欧娜", "Lillia": "莉莉娅",
#     "Lissandra": "丽桑卓", "Lucian": "卢锡安", "Lulu": "璐璐", "Lux": "拉克丝", "Malphite": "墨菲特",
#     "Malzahar": "玛尔扎哈", "Maokai": "茂凯", "Master Yi": "易", "Mel": "梅尔", "Milio": "米利欧",
#     "MissFortune": "厄运小姐", "Wukong": "孙悟空", "Mordekaiser": "莫德凯撒", "Morgana": "莫甘娜", "Naafiri": "纳亚菲利",
#     "Nami": "娜美", "Nasus": "内瑟斯", "Nautilus": "诺提勒斯", "Neeko": "妮蔻", "Nidalee": "奈德丽", "Nilah": "尼菈",
#     "Nocturne": "魔腾", "Nunu & Willump": "努努和威朗普", "Olaf": "奥拉夫", "Orianna": "奥莉安娜", "Ornn": "奥恩",
#     "Pantheon": "潘森", "Poppy": "波比", "Pyke": "派克", "Qiyana": "奇亚娜", "Quinn": "奎因", "Rakan": "洛",
#     "Rammus": "拉莫斯", "Rek'Sai": "雷克塞", "Rell": "芮尔", "Renata Glasc": "烈娜塔", "Renekton": "雷克顿",
#     "Rengar": "雷恩加尔", "Riven": "锐雯", "Rumble": "兰博", "Ryze": "瑞兹", "Samira": "莎弥拉", "Sejuani": "瑟庄妮",
#     "Senna": "赛娜", "Seraphine": "萨勒芬妮", "Sett": "瑟提", "Shaco": "萨科", "Shen": "慎", "Shyvana": "希瓦娜",
#     "Singed": "辛吉德", "Sion": "赛恩", "Sivir": "希维尔", "Skarner": "斯卡纳", "Smolder": "斯莫德", "Sona": "娑娜",
#     "Soraka": "索拉卡", "Swain": "斯维因", "Sylas": "塞拉斯", "Syndra": "辛德拉", "Tahm Kench": "塔姆",
#     "Taliyah": "塔莉垭", "Talon": "泰隆", "Taric": "塔里克", "Teemo": "提莫", "Thresh": "锤石", "Tristana": "崔丝塔娜",
#     "Trundle": "特朗德尔", "Tryndamere": "泰达米尔", "Twisted Fate": "崔斯特", "Twitch": "图奇", "Udyr": "乌迪尔",
#     "Urgot": "厄加特", "Varus": "韦鲁斯", "Vayne": "薇恩", "Veigar": "维迦", "Vel'Koz": "维克兹", "Vex": "薇古丝",
#     "Vi": "蔚", "Viego": "佛耶戈", "Viktor": "维克托", "Vladimir": "弗拉基米尔", "Volibear": "沃利贝尔",
#     "Warwick": "沃里克", "Xayah": "霞", "Xerath": "泽拉斯", "XinZhao": "赵信", "Yasuo": "亚索", "Yone": "永恩",
#     "Yorick": "约里克", "Yuumi": "悠米", "Zac": "扎克", "Zed": "劫", "Zeri": "泽丽", "Ziggs": "吉格斯",
#     "Zilean": "基兰", "Zoe": "佐伊", "Zyra": "婕拉"
# }

# CHAMPION_ZH_TO_ID = {
#     CHAMPION_ZH_MAP.get(en_name, en_name): id
#     for id, en_name in CHAMPION_MAP.items()
# }

# 海克斯天赋 (ARAM Augments) 完整映射
# playerAugment ID对应的图标名称，用于构建CDN URL
# 图标URL格式: https://raw.communitydragon.org/15.19/game/assets/ux/cherry/augments/icons/{name}_large.png
#
# 数据来源: Community Dragon (https://raw.communitydragon.org/latest/cdragon/arena/zh_cn.json)
# 更新时间: 自动生成

# ID到图标名称的映射
AUGMENT_ID_TO_NAME = {
    1001: 'acceleratingsorcery', 1002: 'apexinventor', 1003: 'canttouchthis', 1004: 'backtobasics', 1005: 'bannerofcommand',
    1006: 'bladewaltz', 1007: 'bluntforce', 1009: 'buffbuddies', 1010: 'cannonfodder', 1011: 'canttouchthis',
    1012: 'castle', 1013: 'celestialbody', 1014: 'chauffeur', 1015: 'circleofdeath', 1016: 'combomaster',
    1017: 'contractkiller', 1018: 'courageofthecolossus', 1019: 'dashing', 1020: 'dawnbringersresolve', 1021: 'defensivemaneuvers',
    1022: 'deft', 1023: 'demonsdance', 1024: 'dieanotherday', 1025: 'divebomber', 1026: 'dontblink',
    1027: 'earthwake', 1028: 'erosion', 1029: 'etherealweapon', 1030: 'eureka', 1032: 'executioner',
    1033: 'extendoarm', 1034: 'fallenaegis', 1035: 'feeltheburn', 1036: 'firebrand', 1037: 'firstaidkit',
    1038: 'frombeginningtoend', 1039: 'frostwraith', 1040: 'frozenfoundations', 1041: 'goliath', 1042: 'guiltypleasure',
    1043: 'nowyouseeme', 1044: 'icecold', 1045: 'infernalconduit', 1046: 'infernalsoul', 1047: 'itscritical',
    1048: 'jeweledgauntlet', 1049: 'juicebox', 1050: 'keystoneconjurer', 1051: 'lightemup', 1052: 'lightningstrikes',
    1053: 'madscientist', 1054: 'masterofduality', 1056: 'mindtomatter', 1057: 'mountainsoul', 1058: 'mysticpunch',
    1060: 'oceansoul', 1061: 'okboomerang', 1062: 'omnisoul', 1063: 'outlawsgrit', 1064: 'perseverance',
    1065: 'phenomenalevil', 1066: 'quantumcomputing', 1067: 'rabblerousing', 1068: 'recursion', 1069: 'repulsor',
    1070: 'restlessrestoration', 1071: 'scopierweapons', 1072: 'searingdawn', 1073: 'shadowrunner', 1074: 'shrinkray',
    1075: 'slowcooker', 1076: 'sonicboom', 1077: 'soulsiphon', 1078: 'spiritlink', 1079: 'symphonyofwar',
    1080: 'tankitorleaveit', 1081: 'tapdancer', 1082: 'thebrutalizer', 1084: 'threadtheneedle', 1085: 'tormentor',
    1086: 'trueshotprodigy', 1087: 'typhoon', 1088: 'ultimaterevolution', 1089: 'vanish', 1090: 'vengeance',
    1092: 'vulnerability', 1093: 'warmuproutine', 1094: 'willingsacrifice', 1096: 'wisdomofages', 1097: 'witchfulthinking',
    1098: 'withhaste', 1102: 'dontchase', 1103: 'breadandbutter', 1104: 'minionmancer', 1105: 'homeguard',
    1107: 'twicethrice', 1108: 'selfdestruct', 1109: 'oathsworn', 1110: 'clothesline', 1112: 'ultimateunstoppable',
    1113: 'skilledsniper', 1115: 'scopiestweapons', 1116: 'flashy', 1118: 'criticalhealing', 1120: 'servebeyonddeath',
    1123: 'summonersroulette', 1125: 'raidboss', 1129: 'marksmage', 1133: 'magicmissile', 1134: 'drawyoursword',
    1135: 'spellwake', 1136: 'slaparound', 1138: 'goredrink', 1141: 'allforyou', 1149: 'impassable',
    1150: 'breadandjam', 1151: 'breadandcheese', 1152: 'quest_steelyourheart', 1154: 'quest_urfschampion', 1156: 'quest_woogletswitchcap',
    1165: 'restart', 1166: 'chainlightning', 1170: 'scopedweapons', 1171: 'dematerialize', 1172: 'mirrorimage',
    1174: 'lasereyes', 1175: 'parasiticrelationship', 1176: 'snowballfight', 1177: 'nestingdoll', 1180: 'bigbrain',
    1181: 'heavyhitter', 1187: 'flashbang', 1192: 'quest_angelofretribution', 1193: 'centeroftheuniverse', 1194: 'feymagic',
    1195: 'giantslayer', 1198: 'holyfire', 1200: 'bloodbrother', 1204: 'stackosaurusrex', 1205: 'adapt',
    1206: 'escapade', 1207: 'holdverystill', 1208: 'orbitallaser', 1211: 'itskillingtime', 1214: 'spintowin',
    1215: 'darkblessing', 1216: 'plaguebearer', 1217: 'deathtouch', 1218: 'desecrator', 1219: 'doomsayer',
    1220: 'fanthehammer', 1221: 'trailblazer', 1222: 'fruitarian', 1223: 'summonerrevolution', 1224: 'quest_prismaticegg',
    1225: 'dualwield', 1226: 'stats', 1227: 'statsonstats', 1228: 'statsonstatsonstats', 1229: 'firesale',
    1231: 'lightwarden', 1232: 'slimetime', 1233: 'ultimaterevolution', 1234: 'thiefsgloves', 1236: 'tricksterdemon',
    1237: 'transmutegold', 1238: 'transmuteprismatic', 1239: 'symbioticmutation', 1240: 'parasiticmutation', 1241: 'hattrick',
    1242: 'juicepress', 1243: 'transmutechaos', 1250: 'slowandsteady', 1251: 'numbtopain', 1301: 'slowactingpainkillers',
    1302: 'gohsacrificefor', 1303: 'gohsacrificeforgold', 1304: 'gohsacrificeforprismatic', 1305: 'legday', 1308: 'firfox',
    1309: 'andmyaxe', 1310: 'clowncollege', 1311: 'overflow', 1312: 'wellberightback', 1313: 'tank_engine',
    1317: 'pandoras_box', 1318: 'mad_hatter', 1319: 'threesacredtreasures', 1320: 'calculated_risk', 1321: 'bodyguard',
    1322: 'augmented_power', 1323: 'cerberus', 1324: 'bravestofthebrave', 1326: 'spirit_infusion', 1335: 'goldrend',
    1349: 'ultimateawakening', 1404: 'augment404', 1405: 'augment405',
}

# ID到中文信息的映射（名称和描述）
AUGMENT_ID_TO_INFO = {
    1001: {
        'name': '加速巫术',
        'desc': '使用技能时会为你提供可无限叠加的技能急速，这个效果会在每回合重置。'
    },
    1002: {
        'name': '尖端发明家',
        'desc': '获得@ItemHaste@装备急速(相当于@TooltipCDR@%装备冷却缩减)。装备急速可缩减所有装备技能的冷却时间%i:cooldown%。'
    },
    1003: {
        'name': '虚无强化符文',
        'desc': '虚无'
    },
    1004: {
        'name': '回归基本功',
        'desc': '获得提升过的技能伤害、治疗效果、护盾和技能急速，但你不能使用你的终极技能。'
    },
    1005: {
        'name': '号令之旗',
        'desc': '获得召唤师技能号令之旗。号令之旗可短暂增强你的友军。'
    },
    1006: {
        'name': '利刃华尔兹',
        'desc': '获得召唤师技能利刃华尔兹。利刃华尔兹会让你进入不可被选取状态，在此期间对敌人进行反复突进并造成@TotalHits@次伤害。'
    },
    1007: {
        'name': '大力',
        'desc': '获得@ADAmp*100@%攻击力。'
    },
    1009: {
        'name': '霸符兄弟',
        'desc': '你获得余烬之冠和洞悉之冠。'
    },
    1010: {
        'name': '炮灰',
        'desc': '你会被一门大炮给发射进战斗中。'
    },
    1011: {
        'name': '你摸不到',
        'desc': '施放你的终极技能会使你进入短时间的免疫伤害状态。'
    },
    1012: {
        'name': '王车易位',
        'desc': '获得召唤师技能王车易位。王车易位：与你的友军交换位置，并获得移动速度和一个护盾。'
    },
    1013: {
        'name': '星界躯体',
        'desc': '获得@Health@生命值，但你造成的伤害降低@DamageReduction*100@%。'
    },
    1014: {
        'name': '专属司机',
        'desc': '你附身于你的友军，并且无法自行移动。你的额外移动速度还会提供给你的友军，并且你获得技能急速和攻击速度。'
    },
    1015: {
        'name': '生机绽放',
        'desc': '你造成的治疗效果和生命回复效果会对相距最近的那个敌方英雄造成一部分治疗数额的魔法伤害。'
    },
    1016: {
        'name': '连招大师',
        'desc': '获得电刑和相位猛冲基石符文。'
    },
    1017: {
        'name': '职业杀手',
        'desc': '每一回合，标记一个对方英雄来对其造成@spell.Augment_ContractKiller:DamageAmp*100@%额外伤害并在其阵亡时获得额外的@spell.Augment_ContractKiller:Gold@金币。'
    },
    1018: {
        'name': '巨像的勇气',
        'desc': '定身或缚地一个敌方英雄后获得@TotalShield@护盾值。'
    },
    1019: {
        'name': '全凭身法',
        'desc': '你的冲刺、跳跃、闪烁或传送类技能获得@Haste@技能急速。'
    },
    1020: {
        'name': '黎明使者的坚决',
        'desc': '在跌到@HealthThreshold*100@%生命值以下时，在3秒里持续回复共@HealAmount*100@%最大生命值。'
    },
    1021: {
        'name': '防御计略',
        'desc': '获得召唤师技能防御计略。防御计略会对你和你的队友施放屏障和治疗术。'
    },
    1022: {
        'name': '灵巧',
        'desc': '获得@AttackSpeed*100@%攻击速度。'
    },
    1023: {
        'name': '魔鬼之舞',
        'desc': '获得迅捷步法和不灭之握基石符文。'
    },
    1024: {
        'name': '择日赴死',
        'desc': '获得召唤师技能择日赴死。择日赴死会生成一个持续4秒的地带，期间内其中的单位都不会阵亡。'
    },
    1025: {
        'name': '俯冲轰炸',
        'desc': '你的队伍在每回合的第一次阵亡会爆炸，造成巨额真实伤害。'
    },
    1026: {
        'name': '唯快不破',
        'desc': '你的移动速度比目标越快，则对其造成越多伤害。'
    },
    1027: {
        'name': '大地苏醒',
        'desc': '你的冲刺、闪烁或传送类技能会留下一条在1秒后爆炸的轨迹。'
    },
    1028: {
        'name': '侵蚀',
        'desc': '对敌人造成伤害时会施加一层持续@ShredDuration@秒且可叠加的护甲和魔法抗性击碎效果。'
    },
    1029: {
        'name': '虚幻武器',
        'desc': '你的技能可施加{{ Item_Keyword_OnHit }}。每个目标有1秒冷却时间。'
    },
    1030: {
        'name': '尤里卡',
        'desc': '获得相当于@APToHasteConversion*100@%法术强度的技能急速。'
    },
    1032: {
        'name': '裁决使',
        'desc': '对生命值低于@HealthThreshold*100@%的敌人们多造成@BonusDamage*100@%伤害。在参与击杀后重置你的基础技能。'
    },
    1033: {
        'name': '弹簧飞爪',
        'desc': '自动施放每12秒朝一个附近的敌方英雄发射一个布里茨的飞爪。'
    },
    1034: {
        'name': '堕落圣盾',
        'desc': '带着一个持续@ShieldDuration@秒的黑暗之盾开始战斗。黑暗之盾会格挡魔法伤害和定身效果。'
    },
    1035: {
        'name': '感受燃烧',
        'desc': '获得召唤师技能感受灼烧。感受灼烧会对所有附近的敌人们施放引燃和虚弱。'
    },
    1036: {
        'name': '火上浇油',
        'desc': '你的攻击会施加一个可无限叠加的灼烧{{ Item_Keyword_OnHit }}，持续造成伤害。'
    },
    1037: {
        'name': '急救用具',
        'desc': '获得@HealShieldAmp*100@%治疗和护盾强度。'
    },
    1038: {
        'name': '有始有终',
        'desc': '获得先攻和黑暗收割基石符文。'
    },
    1039: {
        'name': '冰霜 幽灵',
        'desc': '每@Cooldown@秒，自动施放@RootDuration@秒禁锢给附近的敌人们。'
    },
    1040: {
        'name': '冰封地基',
        'desc': '获得召唤师技能冰封地基。冰封地基会在一个位置上召唤一道冰墙。'
    },
    1041: {
        'name': '歌利亚巨人',
        'desc': '体型变大，获得@HealthAmp*100@%生命值和@ADAmp*100@%适应之力。'
    },
    1042: {
        'name': '恶趣味',
        'desc': '定身或缚地敌方英雄时对你进行治疗。'
    },
    1043: {
        'name': '位移魔术',
        'desc': '获得召唤师技能位移魔术。位移魔术可将你传送回你最后一个移动技能的初始位置。'
    },
    1044: {
        'name': '冰寒',
        'desc': '你的减速效果可使移动速度降低额外的100。'
    },
    1045: {
        'name': '炼狱导管',
        'desc': '你的技能会施加一层可无限叠加的灼烧，持续造成魔法伤害。你的灼烧效果会降低你各基础技能的冷却时间。'
    },
    1046: {
        'name': '炼狱龙魂',
        'desc': '你获得炼狱龙魂，在你用技能或攻击命中敌人时造成额外伤害。'
    },
    1047: {
        'name': '关键暴击',
        'desc': '获得@CritChance*100@%暴击几率。'
    },
    1048: {
        'name': '珠光护手',
        'desc': '你的技能可以造成暴击。获得@CritChance*100@%暴击几率。'
    },
    1049: {
        'name': '果汁盒',
        'desc': '每回合，你和你的队友免费获得一份额外的果汁。'
    },
    1050: {
        'name': '基石法师',
        'desc': '获得召唤：艾黎和奥术彗星基石符文。'
    },
    1051: {
        'name': '点亮他们！',
        'desc': '每第4次攻击造成额外魔法伤害{{ Item_Keyword_OnHit }}。'
    },
    1052: {
        'name': '闪电打击',
        'desc': '获得@TotalASValue*100@%总攻击速度。在@Breakpoint1@攻击次数/秒时，造成额外的魔法伤害 {{ Item_Keyword_OnHit }}。'
    },
    1053: {
        'name': '科学狂人',
        'desc': '在回合开始时，你的体型要么变大(适应之力和生命值)要么变小(技能急速和移动速度)。'
    },
    1054: {
        'name': '物法皆修',
        'desc': '你的每次攻击为你提供法术强度{{ Item_Keyword_OnHit }}，并且你的每次技能为你提供攻击力，可无限叠加，持续到战斗结束。'
    },
    1056: {
        'name': '由心及物',
        'desc': '使你的最大生命值提升，数额相当于你一半的法力值。'
    },
    1057: {
        'name': '山脉龙魂',
        'desc': '你获得山脉龙魂，在脱离战斗之后获得一个持续一小段时间的护盾。'
    },
    1058: {
        'name': '秘术冲拳',
        'desc': '{{ Item_Keyword_OnHit }}使你的各个基础技能的冷却时间缩减其@CooldownRefund*100@%剩余冷却时间。'
    },
    1060: {
        'name': '海洋龙魂',
        'desc': '获得【海洋龙魂】，在对敌方英雄造成伤害后提供高额的生命和法力回复。'
    },
    1061: {
        'name': '回力OK镖',
        'desc': '每@BaseCooldown@秒朝着一个附近的敌人自动施放投掷一个回力镖。'
    },
    1062: {
        'name': '全能龙魂',
        'desc': '获得3个随机龙魂。'
    },
    1063: {
        'name': '狂徒豪气',
        'desc': '你的冲刺、闪烁或传送会为你提供@ResistsPerStack@护甲和魔法抗性，至多在@MaxStacks@层时提供@MaxResistTooltipOnly@。'
    },
    1064: {
        'name': '坚韧',
        'desc': '获得巨幅提升的生命回复，这个数额会在低生命值时进一步提升。'
    },
    1065: {
        'name': '超凡邪恶',
        'desc': '在你用技能命中敌人时永久获得@APPerProc@法术强度。如果是作为你的第二个强化符文，则自带@StartingAPIfSecondAugment@法术强度。'
    },
    1066: {
        'name': '量子计算',
        'desc': '周期性地在你周围自动施放一次巨型斩击，造成物理伤害。被外沿命中的敌人会被减速，会受到额外的最大生命值的物理伤害，并且你会回复生命值，数额相当于一部分该额外伤害。'
    },
    1067: {
        'name': '古式佳酿',
        'desc': '使用一个技能时会回复@HealAmount@生命值。'
    },
    1068: {
        'name': '循环往复',
        'desc': '获得@AbilityHaste@技能急速。'
    },
    1069: {
        'name': '退敌力场',
        'desc': '在你跌下@HealthThreshold1*100@%或@HealthThreshold2*100@%生命值时，附近的敌人们会被击退。'
    },
    1070: {
        'name': '无休回复',
        'desc': '你在移动时持续获得治疗。'
    },
    1071: {
        'name': '更万用的瞄准镜',
        'desc': '获得@MeleeRangeIncrease@攻击距离，如果你是远程英雄则降低至@RangedRangeIncrease@攻击距离。'
    },
    1072: {
        'name': '炽烈黎明',
        'desc': '你的技能会标记敌人，使其在被你的友军的下一个攻击或技能命中时会受到额外魔法伤害。'
    },
    1073: {
        'name': '暗影疾奔',
        'desc': '在使用一个冲刺、跳跃、闪烁或传送类技能或离开潜行状态之后，获得持续@spell.Augment_ShadowRunner:BuffDuration@秒的@spell.Augment_ShadowRunner:MSAmount@移动速度。'
    },
    1074: {
        'name': '缩小射线',
        'desc': '你的攻击会对敌人造成持续3秒的@DamageReduction*100@%伤害削减效果。'
    },
    1075: {
        'name': '慢炖',
        'desc': '每一秒，对附近的敌方英雄们施加一层可无限叠加的灼烧，这个效果受益于你的最大生命值。'
    },
    1076: {
        'name': '天音爆',
        'desc': '在为你的友军提供增益效果、治疗效果或护盾效果时，会对其附近的敌人们造成伤害和减速。'
    },
    1077: {
        'name': '灵魂虹吸',
        'desc': '获得@CritChance*100@%暴击几率和作用于暴击的@HealPercentage*100@%生命偷取。'
    },
    1078: {
        'name': '灵魂连接',
        'desc': '你的友军受到的@DamageRedirectPercentage*100@%实际伤害值将被转移给你，并且其所受的@HealCopyPercentage*100@%治疗效果也会转移给你。'
    },
    1079: {
        'name': '战争交响乐',
        'desc': '获得致命节奏和征服者基石符文。'
    },
    1080: {
        'name': '会心防守',
        'desc': '你可以使用你的暴击几率(最大@MaxChance*100@%几率)来进行会心防御，使你有一定几率来使所受伤害降低。获得@CritChance*100@%暴击几率。'
    },
    1081: {
        'name': '踢踏舞',
        'desc': '你的攻击会为你提供@MSPerHit@移动速度，可无限叠加。获得相当于你@MSToASConversion*10000@% 移动速度的攻击速度。'
    },
    1082: {
        'name': '残暴之力',
        'desc': '获得@AD@攻击力、@AbilityHaste@技能急速和@Lethality@穿甲。'
    },
    1084: {
        'name': '穿针引线',
        'desc': '获得@PercentPen*100@%护甲穿透和法术穿透。'
    },
    1085: {
        'name': '折磨之叉',
        'desc': '定身或缚地敌方英雄时提供一层灼烧，这个效果会持续造成伤害并可无限叠加。'
    },
    1086: {
        'name': '精准奇才',
        'desc': '在你从远处对一名敌人造成伤害时，对其发射一道精准弹幕。'
    },
    1087: {
        'name': '台风',
        'desc': '你的攻击会对一个额外目标发射一根弩箭，这个弩箭会造成削减过的伤害并施加{{ Item_Keyword_OnHit }}。'
    },
    1088: {
        'name': '终极刷新',
        'desc': '每回合一次，在你施放终极技能后刷新你的终极技能。'
    },
    1089: {
        'name': '遁入暗影',
        'desc': '获得召唤师技能遁入暗影。遁入暗影会使你进入潜行状态。'
    },
    1090: {
        'name': '复仇',
        'desc': '在你的搭档阵亡后，获得大幅提升伤害和全能吸血，持续到该回合结束。'
    },
    1092: {
        'name': '易损',
        'desc': '你的装备和持续伤害效果可以暴击。获得@CritChance*100@%暴击几率。'
    },
    1093: {
        'name': '热身动作',
        'desc': '获得召唤师技能热身动作。热身动作：引导你的内在之舞来提升你的伤害，持续至回合结束。'
    },
    1094: {
        'name': '自愿牺牲',
        'desc': '当你的友军跌到@AllyHealthThreshold*100@%生命值以下时，将你的一些生命值换成护盾值来提供给你的友军。'
    },
    1096: {
        'name': '时光之智慧',
        'desc': '立刻提升1级，并且每隔一回合额外提升1级。你的等级上限已被移除。如果是作为你的第二个强化符文，则转而提升3级。'
    },
    1097: {
        'name': '巫师式思考',
        'desc': '获得@AP@法术强度。'
    },
    1098: {
        'name': '急急小子',
        'desc': '获得移动速度，相当于你的@AbilityHasteToMSConversion*100@%技能急速。'
    },
    1102: {
        'name': '请勿追击',
        'desc': '你无视单位的碰撞体积并在身后留下一条剧毒踪迹，对其中的敌人造成魔法伤害。'
    },
    1103: {
        'name': '面包和黄油',
        'desc': '你的Q获得@QAbilityHaste@技能急速。'
    },
    1104: {
        'name': '仆从大师',
        'desc': '你的召唤物获得@MinionSizeIncrease*100@%体型提升、生命值和伤害。'
    },
    1105: {
        'name': '家园卫士',
        'desc': '获得@spell.Augment_Homeguard:MovementSpeed*100@%移动速度，在受到伤害后失效@spell.Augment_Homeguard:DisableCooldown@秒。'
    },
    1107: {
        'name': '接二连三',
        'desc': '每第三次攻击，你附带的{{ Item_Keyword_OnHit }}会触发第二次。'
    },
    1108: {
        'name': '自我毁灭',
        'desc': '每个回合开始时会有一个炸弹附在你身上。在@BombDelay@秒后，它会爆炸，造成巨额真实伤害并击飞附近的敌人们。'
    },
    1109: {
        'name': '誓约者',
        'desc': '将召唤师技能【闪人】替换为命运的召唤。命运的召唤会将你的搭档变为不可被选取状态，持续至多4秒。你的友军可以自行脱身，从而击退敌人们。'
    },
    1110: {
        'name': '晾衣绳',
        'desc': '在你和你的搭档之间有一条灵链，它可以不断地对其中的敌人们造成魔法伤害。'
    },
    1112: {
        'name': '终极不可阻挡',
        'desc': '在你使用你的终极技能后，你获得持续@UnstoppableDuration@秒的控制免疫。 (@Cooldown@秒冷却时间)。'
    },
    1113: {
        'name': '老练狙神',
        'desc': '用一个非终极技能命中一个远处的敌人时，将这个技能的冷却时间缩短至@ReducedCooldown@秒(周期性技能为@PeriodicReductionAmount@秒)。'
    },
    1115: {
        'name': '最万用的瞄准镜',
        'desc': '获得@MeleeRangeIncrease@攻击距离，如果你是远程英雄则降低至@RangedRangeIncrease@攻击距离。'
    },
    1116: {
        'name': '闪现向前',
        'desc': '你的【闪现】有@FlashAmmoTooltip@层充能，并且冷却时间为@FlashCooldown@秒。'
    },
    1118: {
        'name': '会心治疗',
        'desc': '你的治疗和护盾可以暴击，获得@CritHeal*100@%额外数额的效果。获得@CritChance*100@%暴击几率。'
    },
    1120: {
        'name': '超越死亡的效劳',
        'desc': '在你每回合第一次即将阵亡时，转而回满生命值并在@DecayDuration@秒里持续衰减。在你的生命值正在衰减的状态下，参与击杀一名敌方英雄后，会使衰减停止并将你的生命值设置为@TriumphPercent@%最大生命值。'
    },
    1123: {
        'name': '召唤师峡谷的轮盘',
        'desc': '将你的召唤师技能替换为随机一个召唤师技能。在你使用一个召唤师技能时，将其换成另一个随机的召唤师技能，并设置@Cooldown@秒的冷却时间。'
    },
    1125: {
        'name': '副本BOSS',
        'desc': '你每个回合开始时都会被封印在竞技场中心，无法进行任何行动。在被封印的状态下，你拥有巨额伤害减免并持续积攒体型、生命值、攻击力和法术强度。在@ImprisonDuration@秒之后或在达到@BreakoutHealthThreshold*100@%生命值时，你会打破封印，击退敌人们并获得基于你最大生命值的护盾值。'
    },
    1129: {
        'name': '神射法师',
        'desc': '你的攻击造成相当于你@APRatio*100@%法术强度的额外物理伤害。'
    },
    1133: {
        'name': '魔法飞弹',
        'desc': '用一个技能造成伤害时，会对其发射@NumberOfMissiles@个魔法飞弹，每个魔法飞弹基于飞行距离造成百分比最大生命值的真实伤害。'
    },
    1134: {
        'name': '亮出你的剑',
        'desc': '你现在是近战状态。获得@BonusAD*100@%攻击力、@BonusHP*100@%生命值、@BonusAS*100@%攻击速度、@BonusLifesteal*100@%生命偷取和@BonusMS*100@%移动速度 (每个属性都已基于攻击距离的损失而进一步提升)。'
    },
    1135: {
        'name': '法术苏醒',
        'desc': '用技能命中敌人时会从你的位置生成一道通向命中敌人位置的震波，来造成魔法伤害。'
    },
    1136: {
        'name': '扇巴掌',
        'desc': '每当你定身或缚地一个敌人时，获得持续到回合结束的@AdaptiveForce@适应之力，可无限叠加。'
    },
    1138: {
        'name': '渴血',
        'desc': '获得@Omnivamp*100@%全能吸血。'
    },
    1141: {
        'name': '全心为你',
        'desc': '你的治疗和护盾在用在一个友军身上时会变强@HealShieldAmp*100@%。'
    },
    1149: {
        'name': '不动如山',
        'desc': '获余震和冰川增幅基石符文。'
    },
    1150: {
        'name': '面包和果酱',
        'desc': '你的W获得@WAbilityHaste@技能急速。'
    },
    1151: {
        'name': '面包和奶酪',
        'desc': '你的E获得@EAbilityHaste@技能急速。'
    },
    1152: {
        'name': '任务：钢化你心',
        'desc': '需求：持有【心之钢】且层数在@StackThreshold@层或以上。奖励：将你的心之钢层数乘以@StackMultiplication@。使你的生命回复提升@StacktoRegenConversion*100@%x你的【心之钢】层数。'
    },
    1154: {
        'name': '任务：海牛阿福的勇士',
        'desc': '需求：参与击杀@TakedownsNeeded@次。奖励：金铲铲'
    },
    1156: {
        'name': '任务：沃格勒特的巫师帽',
        'desc': '即刻：获得【无用大棒】。需求：持有【灭世者的死亡之帽】和【中娅沙漏】。奖励：获得【沃格勒特的巫师帽】。'
    },
    1165: {
        'name': '重启',
        'desc': '你的非终极技能每@CoolDown@秒自动刷新一次。'
    },
    1166: {
        'name': '连锁闪电',
        'desc': '对一个敌人造成伤害时，还会对其搭档造成@DamageMod*100@%已造成伤害的真实伤害，前提是其友军在附近。'
    },
    1170: {
        'name': '万用瞄准镜',
        'desc': '获得@MeleeRangeIncrease@攻击距离，如果你是远程英雄则降低至@RangedRangeIncrease@攻击距离。'
    },
    1171: {
        'name': '去质',
        'desc': '参与击杀后获得@AdaptiveForce@适应之力 ，每回合每个英雄1次。如果是你的第二个强化符文，会自带@SecondPickBonus@初始适应之力。'
    },
    1172: {
        'name': '镜花水月',
        'desc': '当你跌下@HealthThreshold*100@%生命值时，暂时隐形并生成你自己的4个复制体。'
    },
    1174: {
        'name': '镭射眼',
        'desc': '你正在面对的方向会出现一道镭射光束，可造成持续的魔法伤害。'
    },
    1175: {
        'name': '寄生关系',
        'desc': '你获得你搭档@HealPercent*100@%已造成伤害值的治疗效果。'
    },
    1176: {
        'name': '雪球大战！',
        'desc': '将召唤师技能【闪人】替换为【标记】。扔出一团雪球来标记命中的第一个敌人并造成伤害。再次施放来冲刺到被标记敌人的位置。'
    },
    1177: {
        'name': '套娃',
        'desc': '你在@ReviveArmTime@秒后自动开始复活你自己，并且你可以被额外复活一次。你每次复活时，都会变得更小并且具有降低过的最大生命值。在你复活时，击退你周围的敌人们。'
    },
    1180: {
        'name': '超强大脑',
        'desc': '在每个回合开始时，每拥有%i:scaleAP% @AP@法术强度就会获得 @ShieldBase@护盾值。'
    },
    1181: {
        'name': '重量级打击手',
        'desc': '你的攻击造成相当于你@HealthPercent*100@%最大生命值的额外物理伤害。'
    },
    1187: {
        'name': '闪光弹',
        'desc': '你在【闪现】时会在你周围引发爆炸，对命中的敌人们造成魔法伤害和减速。此外，【闪现】每回合都会重置。'
    },
    1192: {
        'name': '任务：惩戒天使',
        'desc': '需求：给友军治疗或预防@RequirementAmount@伤害。奖励：获得@AttackSpeed*100@%攻击速度，并且你的攻击造成相当于@HealPowerToDamageConversion*100@%治疗/护盾强度的额外魔法伤害。'
    },
    1193: {
        'name': '星原之准',
        'desc': '卫星会以你的攻击距离为半径环绕于你，对途经的敌人们造成魔法伤害。'
    },
    1194: {
        'name': '精怪魔法',
        'desc': '你的终极技能的伤害会对敌人造成持续若干秒的变形效果。'
    },
    1195: {
        'name': '巨人杀手',
        'desc': '体型变小，获得移动速度，并基于敌方英雄体型大于你的程度造成额外伤害。'
    },
    1198: {
        'name': '圣火',
        'desc': '你的治疗或护盾会对一个附近的敌人施加一层无限叠加的灼烧，在若干秒内持续造成百分比最大生命值的魔法伤害。'
    },
    1200: {
        'name': '血亲兄弟',
        'desc': '获得德莱厄斯的出血被动。攻击和伤害型技能会使目标出血，在@BleedDuration@秒里持续造成共@BleedDamagePerStack@物理伤害，至多可叠加@MaxStacks@层。德莱文在出血达到@MaxStacks@层时会获得@NoxianMightBonusAD@攻击力。'
    },
    1204: {
        'name': '叠角龙',
        'desc': '在你获得一个技能的永久层数时，多获得@StackModifier*100@%！'
    },
    1205: {
        'name': '物理转魔法',
        'desc': '将额外攻击力转化为法术强度。获得@APAmp*100@%法术强度。'
    },
    1206: {
        'name': '魔法转物理',
        'desc': '将法术强度转化为额外攻击力。获得@ADAmp*100@%攻击力。'
    },
    1207: {
        'name': '纹丝不动',
        'desc': '获得游击队军备。在原地不动@HoldStillDuration@秒后，获得隐形，持续到你移动为止。在你离开这个隐形状态时，你的第一次命中造成额外魔法伤害、获得@BonusAS@攻击速度和@BonusMS*100@%持续衰减的移动速度。'
    },
    1208: {
        'name': '轨道镭射',
        'desc': '将召唤师技能【闪人】替换为轨道镭射。在一阵延迟后，召唤一道轨道镭射光束落下，在@GroundDuration@秒里持续造成@DamagetoChampions*100@%最大生命值的真实伤害外加@TotalDamageOverTimeTooltip@魔法伤害。'
    },
    1211: {
        'name': '杀戮时间到了',
        'desc': '在施放你的终极技能后，将所有敌人打上死亡标记。对带标记的敌人造成伤害时，会将一部分已造成伤害储存起来，然后在标记结束时将已储存的伤害引爆。'
    },
    1214: {
        'name': '旋转至胜',
        'desc': '你的旋转类技能获得@SpinHaste@技能急速并且多造成@SpinDamageAmp*100@%伤害！'
    },
    1215: {
        'name': '黑暗赐福',
        'desc': '治疗/护盾为你提供永久的诅咒能量。从每层诅咒能量中获得技能急速。你每回合可以获得的最大诅咒能量会随着你和你的友军的诅咒来源总和而增长。'
    },
    1216: {
        'name': '恐惧使者',
        'desc': '获得一个光环，从其中每个的敌方英雄处持续收割永久的诅咒能量。获得基于你的诅咒能量的最大生命值。你每回合可以获得的最大诅咒能量会随着你和你的友军的诅咒来源总和而增长。'
    },
    1217: {
        'name': '死亡触摸',
        'desc': '攻击敌方英雄时提供永久的诅咒能量并造成基于你诅咒能量的的额外魔法伤害。你每回合可以获得的最大诅咒能量会随着你和你的友军的诅咒来源总和而增长。'
    },
    1218: {
        'name': '亵渎者',
        'desc': '定身敌方英雄时为你提供永久的诅咒能量。获得基于你的诅咒能量的护甲和魔法抗性。你每回合可以获得的最大诅咒能量会随着你和你的友军的诅咒来源总和而增长。'
    },
    1219: {
        'name': '末日预言者',
        'desc': '用技能命中敌方英雄会为你提供永久的诅咒能量。获得基于你的诅咒能量的适应之力。你每回合可以获得的最大诅咒能量会随着你和你的友军的诅咒来源总和而增长。'
    },
    1220: {
        'name': '连拨击锤',
        'desc': '在你攻击时，发射@AdditionalBolts@个额外箭矢，每个箭矢基于移动的距离造成物理伤害。每个方向都有单独的冷却时间。'
    },
    1221: {
        'name': '引路者',
        'desc': '冲刺或闪烁会对一名附近的敌方英雄时施加一层灼烧，这个效果会持续造成伤害并可无限叠加。'
    },
    1222: {
        'name': '你的劳动果实',
        'desc': '能量花卉在你身上的效能提升@AmpAmountTooltip@%，并且还会分享给你的友军。'
    },
    1223: {
        'name': '召唤师革新',
        'desc': '你的召唤师技能获得一层额外的充能。此外，【闪现】每回合都会重置。'
    },
    1224: {
        'name': '棱彩蛋',
        'desc': '参与击杀时获得@KillStackCredit@层，每回合每个英雄仅触发一次此效果。每@RequiredKillCount@层，这会孵化出一个【棱彩锻造器】和@RerollsToGrant@次额外刷新。'
    },
    1225: {
        'name': '双刀流',
        'desc': '在你攻击时，发射一个次级弩箭，造成@AttackReduction*100@%伤害和@OnHitMod*100@%效能的{{ Item_Keyword_OnHit }}。获得@AttackSpeed*100@%总攻击速度。'
    },
    1226: {
        'name': '属性！',
        'desc': '获得@AmountOfStatAnvils@个【属性锻造器】！'
    },
    1227: {
        'name': '属性叠属性！',
        'desc': '获得@AmountOfStatAnvils@个【属性锻造器】！'
    },
    1228: {
        'name': '属性叠属性叠属性！',
        'desc': '获得@AmountOfStatAnvils@个【属性锻造器】！'
    },
    1229: {
        'name': '火爆甩卖',
        'desc': '立刻售出你的所有非任务装备，换取它们的@SellValueTooltip@%直购价格。对那些打折购买的锻造器来说非常不错。'
    },
    1231: {
        'name': '光明守望者',
        'desc': '每几秒，朝你的友军自动施放一道防护之光，为你自身及其途经的友军提供护盾。它随后会折返，重复该效果。'
    },
    1232: {
        'name': '史莱姆时间',
        'desc': '每几秒，自动施放来自你身体的一团粘液，对附近的敌人们造成魔法伤害。如果你命中了一个英雄，则会分泌出一个液团，在你走上去时治疗你。'
    },
    1233: {
        'name': '终极转盘',
        'desc': '将召唤师技能【闪人】替换成一个随机英雄的终极技能。在施放这个技能后，会将它随机替换为另一个终极技能。'
    },
    1234: {
        'name': '财运锻造器',
        'desc': '获得@GoldBonus@金币并降低所有锻造器的价格。棱彩锻造器数量：@PrismaticCostReduction@传说锻造器数量：@LegendaryCostReduction@属性锻造器数量：@StatCostReduction@从锻造器中获得的装备的售价降低500金币。'
    },
    1236: {
        'name': '诡术恶魔',
        'desc': '当你离开潜行状态时会引发爆炸，造成@TotalDamage@魔法伤害，你的复制体和陷阱将在阵亡时造成相同效果。'
    },
    1237: {
        'name': '质变：黄金阶',
        'desc': '获得1个随机黄金阶强化符文。'
    },
    1238: {
        'name': '质变：棱彩阶',
        'desc': '获得1个随机棱彩阶强化符文。'
    },
    1239: {
        'name': '共生突变',
        'desc': '每回合，这个会转变为你友军的强化符文之一。 仅会突变为你能够刷新到的强化符文。'
    },
    1240: {
        'name': '寄生突变',
        'desc': '每回合，这个会突变为你对手们的强化符文之一。仅会突变为你能够刷新到的强化符文。'
    },
    1241: {
        'name': '帽子戏法',
        'desc': '即刻获得@HatsToGrant@顶帽子，并且【帽子饮品】的价格降低@HatTrickPriceReduction@。在受到将使你的生命值跌入@LowHealthThreshold*100@%以下的伤害时，获得@MoveSpeedBoostPercent*100@%移动速度和@ShieldHealth@护盾值，持续@ShieldDuration@秒，但失去一顶帽子。@Cooldown@秒冷却时间。'
    },
    1242: {
        'name': '榨汁机',
        'desc': '各饮品会为你和你的队友提供额外效果。增益类饮品的花费减少@PriceReduction*100@%。'
    },
    1243: {
        'name': '质变：混沌',
        'desc': '获得2个随机的强化符文。'
    },
    1250: {
        'name': '一板一眼',
        'desc': '你的攻击速度变为@StaticRatio@。所有额外攻击速度会被转化为攻击力。(每1%攻速转@ADPerAS@攻击力)。'
    },
    1251: {
        'name': '疼痛钝感',
        'desc': '你所受的@MeleeReduction*100@%伤害会转而在@BleedDuration@秒里持续发生(远程英雄为@RangedReduction*100@%)。'
    },
    1301: {
        'name': '神圣干预',
        'desc': '在战斗开始@InitalDelay@秒后，召唤一颗护体星星缓慢地降落在你身上。在它着陆时，你和附近的友军们进入持续若干秒的免疫伤害状态。随后每@BaseCD@秒自动施放这个效果。'
    },
    1302: {
        'name': '献祭：换取白银阶',
        'desc': '在@RoundCountCap@回合后，获得一个额外的白银阶强化符文。'
    },
    1303: {
        'name': '献祭：换取黄金阶',
        'desc': '献祭你的@HealthReduction*100@%当前生命值。在@RoundCountCap@回合后，获得一个额外的黄金阶强化符文并回复你的生命值。'
    },
    1304: {
        'name': '献祭：换取棱彩阶',
        'desc': '献祭你的@HealthReduction*100@%当前生命值。在@RoundCountCap@回合后，获得一个额外的棱彩阶强化符文并回复你的生命值。'
    },
    1305: {
        'name': '练腿日',
        'desc': '获得@MovementSpeed@移动速度和@SlowResist*100@%减速抗性。'
    },
    1308: {
        'name': '火狐',
        'desc': '自动施放获得移动速度并召唤3道烈焰环绕于你，瞄准距离内相距最近的那个可见英雄并造成自适应伤害。'
    },
    1309: {
        'name': '还有我的斧头！',
        'desc': '自动施放：周期性地向相距最近的那个对手投掷一柄斧头，造成伤害、减速、护甲击碎和魔抗击碎。如果这柄斧头被拾取，那么这个冷却时间会缩短。'
    },
    1310: {
        'name': '小丑学院',
        'desc': '获得召唤师技能欺诈魔术。获得背刺被动。在你阵亡时，生成一个爆炸盒子来对附近的敌人们造成大量真实伤害和恐惧。'
    },
    1311: {
        'name': '溢流',
        'desc': '你的法力值消耗翻倍。你的技能的治疗效果、护盾效果和伤害获得提升，提升幅度基于你的最大法力值。'
    },
    1312: {
        'name': '我们马上就回来',
        'desc': '获得召唤师技能时间停止。时间停止：所有附近的英雄都被置入凝滞状态。你离开凝滞状态的时间加快，并且在此效果期间，基于你的已损失生命值为你提供治疗。'
    },
    1313: {
        'name': '坦克引擎',
        'desc': '每次参与击杀获得@SizeIncrement*100@%体型提升和@MaxHPIncrement*100@%额外生命值。'
    },
    1317: {
        'name': '潘朵拉的盒子',
        'desc': '将你的所有强化符文变为随机的棱彩阶强化符文。'
    },
    1318: {
        'name': '任务：疯狂帽子人',
        'desc': '需求：在战斗结束时戴着@QuestThreshold@顶帽子。奖励：从每顶帽子获得@AFPerHat@适应之力、@ArmorMRPerHat@护甲和魔法抗性、@TenacityPerHat*100@%韧性，以及@MSPerHat@移动速度。当你输掉一个回合时，失去你一半的帽子。'
    },
    1319: {
        'name': '任务：三圣宝',
        'desc': '需求：持有【无尽之刃】、【困惑】和【海克斯科技枪刃】。奖励：芸阿娜的攻击被替换为造成混合伤害的激光。'
    },
    1320: {
        'name': '精算风险',
        'desc': '你不再能够刷新。选择一个黄金阶强化符文，如果消耗了至少@PrismaticThreshold@个刷新次数，则强化此效果来选择一个棱彩阶强化符文作为替代。'
    },
    1321: {
        'name': '保镖',
        'desc': '使用一次冲刺、闪烁或传送时可为你自己提供持续@ShieldDuration@秒的护盾，这个护盾也会提供给你途经的任何友军。这个护盾的护盾值基于你的技能在1级时的基础冷却时间。'
    },
    1322: {
        'name': '强化之能量',
        'desc': '使你的强化符文和装备的伤害提升@DamageAmp@。'
    },
    1323: {
        'name': '地狱三头犬',
        'desc': '获得丛刃和强攻基石符文。'
    },
    1324: {
        'name': '勇中最勇',
        'desc': '将未来的强化符文供应提升@tierValueIncrease@阶。如果强化符文已经是棱彩阶，则获得额外的@GoldAmount@金币。'
    },
    1326: {
        'name': '灵之灌注',
        'desc': '获得治疗和护盾强度，这个效果在低生命值时会提升。在施放终极技能时，将你的治疗和护盾强度翻倍。'
    },
    1335: {
        'name': '夺金',
        'desc': '使用攻击或技能对敌方英雄造成伤害时，额外造成50-150（+20%法术强度，+40%基础攻击力）的魔法伤害，同时获得15金币与25%移动速度（持续1.5秒）；每个敌方英雄有30秒冷却时间（对不同英雄可分别触发）。'
    },
    1349: {
        'name': '终极觉醒',
        'desc': '使用大招后，重置所有基础技能冷却时间（冷却时间10秒）。'
    },
    1404: {
        'name': '404 强化符文未找到',
        'desc': '你怎么找到这个的？！？！？获得@HatsToGrant@顶帽子。'
    },
    1405: {
        'name': '强化符文405',
        'desc': '你每穿戴一顶帽子，就会获得@DamageAmpPerHat*100@%伤害。'
    },
}

def get_augment_icon_url(augment_id, version='15.19'):
    """
    获取海克斯天赋图标的CDN URL
    
    Args:
        augment_id: playerAugment字段的ID值 (如 1084, 1314)
        version: CDN版本号，默认为 '15.19'
    
    Returns:
        图标URL，如果ID未找到则返回None
    """
    name = AUGMENT_ID_TO_NAME.get(augment_id)
    if name:
        return f'https://raw.communitydragon.org/{version}/game/assets/ux/cherry/augments/icons/{name}_large.png'
    return None

def get_augment_info(augment_id):
    """
    获取海克斯天赋的中文信息
    
    Args:
        augment_id: playerAugment字段的ID值
    
    Returns:
        dict: {'name': '中文名称', 'desc': '中文描述'} 或 None
    """
    return AUGMENT_ID_TO_INFO.get(augment_id)