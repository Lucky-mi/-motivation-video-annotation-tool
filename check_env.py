#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
环境检查脚本
用于诊断项目环境是否配置正确
"""
import sys
from pathlib import Path


def check_environment():
    """检查运行环境"""
    print("=" * 60)
    print("🔍 VLM Motivation 标注平台 - 环境检查")
    print("=" * 60)
    print()

    all_ok = True

    # 1. Python 版本检查
    print("📌 Python 环境")
    print("-" * 60)
    major, minor = sys.version_info[:2]
    print(f"Python 版本: {sys.version.split()[0]}")

    if major >= 3 and minor >= 8:
        print("✅ Python 版本符合要求 (>= 3.8)")
    else:
        print(f"❌ Python 版本过低，需要 >= 3.8，当前 {major}.{minor}")
        all_ok = False
    print()

    # 2. 依赖包检查
    print("📦 依赖包检查")
    print("-" * 60)

    packages = {
        'streamlit': 'Streamlit (Web界面)',
        'cv2': 'OpenCV (视频处理)',
        'google.generativeai': 'Gemini API (AI分析)',
        'yaml': 'PyYAML (配置文件)',
        'numpy': 'NumPy (数值计算)',
        'PIL': 'Pillow (图像处理)',
        'pathlib': 'Pathlib (路径处理)'
    }

    missing_packages = []

    for pkg, desc in packages.items():
        try:
            if pkg == 'cv2':
                import cv2
                version = cv2.__version__
            elif pkg == 'PIL':
                import PIL
                version = PIL.__version__
            elif pkg == 'yaml':
                import yaml
                version = getattr(yaml, '__version__', 'unknown')
            elif pkg == 'google.generativeai':
                import google.generativeai as genai
                version = getattr(genai, '__version__', 'unknown')
            else:
                mod = __import__(pkg)
                version = getattr(mod, '__version__', 'unknown')

            print(f"✅ {pkg:25} ({desc})")
            print(f"   版本: {version}")
        except ImportError as e:
            print(f"❌ {pkg:25} ({desc}) - 未安装")
            missing_packages.append(pkg)
            all_ok = False

    print()

    # 3. 目录结构检查
    print("📁 目录结构检查")
    print("-" * 60)

    required_dirs = [
        'data/videos',
        'data/keyframes',
        'data/annotations',
        'frontend',
        'backend',
        'config'
    ]

    for dir_path in required_dirs:
        p = Path(dir_path)
        if p.exists() and p.is_dir():
            print(f"✅ {dir_path:30} 存在")
        else:
            print(f"❌ {dir_path:30} 不存在")
            all_ok = False

    print()

    # 4. 关键文件检查
    print("📄 关键文件检查")
    print("-" * 60)

    required_files = [
        'frontend/app.py',
        'backend/video_processor_v2.py',
        'backend/annotation_schema.py',
        'config/config.py',
        'requirements.txt'
    ]

    for file_path in required_files:
        p = Path(file_path)
        if p.exists() and p.is_file():
            size = p.stat().st_size
            print(f"✅ {file_path:40} ({size} bytes)")
        else:
            print(f"❌ {file_path:40} 不存在")
            all_ok = False

    print()

    # 5. 配置文件检查
    print("⚙️  配置检查")
    print("-" * 60)

    try:
        from config.config import config

        print("✅ 配置模块加载成功")

        # 检查关键配置
        paths_videos = config.get('paths.videos')
        paths_keyframes = config.get('paths.keyframes')
        paths_annotations = config.get('paths.annotations')

        print(f"   视频目录: {paths_videos}")
        print(f"   关键帧目录: {paths_keyframes}")
        print(f"   标注目录: {paths_annotations}")

        # 检查 Gemini API Key
        gemini_key = config.get_api_key('gemini')
        if gemini_key:
            print(f"✅ Gemini API Key 已配置 ({gemini_key[:10]}...)")
        else:
            print("⚠️  Gemini API Key 未配置（均匀采样模式可用）")

    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        all_ok = False

    print()

    # 6. 总结
    print("=" * 60)
    if all_ok:
        print("🎉 环境检查通过！所有依赖和文件都已就绪")
        print()
        print("💡 下一步：")
        print("   1. 运行 run.bat (Windows) 或 ./run.sh (Linux/Mac)")
        print("   2. 或手动运行: streamlit run frontend/app.py")
    else:
        print("⚠️  环境检查发现问题！")
        print()
        if missing_packages:
            print("📦 缺少的依赖包：")
            for pkg in missing_packages:
                print(f"   - {pkg}")
            print()
            print("💡 解决方案：")
            print("   pip install -r requirements.txt")
        print()
        print("📖 详细排查指南请查看: TROUBLESHOOTING.md")

    print("=" * 60)
    print()

    return all_ok


if __name__ == "__main__":
    try:
        success = check_environment()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ 检查被中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 检查过程出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
