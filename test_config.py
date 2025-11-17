#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
配置功能测试脚本
验证所有配置方法是否正常工作
"""
from pathlib import Path
import sys

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent))

from config.config import config


def test_config_methods():
    """测试配置方法"""
    print("=" * 60)
    print("🧪 配置功能测试")
    print("=" * 60)
    print()

    # 测试 get_str
    print("1️⃣ 测试 get_str() 方法")
    print("-" * 60)

    videos_path = config.get_str('paths.videos', 'data/videos')
    print(f"✅ videos_path = '{videos_path}'")
    print(f"   类型: {type(videos_path)}")
    assert isinstance(videos_path, str), "应该返回 str 类型"
    assert videos_path is not None, "不应该返回 None"

    keyframes_path = config.get_str('paths.keyframes', 'data/keyframes')
    print(f"✅ keyframes_path = '{keyframes_path}'")
    print(f"   类型: {type(keyframes_path)}")
    assert isinstance(keyframes_path, str), "应该返回 str 类型"

    annotations_path = config.get_str('paths.annotations', 'data/annotations')
    print(f"✅ annotations_path = '{annotations_path}'")
    print(f"   类型: {type(annotations_path)}")
    assert isinstance(annotations_path, str), "应该返回 str 类型"

    print()

    # 测试 get_int
    print("2️⃣ 测试 get_int() 方法")
    print("-" * 60)

    max_frames = config.get_int('extraction.max_frames', 50)
    print(f"✅ max_frames = {max_frames}")
    print(f"   类型: {type(max_frames)}")
    assert isinstance(max_frames, int), "应该返回 int 类型"
    assert max_frames is not None, "不应该返回 None"

    print()

    # 测试 get_float
    print("3️⃣ 测试 get_float() 方法")
    print("-" * 60)

    interval = config.get_float('extraction.interval_seconds', 5.0)
    print(f"✅ interval = {interval}")
    print(f"   类型: {type(interval)}")
    assert isinstance(interval, float), "应该返回 float 类型"
    assert interval is not None, "不应该返回 None"

    print()

    # 测试 get_api_key
    print("4️⃣ 测试 get_api_key() 方法")
    print("-" * 60)

    gemini_key = config.get_api_key('gemini')
    print(f"✅ gemini_key = {gemini_key}")
    print(f"   类型: {type(gemini_key)}")
    # API Key 可以是 None（未配置时）
    assert gemini_key is None or isinstance(gemini_key, str), "应该返回 str 或 None"

    print()

    # 测试 Path 构造
    print("5️⃣ 测试 Path() 构造")
    print("-" * 60)

    try:
        video_dir = Path(config.get_str('paths.videos', 'data/videos'))
        print(f"✅ video_dir = {video_dir}")
        print(f"   类型: {type(video_dir)}")
        assert isinstance(video_dir, Path), "应该返回 Path 对象"

        keyframes_dir = Path(config.get_str('paths.keyframes', 'data/keyframes'))
        print(f"✅ keyframes_dir = {keyframes_dir}")

        annotations_dir = Path(config.get_str('paths.annotations', 'data/annotations'))
        print(f"✅ annotations_dir = {annotations_dir}")

        print()
        print("🎉 所有测试通过！")

    except Exception as e:
        print(f"❌ Path 构造失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    print()

    # 测试不存在的键（应该返回默认值）
    print("6️⃣ 测试不存在的键")
    print("-" * 60)

    nonexistent_str = config.get_str('nonexistent.key', 'default_value')
    print(f"✅ nonexistent_str = '{nonexistent_str}' (应该是 'default_value')")
    assert nonexistent_str == 'default_value', "应该返回默认值"

    nonexistent_int = config.get_int('nonexistent.key', 100)
    print(f"✅ nonexistent_int = {nonexistent_int} (应该是 100)")
    assert nonexistent_int == 100, "应该返回默认值"

    nonexistent_float = config.get_float('nonexistent.key', 3.14)
    print(f"✅ nonexistent_float = {nonexistent_float} (应该是 3.14)")
    assert nonexistent_float == 3.14, "应该返回默认值"

    print()
    print("=" * 60)
    print("✅ 所有测试通过！配置方法工作正常！")
    print("=" * 60)

    return True


if __name__ == "__main__":
    try:
        success = test_config_methods()
        sys.exit(0 if success else 1)
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
