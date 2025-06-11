"""
Dream.OS Beta Verification System

Validates critical systems, configurations, and components before beta deployment.
Provides both human-readable and machine-friendly output formats.
"""

import os
import json
import yaml
import logging
import subprocess
import argparse
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class CheckResult:
    """Result of a verification check."""
    name: str
    status: bool
    details: str
    error: Optional[str] = None
    timestamp: str = None
    category: str = None
    severity: str = "medium"
    recommendations: List[str] = None
    
    def __post_init__(self):
        """Initialize default values."""
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
        if self.recommendations is None:
            self.recommendations = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON output."""
        return {
            "name": self.name,
            "status": self.status,
            "details": self.details,
            "error": self.error,
            "timestamp": self.timestamp,
            "category": self.category,
            "severity": self.severity,
            "recommendations": self.recommendations
        }

class BetaVerifier:
    """Dream.OS Beta Deployment Validator."""
    
    def __init__(self, base_path: Optional[Path] = None):
        """Initialize verifier.
        
        Args:
            base_path: Optional base path for verification
        """
        self.base_path = base_path or Path(__file__).parent.parent.parent.resolve()
        self.logger = logging.getLogger(__name__)
        self.results: List[CheckResult] = []
        self.start_time = datetime.now()
        
        # Setup logging
        self._setup_logging()
        
    def _setup_logging(self) -> None:
        """Setup verification logging."""
        log_dir = self.base_path / "logs"
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / f"verify_beta_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        handler = logging.FileHandler(log_file)
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
        
    def check_mailboxes(self) -> CheckResult:
        """Check agent mailboxes exist and are non-empty."""
        try:
            mailboxes = self.base_path / "runtime/agent_memory"
            missing_or_empty = [
                str(p) for p in mailboxes.glob("agent-*/inbox.json")
                if not p.exists() or p.stat().st_size == 0
            ]
            
            if missing_or_empty:
                return CheckResult(
                    name="Agent Mailboxes",
                    status=False,
                    details=f"Missing or empty mailboxes: {', '.join(missing_or_empty)}",
                    error=f"Missing or empty mailboxes: {', '.join(missing_or_empty)}"
                )
                
            return CheckResult(
                name="Agent Mailboxes",
                status=True,
                details=f"All {len(list(mailboxes.glob('agent-*')))} mailboxes present and non-empty"
            )
            
        except Exception as e:
            return CheckResult(
                name="Agent Mailboxes",
                status=False,
                details=f"Error checking mailboxes: {str(e)}",
                error=str(e)
            )
            
    def check_required_docs(self) -> CheckResult:
        """Check required protocol documentation."""
        try:
            required = [
                "CORE_AGENT_IDENTITY_PROTOCOL.md",
                "AGENT_OPERATIONAL_LOOP_PROTOCOL.md",
                "AGENT_ONBOARDING_CHECKLIST.md",
            ]
            
            missing = [
                f for f in required
                if not (self.base_path / "docs/onboarding" / f).exists()
            ]
            
            if missing:
                return CheckResult(
                    name="Required Documentation",
                    status=False,
                    details=f"Missing docs: {', '.join(missing)}",
                    error=f"Missing docs: {', '.join(missing)}"
                )
                
            return CheckResult(
                name="Required Documentation",
                status=True,
                details=f"All {len(required)} required docs present"
            )
            
        except Exception as e:
            return CheckResult(
                name="Required Documentation",
                status=False,
                details=f"Error checking required docs: {str(e)}",
                error=str(e)
            )
            
    def check_unit_tests(self) -> CheckResult:
        """Check unit test status."""
        try:
            result = subprocess.run(
                ["pytest", "tests", "-q", "--maxfail=1", "--disable-warnings"],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                return CheckResult(
                    name="Unit Tests",
                    status=False,
                    details=result.stdout + result.stderr,
                    error=result.stderr
                )
                
            return CheckResult(
                name="Unit Tests",
                status=True,
                details="All tests passed"
            )
            
        except Exception as e:
            return CheckResult(
                name="Unit Tests",
                status=False,
                details=f"Error running unit tests: {str(e)}",
                error=str(e)
            )
            
    def check_orphans_and_dupes(self) -> CheckResult:
        """Check for orphaned or duplicate files."""
        try:
            flagged = self.base_path / "reports/orphaned_files.json"
            
            if not flagged.exists():
                return CheckResult(
                    name="File Structure",
                    status=True,
                    details="No orphaned files report found"
                )
                
            orphaned = json.loads(flagged.read_text())
            
            if orphaned:
                return CheckResult(
                    name="File Structure",
                    status=False,
                    details=f"Found {len(orphaned)} orphaned/duplicate files",
                    error=f"Found {len(orphaned)} orphaned/duplicate files"
                )
                
            return CheckResult(
                name="File Structure",
                status=True,
                details="No orphaned or duplicate files found"
            )
            
        except Exception as e:
            return CheckResult(
                name="File Structure",
                status=False,
                details=f"Error checking file structure: {str(e)}",
                error=str(e)
            )
            
    def check_agent_state_files(self) -> CheckResult:
        """Check agent state files."""
        try:
            states = list((self.base_path / "runtime/agent_memory").glob("agent-*/agent_status.json"))
            
            if len(states) != 8:
                return CheckResult(
                    name="Agent States",
                    status=False,
                    details=f"Found {len(states)} state files, expected 8",
                    error=f"Found {len(states)} state files, expected 8"
                )
                
            # Validate each state file
            invalid_states = []
            for state_file in states:
                try:
                    state = json.loads(state_file.read_text())
                    if not isinstance(state, dict) or "status" not in state:
                        invalid_states.append(state_file.name)
                except Exception:
                    invalid_states.append(state_file.name)
                    
            if invalid_states:
                return CheckResult(
                    name="Agent States",
                    status=False,
                    details=f"Invalid state files: {', '.join(invalid_states)}",
                    error=f"Invalid state files: {', '.join(invalid_states)}"
                )
                
            return CheckResult(
                name="Agent States",
                status=True,
                details="All 8 agent state files present and valid"
            )
            
        except Exception as e:
            return CheckResult(
                name="Agent States",
                status=False,
                details=f"Error checking agent states: {str(e)}",
                error=str(e)
            )
            
    def check_backlog_and_episodes(self) -> CheckResult:
        """Check task backlog and episodes."""
        try:
            backlog = self.base_path / "task_backlog.json"
            episodes = list((self.base_path / "episodes").glob("episode-*.yaml"))
            
            if not backlog.exists():
                return CheckResult(
                    name="Task Management",
                    status=False,
                    details="Task backlog not found",
                    error="Task backlog not found"
                )
                
            if not episodes:
                return CheckResult(
                    name="Task Management",
                    status=False,
                    details="No episode files found",
                    error="No episode files found"
                )
                
            # Validate backlog
            try:
                backlog_data = json.loads(backlog.read_text())
                if not isinstance(backlog_data, dict):
                    return CheckResult(
                        name="Task Management",
                        status=False,
                        details="Invalid task backlog format",
                        error="Invalid task backlog format"
                    )
            except Exception as e:
                return CheckResult(
                    name="Task Management",
                    status=False,
                    details=f"Error reading task backlog: {e}",
                    error=str(e)
                )
                
            # Validate episodes
            invalid_episodes = []
            for episode in episodes:
                try:
                    with open(episode, 'r') as f:
                        yaml.safe_load(f)
                except Exception:
                    invalid_episodes.append(episode.name)
                    
            if invalid_episodes:
                return CheckResult(
                    name="Task Management",
                    status=False,
                    details=f"Invalid episode files: {', '.join(invalid_episodes)}",
                    error=f"Invalid episode files: {', '.join(invalid_episodes)}"
                )
                
            return CheckResult(
                name="Task Management",
                status=True,
                details=f"Task backlog and {len(episodes)} episodes present and valid"
            )
            
        except Exception as e:
            return CheckResult(
                name="Task Management",
                status=False,
                details=f"Error checking task backlog: {str(e)}",
                error=str(e)
            )
            
    def check_autonomy_loop(self) -> CheckResult:
        """Check autonomy loop status."""
        try:
            flag = self.base_path / "runtime/autonomy_loop_active.flag"
            
            if not flag.exists():
                return CheckResult(
                    name="Autonomy Loop",
                    status=False,
                    details="Autonomy loop not active",
                    error="Autonomy loop not active"
                )
                
            # Check flag timestamp
            flag_time = datetime.fromtimestamp(flag.stat().st_mtime)
            if (datetime.now() - flag_time).total_seconds() > 300:  # 5 minutes
                return CheckResult(
                    name="Autonomy Loop",
                    status=False,
                    details="Autonomy loop flag is stale",
                    error="Autonomy loop flag is stale"
                )
                
            return CheckResult(
                name="Autonomy Loop",
                status=True,
                details="Autonomy loop active and current"
            )
            
        except Exception as e:
            return CheckResult(
                name="Autonomy Loop",
                status=False,
                details=f"Error checking autonomy loop: {str(e)}",
                error=str(e)
            )
            
    def check_discord_commander(self) -> CheckResult:
        """Check Discord commander status and functionality."""
        try:
            # Check commander module
            commander_path = self.base_path / "core/agent_control/discord_commander.py"
            if not commander_path.exists():
                return CheckResult(
                    name="Discord Commander",
                    status=False,
                    details="Commander module not found",
                    error="Commander module not found"
                )

            # Check commander configuration
            commander_config = self.base_path / "configs/discord_commander_config.json"
            if not commander_config.exists():
                return CheckResult(
                    name="Discord Commander",
                    status=False,
                    details="Commander configuration not found",
                    error="Commander configuration not found"
                )

            config = json.loads(commander_config.read_text())
            required_keys = [
                "bot_token",
                "command_prefix",
                "admin_roles",
                "allowed_channels",
                "health_check_interval"
            ]
            missing_keys = [k for k in required_keys if k not in config]
            
            if missing_keys:
                return CheckResult(
                    name="Discord Commander",
                    status=False,
                    details=f"Missing configuration keys: {', '.join(missing_keys)}",
                    error=f"Missing configuration keys: {', '.join(missing_keys)}"
                )

            # Check health endpoint
            try:
                response = requests.get(
                    "http://localhost:8080/health",
                    timeout=5
                )
                if response.status_code != 200:
                    return CheckResult(
                        name="Discord Commander",
                        status=False,
                        details=f"Health check failed: {response.status_code}",
                        error=f"Health check failed: {response.status_code}"
                    )
                
                health_data = response.json()
                if not isinstance(health_data, dict) or "status" not in health_data:
                    return CheckResult(
                        name="Discord Commander",
                        status=False,
                        details="Invalid health check response format",
                        error="Invalid health check response format"
                    )
            except Exception as e:
                return CheckResult(
                    name="Discord Commander",
                    status=False,
                    details=f"Health check error: {str(e)}",
                    error=str(e)
                )

            # Check command registry
            commands_path = self.base_path / "core/agent_control/commands"
            if not commands_path.exists():
                return CheckResult(
                    name="Discord Commander",
                    status=False,
                    details="Commands directory not found",
                    error="Commands directory not found"
                )

            # Verify required commands
            required_commands = [
                "start.py",
                "stop.py",
                "status.py",
                "help.py",
                "deploy.py"
            ]
            missing_commands = [
                cmd for cmd in required_commands
                if not (commands_path / cmd).exists()
            ]
            
            if missing_commands:
                return CheckResult(
                    name="Discord Commander",
                    status=False,
                    details=f"Missing command files: {', '.join(missing_commands)}",
                    error=f"Missing command files: {', '.join(missing_commands)}"
                )

            # Check command permissions
            permissions_path = self.base_path / "configs/command_permissions.json"
            if not permissions_path.exists():
                return CheckResult(
                    name="Discord Commander",
                    status=False,
                    details="Command permissions configuration not found",
                    error="Command permissions configuration not found"
                )

            # Verify permission structure
            try:
                permissions = json.loads(permissions_path.read_text())
                if not isinstance(permissions, dict):
                    return CheckResult(
                        name="Discord Commander",
                        status=False,
                        details="Invalid permissions configuration format",
                        error="Invalid permissions configuration format"
                    )

                # Check each command has required permission fields
                for cmd, perms in permissions.items():
                    if not isinstance(perms, dict) or "roles" not in perms or "channels" not in perms:
                        return CheckResult(
                            name="Discord Commander",
                            status=False,
                            details=f"Invalid permission structure for command: {cmd}",
                            error=f"Invalid permission structure for command: {cmd}"
                        )
            except Exception as e:
                return CheckResult(
                    name="Discord Commander",
                    status=False,
                    details=f"Error reading permissions: {str(e)}",
                    error=str(e)
                )

            # Check integration with agent system
            agent_integration_path = self.base_path / "core/agent_control/discord_agent_integration.py"
            if not agent_integration_path.exists():
                return CheckResult(
                    name="Discord Commander",
                    status=False,
                    details="Agent integration module not found",
                    error="Agent integration module not found"
                )

            return CheckResult(
                name="Discord Commander",
                status=True,
                details="Commander system fully configured and operational"
            )

        except Exception as e:
            return CheckResult(
                name="Discord Commander",
                status=False,
                details=f"Error checking Discord commander: {str(e)}",
                error=str(e)
            )

    def check_discord_devlog(self) -> CheckResult:
        """Check Discord devlog integration."""
        try:
            # Check devlog configuration
            devlog_config = self.base_path / "configs/discord_devlog_config.json"
            if not devlog_config.exists():
                return CheckResult(
                    name="Discord Devlog",
                    status=False,
                    details="Devlog configuration not found",
                    error="Devlog configuration not found"
                )

            config = json.loads(devlog_config.read_text())
            required_keys = ["channel_id", "webhook_url", "bot_token"]
            missing_keys = [k for k in required_keys if k not in config]
            
            if missing_keys:
                return CheckResult(
                    name="Discord Devlog",
                    status=False,
                    details=f"Missing configuration keys: {', '.join(missing_keys)}",
                    error=f"Missing configuration keys: {', '.join(missing_keys)}"
                )

            # Test webhook
            try:
                response = requests.post(
                    config["webhook_url"],
                    json={"content": "🧪 Dream.OS Beta Verification Test"},
                    timeout=5
                )
                if response.status_code != 204:
                    return CheckResult(
                        name="Discord Devlog",
                        status=False,
                        details=f"Webhook test failed: {response.status_code}",
                        error=f"Webhook test failed: {response.status_code}"
                    )
            except Exception as e:
                return CheckResult(
                    name="Discord Devlog",
                    status=False,
                    details=f"Webhook test error: {str(e)}",
                    error=str(e)
                )

            return CheckResult(
                name="Discord Devlog",
                status=True,
                details="Devlog configuration valid and webhook functional"
            )

        except Exception as e:
            return CheckResult(
                name="Discord Devlog",
                status=False,
                details=f"Error checking Discord devlog: {str(e)}",
                error=str(e)
            )

    def check_social_integrations(self) -> CheckResult:
        """Check social media integrations."""
        try:
            social_config = self.base_path / "configs/social_integrations.json"
            if not social_config.exists():
                return CheckResult(
                    name="Social Integrations",
                    status=False,
                    details="Social integrations configuration not found",
                    error="Social integrations configuration not found"
                )

            config = json.loads(social_config.read_text())
            required_platforms = ["twitter", "github", "discord"]
            missing_platforms = [p for p in required_platforms if p not in config]
            
            if missing_platforms:
                return CheckResult(
                    name="Social Integrations",
                    status=False,
                    details=f"Missing platform configurations: {', '.join(missing_platforms)}",
                    error=f"Missing platform configurations: {', '.join(missing_platforms)}"
                )

            # Verify each platform's configuration
            for platform, platform_config in config.items():
                if not isinstance(platform_config, dict):
                    return CheckResult(
                        name="Social Integrations",
                        status=False,
                        details=f"Invalid configuration for {platform}",
                        error=f"Invalid configuration for {platform}"
                    )

            return CheckResult(
                name="Social Integrations",
                status=True,
                details=f"All {len(config)} social platforms configured"
            )

        except Exception as e:
            return CheckResult(
                name="Social Integrations",
                status=False,
                details=f"Error checking social integrations: {str(e)}",
                error=str(e)
            )

    def check_resumer(self) -> CheckResult:
        """Check resumer functionality."""
        try:
            resumer_path = self.base_path / "core/agent_control/resumer.py"
            if not resumer_path.exists():
                return CheckResult(
                    name="Resumer",
                    status=False,
                    details="Resumer module not found",
                    error="Resumer module not found"
                )

            # Check resumer configuration
            resumer_config = self.base_path / "configs/resumer_config.json"
            if not resumer_config.exists():
                return CheckResult(
                    name="Resumer",
                    status=False,
                    details="Resumer configuration not found",
                    error="Resumer configuration not found"
                )

            config = json.loads(resumer_config.read_text())
            required_keys = ["checkpoint_interval", "max_retries", "backup_path"]
            missing_keys = [k for k in required_keys if k not in config]
            
            if missing_keys:
                return CheckResult(
                    name="Resumer",
                    status=False,
                    details=f"Missing configuration keys: {', '.join(missing_keys)}",
                    error=f"Missing configuration keys: {', '.join(missing_keys)}"
                )

            # Verify backup directory
            backup_dir = Path(config["backup_path"])
            if not backup_dir.exists():
                return CheckResult(
                    name="Resumer",
                    status=False,
                    details="Backup directory not found",
                    error="Backup directory not found"
                )

            return CheckResult(
                name="Resumer",
                status=True,
                details="Resumer module and configuration valid"
            )

        except Exception as e:
            return CheckResult(
                name="Resumer",
                status=False,
                details=f"Error checking resumer: {str(e)}",
                error=str(e)
            )

    def check_onboarder(self) -> CheckResult:
        """Check onboarder functionality."""
        try:
            # Check onboarder module
            onboarder_path = self.base_path / "core/agent_control/onboarding"
            if not onboarder_path.exists():
                return CheckResult(
                    name="Onboarder",
                    status=False,
                    details="Onboarder module not found",
                    error="Onboarder module not found"
                )

            # Check required onboarder files
            required_files = [
                "onboarder.py",
                "message_manager.py",
                "captain_onboarder.py"
            ]
            missing_files = [
                f for f in required_files
                if not (onboarder_path / f).exists()
            ]
            
            if missing_files:
                return CheckResult(
                    name="Onboarder",
                    status=False,
                    details=f"Missing onboarder files: {', '.join(missing_files)}",
                    error=f"Missing onboarder files: {', '.join(missing_files)}"
                )

            # Check onboarding templates
            templates_path = self.base_path / "configs/onboarding_templates"
            if not templates_path.exists():
                return CheckResult(
                    name="Onboarder",
                    status=False,
                    details="Onboarding templates not found",
                    error="Onboarding templates not found"
                )

            required_templates = [
                "network_activation.j2",
                "individual_activation.j2",
                "broadcast.j2"
            ]
            missing_templates = [
                t for t in required_templates
                if not (templates_path / t).exists()
            ]
            
            if missing_templates:
                return CheckResult(
                    name="Onboarder",
                    status=False,
                    details=f"Missing templates: {', '.join(missing_templates)}",
                    error=f"Missing templates: {', '.join(missing_templates)}"
                )

            return CheckResult(
                name="Onboarder",
                status=True,
                details="Onboarder module and templates present"
            )

        except Exception as e:
            return CheckResult(
                name="Onboarder",
                status=False,
                details=f"Error checking onboarder: {str(e)}",
                error=str(e)
            )

    def check_chatgpt_bridge(self) -> CheckResult:
        """Check ChatGPT bridge integration."""
        try:
            # Check bridge module
            bridge_path = self.base_path / "core/agent_control/chatgpt_bridge.py"
            if not bridge_path.exists():
                return CheckResult(
                    name="ChatGPT Bridge",
                    status=False,
                    details="ChatGPT bridge module not found",
                    error="ChatGPT bridge module not found"
                )

            # Check bridge configuration
            bridge_config = self.base_path / "configs/chatgpt_bridge_config.json"
            if not bridge_config.exists():
                return CheckResult(
                    name="ChatGPT Bridge",
                    status=False,
                    details="Bridge configuration not found",
                    error="Bridge configuration not found"
                )

            config = json.loads(bridge_config.read_text())
            required_keys = ["api_key", "model", "max_tokens", "temperature"]
            missing_keys = [k for k in required_keys if k not in config]
            
            if missing_keys:
                return CheckResult(
                    name="ChatGPT Bridge",
                    status=False,
                    details=f"Missing configuration keys: {', '.join(missing_keys)}",
                    error=f"Missing configuration keys: {', '.join(missing_keys)}"
                )

            # Check Cursor integration
            cursor_config = self.base_path / "configs/cursor_integration.json"
            if not cursor_config.exists():
                return CheckResult(
                    name="ChatGPT Bridge",
                    status=False,
                    details="Cursor integration configuration not found",
                    error="Cursor integration configuration not found"
                )

            return CheckResult(
                name="ChatGPT Bridge",
                status=True,
                details="ChatGPT bridge and Cursor integration configured"
            )

        except Exception as e:
            return CheckResult(
                name="ChatGPT Bridge",
                status=False,
                details=f"Error checking ChatGPT bridge: {str(e)}",
                error=str(e)
            )

    def check_system_initialization(self) -> CheckResult:
        """Check system initialization components."""
        try:
            # Check system init module
            init_path = self.base_path / "core/system_init.py"
            if not init_path.exists():
                return CheckResult(
                    name="System Initialization",
                    status=False,
                    details="System initialization module not found",
                    error="System initialization module not found"
                )

            # Check core components
            required_components = [
                "coordinate_manager",
                "cell_phone",
                "message_processor",
                "agent_logger"
            ]
            
            # Verify each component's configuration
            for component in required_components:
                config_path = self.base_path / f"configs/{component}_config.json"
                if not config_path.exists():
                    return CheckResult(
                        name="System Initialization",
                        status=False,
                        details=f"Missing configuration for {component}",
                        error=f"Missing configuration for {component}"
                    )

            return CheckResult(
                name="System Initialization",
                status=True,
                details="All core components configured"
            )

        except Exception as e:
            return CheckResult(
                name="System Initialization",
                status=False,
                details=f"Error checking system initialization: {str(e)}",
                error=str(e)
            )

    def check_autonomy_system(self) -> CheckResult:
        """Check autonomy system components."""
        try:
            # Check autonomy module
            autonomy_path = self.base_path / "core/autonomy"
            if not autonomy_path.exists():
                return CheckResult(
                    name="Autonomy System",
                    status=False,
                    details="Autonomy system module not found",
                    error="Autonomy system module not found"
                )

            # Check required components
            required_components = [
                "autonomy_loop_runner.py",
                "midnight_runner.py",
                "test_watcher.py",
                "handlers/bridge_outbox_handler.py"
            ]
            
            missing_components = [
                comp for comp in required_components
                if not (autonomy_path / comp).exists()
            ]
            
            if missing_components:
                return CheckResult(
                    name="Autonomy System",
                    status=False,
                    details=f"Missing components: {', '.join(missing_components)}",
                    error=f"Missing components: {', '.join(missing_components)}"
                )

            # Check autonomy configuration
            autonomy_config = self.base_path / "configs/autonomy_config.json"
            if not autonomy_config.exists():
                return CheckResult(
                    name="Autonomy System",
                    status=False,
                    details="Autonomy configuration not found",
                    error="Autonomy configuration not found"
                )

            return CheckResult(
                name="Autonomy System",
                status=True,
                details="Autonomy system fully configured"
            )

        except Exception as e:
            return CheckResult(
                name="Autonomy System",
                status=False,
                details=f"Error checking autonomy system: {str(e)}",
                error=str(e)
            )

    def check_runtime_directories(self) -> CheckResult:
        """Check runtime directories and permissions."""
        try:
            required_dirs = [
                "runtime/agent_memory",
                "runtime/response_outbox",
                "runtime/response_archive",
                "runtime/memory",
                "data/mailbox",
                "data/archive",
                "data/failed"
            ]
            
            missing_dirs = []
            permission_issues = []
            
            for dir_path in required_dirs:
                full_path = self.base_path / dir_path
                if not full_path.exists():
                    missing_dirs.append(dir_path)
                elif not os.access(full_path, os.W_OK):
                    permission_issues.append(dir_path)
            
            if missing_dirs or permission_issues:
                details = []
                if missing_dirs:
                    details.append(f"Missing directories: {', '.join(missing_dirs)}")
                if permission_issues:
                    details.append(f"Permission issues: {', '.join(permission_issues)}")
                
                return CheckResult(
                    name="Runtime Directories",
                    status=False,
                    details="\n".join(details),
                    error="\n".join(details)
                )

            return CheckResult(
                name="Runtime Directories",
                status=True,
                details="All runtime directories present and writable"
            )

        except Exception as e:
            return CheckResult(
                name="Runtime Directories",
                status=False,
                details=f"Error checking runtime directories: {str(e)}",
                error=str(e)
            )

    def check_test_coverage(self) -> CheckResult:
        """Check test coverage and test infrastructure."""
        try:
            # Check test directory structure
            tests_dir = self.base_path / "tests"
            if not tests_dir.exists():
                return CheckResult(
                    name="Test Coverage",
                    status=False,
                    details="Tests directory not found",
                    error="Tests directory not found"
                )

            # Check test categories
            required_categories = ["unit", "integration", "core"]
            missing_categories = [
                cat for cat in required_categories
                if not (tests_dir / cat).exists()
            ]
            
            if missing_categories:
                return CheckResult(
                    name="Test Coverage",
                    status=False,
                    details=f"Missing test categories: {', '.join(missing_categories)}",
                    error=f"Missing test categories: {', '.join(missing_categories)}"
                )

            # Check test runner
            runner_path = self.base_path / "scripts/run_tests.py"
            if not runner_path.exists():
                return CheckResult(
                    name="Test Coverage",
                    status=False,
                    details="Test runner script not found",
                    error="Test runner script not found"
                )

            # Run coverage check
            try:
                result = subprocess.run(
                    ["python", str(runner_path), "--coverage", "--ci"],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    return CheckResult(
                        name="Test Coverage",
                        status=False,
                        details=f"Coverage check failed: {result.stderr}",
                        error=result.stderr
                    )
                
                # Parse coverage results
                coverage_data = {}
                for line in result.stdout.split("\n"):
                    if "TOTAL" in line:
                        try:
                            coverage = int(line.split("%")[0].split()[-1])
                            coverage_data["total"] = coverage
                        except (ValueError, IndexError):
                            pass
                
                if coverage_data.get("total", 0) < 80:
                    return CheckResult(
                        name="Test Coverage",
                        status=False,
                        details=f"Insufficient coverage: {coverage_data.get('total', 0)}%",
                        error=f"Insufficient coverage: {coverage_data.get('total', 0)}%"
                    )

            except Exception as e:
                return CheckResult(
                    name="Test Coverage",
                    status=False,
                    details=f"Error running coverage check: {str(e)}",
                    error=str(e)
                )

            return CheckResult(
                name="Test Coverage",
                status=True,
                details=f"Test coverage at {coverage_data.get('total', 0)}%"
            )

        except Exception as e:
            return CheckResult(
                name="Test Coverage",
                status=False,
                details=f"Error checking test coverage: {str(e)}",
                error=str(e)
            )

    def check_security_config(self) -> CheckResult:
        """Check security configuration and authentication."""
        try:
            # Check security config file
            config_path = Path("configs/security_config.json")
            if not config_path.exists():
                return CheckResult(
                    name="Security Configuration",
                    status=False,
                    details="Security configuration file missing",
                    error="configs/security_config.json not found"
                )
                
            with open(config_path) as f:
                config = json.load(f)
                
            # Validate required sections
            required_sections = ["auth", "session", "identity"]
            missing = [s for s in required_sections if s not in config]
            if missing:
                return CheckResult(
                    name="Security Configuration",
                    status=False,
                    details=f"Missing required sections: {', '.join(missing)}",
                    error="Incomplete security configuration"
                )
                
            # Check auth settings
            auth_config = config["auth"]
            required_auth = ["token_expiry", "max_login_attempts", "lockout_duration"]
            missing_auth = [k for k in required_auth if k not in auth_config]
            if missing_auth:
                return CheckResult(
                    name="Security Configuration",
                    status=False,
                    details=f"Missing auth settings: {', '.join(missing_auth)}",
                    error="Incomplete auth configuration"
                )
                
            return CheckResult(
                name="Security Configuration",
                status=True,
                details="Security configuration validated"
            )
            
        except Exception as e:
            return CheckResult(
                name="Security Configuration",
                status=False,
                details=f"Error checking security config: {str(e)}",
                error=str(e)
            )
            
    def check_monitoring_system(self) -> CheckResult:
        """Check monitoring and health check system."""
        try:
            # Check health monitor
            health_path = Path("dreamos/core/monitoring/health")
            if not health_path.exists():
                return CheckResult(
                    name="Monitoring System",
                    status=False,
                    details="Health monitoring module missing",
                    error="Health monitoring directory not found"
                )
                
            # Check required health monitors
            required_monitors = ["base.py", "bridge_health.py"]
            missing = [m for m in required_monitors if not (health_path / m).exists()]
            if missing:
                return CheckResult(
                    name="Monitoring System",
                    status=False,
                    details=f"Missing health monitors: {', '.join(missing)}",
                    error="Incomplete health monitoring system"
                )
                
            # Check metrics collection
            metrics_path = Path("dreamos/core/bridge/monitoring/metrics.py")
            if not metrics_path.exists():
                return CheckResult(
                    name="Monitoring System",
                    status=False,
                    details="Metrics collection module missing",
                    error="Metrics module not found"
                )
                
            return CheckResult(
                name="Monitoring System",
                status=True,
                details="Monitoring system validated"
            )
            
        except Exception as e:
            return CheckResult(
                name="Monitoring System",
                status=False,
                details=f"Error checking monitoring system: {str(e)}",
                error=str(e)
            )
            
    def check_error_handling(self) -> CheckResult:
        """Check error handling and recovery systems."""
        try:
            # Check error tracking
            error_path = Path("dreamos/core/autonomy/error_tracking.py")
            if not error_path.exists():
                return CheckResult(
                    name="Error Handling",
                    status=False,
                    details="Error tracking module missing",
                    error="Error tracking module not found"
                )
                
            # Check backup/restore functionality
            backup_utils = Path("dreamos/core/utils/serialization.py")
            if not backup_utils.exists():
                return CheckResult(
                    name="Error Handling",
                    status=False,
                    details="Backup utilities missing",
                    error="Backup utilities not found"
                )
                
            # Check atomic file operations
            atomic_path = Path("dreamos/core/resumer_v2/atomic_file_manager.py")
            if not atomic_path.exists():
                return CheckResult(
                    name="Error Handling",
                    status=False,
                    details="Atomic file operations missing",
                    error="Atomic file manager not found"
                )
                
            return CheckResult(
                name="Error Handling",
                status=True,
                details="Error handling system validated"
            )
            
        except Exception as e:
            return CheckResult(
                name="Error Handling",
                status=False,
                details=f"Error checking error handling: {str(e)}",
                error=str(e)
            )
            
    def check_coordinate_system(self) -> CheckResult:
        """Check coordinate management system."""
        try:
            # Check coordinate manager
            coord_path = Path("dreamos/core/shared/coordinate_manager.py")
            if not coord_path.exists():
                return CheckResult(
                    name="Coordinate System",
                    status=False,
                    details="Coordinate manager missing",
                    error="Coordinate manager not found"
                )
                
            # Check coordinate utils
            utils_path = Path("dreamos/core/shared/coordinate_utils.py")
            if not utils_path.exists():
                return CheckResult(
                    name="Coordinate System",
                    status=False,
                    details="Coordinate utilities missing",
                    error="Coordinate utilities not found"
                )
                
            return CheckResult(
                name="Coordinate System",
                status=True,
                details="Coordinate system validated"
            )
            
        except Exception as e:
            return CheckResult(
                name="Coordinate System",
                status=False,
                details=f"Error checking coordinate system: {str(e)}",
                error=str(e)
            )

    def check_cursor_agent_bridge(self) -> CheckResult:
        """Check Cursor agent bridge functionality."""
        try:
            bridge_config = self.base_path / "config/bridge_config.yaml"
            if not bridge_config.exists():
                return CheckResult(
                    name="Cursor Bridge",
                    status=False,
                    details="Bridge configuration not found",
                    error="Bridge configuration not found"
                )
                
            config = yaml.safe_load(bridge_config.read_text())
            required_keys = ["cursor_window_title", "bridge_outbox", "bridge_inbox"]
            missing_keys = [k for k in required_keys if k not in config]
            
            if missing_keys:
                return CheckResult(
                    name="Cursor Bridge",
                    status=False,
                    details=f"Missing config keys: {', '.join(missing_keys)}",
                    error=f"Missing config keys: {', '.join(missing_keys)}"
                )
                
            # Check coordinate system
            coords_file = self.base_path / "config/cursor_agent_coords.json"
            if not coords_file.exists():
                return CheckResult(
                    name="Cursor Bridge",
                    status=False,
                    details="Agent coordinates file not found",
                    error="Agent coordinates file not found"
                )
                
            return CheckResult(
                name="Cursor Bridge",
                status=True,
                details="Bridge configuration and coordinates present"
            )
            
        except Exception as e:
            return CheckResult(
                name="Cursor Bridge",
                status=False,
                details=f"Error checking cursor bridge: {str(e)}",
                error=str(e)
            )

    def check_agent_recovery(self) -> CheckResult:
        """Check agent recovery system."""
        try:
            recovery_config = self.base_path / "config/recovery_config.yaml"
            if not recovery_config.exists():
                return CheckResult(
                    name="Agent Recovery",
                    status=False,
                    details="Recovery configuration not found",
                    error="Recovery configuration not found"
                )
                
            config = yaml.safe_load(recovery_config.read_text())
            required_keys = ["max_retries", "retry_delay", "heartbeat_timeout"]
            missing_keys = [k for k in required_keys if k not in config]
            
            if missing_keys:
                return CheckResult(
                    name="Agent Recovery",
                    status=False,
                    details=f"Missing config keys: {', '.join(missing_keys)}",
                    error=f"Missing config keys: {', '.join(missing_keys)}"
                )
                
            return CheckResult(
                name="Agent Recovery",
                status=True,
                details="Recovery configuration present and valid"
            )
            
        except Exception as e:
            return CheckResult(
                name="Agent Recovery",
                status=False,
                details=f"Error checking agent recovery: {str(e)}",
                error=str(e)
            )

    def check_response_collection(self) -> CheckResult:
        """Check response collection system."""
        try:
            collector_config = self.base_path / "config/collector_config.yaml"
            if not collector_config.exists():
                return CheckResult(
                    name="Response Collection",
                    status=False,
                    details="Collector configuration not found",
                    error="Collector configuration not found"
                )
                
            config = yaml.safe_load(collector_config.read_text())
            required_keys = ["collection_interval", "max_retries", "timeout"]
            missing_keys = [k for k in required_keys if k not in config]
            
            if missing_keys:
                return CheckResult(
                    name="Response Collection",
                    status=False,
                    details=f"Missing config keys: {', '.join(missing_keys)}",
                    error=f"Missing config keys: {', '.join(missing_keys)}"
                )
                
            return CheckResult(
                name="Response Collection",
                status=True,
                details="Collector configuration present and valid"
            )
            
        except Exception as e:
            return CheckResult(
                name="Response Collection",
                status=False,
                details=f"Error checking response collection: {str(e)}",
                error=str(e)
            )

    def _categorize_check(self, check_name: str) -> str:
        """Categorize a check based on its name."""
        categories = {
            "Core": ["mailboxes", "docs", "tests", "orphans", "state", "backlog"],
            "System": ["initialization", "autonomy", "runtime", "coordinate"],
            "Security": ["security", "auth", "session", "identity"],
            "Monitoring": ["monitoring", "health", "metrics", "bridge"],
            "Error": ["error", "recovery", "backup", "atomic"],
            "Integration": ["discord", "social", "resumer", "onboarder", "chatgpt", "cursor"],
            "Collection": ["response", "collector"]
        }
        
        for category, keywords in categories.items():
            if any(k in check_name.lower() for k in keywords):
                return category
        return "Other"
        
    def _determine_severity(self, check_name: str, status: bool) -> str:
        """Determine severity of a check result."""
        critical_checks = {
            "security": "high",
            "auth": "high",
            "initialization": "high",
            "autonomy": "high",
            "runtime": "high",
            "error": "high",
            "recovery": "high"
        }
        
        if not status:
            return critical_checks.get(check_name.lower(), "medium")
        return "low"
        
    def _generate_recommendations(self, check_name: str, status: bool, error: Optional[str] = None) -> List[str]:
        """Generate recommendations based on check result."""
        if status:
            return []
            
        recommendations = {
            "security": [
                "Review security configuration",
                "Check authentication settings",
                "Verify access controls"
            ],
            "monitoring": [
                "Check health check intervals",
                "Verify metrics collection",
                "Review alert thresholds"
            ],
            "error": [
                "Review error handling procedures",
                "Check backup configurations",
                "Verify recovery mechanisms"
            ],
            "integration": [
                "Check API configurations",
                "Verify connection settings",
                "Review integration status"
            ]
        }
        
        for key, recs in recommendations.items():
            if key in check_name.lower():
                return recs
        return ["Review configuration", "Check logs for details"]

    def run_verification(self) -> List[CheckResult]:
        """Run all verification checks.
        
        Returns:
            List of check results
        """
        checks = [
            self.check_mailboxes,
            self.check_required_docs,
            self.check_unit_tests,
            self.check_orphans_and_dupes,
            self.check_agent_state_files,
            self.check_backlog_and_episodes,
            self.check_autonomy_loop,
            self.check_discord_commander,
            self.check_discord_devlog,
            self.check_social_integrations,
            self.check_resumer,
            self.check_onboarder,
            self.check_chatgpt_bridge,
            self.check_system_initialization,
            self.check_autonomy_system,
            self.check_runtime_directories,
            self.check_test_coverage,
            self.check_security_config,
            self.check_monitoring_system,
            self.check_error_handling,
            self.check_coordinate_system,
            self.check_cursor_agent_bridge,
            self.check_agent_recovery,
            self.check_response_collection
        ]
        
        self.results = []
        for check in checks:
            result = check()
            # Enhance result with additional metadata
            result.category = self._categorize_check(result.name)
            result.severity = self._determine_severity(result.name, result.status)
            result.recommendations = self._generate_recommendations(result.name, result.status, result.error)
            self.results.append(result)
            
            if not result.status:
                logger.error(f"Check failed: {result.name} - {result.error}")
                
        return self.results
        
    def generate_report(self, output_path: Optional[str] = None) -> str:
        """Generate verification report.
        
        Args:
            output_path: Optional path to save report
            
        Returns:
            Report content
        """
        report = [
            "# Dream.OS Beta Verification Report\n",
            f"Generated: {datetime.now().isoformat()}\n",
            f"Duration: {(datetime.now() - self.start_time).total_seconds():.1f} seconds\n"
        ]
        
        # Summary
        total = len(self.results)
        passed = sum(1 for r in self.results if r.status)
        failed = total - passed
        
        report.extend([
            "## Summary\n",
            f"- Total Checks: {total}",
            f"- Passed: {passed}",
            f"- Failed: {failed}",
            f"- Success Rate: {(passed/total)*100:.1f}%\n"
        ])
        
        # Critical Issues
        critical_failures = [r for r in self.results if not r.status and r.severity == "high"]
        if critical_failures:
            report.extend([
                "## ⚠️ Critical Issues\n",
                "The following critical checks failed:\n"
            ])
            for result in critical_failures:
                report.extend([
                    f"### ❌ {result.name}",
                    f"- Category: {result.category}",
                    f"- Error: {result.error}",
                    f"- Recommendations:",
                    *[f"  - {rec}" for rec in result.recommendations],
                    ""
                ])
        
        # Detailed Results by Category
        report.append("## Detailed Results\n")
        
        categories = sorted(set(r.category for r in self.results))
        for category in categories:
            category_results = [r for r in self.results if r.category == category]
            passed_count = sum(1 for r in category_results if r.status)
            
            report.extend([
                f"### {category} ({passed_count}/{len(category_results)} passed)\n"
            ])
            
            for result in category_results:
                status = "✅" if result.status else "❌"
                severity = "🔴" if result.severity == "high" else "🟡" if result.severity == "medium" else "🟢"
                
                report.extend([
                    f"#### {status} {severity} {result.name}",
                    f"- Status: {'Passed' if result.status else 'Failed'}",
                    f"- Details: {result.details}",
                    f"- Timestamp: {result.timestamp}"
                ])
                
                if result.error:
                    report.append(f"- Error: {result.error}")
                    
                if result.recommendations:
                    report.extend([
                        "- Recommendations:",
                        *[f"  - {rec}" for rec in result.recommendations]
                    ])
                    
                report.append("")
        
        # System Health
        report.extend([
            "## System Health\n",
            "### Resource Usage",
            "- CPU: [To be implemented]",
            "- Memory: [To be implemented]",
            "- Disk: [To be implemented]",
            "\n### Performance Metrics",
            "- Response Time: [To be implemented]",
            "- Throughput: [To be implemented]",
            "- Error Rate: [To be implemented]"
        ])
        
        # Recommendations
        if failed > 0:
            report.extend([
                "\n## Recommendations\n",
                "1. Address critical issues first",
                "2. Review failed checks in each category",
                "3. Implement recommended fixes",
                "4. Re-run verification after fixes"
            ])
        
        content = "\n".join(report)
        if output_path:
            with open(output_path, "w") as f:
                f.write(content)
                
        return content

def main():
    """Run the verification system."""
    parser = argparse.ArgumentParser(description="Dream.OS Beta Verification System")
    parser.add_argument("--output", "-o", help="Output file path for the report")
    parser.add_argument("--json", "-j", action="store_true", help="Output in JSON format")
    args = parser.parse_args()
    
    verifier = BetaVerifier()
    results = verifier.run_verification()
    
    if args.json:
        print(json.dumps([r.to_dict() for r in results], indent=2))
    else:
        report = verifier.generate_report(args.output)
        if not args.output:
            print(report)

if __name__ == "__main__":
    main() 