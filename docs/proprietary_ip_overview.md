# Proprietary Logic Overview

This document summarizes components in the repository that contain or plan to contain proprietary or important logic. The repository does not include an explicit license, so all content should be treated as proprietary by default.

## Key Modules

- **dreamos/core** – Central orchestrator, messaging, and agent management logic.
  - `dreamscribe.py` – Handles the narrative memory system. Future plans include NLP-driven keyword extraction and pattern learning to surface insights automatically. A simple keyword extractor has been implemented as a stepping stone.
  - `memory_querier.py` – Provides querying and analysis of stored memories. Similarity checks now use `difflib.SequenceMatcher`, and future iterations may incorporate vector embeddings for semantic search.
  - `auth/token.py` – Token generation and validation utilities. Tokens are now signed with an HMAC digest; a full JWT-style system could further enhance security.
  - `autonomy/auto_trigger_runner.py` – Automatically triggers agents to fix failing tests. A more advanced version could select agents based on historical performance metrics and task expertise.
  - `autonomy/bridge_outbox_handler.py` – Applies code changes from bridge conversations. TODO: Implement AST-based modifications to ensure syntax integrity and minimize merge conflicts.
  - `agents/perpetual_test_fixer.py` – Manages automated test fixing loop. TODO: Finalize the agent communication channel for distributed repair workflows.
- **dreamos/core/logging/log_config.py** – Configures unified logging across the system.
- **dreamos/core/messaging/message_system.py** – Implements the unified message system for inter-agent communication.
- **discord_bot/** – Provides Discord integration for remote control and monitoring.

## Notes

Many of the modules above contain TODO comments where more sophisticated algorithms are intended to be implemented. These areas likely represent proprietary plans for advanced functionality. This overview can serve as a starting point for further IP documentation efforts.

