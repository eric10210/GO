import yaml
import os
from pathlib import Path

def load_config() -> dict:
    """
    Loads configuration from config.yaml in the root directory.
    """
    # Determine path to config.yaml (assuming script runs from root)
    root_dir = Path(__file__).resolve().parents[2]
    config_path = root_dir / "config.yaml"

    if not config_path.exists():
        # Fallback if running from different context
        config_path = Path("config.yaml")

    try:
        with open(config_path, "r") as file:
            config = yaml.safe_load(file)
        return config
    except FileNotFoundError:
        raise FileNotFoundError("config.yaml not found. Please create it from template.")
    except yaml.YAMLError as e:
        raise ValueError(f"Error parsing config.yaml: {e}")