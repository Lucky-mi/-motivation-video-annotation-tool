#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
YouTube 封禁问题诊断和解决脚本
============================
自动检测并提供解决方案
"""
import sys
import os
from pathlib import Path

# 修复 Windows 终端编码问题
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import yt_dlp
from datetime import datetime

def check_cookies():
    """检查 cookies 文件状态"""
    print("\n" + "="*60)
    print("🔍 步骤 1/4: 检查 Cookies 文件")
    print("="*60)

    cookies_path = project_root / "cookies.txt"

    if not cookies_path.exists():
        print("❌ cookies.txt 不存在")
        print("\n💡 解决方案:")
        print("   1. 安装浏览器扩展:")
        print("      Chrome: https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc")
        print("      Firefox: https://addons.mozilla.org/firefox/addon/cookies-txt/")
        print("   2. 在浏览器中登录 youtube.com")
        print("   3. 点击扩展图标，导出为 cookies.txt")
        print("   4. 将文件保存到项目根目录")
        return False

    # 检查文件大小和更新时间
    file_size = cookies_path.stat().st_size
    mod_time = datetime.fromtimestamp(cookies_path.stat().st_mtime)
    days_old = (datetime.now() - mod_time).days

    print(f"✅ cookies.txt 存在")
    print(f"   文件大小: {file_size} 字节")
    print(f"   最后更新: {mod_time.strftime('%Y-%m-%d %H:%M:%S')} ({days_old} 天前)")

    # 检查关键 cookies
    with open(cookies_path, 'r', encoding='utf-8') as f:
        content = f.read()

    has_visitor = 'VISITOR_INFO1_LIVE' in content
    has_sid = 'SSID' in content or 'PSID' in content

    print(f"   关键 Cookie - VISITOR_INFO: {'✅' if has_visitor else '❌'}")
    print(f"   关键 Cookie - SID: {'✅' if has_sid else '❌'}")

    if days_old > 7:
        print("\n⚠️  警告: Cookies 已超过 7 天，建议更新")
        return False

    if not (has_visitor and has_sid):
        print("\n⚠️  警告: Cookies 不完整")
        return False

    print("✅ Cookies 状态良好")
    return True

def test_youtube_access():
    """测试 YouTube 访问"""
    print("\n" + "="*60)
    print("🔍 步骤 2/4: 测试 YouTube 访问")
    print("="*60)

    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Astley - Never Gonna Give You Up

    cookies_path = project_root / "cookies.txt"

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'extract_flat': False,
        'cookiefile': str(cookies_path) if cookies_path.exists() else None,
    }

    try:
        print(f"正在访问测试视频...")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(test_url, download=False)

        print(f"✅ 成功访问 YouTube")
        print(f"   视频标题: {info.get('title', 'Unknown')[:50]}")
        print(f"   时长: {info.get('duration', 0)} 秒")
        return True

    except Exception as e:
        error_msg = str(e)
        print(f"❌ 访问失败: {error_msg[:200]}")

        if "Sign in to confirm" in error_msg or "not a bot" in error_msg:
            print("\n💡 检测原因: YouTube 要求人机验证")
            print("   解决方案:")
            print("   1. 更新 cookies.txt (推荐)")
            print("   2. 使用代理/VPN")
            print("   3. 增加请求间隔时间")

        elif "rate-limited" in error_msg.lower():
            print("\n💡 检测原因: 请求过于频繁")
            print("   解决方案:")
            print("   1. 等待 10-30 分钟后重试")
            print("   2. 降低并发数 (AI_REVIEW_WORKERS=1)")
            print("   3. 增加请求延迟")

        elif "unavailable" in error_msg.lower():
            print("\n💡 检测原因: 视频不可用或地区限制")
            print("   解决方案:")
            print("   1. 检查网络连接")
            print("   2. 使用 VPN 更换地区")

        return False

def check_network():
    """检查网络配置"""
    print("\n" + "="*60)
    print("🔍 步骤 3/4: 检查网络配置")
    print("="*60)

    import socket

    try:
        # 测试 DNS 解析
        socket.gethostbyname("www.youtube.com")
        print("✅ DNS 解析正常")
    except:
        print("❌ DNS 解析失败")
        print("   解决方案: 检查网络连接或 DNS 设置")
        return False

    try:
        # 测试连接
        sock = socket.create_connection(("www.youtube.com", 443), timeout=5)
        sock.close()
        print("✅ 网络连接正常")
        return True
    except:
        print("❌ 无法连接 YouTube")
        print("   解决方案:")
        print("   1. 检查防火墙设置")
        print("   2. 检查是否需要 VPN")
        return False

def provide_solutions():
    """提供综合解决方案"""
    print("\n" + "="*60)
    print("📋 步骤 4/4: 综合解决方案")
    print("="*60)

    print("\n【优先级 1 - 立即尝试】更新 Cookies")
    print("─" * 60)
    print("1. 在浏览器中访问 https://youtube.com 并登录")
    print("2. 安装 cookies 导出扩展:")
    print("   - Chrome/Edge: Get cookies.txt LOCALLY")
    print("   - Firefox: cookies.txt")
    print("3. 导出并替换 cookies.txt 文件")
    print("4. 重新运行下载脚本")

    print("\n【优先级 2 - 配置优化】减少请求频率")
    print("─" * 60)
    print("修改 config/search_config.py:")
    print("   AI_REVIEW_WORKERS = 1  # 降低并发")
    print("   VIDEOS_PER_KEYWORD = 5  # 减少每次搜索数量")

    print("\n【优先级 3 - 使用代理】")
    print("─" * 60)
    print("如果有代理，可以在脚本中添加:")
    print("   dl = VideoDownloader(proxy='http://127.0.0.1:7890')")

    print("\n【优先级 4 - 等待冷却】")
    print("─" * 60)
    print("如果被限制，建议:")
    print("   1. 等待 30 分钟 - 2 小时")
    print("   2. 更换 IP (重启路由器或使用 VPN)")
    print("   3. 使用不同的 Google 账号")

    print("\n【紧急方案】使用备用下载方式")
    print("─" * 60)
    print("尝试使用:")
    print("   yt-dlp --cookies cookies.txt --proxy socks5://127.0.0.1:1080 [URL]")

def main():
    print("\n" + "="*60)
    print("🔧 YouTube 封禁问题诊断工具")
    print("="*60)
    print(f"项目路径: {project_root}")
    print(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 运行诊断
    cookies_ok = check_cookies()
    network_ok = check_network()
    access_ok = test_youtube_access()

    # 总结
    print("\n" + "="*60)
    print("📊 诊断结果")
    print("="*60)
    print(f"Cookies 状态: {'✅ 正常' if cookies_ok else '❌ 需要更新'}")
    print(f"网络状态: {'✅ 正常' if network_ok else '❌ 异常'}")
    print(f"YouTube 访问: {'✅ 正常' if access_ok else '❌ 被限制'}")

    if access_ok:
        print("\n🎉 一切正常！可以正常使用下载功能")
        return 0
    else:
        provide_solutions()
        return 1

if __name__ == "__main__":
    exit(main())
