from pathlib import Path

from src.common.config import load_config



def test_load_config_reads_yaml():
    cfg = load_config(Path("config/app_config.example.yaml"))
    assert cfg.catalog == "main"
    assert cfg.rules_table == "main.governance.quality_rules"
