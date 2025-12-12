#!/usr/bin/env python3
"""
自动构建发布包脚本

使用方法：
    python scripts/build_release.py --version lite  # 构建轻量版
    python scripts/build_release.py --version full  # 构建完整版
    python scripts/build_release.py --version both  # 构建两个版本
"""
import os
import shutil
import zipfile
from pathlib import Path
import argparse
from datetime import datetime


class ReleaseBuilder:
    """发布包构建器"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.release_dir = project_root / "release_packages"
        self.output_dir = project_root / "releases"
        self.output_dir.mkdir(exist_ok=True)

    def build_lite_version(self):
        """构建轻量级版本"""
        print("Building V3 Lite Annotation Package...")

        lite_name = f"video_annotation_v3_lite_{datetime.now().strftime('%Y%m%d')}"
        lite_dir = self.output_dir / lite_name

        # 清理旧目录
        if lite_dir.exists():
            shutil.rmtree(lite_dir)
        lite_dir.mkdir(parents=True)

        # 1. 复制核心脚本
        print("  Copying scripts...")
        scripts_dir = lite_dir / "scripts"
        scripts_dir.mkdir()
        shutil.copy2(
            self.project_root / "scripts" / "annotate_with_v3.py",
            scripts_dir / "annotate_with_v3.py"
        )

        # 2. 复制 backend
        print("  Copying backend code...")
        backend_src = self.project_root / "backend"
        backend_dst = lite_dir / "backend"

        # 需要的文件
        backend_files = [
            "__init__.py",
            "annotation_schema_v3.py",
            "vlm_analyzer.py",
            "models.py",
        ]

        backend_dst.mkdir()
        for file in backend_files:
            src = backend_src / file
            if src.exists():
                shutil.copy2(src, backend_dst / file)

        # 复制 ai_providers 目录
        ai_providers_src = backend_src / "ai_providers"
        ai_providers_dst = backend_dst / "ai_providers"
        if ai_providers_src.exists():
            shutil.copytree(ai_providers_src, ai_providers_dst)

        # 3. 复制 config
        print("  Copying config...")
        config_src = self.project_root / "config"
        config_dst = lite_dir / "config"
        config_dst.mkdir()

        config_files = ["__init__.py", "config.py"]
        for file in config_files:
            src = config_src / file
            if src.exists():
                shutil.copy2(src, config_dst / file)

        # 创建默认 config.yaml
        config_yaml = config_dst / "config.yaml"
        config_yaml.write_text("""paths:
  videos: 'data/videos'
  keyframes: 'data/keyframes'
  annotations: 'data/annotations_v3'

extraction:
  mode: 'uniform'
  interval_seconds: 5.0
  max_frames: 50

api_keys:
  gemini: null
  openai: null
""")

        # 4. 创建数据目录
        print("  Creating data directories...")
        (lite_dir / "data" / "videos").mkdir(parents=True)
        (lite_dir / "data" / "keyframes").mkdir(parents=True)
        (lite_dir / "data" / "annotations_v3").mkdir(parents=True)

        # 添加 .gitkeep
        for d in ["videos", "keyframes", "annotations_v3"]:
            (lite_dir / "data" / d / ".gitkeep").touch()

        # 5. 复制配置文件
        print("  Copying config files...")
        shutil.copy2(
            self.release_dir / "v3_lite" / "requirements.txt",
            lite_dir / "requirements.txt"
        )
        shutil.copy2(
            self.release_dir / "v3_lite" / ".env.example",
            lite_dir / ".env.example"
        )
        shutil.copy2(
            self.release_dir / "v3_lite" / "README.md",
            lite_dir / "README.md"
        )

        # 6. 创建快速启动脚本
        print("  Creating startup scripts...")

        # Windows 批处理
        quick_start_bat = lite_dir / "quick_start.bat"
        quick_start_bat.write_text("""@echo off
echo ====================================
echo Theory of Mind 视频标注系统 V3
echo ====================================
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

REM 检查 .env
if not exist .env (
    echo 首次运行，需要配置...
    if not exist .env.example (
        echo 错误: 未找到 .env.example
        pause
        exit /b 1
    )
    copy .env.example .env
    echo 已创建 .env 文件
    echo 请编辑 .env 填入你的 Gemini API Key
    echo 然后重新运行此脚本
    pause
    exit /b 0
)

REM 检查依赖
echo 检查依赖...
pip install -r requirements.txt

echo.
echo 系统已就绪！
echo.
echo 使用方法：
echo 1. 将视频放入 data/videos/ 目录
echo 2. 运行: python scripts/annotate_with_v3.py data/videos/your_video.mp4
echo 3. 查看结果: data/annotations_v3/your_video.json
echo.
pause
""")

        # Linux/Mac 脚本
        quick_start_sh = lite_dir / "quick_start.sh"
        quick_start_sh.write_text("""#!/bin/bash

