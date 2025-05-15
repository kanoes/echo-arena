import json

from config.settings import CHARACTERS_DIR, WORLD_TEMPLATES_DIR
from config.logging import LoggingConfig

# ログ設定
logging_config = LoggingConfig()
logger = logging_config.get_logger()


def create_sample_character():
    """サンプルキャラクターを作成"""
    sample_character = {
        "id": "sample_npc",
        "name": "アリス",
        "description": "魔法学校の優等生。幼い頃から魔法の才能に恵まれ、特に風の魔法が得意。",
        "personality": "好奇心旺盛で明るい性格。新しいことを学ぶのが大好きだが、時々夢見がちになることも。人付き合いは得意で、誰とでもすぐに打ち解ける。",
        "background": "裕福な魔法使いの家庭に生まれ、5歳の時に魔法の才能が開花。現在は魔法学校の上級生として、様々な魔法を学んでいる。将来は魔法研究者になることを夢見ている。",
        "emotions": {
            "JOY": 0.7,
            "TRUST": 0.6,
            "ANTICIPATION": 0.8
        }
    }
    
    file_path = CHARACTERS_DIR / "sample_npc.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(sample_character, f, ensure_ascii=False, indent=2)
        
    logger.info("サンプルキャラクターを作成しました")


def create_sample_world():
    """サンプル世界を作成"""
    sample_world = {
        "id": "fantasy_world",
        "name": "ファンタジー世界",
        "description": "魔法と冒険に満ちた世界。ドラゴンや精霊など様々な幻想的な生き物が存在する。",
        "locations": [
            {
                "id": "magic_academy",
                "name": "魔法学園",
                "description": "若い魔法使いたちが学ぶ巨大な学園。古い石造りの建物には数千年の歴史がある。",
                "connected_locations": ["city_square", "library"],
                "items": ["魔法の杖", "古い魔道書", "クリスタルボール"]
            },
            {
                "id": "city_square",
                "name": "中央広場",
                "description": "王国の中心に位置する広い広場。噴水や露店が立ち並び、常に人で賑わっている。",
                "connected_locations": ["magic_academy", "inn", "shop"],
                "items": ["水筒", "パン", "リンゴ"]
            },
            {
                "id": "inn",
                "name": "冒険者の宿",
                "description": "冒険者たちが集まる古い宿屋。暖炉の火が温かく、様々な噂話が飛び交う。",
                "connected_locations": ["city_square"],
                "items": ["ビール", "ベッド", "ろうそく"]
            }
        ],
        "starting_location": "magic_academy",
        "time": {
            "hour": 12,
            "minute": 0
        },
        "weather": "SUNNY"
    }
    
    file_path = WORLD_TEMPLATES_DIR / "fantasy_world.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(sample_world, f, ensure_ascii=False, indent=2)
        
    logger.info("サンプル世界を作成しました")