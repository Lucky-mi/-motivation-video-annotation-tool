#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试YouTube cookies是否有效
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.downloader import VideoDownloader
import yt_dlp

def test_cookies():
    """测试cookies是否能成功访问YouTube"""

    # 检查cookies文件
    cookies_path = project_root / "cookies.txt"
    print(f"📍 检查cookies文件: {cookies_path}")

    if not cookies_path.exists():
        print(f"❌ cookies.txt 不存在!")
        print(f"\n请按以下步骤导出cookies:")
        print(f"1. 安装浏览器扩展: 'Get cookies.txt LOCALLY'")
        print(f"2. 访问 https://www.youtube.com 并登录")
        print(f"3. 点击扩展图标，导出cookies.txt")
        print(f"4. 将文件保存到: {cookies_path}")
        return False

    print(f"✅ cookies.txt 存在 (大小: {cookies_path.stat().st_size} bytes)")

    # 测试一个简单的YouTube视频
    test_url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"  # YouTube官方测试视频

    print(f"\n🧪 测试下载YouTube视频...")
    print(f"   URL: {test_url}")

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'cookiefile': str(cookies_path.absolute()),
        'extract_flat': True,  # 只提取信息，不下载
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Accept-Language': 'en-us,en;q=0.5',
        },
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print("   正在提取视频信息...")
            info = ydl.extract_info(test_url, download=False)

            print(f"\n✅ Cookies有效!")
            print(f"   视频标题: {info.get('title', 'N/A')}")
            print(f"   上传者: {info.get('uploader', 'N/A')}")
            print(f"   时长: {info.get('duration', 0)} 秒")
            return True

    except Exception as e:
        error_msg = str(e)
        print(f"\n❌ Cookies测试失败!")
        print(f"   错误: {error_msg}")

        if "Sign in to confirm" in error_msg or "bot" in error_msg:
            print(f"\n💡 解决方案:")
            print(f"   1. cookies可能已过期，请重新导出")
            print(f"   2. 确保在登录状态下导出cookies")
            print(f"   3. 导出后立即使用（cookies有时效性）")
            print(f"   4. 尝试使用无痕模式登录YouTube后再导出")

        return False

if __name__ == "__main__":
    print("=" * 60)
    print("YouTube Cookies 测试工具")
    print("=" * 60)

    success = test_cookies()

    if success:
        print("\n" + "=" * 60)
        print("🎉 测试通过! 现在可以开始下载视频了")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("⚠️ 请修复cookies问题后再运行下载任务")
        print("=" * 60)
        sys.exit(1)
