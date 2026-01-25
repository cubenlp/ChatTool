from pathlib import Path
import pytest
from dotenv import load_dotenv
import os
import platformdirs
from chattool.utils import load_envs
import chattool.const
from chattool.utils import create_env_file

def test_env_mechanism(tmp_path):
    """测试环境变量加载机制"""
    # 模拟用户配置目录
    mock_config_dir = tmp_path / "config"
    mock_config_dir.mkdir()
    mock_env_file = mock_config_dir / ".env"
    
    # 创建模拟的 .env 文件
    env_content = """
    OPENAI_API_KEY=test-openai-key
    ZULIP_BOT_EMAIL=test-bot@example.com
    ALIBABA_CLOUD_REGION_ID=cn-shanghai
    """
    with open(mock_env_file, "w") as f:
        f.write(env_content)
    
    # 加载模拟的 .env
    load_envs(mock_env_file)
    
    # 验证是否正确加载到了 const
    assert chattool.const.OPENAI_API_KEY == "test-openai-key"
    assert chattool.const.ZULIP_BOT_EMAIL == "test-bot@example.com"
    assert chattool.const.ALIBABA_CLOUD_REGION_ID == "cn-shanghai"
    
    # 验证 create_env_file 能否生成包含所有字段的文件
    output_env = tmp_path / "output.env"
    
    # 设置一些默认值
    chattool.const.TENCENT_SECRET_ID = "test-tencent-id"
    
    create_env_file(output_env)
    
    assert output_env.exists()
    content = output_env.read_text()
    
    # 验证生成的模板包含关键字段
    assert "OPENAI_API_KEY='test-openai-key'" in content
    assert "ZULIP_BOT_EMAIL='test-bot@example.com'" in content
    assert "TENCENT_SECRET_ID='test-tencent-id'" in content
    assert "# Zulip Configuration" in content

if __name__ == "__main__":
    pytest.main([__file__])