echo "===================================="
echo "Theory of Mind 视频标注系统 V3"
echo "===================================="
echo

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 Python，请先安装 Python 3.8+"
    exit 1
fi

# 检查 .env
if [ ! -f .env ]; then
    echo "首次运行，需要配置..."
    if [ ! -f .env.example ]; then
        echo "错误: 未找到 .env.example"
        exit 1
    fi
    cp .env.example .env
    echo "已创建 .env 文件"
    echo "请编辑 .env 填入你的 Gemini API Key"
    echo "然后重新运行此脚本"
    exit 0
fi

# 检查依赖
echo "检查依赖..."
pip3 install -r requirements.txt

echo
echo "系统已就绪！"
echo
echo "使用方法："
echo "1. 将视频放入 data/videos/ 目录"
echo "2. 运行: python3 scripts/annotate_with_v3.py data/videos/your_video.mp4"
echo "3. 查看结果: data/annotations_v3/your_video.json"
echo
""")
        quick_start_sh.chmod(0o755)

        # 7. 打包为 zip
        print("  Creating ZIP package...")
        zip_path = self.output_dir / f"{lite_name}.zip"
        self._create_zip(lite_dir, zip_path)

        print(f"Lite version build complete: {zip_path}")
        return zip_path

    def build_full_version(self):
        """构建完整版本"""
        print("Building Full Annotation System...")

        full_name = f"video_annotation_full_{datetime.now().strftime('%Y%m%d')}"
        full_dir = self.output_dir / full_name

        # 清理旧目录
        if full_dir.exists():
            shutil.rmtree(full_dir)
        full_dir.mkdir(parents=True)

        print("  Copying project files...")

        # 要包含的目录和文件
        include_dirs = [
            "scripts",
            "backend",
            "frontend",
            "config"
        ]

        include_files = [
            "annotation.py",
            "requirements.txt",
            ".env.example",
        ]

        # 复制目录
        for dir_name in include_dirs:
            src = self.project_root / dir_name
            dst = full_dir / dir_name
            if src.exists():
                shutil.copytree(
                    src, dst,
                    ignore=shutil.ignore_patterns(
                        '__pycache__', '*.pyc', '*.pyo', '.pytest_cache'
                    )
                )

        # 复制文件
        for file_name in include_files:
            src = self.project_root / file_name
            if src.exists():
                shutil.copy2(src, full_dir / file_name)

        # 复制 README
        shutil.copy2(
            self.release_dir / "full_version" / "README.md",
            full_dir / "README.md"
        )

        # 创建数据目录
        print("  Creating data directories...")
        data_dirs = ["videos", "keyframes", "annotations", "annotations_v3", "metadata"]
        for d in data_dirs:
            dir_path = full_dir / "data" / d
            dir_path.mkdir(parents=True, exist_ok=True)
            (dir_path / ".gitkeep").touch()

        # 创建启动脚本
        print("  Creating startup scripts...")

        # Web 启动脚本 (Windows)
        start_web_bat = full_dir / "start_web.bat"
        start_web_bat.write_text("""@echo off
echo 启动 Web 界面...
streamlit run frontend/app_v2.py
pause
""")

        # Web 启动脚本 (Linux/Mac)
        start_web_sh = full_dir / "start_web.sh"
        start_web_sh.write_text("""#!/bin/bash
echo "启动 Web 界面..."
streamlit run frontend/app_v2.py
""")
        start_web_sh.chmod(0o755)

        # 打包为 zip
        print("  Creating ZIP package...")
        zip_path = self.output_dir / f"{full_name}.zip"
        self._create_zip(full_dir, zip_path)

        print(f"Full version build complete: {zip_path}")
        return zip_path

    def _create_zip(self, source_dir: Path, output_path: Path):
        """创建 ZIP 压缩包"""
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in source_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(source_dir.parent)
                    zipf.write(file_path, arcname)


def main():
    # 设置控制台编码为 UTF-8（Windows）
    import sys
    if sys.platform == 'win32':
        try:
            import locale
            locale.setlocale(locale.LC_ALL, '')
        except:
            pass

    parser = argparse.ArgumentParser(description="构建发布包")
    parser.add_argument(
        '--version',
        choices=['lite', 'full', 'both'],
        default='both',
        help='要构建的版本'
    )

    args = parser.parse_args()

    # 获取项目根目录
    project_root = Path(__file__).parent.parent

    builder = ReleaseBuilder(project_root)

    print("=" * 60)
    print("Video Annotation System - Release Builder")
    print("=" * 60)
    print()

    if args.version in ['lite', 'both']:
        builder.build_lite_version()
        print()

    if args.version in ['full', 'both']:
        builder.build_full_version()
        print()

    print("=" * 60)
    print("Build Complete!")
    print(f"Output directory: {builder.output_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()
