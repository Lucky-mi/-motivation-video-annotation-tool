#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
配置检查工具 - 验证API Key配置是否正确
"""
from pathlib import Path
from dotenv import load_dotenv
import os
import sys

# 设置Windows控制台编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def check_config():
    """检查配置"""
    print("=" * 60)
    print("  API配置检查工具")
    print("=" * 60)
    print()

    # 加载 .env 文件
    env_path = Path(".env")
    if env_path.exists():
        print(f"✅ 找到配置文件: {env_path.absolute()}")
        load_dotenv()
    else:
        print(f"❌ 未找到 .env 文件")
        print(f"   请在项目根目录创建 .env 文件")
        print(f"   参考: API_KEY配置说明.md")
        return False

    print()
    print("-" * 60)
    print("API Key 配置状态:")
    print("-" * 60)

    # 检查各个API Key
    api_keys = {
        'GEMINI_API_KEY': 'Gemini (Google AI)',
        'OPENAI_API_KEY': 'OpenAI',
        'ANTHROPIC_API_KEY': 'Claude (Anthropic)'
    }

    found_any = False

    for key, name in api_keys.items():
        value = os.getenv(key)
        if value:
            # 隐藏大部分密钥，只显示前后几位
            masked = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "***"
            print(f"✅ {name:25s} : {masked}")
            found_any = True
        else:
            print(f"⚠️  {name:25s} : 未配置")

    print("-" * 60)

    if not found_any:
        print()
        print("❌ 没有配置任何API Key！")
        print()
        print("请编辑 .env 文件并添加至少一个API Key:")
        print()
        print("  GEMINI_API_KEY=your_key_here")
        print()
        return False

    # 检查端口配置
    print()
    print("-" * 60)
    print("端口配置:")
    print("-" * 60)

    backend_port = os.getenv('BACKEND_PORT', '8000')
    frontend_port = os.getenv('FRONTEND_PORT', '8502')

    print(f"后端API端口: {backend_port}")
    print(f"前端应用端口: {frontend_port}")
    print("-" * 60)

    # 测试配置管理器
    print()
    print("-" * 60)
    print("测试配置管理器:")
    print("-" * 60)

    try:
        from config.config import config

        # 测试读取
        gemini_key = config.get_api_key('gemini')
        if gemini_key:
            print(f"✅ config.get_api_key('gemini'): {gemini_key[:8]}...")
        else:
            print(f"⚠️  config.get_api_key('gemini'): 未配置")

        print("-" * 60)
    except Exception as e:
        print(f"❌ 配置管理器测试失败: {e}")

    print()
    print("=" * 60)
    print("✅ 配置检查完成！")
    print("=" * 60)
    print()
    print("提示:")
    print("  - 如需修改API Key，请编辑 .env 文件")
    print("  - 修改后需要重启应用才能生效")
    print("  - 详细说明请查看: API_KEY配置说明.md")
    print()

    return True

if __name__ == "__main__":
    check_config()
