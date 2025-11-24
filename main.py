#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
主启动脚本 - AI辅助视频动机标注系统
"""
import sys
from pathlib import Path
from dotenv import load_dotenv

# 设置Windows控制台编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 加载环境变量
load_dotenv()

# 导入配置管理
from config.config import config

def check_environment():
    """检查环境配置"""
    print("=" * 60)
    print("检查环境配置...")
    print("=" * 60)

    # 检查API Key
    gemini_key = config.get_api_key('gemini')
    if not gemini_key:
        print("⚠️  警告: 未配置 GEMINI_API_KEY")
        print("   AI分析功能将不可用")
        print("   配置方法: 编辑 .env 文件")
    else:
        print(f"✅ GEMINI_API_KEY: {gemini_key[:8]}...")

    # 检查必要的依赖
    required_packages = [
        'streamlit',
        'fastapi',
        'google.generativeai',
        'cv2',
        'pydantic'
    ]

    missing_packages = []
    for package in required_packages:
        try:
            if package == 'cv2':
                __import__('cv2')
            else:
                __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} 未安装")
            missing_packages.append(package)

    if missing_packages:
        print("\n缺少依赖包，请运行:")
        print("  pip install -r requirements.txt")
        return False

    print("\n✅ 环境检查通过!")
    return True


def show_menu():
    """显示菜单"""
    print("\n" + "=" * 60)
    print("AI辅助视频动机标注系统")
    print("=" * 60)
    print("\n请选择启动模式:")
    print("  1. 启动完整系统 (FastAPI后端 + Streamlit前端)")
    print("  2. 仅启动后端API服务 (端口: 8000)")
    print("  3. 仅启动前端界面 (端口: 8501)")
    print("  4. 测试Gemini API连接")
    print("  5. 退出")
    print()


def start_backend():
    """启动后端API服务"""
    import uvicorn
    from backend.api_v2 import app

    backend_port = int(config.get('server.backend_port', 8000))

    print("\n🚀 启动FastAPI后端服务...")
    print(f"📍 API地址: http://localhost:{backend_port}")
    print(f"📖 API文档: http://localhost:{backend_port}/docs")
    print("\n按 Ctrl+C 停止服务\n")

    uvicorn.run(app, host="0.0.0.0", port=backend_port, log_level="info")


def start_frontend():
    """启动前端Streamlit应用 (校验平台)"""
    import subprocess

    frontend_port = int(config.get('server.frontend_port', 8502))

    print("\n🚀 启动Streamlit校验平台...")
    print(f"📍 应用地址: http://localhost:{frontend_port}")
    print("\n按 Ctrl+C 停止服务\n")

    app_path = project_root / "frontend" / "app_verification_only.py"
    subprocess.run([
        sys.executable, "-m", "streamlit", "run",
        str(app_path),
        f"--server.port={frontend_port}"
    ])


def start_full_system():
    """启动完整系统 (后端 + 前端)"""
    import subprocess
    import time

    backend_port = int(config.get('server.backend_port', 8000))
    frontend_port = int(config.get('server.frontend_port', 8502))

    print("\n🚀 启动完整系统...")
    print(f"📍 后端API: http://localhost:{backend_port}")
    print(f"📍 前端界面: http://localhost:{frontend_port}")
    print("\n按 Ctrl+C 停止所有服务\n")

    # 启动后端
    backend_process = subprocess.Popen([
        sys.executable, "-m", "uvicorn",
        "backend.api_v2:app",
        "--host", "0.0.0.0",
        "--port", str(backend_port)
    ])

    # 等待后端启动
    print("⏳ 等待后端启动...")
    time.sleep(3)

    # 启动前端
    app_path = project_root / "frontend" / "app_verification_only.py"
    frontend_process = subprocess.Popen([
        sys.executable, "-m", "streamlit", "run",
        str(app_path),
        f"--server.port={frontend_port}"
    ])

    try:
        # 等待进程
        backend_process.wait()
        frontend_process.wait()
    except KeyboardInterrupt:
        print("\n\n🛑 停止服务...")
        backend_process.terminate()
        frontend_process.terminate()
        print("✅ 已停止所有服务")


def test_gemini():
    """测试Gemini API"""
    from test_gemini import test_gemini_api

    api_key = config.get_api_key('gemini')
    if not api_key:
        print("\n❌ 错误: 未配置 GEMINI_API_KEY")
        print("   配置方法: 编辑 .env 文件")
        print("   获取API Key: https://aistudio.google.com/app/apikey")
        return

    test_gemini_api(api_key)


def main():
    """主函数"""
    # 检查环境
    if not check_environment():
        sys.exit(1)

    while True:
        show_menu()
        choice = input("请选择 (1-5): ").strip()

        if choice == '1':
            start_full_system()
            break
        elif choice == '2':
            start_backend()
            break
        elif choice == '3':
            start_frontend()
            break
        elif choice == '4':
            test_gemini()
        elif choice == '5':
            print("\n👋 再见!")
            break
        else:
            print("\n❌ 无效选择，请重新输入")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 再见!")
        sys.exit(0)
