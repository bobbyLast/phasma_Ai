from core.config import PhasmaConfig

config = PhasmaConfig()
print(f"Config path: {config.config_path}")
print(f"kalshi_enabled: {config.get('kalshi_enabled', 'NOT_FOUND')}")
print(f"Config keys: {list(config.data.keys())}")
