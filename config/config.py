# config/config.py
"""
配置管理模块
"""
from pathlib import Path
from typing import Optional
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
                    'videos': 'data/videos',
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
    
    def get(self, key: str, default=None):
        """获取配置值（支持点号访问）"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            value = value.get(k, {})
            if value == {}:
                return default
        return value if value != {} else default
    
    def set(self, key: str, value):
        """设置配置值"""
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            config = config.setdefault(k, {})
        config[keys[-1]] = value
        self._save_config(self.config)
    
    def set_api_key(self, service: str, api_key: str):
        """设置API密钥"""
        self.set(f'api_keys.{service}', api_key)
    
    def get_api_key(self, service: str) -> Optional[str]:
        """获取API密钥（优先从环境变量）"""
        # 优先从环境变量读取
        env_key = f"{service.upper()}_API_KEY"
        env_value = os.getenv(env_key)
        if env_value:
            return env_value
        # 否则从配置文件读取
        def get(self, key: str, default=None) -> Optional[str]:
            """获取配置值（支持点号访问）"""
            keys = key.split('.')
            value = self.config
            for k in keys:
                value = value.get(k, {})
                if value == {}:
                    return default
            return value if value != {} else default

# 全局配置实例
config: Config = Config()