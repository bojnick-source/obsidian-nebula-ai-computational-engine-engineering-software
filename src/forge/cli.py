"""FORGE CLI entry point — M1 Phase 0.1.

Boots FORGE, loads forge.yaml, prints version, logs JSONL.
This is the first running code artifact.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from forge import __version__
from forge.config import load_config, ForgeConfig
from forge.logging import init_logger, ForgeLogger


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="forge",
        description="FORGE — AI Computational Engine for Engineering Software",
    )
    parser.add_argument(
        "--version", action="version", version=f"FORGE v{__version__}"
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("forge.yaml"),
        help="Path to forge.yaml configuration file (default: ./forge.yaml)",
    )
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="Run smoke test: load config, log a trace, verify blackboard, exit.",
    )
    return parser


def smoke_test(config: ForgeConfig, logger: ForgeLogger) -> int:
    """M1 gate: forge --smoke-test passes."""
    from forge.blackboard import Blackboard

    logger.info("smoke_test_start", message="FORGE smoke test initiated")

    # Verify config loaded
    logger.info(
        "config_loaded",
        version=config.forge.version,
        mode=config.forge.mode,
        agent_count=len(config.agents),
        provider_count=len(config.providers),
    )

    # Verify blackboard stores typed dict
    bb = Blackboard()
    bb.put("smoke_test", {"status": "pass", "version": config.forge.version})
    result = bb.get("smoke_test")
    if result is None or result["status"] != "pass":
        logger.error("smoke_test_fail", message="Blackboard read-back failed")
        return 1

    logger.info(
        "blackboard_verified",
        message="Blackboard write-read cycle passed",
        entry=result,
    )

    # Summary
    logger.info(
        "smoke_test_pass",
        message="All smoke test checks passed",
        forge_version=config.forge.version,
        agents=[a_id for a_id in config.agents],
        providers=[p_id for p_id in config.providers],
        memory_mode=config.memory.mode,
    )

    print(f"FORGE v{config.forge.version} — smoke test PASSED")
    print(f"  Agents:    {len(config.agents)}")
    print(f"  Providers: {len(config.providers)}")
    print(f"  Memory:    {config.memory.mode}")
    print(f"  Log:       {logger.log_path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    config_path: Path = args.config
    if not config_path.exists():
        print(f"Error: config file not found: {config_path}", file=sys.stderr)
        return 1

    config = load_config(config_path)
    logger = init_logger(config)

    logger.info(
        "forge_boot",
        version=config.forge.version,
        config_path=str(config_path),
    )

    if args.smoke_test:
        return smoke_test(config, logger)

    print(f"FORGE v{config.forge.version}")
    print("Use --smoke-test to run M1 gate validation.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
