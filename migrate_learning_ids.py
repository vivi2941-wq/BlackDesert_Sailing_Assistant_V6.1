#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
遷移學習記錄中的ID

當公共種子數據更新時，ITEM_MISC_* ID被替換為ITEM_PUBLIC_* ID
這個腳本會自動將學習記錄中的舊ID更新為新ID

需要遷移的文件：
1. ocr_evidence_identity_corrections.json - OCR原文學習
2. ocr_visual_item_memory.json - 視覺學習
3. ocr_aliases.json - 別名系統
"""

import json
import os
import shutil
from datetime import datetime

# 路徑
# 從環境變量或默認位置獲取玩家數據路徑
PLAYER_DATA = os.environ.get("BDO_PLAYER_DATA", os.path.join(os.getenv("LOCALAPPDATA"), "BDO_Sailing_Assistant_Player", "data"))
OBSERVED_REGISTRY = os.path.join(PLAYER_DATA, "observed_item_registry.json")
IDENTITY_CORRECTIONS = os.path.join(PLAYER_DATA, "ocr_evidence_identity_corrections.json")
VISUAL_MEMORY = os.path.join(PLAYER_DATA, "ocr_visual_item_memory.json")
ALIASES = os.path.join(PLAYER_DATA, "ocr_aliases.json")

def normalize_name(name):
    """正規化名稱（與程式使用的相同邏輯）"""
    import unicodedata
    text = "".join(unicodedata.normalize("NFKC", str(name or "")).strip().split())
    table = str.maketrans({
        "島":"岛","黃":"黄","賊":"贼","餘":"余","換":"换","數":"数",
        "罈":"罐","瑪":"玛","麗":"丽","燈":"灯","鹽":"盐","幣":"币",
        "華":"华","團":"团","騎":"骑","頭":"头","龍":"龙","樹":"树",
        "塊":"块","觀":"观","測":"测","報":"报","書":"书","鴉":"鸦",
        "烏":"乌","遺":"遗","運":"运","結":"结","質":"质","貿":"贸",
        "維":"维","藍":"蓝","鑄":"铸","鏡":"镜","偵":"侦","戰":"战",
        "鬥":"斗","糧":"粮","統":"统","傳":"传","遠":"远","裝":"装",
        "飾":"饰","漿":"浆","櫻":"樱","參":"参","鱗":"鳞","斷":"断",
        "萬":"万","綠":"绿","門":"门","槍":"枪","飲":"饮","錫":"锡",
        "魚":"鱼","鷹":"鹰","頸":"颈","髏":"髅","製":"制","絲":"丝",
        "綢":"绸","銅":"铜","鑰":"钥","蘿":"萝","蔔":"卜","練":"练",
        "堅":"坚","縫":"缝","織":"织","獲":"获","協":"协","級":"级",
        "燭":"烛","臺":"台","楓":"枫"
    })
    return text.translate(table)

def build_id_mapping():
    """
    建立ID映射表
    將學習記錄中的ID映射到registry中對應的ID
    根據名稱匹配
    """
    print("讀取 observed_item_registry.json...")
    with open(OBSERVED_REGISTRY, "r", encoding="utf-8") as f:
        registry = json.load(f)
    
    # 建立名稱到ID的映射
    name_to_id = {}
    for item in registry.get("items", []):
        if isinstance(item, dict):
            item_id = item.get("item_id")
            names = item.get("names", [])
            for name in names:
                norm_name = normalize_name(name)
                if norm_name:
                    name_to_id[norm_name] = item_id
    
    print(f"Registry中共有 {len(name_to_id)} 個名稱")
    return name_to_id

def migrate_file(file_path, name_to_id, id_field_name="id", name_field_name="name"):
    """
    遷移文件中的ID
    根據名稱匹配registry中的ID
    
    Args:
        file_path: 文件路徑
        name_to_id: 名稱到ID的映射
        id_field_name: ID字段名（如 "id" 或 "item_id"）
        name_field_name: 名稱字段名
    """
    if not os.path.exists(file_path):
        print(f"跳過不存在的文件: {file_path}")
        return 0
    
    print(f"處理文件: {file_path}")
    
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        print(f"  文件格式不是列表，跳過")
        return 0
    
    changed = 0
    for record in data:
        if not isinstance(record, dict):
            continue
        
        old_id = record.get(id_field_name)
        name = record.get(name_field_name, "")
        
        if old_id and name:
            norm_name = normalize_name(name)
            if norm_name in name_to_id:
                new_id = name_to_id[norm_name]
                if new_id != old_id:
                    record[id_field_name] = new_id
                    changed += 1
                    # print(f"  更新: {old_id} → {new_id} ({name})")
    
    if changed > 0:
        # 備份
        backup_path = file_path + f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(file_path, backup_path)
        print(f"  備份: {backup_path}")
        
        # 保存
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"  已更新 {changed} 條記錄")
    else:
        print(f"  沒有需要更新的記錄")
    
    return changed

def main():
    print("=" * 60)
    print("學習記錄ID遷移工具")
    print("=" * 60)
    print()
    
    # 檢查文件是否存在
    if not os.path.exists(OBSERVED_REGISTRY):
        print(f"錯誤: observed_item_registry.json 不存在")
        print(f"路徑: {OBSERVED_REGISTRY}")
        return
    
    # 建立名稱到ID的映射
    name_to_id = build_id_mapping()
    print()
    
    if not name_to_id:
        print("Registry中沒有名稱映射")
        return
    
    print()
    print("開始遷移...")
    print()
    
    # 遷移各個文件
    total_changed = 0
    
    # 1. OCR原文學習
    print("1. 遷移 OCR原文學習記錄...")
    total_changed += migrate_file(IDENTITY_CORRECTIONS, name_to_id, "id", "name")
    print()
    
    # 2. 視覺學習
    print("2. 遷移視覺學習記錄...")
    total_changed += migrate_file(VISUAL_MEMORY, name_to_id, "item_id", "name")
    print()
    
    # 3. 別名系統
    print("3. 遷移別名記錄...")
    total_changed += migrate_file(ALIASES, name_to_id, "id", "alias")
    print()
    
    print("=" * 60)
    print(f"遷移完成！共更新 {total_changed} 條記錄")
    print("=" * 60)
    print()
    print("建議:")
    print("1. 檢查備份文件，確認遷移正確")
    print("2. 重新啟動程式測試OCR識別")
    print("3. 如果發現問題，可以從備份恢復")

if __name__ == "__main__":
    main()
