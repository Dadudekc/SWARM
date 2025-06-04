import json
from pathlib import Path

from social.utils import JSONConfig
from social.utils.log_manager import LogManager, LogConfig


def test_json_config_access(tmp_path):
    data = {
        "logging": {
            "log_dir": str(tmp_path / "logs"),
            "level": "INFO"
        },
        "backend": {
            "url": "http://localhost"
        }
    }
    cfg_path = tmp_path / "config.json"
    with open(cfg_path, "w") as f:
        json.dump(data, f)

    cfg = JSONConfig(cfg_path)

    assert cfg.logging.log_dir == str(tmp_path / "logs")
    assert cfg.backend.url == "http://localhost"
    assert cfg.as_dict()["logging"]["level"] == "INFO"


def test_json_config_integration_with_log_manager(tmp_path):
    log_dir = tmp_path / "logs"
    cfg_path = tmp_path / "config.json"
    data = {"logging": {"log_dir": str(log_dir), "platforms": {"system": "system.log"}}}
    with open(cfg_path, "w") as f:
        json.dump(data, f)

    cfg = JSONConfig(cfg_path)
    log_cfg = LogConfig(log_dir=cfg.logging.log_dir, platforms=cfg.logging.platforms)
    manager = LogManager(log_cfg)
    manager.info("system", "hello")

    log_file = log_dir / "system.log"
    assert log_file.exists()
