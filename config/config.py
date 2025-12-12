# config/config.py
"""
配置管理模块
"""
from pathlib import Path
from typing import Optional, Any
import yaml
import os


class Config:
    """配置类"""

    def __init__(self, config_path: str = "config/config.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()

    def _load_config(self) -> dict:
        """加载配置文件"""
        if self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        else:
            # 默认配置
            default_config = {
                'paths': {
                    'videos': 'data/Youtube_videos',
                    'keyframes': 'data/keyframes',
                    'annotations': 'data/annotations'
                },
                'extraction': {
                    'mode': 'uniform',  # 'uniform' 或 'gemini'
                    'interval_seconds': 5.0,
                    'max_frames': 50
                },
                'api_keys': {
                    'gemini': None,
                    'openai': None
                }
            }
            self._save_config(default_config)
            return default_config

    def _save_config(self, config: dict):
        """保存配置"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True)

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值（支持点号访问，优先从环境变量读取）

        Args:
            key: 配置键，支持点号访问（如 'paths.videos'）
            default: 默认值

        Returns:
            配置值，如果不存在则返回 default
        """
        # 特殊处理：服务端口从环境变量读取
        if key == 'server.backend_port':
            env_value = os.getenv('BACKEND_PORT')
            if env_value:
                try:
                    return int(env_value)
                except ValueError:
                    pass
        elif key == 'server.frontend_port':
            env_value = os.getenv('FRONTEND_PORT')
            if env_value:
                try:
                    return int(env_value)
                except ValueError:
                    pass

        # 从配置文件读取
        keys = key.split('.')
        value: Any = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, {})
                if value == {}:
                    return default
            else:
                return default
        return value if value != {} else default

    def get_str(self, key: str, default: str = "") -> str:
        """获取字符串配置值

        Args:
            key: 配置键
            default: 默认值

        Returns:
            字符串类型的配置值
        """
        value = self.get(key, default)
        return str(value) if value is not None else default

    def get_int(self, key: str, default: int = 0) -> int:
        """获取整数配置值

        Args:
            key: 配置键
            default: 默认值

        Returns:
            整数类型的配置值
        """
        value = self.get(key, default)
        try:
            return int(value) if value is not None else default
        except (ValueError, TypeError):
            return default

    def get_float(self, key: str, default: float = 0.0) -> float:
        """获取浮点数配置值

        Args:
            key: 配置键
            default: 默认值

        Returns:
            浮点数类型的配置值
        """
        value = self.get(key, default)
        try:
            return float(value) if value is not None else default
        except (ValueError, TypeError):
            return default

    def set(self, key: str, value: Any) -> None:
        """设置配置值

        Args:
            key: 配置键，支持点号访问（如 'paths.videos'）
            value: 配置值
        """
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            config = config.setdefault(k, {})
        config[keys[-1]] = value
        self._save_config(self.config)

    def set_api_key(self, service: str, api_key: str):
        """设置API密钥

        Args:
            service: 服务名称（如 'gemini', 'openai'）
            api_key: API密钥
        """
        self.set(f'api_keys.{service}', api_key)

    def get_api_key(self, service: str) -> Optional[str]:
        """获取API密钥（优先从环境变量）

        Args:
            service: 服务名称（如 'gemini', 'openai'）

        Returns:
            API密钥，如果不存在则返回 None
        """
        # 优先从环境变量读取
        env_key = f"{service.upper()}_API_KEY"
        env_value = os.getenv(env_key)
        if env_value:
            return env_value
        # 否则从配置文件读取
        return self.get(f'api_keys.{service}')


# 全局配置实例
config: Config = Config()
