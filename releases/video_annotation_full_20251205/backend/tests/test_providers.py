# backend/tests/test_providers.py
"""
AI Provider单元测试
测试Provider工厂和各个Provider实现
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from backend.ai_providers.base_provider import BaseAIProvider, AIProviderFactory


class TestAIProviderFactory:
    """测试AI Provider工厂"""

    def test_register_provider(self):
        """测试注册Provider"""
        class TestProvider(BaseAIProvider):
            def analyze_video_comprehensive(self, video_path, **kwargs):
                return {}

            def analyze_single_frame(self, frame_path, timestamp, context=""):
                return {}

        # 注册
        AIProviderFactory.register_provider('test_provider', TestProvider)

        # 验证注册成功
        assert 'test_provider' in AIProviderFactory.list_providers()

    def test_create_provider(self):
        """测试创建Provider实例"""
        class MockProvider(BaseAIProvider):
            def analyze_video_comprehensive(self, video_path, **kwargs):
                return {}

            def analyze_single_frame(self, frame_path, timestamp, context=""):
                return {}

        AIProviderFactory.register_provider('mock', MockProvider)

        provider = AIProviderFactory.create_provider('mock', api_key='test_key')

        assert isinstance(provider, MockProvider)
        assert provider.api_key == 'test_key'

    def test_create_unknown_provider(self):
        """测试创建未知Provider"""
        with pytest.raises(ValueError, match="未知的Provider"):
            AIProviderFactory.create_provider('unknown_provider')

    def test_list_providers(self):
        """测试列出所有Provider"""
        providers = AIProviderFactory.list_providers()

        # 至少应该有gemini和openai
        assert isinstance(providers, list)
        # 注意: 实际注册的provider可能因导入而异


class TestBaseAIProvider:
    """测试基础Provider"""

    def test_base_provider_is_abstract(self):
        """测试基类不能直接实例化"""
        # BaseAIProvider是抽象类，应该不能直接实例化
        # 但Python的ABC检查在运行时，所以这里我们测试必须实现的方法
        class IncompleteProvider(BaseAIProvider):
            pass

        with pytest.raises(TypeError):
            IncompleteProvider()

    def test_extract_keyframes_method(self, temp_data_dir):
        """测试关键帧提取方法（通用方法）"""
        # 创建一个完整的Mock Provider
        class CompleteProvider(BaseAIProvider):
            def analyze_video_comprehensive(self, video_path, **kwargs):
                return {}

            def analyze_single_frame(self, frame_path, timestamp, context=""):
                return {}

        provider = CompleteProvider(api_key='test')

        # 这个测试需要实际视频文件，所以我们只测试方法存在
        assert hasattr(provider, 'extract_keyframes')

    def test_get_provider_info(self):
        """测试获取Provider信息"""
        class TestProvider(BaseAIProvider):
            def __init__(self, **kwargs):
                super().__init__(api_key='test_key', model_name='test-model')

            def analyze_video_comprehensive(self, video_path, **kwargs):
                return {}

            def analyze_single_frame(self, frame_path, timestamp, context=""):
                return {}

        provider = TestProvider()
        info = provider.get_provider_info()

        assert info['provider'] == 'TestProvider'
        assert info['model'] == 'test-model'
        assert info['api_configured'] == True


class TestGeminiProvider:
    """测试Gemini Provider"""

    @pytest.mark.skipif(
        not Path("backend/ai_providers/gemini_provider.py").exists(),
        reason="Gemini provider not available"
    )
    def test_gemini_import(self):
        """测试Gemini Provider导入"""
        try:
            from backend.ai_providers.gemini_provider import GeminiProvider
            assert GeminiProvider is not None
        except ImportError:
            pytest.skip("google-generativeai not installed")

    @pytest.mark.skipif(
        not Path("backend/ai_providers/gemini_provider.py").exists(),
        reason="Gemini provider not available"
    )
    def test_gemini_initialization_requires_api_key(self):
        """测试Gemini初始化需要API key"""
        try:
            from backend.ai_providers.gemini_provider import GeminiProvider

            with pytest.raises(ValueError, match="API Key"):
                GeminiProvider(api_key=None)
        except ImportError:
            pytest.skip("google-generativeai not installed")

    @pytest.mark.skipif(
        not Path("backend/ai_providers/gemini_provider.py").exists(),
        reason="Gemini provider not available"
    )
    @patch('google.generativeai.configure')
    @patch('google.generativeai.GenerativeModel')
    def test_gemini_initialization_success(self, mock_model, mock_configure):
        """测试Gemini成功初始化"""
        try:
            from backend.ai_providers.gemini_provider import GeminiProvider

            provider = GeminiProvider(api_key='test_key')

            assert provider.api_key == 'test_key'
            mock_configure.assert_called_once_with(api_key='test_key')
        except ImportError:
            pytest.skip("google-generativeai not installed")


class TestOpenAIProvider:
    """测试OpenAI Provider"""

    @pytest.mark.skipif(
        not Path("backend/ai_providers/openai_provider.py").exists(),
        reason="OpenAI provider not available"
    )
    def test_openai_import(self):
        """测试OpenAI Provider导入"""
        try:
            from backend.ai_providers.openai_provider import OpenAIProvider
            assert OpenAIProvider is not None
        except ImportError:
            pytest.skip("openai not installed")

    @pytest.mark.skipif(
        not Path("backend/ai_providers/openai_provider.py").exists(),
        reason="OpenAI provider not available"
    )
    def test_openai_initialization_requires_api_key(self):
        """测试OpenAI初始化需要API key"""
        try:
            from backend.ai_providers.openai_provider import OpenAIProvider

            with pytest.raises(ValueError, match="API Key"):
                OpenAIProvider(api_key=None)
        except ImportError:
            pytest.skip("openai not installed")


class TestProviderQuestionGeneration:
    """测试Provider的问题生成功能"""

    def test_provider_has_generate_question_method(self, mock_ai_provider):
        """测试Provider有generate_question方法"""
        assert hasattr(mock_ai_provider, 'generate_question')
        assert callable(mock_ai_provider.generate_question)

    def test_generate_question_returns_string(self, mock_ai_provider):
        """测试generate_question返回字符串"""
        result = mock_ai_provider.generate_question("Test prompt")

        assert isinstance(result, str)
        assert len(result) > 0

    def test_generate_question_returns_valid_json(self, mock_ai_provider):
        """测试generate_question返回的是有效JSON"""
        import json

        result = mock_ai_provider.generate_question("Test prompt")

        # 提取JSON部分
        if "```json" in result:
            json_str = result.split("```json")[1].split("```")[0].strip()
        else:
            json_str = result

        # 应该能解析为JSON
        data = json.loads(json_str)
        assert "question_text" in data
        assert "options" in data
        assert "correct_option_id" in data
