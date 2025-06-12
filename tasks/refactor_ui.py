{
    "file": "dreamos/core/messaging/ui.py",
    "duplicates": 90,
    "complexity": 38,
    "analysis": {
        "duplicate_patterns": [
            {
                "pattern": "Message formatting functions",
                "count": 35,
                "files": [
                    "dreamos/core/messaging/formatters.py",
                    "dreamos/core/social/formatters.py"
                ]
            },
            {
                "pattern": "UI component builders",
                "count": 28,
                "files": [
                    "dreamos/core/messaging/components.py",
                    "dreamos/core/social/components.py"
                ]
            },
            {
                "pattern": "Layout templates",
                "count": 27,
                "files": [
                    "dreamos/core/messaging/templates.py",
                    "dreamos/core/social/templates.py"
                ]
            }
        ],
        "complexity_hotspots": [
            {
                "name": "format_message",
                "complexity": 14,
                "lines": 105,
                "calls": 78
            },
            {
                "name": "build_ui_component",
                "complexity": 12,
                "lines": 92,
                "calls": 65
            },
            {
                "name": "apply_template",
                "complexity": 9,
                "lines": 75,
                "calls": 52
            }
        ]
    },
    "refactor_plan": {
        "new_classes": [
            {
                "name": "UIMessageBuilder",
                "responsibility": "Build and format UI messages",
                "methods": [
                    "create_basic_message",
                    "create_rich_message",
                    "create_embed_message",
                    "create_interactive_message"
                ]
            },
            {
                "name": "UIComponentFactory",
                "responsibility": "Create UI components",
                "methods": [
                    "create_button",
                    "create_select",
                    "create_modal",
                    "create_embed"
                ]
            },
            {
                "name": "UILayoutManager",
                "responsibility": "Manage UI layouts and templates",
                "methods": [
                    "apply_template",
                    "customize_layout",
                    "validate_layout",
                    "optimize_layout"
                ]
            }
        ],
        "migration_steps": [
            {
                "step": 1,
                "description": "Create new UI builder classes",
                "files": [
                    "dreamos/core/ui/builders/message_builder.py",
                    "dreamos/core/ui/builders/component_factory.py",
                    "dreamos/core/ui/builders/layout_manager.py"
                ]
            },
            {
                "step": 2,
                "description": "Update message handling",
                "files": [
                    "dreamos/core/messaging/handlers.py",
                    "dreamos/core/social/handlers.py"
                ],
                "changes": [
                    "Replace direct UI calls with builder pattern",
                    "Update message formatting"
                ]
            },
            {
                "step": 3,
                "description": "Migrate templates",
                "files": [
                    "dreamos/core/ui/templates/basic.py",
                    "dreamos/core/ui/templates/rich.py",
                    "dreamos/core/ui/templates/interactive.py"
                ]
            },
            {
                "step": 4,
                "description": "Update documentation",
                "files": [
                    "docs/ui/message_building.md",
                    "docs/ui/components.md",
                    "docs/ui/templates.md"
                ]
            }
        ],
        "expected_benefits": [
            "Cleaner message building",
            "Reusable UI components",
            "Consistent layouts",
            "Better type safety",
            "Easier testing"
        ]
    }
} 