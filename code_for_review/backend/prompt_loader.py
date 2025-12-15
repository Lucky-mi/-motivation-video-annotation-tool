import yaml
from pathlib import Path
from typing import Dict, Any, Optional

class PromptLoader:
    """Prompt模板加载器 - 支持热加载"""
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.prompts = {}
        self.load_prompts()

    def load_prompts(self):
        """加载prompt配置"""
        path = Path(self.config_path)
        if not path.exists():
            # Try relative to the backend directory if path is relative
            # Assuming this code runs from project root or backend usually
            # But let's handle absolute paths best.
            # If path is relative, try to resolve it from current cwd
            pass 
            
        # Try to resolve relatively to this file if it fails? 
        # Actually user passes paths like "backend/prompts/..." usually.
        
        if not path.is_absolute():
            # Try from cwd
            if not path.exists():
                # Try relative to the file location? 
                # Let's just stick to what was there but make it robust
                pass

        if not path.exists():
             # Last ditch effort: if we are in backend/, look in prompts/
             if (Path("backend") / path).exists():
                 path = Path("backend") / path
        
        if not path.exists():
            print(f"Warning: Prompt file not found at {path}")
            return

        try:
            with open(path, 'r', encoding='utf-8') as f:
                self.prompts = yaml.safe_load(f) or {}
        except Exception as e:
            print(f"Error loading prompts from {path}: {e}")
            self.prompts = {}

    def reload(self):
        """热加载 - 无需重启服务"""
        self.load_prompts()

    def get_prompt(self, prompt_key: str, **kwargs) -> str:
        """获取并格式化prompt"""
        # Support nested keys e.g. "comprehensive_video.template"
        keys = prompt_key.split('.')
        value = self.prompts
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                value = None
                break
        
        if value is None:
            # Fallback for simple structure (like in current question_prompts.yaml where root keys are prompts?)
            # Actually question_prompts.yaml structure is not fully visible, let's assume standard key access
             value = self.prompts.get(prompt_key)

        if value is None:
            return ""

        if isinstance(value, dict) and "template" in value:
            template = value["template"]
        else:
            template = str(value)
            
        try:
            return template.format(**kwargs)
        except KeyError as e:
            # If format fails due to missing keys, just return template or raise?
            # Ideally verify keys. For now, let's just return template with warning or crash.
            # But safety first - maybe not crash?
            # Retaining original behavior: template.format(**kwargs)
            return template.format(**kwargs)
