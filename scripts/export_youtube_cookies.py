#!/usr/bin/env python3
"""
导出YouTube Cookies并配置到downloader
使用方法：
1. 在Chrome/Edge浏览器登录YouTube
2. 运行此脚本: python scripts/export_youtube_cookies.py
3. 重新运行下载脚本
"""
import subprocess
import sys
from pathlib import Path

def export_cookies():
    print("=" * 80)
    print("📝 YouTube Cookies导出工具")
    print("=" * 80)

    print("\n请选择浏览器:")
    print("1. Chrome")
    print("2. Edge")
    print("3. Firefox")
    print("4. 手动提供cookies文件路径")

    choice = input("\n选择 (1-4): ").strip()

    browser_map = {
        "1": "chrome",
        "2": "edge",
        "3": "firefox"
    }

    cookies_file = Path("data/youtube_cookies.txt")

    if choice in browser_map:
        browser = browser_map[choice]
        print(f"\n🔍 正在从 {browser} 导出cookies...")

        # 使用yt-dlp导出cookies
        cmd = [
            "yt-dlp",
            "--cookies-from-browser", browser,
            "--cookies", str(cookies_file),
            "--no-download",
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # 任意YouTube视频
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if cookies_file.exists():
                print(f"✅ Cookies已导出到: {cookies_file}")
                print(f"   文件大小: {cookies_file.stat().st_size} bytes")

                # 更新downloader配置
                update_downloader_config(str(cookies_file))
            else:
                print("❌ Cookies导出失败")
                print(f"错误: {result.stderr}")
                print("\n💡 提示:")
                print("   1. 确保你已在浏览器中登录YouTube")
                print("   2. 尝试关闭浏览器后重试")
        except FileNotFoundError:
            print("❌ yt-dlp未安装")
            print("请运行: pip install yt-dlp")

    elif choice == "4":
        manual_path = input("请输入cookies文件路径: ").strip()
        if Path(manual_path).exists():
            cookies_file = Path(manual_path)
            update_downloader_config(str(cookies_file))
        else:
            print(f"❌ 文件不存在: {manual_path}")
    else:
        print("❌ 无效选择")

def update_downloader_config(cookies_path):
    """更新downloader配置以使用cookies"""
    print(f"\n⚙️ 更新配置...")

    # 读取downloader.py
    downloader_file = Path("backend/downloader.py")
    content = downloader_file.read_text(encoding='utf-8')

    # 检查是否已配置cookies
    if "self.cookies_file" in content:
        print("✅ Cookies配置已存在")
    else:
        print("💡 请手动在 backend/downloader.py 中添加cookies配置")
        print("\n添加方法:")
        print("1. 在 __init__ 方法中添加:")
        print(f'   self.cookies_file = "{cookies_path}"')
        print("\n2. 在 ydl_opts 中添加:")
        print('   "cookiefile": self.cookies_file,')

    print(f"\n✅ 完成！Cookies文件位置: {cookies_path}")
    print("\n下次运行下载脚本时会自动使用这些cookies")

if __name__ == "__main__":
    export_cookies()
