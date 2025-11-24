# frontend/utils/api_client.py
"""API客户端封装"""
import requests
from typing import Dict, List, Optional
import streamlit as st


class APIClient:
    """统一的API客户端"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.timeout = 600

    def health_check(self) -> bool:
        """健康检查"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False

    def upload_video(self, file, provider: str = "gemini", api_key: str = "") -> Dict:
        """上传并分析视频"""
        files = {"file": file}
        data = {
            "provider": provider,
            "api_key": api_key,
            "analyze_actions": True,
            "analyze_motivations": True
        }

        response = requests.post(
            f"{self.base_url}/analyze/video",
            files=files,
            data=data,
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()

    def list_videos(self) -> List[Dict]:
        """获取视频列表"""
        response = requests.get(f"{self.base_url}/videos", timeout=10)
        response.raise_for_status()
        return response.json()

    def get_annotation(self, video_id: str) -> Optional[Dict]:
        """获取视频标注"""
        try:
            response = requests.get(
                f"{self.base_url}/annotations/{video_id}",
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            return None
        except:
            return None

    def update_annotation(self, video_id: str, annotation_data: Dict) -> Dict:
        """更新标注数据"""
        response = requests.put(
            f"{self.base_url}/annotations/{video_id}",
            json=annotation_data,
            timeout=30
        )
        response.raise_for_status()
        return response.json()

    def batch_process(self, folder_path: str, provider: str, api_key: str) -> Dict:
        """批量处理"""
        data = {
            "folder_path": folder_path,
            "provider": provider,
            "api_key": api_key
        }

        response = requests.post(
            f"{self.base_url}/batch/process",
            json=data,
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()

    def rename_video(self, video_id: str, new_name: str) -> Dict:
        """重命名视频"""
        data = {"video_id": video_id, "new_name": new_name}
        response = requests.post(
            f"{self.base_url}/videos/rename",
            json=data,
            timeout=10
        )
        response.raise_for_status()
        return response.json()


# 全局客户端实例
@st.cache_resource
def get_api_client() -> APIClient:
    """获取API客户端单例"""
    return APIClient()
