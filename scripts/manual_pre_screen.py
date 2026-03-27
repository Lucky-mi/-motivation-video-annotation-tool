import sys
import os
import json
import subprocess
import logging
from pathlib import Path

# ================= 配置区域 =================
VIDEO_DIR = Path("data/Youtube_videos")
# 专门记录人工审核结果的文件 (文件名 -> 状态)
STATUS_FILE = Path("data/manual_review_status.json")

# 自动查找 PotPlayer
POTPLAYER_CANDIDATES = [
    r"C:\\Program Files\\DAUM\\PotPlayer\\PotPlayerMini64.exe",
    r"C:\\Program Files (x86)\\DAUM\\PotPlayer\\PotPlayerMini64.exe",
    r"C:\\Program Files\\DAUM\\PotPlayer\\PotPlayerMini.exe",
    r"D:\\Program Files\\DAUM\\PotPlayer\\PotPlayerMini64.exe",
    r"D:\\Appdata\\PotPlayer\\PotPlayerMini64.exe",
]
MANUAL_PLAYER_PATH = None
# ===========================================

logging.basicConfig(level=logging.INFO, format='%(message)s')

def get_player_path():
    if MANUAL_PLAYER_PATH and os.path.exists(MANUAL_PLAYER_PATH):
        return MANUAL_PLAYER_PATH
    for path in POTPLAYER_CANDIDATES:
        if os.path.exists(path):
            return path
    return None

def load_status():
    if not STATUS_FILE.exists():
        return {}
    try:
        with open(STATUS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

def save_status(status_data):
    try:
        with open(STATUS_FILE, 'w', encoding='utf-8') as f:
            json.dump(status_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"❌ 保存状态失败: {e}")

def open_video(filepath):
    """
    启动播放器并返回进程对象
    """
    player = get_player_path()
    try:
        if player:
            # 使用 Popen 启动，非阻塞，且返回进程句柄
            return subprocess.Popen([player, str(filepath)])
        else:
            # 回退方案 (无法自动关闭)
            if sys.platform == 'win32': os.startfile(filepath)
            elif sys.platform == 'darwin': subprocess.call(('open', filepath))
            else: subprocess.call(('xdg-open', filepath))
            return None
    except Exception as e:
        print(f"❌ 启动播放器失败: {e}")
        return None

def main():
    print("==================================================")
    print("🎬 视频筛选器 (自动关闭版)")
    print("==================================================")
    print(f"📄 状态记录: {STATUS_FILE}")
    
    if not VIDEO_DIR.exists():
        print("❌ 视频目录不存在")
        return

    # 1. 加载历史记录
    status_db = load_status()
    
    # 2. 扫描文件夹
    video_exts = {'.mp4', '.mkv', '.webm'}
    all_files = sorted([f for f in VIDEO_DIR.iterdir() if f.suffix.lower() in video_exts], key=lambda x: x.name)
    
    # 3. 过滤出未审核的视频
    to_review = []
    stats = {"keep": 0, "delete": 0, "pending": 0}
    
    for f in all_files:
        filename = f.name
        # 检查记录
        if filename in status_db:
            s = status_db[filename]
            if s == "keep": stats["keep"] += 1
            elif s == "delete": stats["delete"] += 1
        else:
            to_review.append(f)
            stats["pending"] += 1

    print(f"📊 统计: 总文件 {len(all_files)}")
    print(f"   ✅ 已保留: {stats['keep']}")
    print(f"   🗑️ 待删除: {stats['delete']} (在列表中但文件未删)")
    print(f"   ⏳ 待审核: {len(to_review)}")

    # 4. 如果有待删除的任务，先问一下是否执行清理
    if stats["delete"] > 0:
        check_cleanup(status_db)
        # 重新加载一遍状态和文件，因为可能刚刚删除了
        status_db = load_status()
        to_review = [f for f in to_review if f.exists()] # 刷新列表

    if not to_review:
        print("\n🎉 没有新视频需要审核！")
        return

    # 5. 开始审核
    print("\n🚀 开始审核新视频 (按 Q 退出并保存)")
    print("--------------------------------------------------")
    
    player_path = get_player_path()
    if not player_path:
        print("⚠️ 未找到PotPlayer，使用系统默认 (可能无法自动关闭窗口)。")

    count = 0
    for vid_file in to_review:
        count += 1
        print(f"\n[{count}/{len(to_review)}] 📺 {vid_file.name}")
        
        # 启动播放器并获取进程句柄
        player_process = open_video(vid_file)
        
        while True:
            # 交互循环
            choice = input("   👉 保留? (Y/n/q): ").strip().lower()
            
            # 做出决定后，立即关闭播放器
            if player_process:
                try:
                    player_process.kill()  # 强行关闭窗口
                    player_process.wait()  # 等待进程完全结束
                except Exception:
                    pass # 忽略关闭失败的情况 (比如用户已经手动关了)

            if choice == 'q':
                print("👋 暂停审核")
                check_cleanup(status_db)
                return
            
            elif choice == '' or choice == 'y':
                print("   ✅ [KEEP]")
                status_db[vid_file.name] = "keep"
                save_status(status_db)
                break
                
            elif choice == 'n':
                print("   ❌ [DELETE] (标记为待删除)")
                status_db[vid_file.name] = "delete"
                save_status(status_db)
                break
    
    print("\n🎉 审核完成！")
    check_cleanup(status_db)

def check_cleanup(status_db):
    """根据JSON记录执行批量删除"""
    to_delete_files = []
    
    # 遍历 status_db 找到标记为 delete 且文件依然存在的
    for filename, status in status_db.items():
        if status == "delete":
            file_path = VIDEO_DIR / filename
            if file_path.exists():
                to_delete_files.append(file_path)
    
    if not to_delete_files:
        return

    print(f"\n🧹 清理助手: 发现 {len(to_delete_files)} 个标记为 'delete' 的文件。")
    print(f"   (这些文件记录在 {STATUS_FILE} 中)")
    
    user_input = input("   ⚠️  是否立即执行物理删除? (yes/N): ").strip().lower()
    
    if user_input == 'yes':
        deleted_count = 0
        for f in to_delete_files:
            try:
                f.unlink()
                deleted_count += 1
                print(f"   已删除: {f.name}")
            except Exception as e:
                print(f"   删除失败 {f.name}: {e}")
        print(f"✅ 清理完毕，共删除 {deleted_count} 个文件。")
    else:
        print("   已取消，文件保留。下次运行脚本时会再次询问。")

if __name__ == "__main__":
    main()