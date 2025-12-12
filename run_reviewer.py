# run_reviewer.py
"""
标注审核平台启动脚本
"""
import subprocess
import sys
import os
import time
from pathlib import Path

def check_dependencies():
    """检查依赖"""
    required = ['streamlit', 'fastapi', 'uvicorn']
    missing = []

    for pkg in required:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)

    if missing:
        print(f"缺少依赖: {', '.join(missing)}")
        print("请运行: pip install " + ' '.join(missing))
        return False
    return True


def start_backend():
    """启动后端API"""
    print("启动后端API服务...")
    backend_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.api_reviewer:app", "--host", "0.0.0.0", "--port", "8001", "--reload"],
        cwd=Path(__file__).parent
    )
    return backend_process


def start_frontend():
    """启动前端"""
    print("启动前端服务...")
    frontend_process = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "frontend/annotation_reviewer_v3.py", "--server.port", "8502"],
        cwd=Path(__file__).parent
    )
    return frontend_process


def main():
    print("=" * 50)
    print("  标注质量检查平台")
    print("=" * 50)
    print()

    if not check_dependencies():
        sys.exit(1)

    print("选择启动模式:")
    print("1. 完整系统 (后端API + 前端)")
    print("2. 仅前端 (Streamlit)")
    print("3. 仅后端API")
    print("4. 退出")
    print()

    choice = input("请选择 (1-4): ").strip()

    processes = []

    try:
        if choice == '1':
            # 启动后端
            backend = start_backend()
            processes.append(backend)
            time.sleep(2)

            # 启动前端
            frontend = start_frontend()
            processes.append(frontend)

            print()
            print("=" * 50)
            print("服务已启动:")
            print("  前端: http://localhost:8502")
            print("  后端API: http://localhost:8001")
            print("  API文档: http://localhost:8001/docs")
            print("=" * 50)
            print()
            print("按 Ctrl+C 停止服务")

            # 等待进程
            for p in processes:
                p.wait()

        elif choice == '2':
            frontend = start_frontend()
            processes.append(frontend)

            print()
            print("前端已启动: http://localhost:8502")
            print("按 Ctrl+C 停止服务")

            frontend.wait()

        elif choice == '3':
            backend = start_backend()
            processes.append(backend)

            print()
            print("后端API已启动: http://localhost:8001")
            print("API文档: http://localhost:8001/docs")
            print("按 Ctrl+C 停止服务")

            backend.wait()

        elif choice == '4':
            print("退出")
            sys.exit(0)

        else:
            print("无效选择")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n正在停止服务...")
        for p in processes:
            p.terminate()
        print("服务已停止")


if __name__ == "__main__":
    main()
