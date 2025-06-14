"""
Security Overlay Generator for Dream.OS Tasks

This module provides a standardized way to generate security overlays for tasks,
ensuring consistent security review and mitigation planning across the system.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
import json
import yaml
from pathlib import Path

@dataclass
class SecurityRisk:
    """Represents a potential security risk in a task."""
    name: str
    description: str
    severity: str  # 'critical', 'high', 'medium', 'low'
    impact: str
    likelihood: str  # 'high', 'medium', 'low'

@dataclass
class ValidationCheck:
    """Represents a security validation check."""
    name: str
    description: str
    required: bool
    automated: bool
    priority: str  # 'high', 'medium', 'low'

@dataclass
class AttackSurface:
    """Represents a potential attack surface in a task."""
    name: str
    description: str
    entry_points: List[str]
    potential_impact: str
    mitigation_priority: str  # 'high', 'medium', 'low'

@dataclass
class MitigationStep:
    """Represents a security mitigation step."""
    name: str
    description: str
    implementation_priority: str  # 'high', 'medium', 'low'
    dependencies: List[str]
    validation_requirements: List[str]

@dataclass
class SecurityOverlay:
    """Represents a complete security overlay for a task."""
    task_id: str
    risks: List[SecurityRisk]
    validation_checks: List[ValidationCheck]
    attack_surfaces: List[AttackSurface]
    mitigation_steps: List[MitigationStep]
    security_dependencies: List[str]
    monitoring_requirements: List[str]

class SecurityOverlayGenerator:
    """Generates security overlays for tasks."""
    
    def __init__(self, template_dir: Optional[Path] = None):
        self.template_dir = template_dir or Path(__file__).parent / 'templates'
        self.template_dir.mkdir(exist_ok=True)
        
    def generate_markdown(self, overlay: SecurityOverlay) -> str:
        """Generates a markdown representation of the security overlay."""
        return f"""### 🔒 Security Overlay

#### Potential Risks
{self._format_risks(overlay.risks)}

#### Validation Checks
{self._format_validation_checks(overlay.validation_checks)}

#### Attack Surfaces
{self._format_attack_surfaces(overlay.attack_surfaces)}

#### Mitigation Plan
{self._format_mitigation_steps(overlay.mitigation_steps)}

#### Security Dependencies
{self._format_dependencies(overlay.security_dependencies)}

#### Monitoring Requirements
{self._format_monitoring(overlay.monitoring_requirements)}
"""

    def _format_risks(self, risks: List[SecurityRisk]) -> str:
        return "\n".join(
            f"- **{risk.name}** ({risk.severity.upper()})\n"
            f"  - Description: {risk.description}\n"
            f"  - Impact: {risk.impact}\n"
            f"  - Likelihood: {risk.likelihood}"
            for risk in risks
        )

    def _format_validation_checks(self, checks: List[ValidationCheck]) -> str:
        return "\n".join(
            f"- [ ] **{check.name}** ({check.priority.upper()})\n"
            f"  - Description: {check.description}\n"
            f"  - Automated: {'Yes' if check.automated else 'No'}"
            for check in checks
        )

    def _format_attack_surfaces(self, surfaces: List[AttackSurface]) -> str:
        return "\n".join(
            f"- **{surface.name}** ({surface.mitigation_priority.upper()})\n"
            f"  - Description: {surface.description}\n"
            f"  - Entry Points: {', '.join(surface.entry_points)}\n"
            f"  - Potential Impact: {surface.potential_impact}"
            for surface in surfaces
        )

    def _format_mitigation_steps(self, steps: List[MitigationStep]) -> str:
        return "\n".join(
            f"- **{step.name}** ({step.implementation_priority.upper()})\n"
            f"  - Description: {step.description}\n"
            f"  - Dependencies: {', '.join(step.dependencies)}\n"
            f"  - Validation Requirements: {', '.join(step.validation_requirements)}"
            for step in steps
        )

    def _format_dependencies(self, dependencies: List[str]) -> str:
        return "\n".join(f"- {dep}" for dep in dependencies)

    def _format_monitoring(self, requirements: List[str]) -> str:
        return "\n".join(f"- {req}" for req in requirements)

    def save_overlay(self, overlay: SecurityOverlay, output_path: Path):
        """Saves the security overlay to a file."""
        output_path.write_text(self.generate_markdown(overlay))

    def load_template(self, template_name: str) -> Dict:
        """Loads a security template from the templates directory."""
        template_path = self.template_dir / f"{template_name}.yaml"
        if not template_path.exists():
            raise FileNotFoundError(f"Template {template_name} not found")
        return yaml.safe_load(template_path.read_text())

    def create_overlay_from_template(self, task_id: str, template_name: str) -> SecurityOverlay:
        """Creates a security overlay from a template."""
        template = self.load_template(template_name)
        return SecurityOverlay(
            task_id=task_id,
            risks=[SecurityRisk(**risk) for risk in template['risks']],
            validation_checks=[ValidationCheck(**check) for check in template['validation_checks']],
            attack_surfaces=[AttackSurface(**surface) for surface in template['attack_surfaces']],
            mitigation_steps=[MitigationStep(**step) for step in template['mitigation_steps']],
            security_dependencies=template['security_dependencies'],
            monitoring_requirements=template['monitoring_requirements']
        )

def main():
    """Example usage of the SecurityOverlayGenerator."""
    generator = SecurityOverlayGenerator()
    
    # Example overlay
    overlay = SecurityOverlay(
        task_id="TASK-001",
        risks=[
            SecurityRisk(
                name="File Injection",
                description="Potential for malicious file injection through bridge outbox",
                severity="high",
                impact="System compromise",
                likelihood="medium"
            )
        ],
        validation_checks=[
            ValidationCheck(
                name="File Path Sanitization",
                description="Validate and sanitize all file paths",
                required=True,
                automated=True,
                priority="high"
            )
        ],
        attack_surfaces=[
            AttackSurface(
                name="Bridge Outbox",
                description="File processing endpoint for bridge communications",
                entry_points=["file_upload", "message_processing"],
                potential_impact="System access",
                mitigation_priority="high"
            )
        ],
        mitigation_steps=[
            MitigationStep(
                name="Implement File Validation",
                description="Add strict file validation and sanitization",
                implementation_priority="high",
                dependencies=["file_validator", "path_sanitizer"],
                validation_requirements=["unit_tests", "integration_tests"]
            )
        ],
        security_dependencies=[
            "File Validator Service",
            "Path Sanitizer",
            "Access Control System"
        ],
        monitoring_requirements=[
            "File access logging",
            "Validation failure alerts",
            "Attack pattern detection"
        ]
    )
    
    # Generate and save overlay
    output_path = Path("security_overlay.md")
    generator.save_overlay(overlay, output_path)
    print(f"Security overlay saved to {output_path}")

if __name__ == "__main__":
    main() 
