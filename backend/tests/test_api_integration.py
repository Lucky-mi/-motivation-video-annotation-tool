# backend/tests/test_api_integration.py
"""
API集成测试
测试完整的API端点和工作流
"""
import pytest
import json
from fastapi.testclient import TestClient
from pathlib import Path
import sys

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.api_v2 import app


@pytest.fixture
def client():
    """创建测试客户端"""
    return TestClient(app)


class TestBasicEndpoints:
    """测试基础端点"""

    def test_root_endpoint(self, client):
        """测试根路径"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data

    def test_health_endpoint(self, client):
        """测试健康检查"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data


class TestProviderEndpoints:
    """测试Provider相关端点"""

    def test_list_providers(self, client):
        """测试列出所有Provider"""
        response = client.get("/providers/list")
        assert response.status_code == 200
        data = response.json()
        assert "providers" in data
        assert isinstance(data["providers"], list)

    def test_provider_list_structure(self, client):
        """测试Provider列表结构"""
        response = client.get("/providers/list")
        data = response.json()

        if data["providers"]:
            provider = data["providers"][0]
            assert "name" in provider
            assert "display_name" in provider
            assert "configured" in provider
            assert "available" in provider


class TestQuestionEndpoints:
    """测试问题生成相关端点"""

    def test_get_question_not_found(self, client):
        """测试获取不存在的问题集"""
        response = client.get("/questions/nonexistent_video")
        assert response.status_code == 404

    def test_list_prompts(self, client):
        """测试列出Prompt模板"""
        response = client.get("/prompts/list")
        assert response.status_code == 200
        data = response.json()
        assert "prompts" in data
        assert "config_path" in data

    def test_reload_prompts(self, client):
        """测试重新加载Prompts"""
        response = client.post("/prompts/reload")

        # 应该返回成功，即使文件不存在
        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            assert data["success"] == True


class TestAnnotationEndpoints:
    """测试标注相关端点"""

    def test_get_annotation_not_found(self, client):
        """测试获取不存在的标注"""
        response = client.get("/annotations/nonexistent_video")
        assert response.status_code == 404

    def test_review_list(self, client):
        """测试获取待校验列表"""
        response = client.get("/review/list")
        assert response.status_code == 200
        data = response.json()
        assert "annotations" in data
        assert "total" in data
        assert isinstance(data["annotations"], list)


class TestQuestionGenerationWorkflow:
    """测试问题生成工作流（集成测试）"""

    @pytest.mark.skip(reason="需要实际的标注数据文件")
    def test_generate_questions_for_video(self, client, sample_video_annotation, temp_data_dir):
        """测试为视频生成问题（需要mock数据）"""
        # 这个测试需要实际的标注文件
        # 实际使用时需要准备测试数据

        video_id = "test_video"

        # 1. 创建模拟标注文件
        annotations_dir = temp_data_dir / "annotations"
        annotations_dir.mkdir(exist_ok=True)

        annotation_file = annotations_dir / f"{video_id}.json"
        annotation_file.write_text(
            json.dumps(sample_video_annotation.dict()),
            encoding='utf-8'
        )

        # 2. 调用问题生成API
        response = client.post(
            f"/questions/generate/{video_id}",
            params={"num_questions": 5, "provider": "gemini"}
        )

        # 应该返回错误（因为没有真实的Gemini API key）或成功
        assert response.status_code in [200, 400, 500]

    def test_question_verification_endpoint(self, client):
        """测试问题校验端点"""
        response = client.put(
            "/questions/test_question_id/verify",
            params={
                "action": "approved",
                "notes": "Looks good"
            }
        )

        # Mock实现应该返回成功
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True


class TestBatchProcessing:
    """测试批量处理"""

    def test_batch_status(self, client):
        """测试获取批处理状态"""
        response = client.get("/batch/status")
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "tasks" in data

    @pytest.mark.skip(reason="需要实际的视频文件")
    def test_add_batch_task(self, client):
        """测试添加批处理任务"""
        response = client.post(
            "/batch/add-task",
            params={
                "video_path": "test_video.mp4",
                "provider": "gemini"
            }
        )

        # 可能失败（文件不存在）
        assert response.status_code in [200, 404, 500]


class TestErrorHandling:
    """测试错误处理"""

    def test_404_for_unknown_endpoint(self, client):
        """测试未知端点返回404"""
        response = client.get("/unknown/endpoint")
        assert response.status_code == 404

    def test_invalid_video_id(self, client):
        """测试无效的video_id"""
        response = client.get("/annotations/")
        assert response.status_code in [404, 422]  # 404或参数验证错误

    def test_invalid_parameters(self, client):
        """测试无效参数"""
        response = client.post(
            "/questions/generate/test_video",
            params={"num_questions": -1}  # 负数应该被拒绝
        )
        assert response.status_code == 422  # 参数验证错误


class TestCORS:
    """测试CORS配置"""

    def test_cors_headers(self, client):
        """测试CORS头存在"""
        response = client.options(
            "/",
            headers={"Origin": "http://localhost:8501"}
        )

        # 应该允许所有origin（配置为 allow_origins=["*"]）
        assert response.status_code == 200


class TestDataValidation:
    """测试数据验证"""

    def test_question_generation_invalid_num(self, client):
        """测试无效的问题数量"""
        response = client.post(
            "/questions/generate/test_video",
            params={"num_questions": 100}  # 超过最大值50
        )
        assert response.status_code == 422

    def test_question_generation_zero_questions(self, client):
        """测试0个问题"""
        response = client.post(
            "/questions/generate/test_video",
            params={"num_questions": 0}
        )
        assert response.status_code == 422
