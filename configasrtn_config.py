"""
ASRTN Configuration Manager
Centralized configuration with environment-specific settings
Handles secure credential loading and validation
"""
import os
import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import logging
from datetime import timedelta

@dataclass
class NetworkConfig:
    """Network-level configuration"""
    node_id: str = "node_001"
    network_id: str = "asrtn_mainnet"
    heartbeat_interval: int = 60  # seconds
    replication_check_interval: int = 3600  # 1 hour
    max_nodes_per_parent: int = 5
    min_performance_for_replication: float = 0.15  # 15% ROI threshold
    firestore_collection: str = "asrtn_nodes"
    strategy_sharing_enabled: bool = True
    backup_interval: int = 86400  # 24 hours

@dataclass
class TradingConfig:
    """Trading-specific configuration"""
    exchanges: Dict[str, Dict[str, Any]] = field(default_factory=lambda: {
        "binance": {"enabled": True, "timeout": 30000},
        "kraken": {"enabled": False, "timeout": 30000}
    })
    trading_pairs: list = field(default_factory=lambda: ["BTC/USDT", "ETH/USDT"])
    max_position_size: float = 0.1  # 10% of capital per trade
    min_volume_threshold: float = 100000.0  # USD
    risk_free_rate: float = 0.02  # 2% annual
    slippage_tolerance: float = 0.001  # 0.1%

@dataclass
class RLConfig:
    """Reinforcement Learning configuration"""
    learning_rate: float = 0.001
    discount_factor: float = 0.95
    exploration_rate: float = 0.1
    batch_size: int = 32
    memory_size: int = 10000
    training_interval: int = 100  # trades
    state_dimension: int = 10
    action_space: list = field(default_factory=lambda: ["BUY", "SELL", "HOLD"])

@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: str = "logs/asrtn.log"
    max_file_size: int = 10485760  # 10MB
    backup_count: int = 5

class ASRTNConfig:
    """Main configuration manager with validation and fallback handling"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.config_path = config_path or "config/settings.yaml"
        self.network = NetworkConfig()
        self.trading = TradingConfig()
        self.rl = RLConfig()
        self.logging = LoggingConfig()
        
        # Load environment variables
        self._load_environment()
        
        # Load YAML config if exists
        self._load_yaml_config()
        
        # Validate configuration
        self._validate_config()
        
    def _load_environment(self):
        """Load configuration from environment variables"""
        try:
            from dotenv import load_dotenv
            load_dotenv()
            
            # Network settings
            if node_id := os.getenv("ASRTN_NODE_ID"):
                self.network.node_id = node_id
            if network_id := os.getenv("ASRTN_NETWORK_ID"):
                self.network.network_id = network_id
            
            # Firebase configuration (CRITICAL - per mission requirements)
            self.firebase_credentials = os.getenv("FIREBASE_CREDENTIALS_PATH")
            self.firebase_database_url = os.getenv("FIREBASE_DATABASE_URL")
            
            # Exchange API keys (secure handling)
            self.api_keys = {
                "binance": {
                    "api_key": os.getenv("BINANCE_API_KEY"),
                    "secret": os.getenv("BINANCE_SECRET")
                }
            }
            
            self.logger.info("Environment variables loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to load environment variables: {e}")
            raise RuntimeError(f"Configuration error: {e}")
    
    def _load_yaml_config(self):
        """Load configuration from YAML file with graceful fallback"""
        try:
            config_file = Path(self.config_path)
            if config_file.exists():
                with open(config_file, 'r') as f:
                    yaml_config = yaml.safe_load(f)
                    
                # Merge YAML config with defaults