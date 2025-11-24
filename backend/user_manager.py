# backend/user_manager.py
"""
用户管理系统 - 支持登录、标注历史、个人设置
"""
import json
import hashlib
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime, timedelta
import secrets


class User:
    """用户模型"""
    
    def __init__(
        self,
        user_id: str,
        username: str,
        email: str,
        password_hash: str,
        created_at: str = None
    ):
        self.user_id = user_id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.created_at = created_at or datetime.now().isoformat()
        self.last_login = None
        self.settings = {
            "default_provider": "gemini",
            "auto_save": True,
            "show_ai_confidence": True,
            "keyboard_shortcuts": True
        }
        self.annotation_history = []  # 标注历史记录
    
    def to_dict(self) -> Dict:
        """转为字典(不包含密码)"""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email,
            "created_at": self.created_at,
            "last_login": self.last_login,
            "settings": self.settings,
            "annotation_count": len(self.annotation_history)
        }
    
    def check_password(self, password: str) -> bool:
        """验证密码"""
        return self.password_hash == self._hash_password(password)
    
    @staticmethod
    def _hash_password(password: str) -> str:
        """密码哈希"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def add_annotation_history(
        self,
        video_id: str,
        video_name: str,
        annotation_path: str
    ):
        """添加标注历史"""
        self.annotation_history.append({
            "video_id": video_id,
            "video_name": video_name,
            "annotation_path": annotation_path,
            "annotated_at": datetime.now().isoformat()
        })
        
        # 保持最近100条
        if len(self.annotation_history) > 100:
            self.annotation_history = self.annotation_history[-100:]


class UserManager:
    """用户管理器"""
    
    def __init__(self, data_dir: str = "data/users"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.users_file = self.data_dir / "users.json"
        self.sessions_file = self.data_dir / "sessions.json"
        
        self.users: Dict[str, User] = {}
        self.sessions: Dict[str, Dict] = {}  # token -> user_info
        
        self._load_users()
        self._load_sessions()
    
    def _load_users(self):
        """加载用户数据"""
        if self.users_file.exists():
            with open(self.users_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for user_id, user_data in data.items():
                    self.users[user_id] = User(**user_data)
    
    def _save_users(self):
        """保存用户数据"""
        data = {}
        for user_id, user in self.users.items():
            user_dict = user.to_dict()
            user_dict['password_hash'] = user.password_hash
            user_dict['annotation_history'] = user.annotation_history
            data[user_id] = user_dict
        
        with open(self.users_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _load_sessions(self):
        """加载会话数据"""
        if self.sessions_file.exists():
            with open(self.sessions_file, 'r', encoding='utf-8') as f:
                self.sessions = json.load(f)
            
            # 清理过期会话
            self._cleanup_expired_sessions()
    
    def _save_sessions(self):
        """保存会话数据"""
        with open(self.sessions_file, 'w', encoding='utf-8') as f:
            json.dump(self.sessions, f, ensure_ascii=False, indent=2)
    
    def _cleanup_expired_sessions(self):
        """清理过期会话(7天)"""
        now = datetime.now()
        expired = []
        
        for token, session in self.sessions.items():
            expires_at = datetime.fromisoformat(session['expires_at'])
            if expires_at < now:
                expired.append(token)
        
        for token in expired:
            del self.sessions[token]
        
        if expired:
            self._save_sessions()
    
    def register(
        self,
        username: str,
        email: str,
        password: str
    ) -> Optional[User]:
        """注册用户"""
        # 检查用户名是否存在
        for user in self.users.values():
            if user.username == username:
                raise ValueError("用户名已存在")
            if user.email == email:
                raise ValueError("邮箱已注册")
        
        # 创建用户
        import uuid
        user_id = str(uuid.uuid4())
        password_hash = User._hash_password(password)
        
        user = User(
            user_id=user_id,
            username=username,
            email=email,
            password_hash=password_hash
        )
        
        self.users[user_id] = user
        self._save_users()
        
        print(f"✅ 注册成功: {username}")
        return user
    
    def login(
        self,
        username: str,
        password: str
    ) -> Optional[str]:
        """登录,返回token"""
        # 查找用户
        user = None
        for u in self.users.values():
            if u.username == username:
                user = u
                break
        
        if not user:
            raise ValueError("用户名或密码错误")
        
        if not user.check_password(password):
            raise ValueError("用户名或密码错误")
        
        # 更新最后登录时间
        user.last_login = datetime.now().isoformat()
        self._save_users()
        
        # 创建会话
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(days=7)
        
        self.sessions[token] = {
            "user_id": user.user_id,
            "username": user.username,
            "created_at": datetime.now().isoformat(),
            "expires_at": expires_at.isoformat()
        }
        
        self._save_sessions()
        
        print(f"✅ 登录成功: {username}")
        return token
    
    def logout(self, token: str) -> bool:
        """登出"""
        if token in self.sessions:
            del self.sessions[token]
            self._save_sessions()
            return True
        return False
    
    def validate_token(self, token: str) -> Optional[User]:
        """验证token,返回用户"""
        if token not in self.sessions:
            return None
        
        session = self.sessions[token]
        expires_at = datetime.fromisoformat(session['expires_at'])
        
        if expires_at < datetime.now():
            del self.sessions[token]
            self._save_sessions()
            return None
        
        user_id = session['user_id']
        return self.users.get(user_id)
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """根据ID获取用户"""
        return self.users.get(user_id)
    
    def update_settings(self, user_id: str, settings: Dict):
        """更新用户设置"""
        user = self.users.get(user_id)
        if user:
            user.settings.update(settings)
            self._save_users()
            return True
        return False
    
    def add_annotation_to_history(
        self,
        user_id: str,
        video_id: str,
        video_name: str,
        annotation_path: str
    ):
        """添加标注到历史"""
        user = self.users.get(user_id)
        if user:
            user.add_annotation_history(video_id, video_name, annotation_path)
            self._save_users()


# 全局用户管理器
user_manager = UserManager()