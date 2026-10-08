#!/usr/bin/env python3
"""Main Entry Point for CDT Automated Execution and Experimentation.

Usage:
  python run_pipeline.py --check-env
  python run_pipeline.py --config config/experimentos_precipitacion.yaml
  python run_pipeline.py --config config/experimentos_temperatura.yaml
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from launcher.env_checker import check_system_environment, print_environment_report
from launcher.experiment_runner import ExperimentRunner


def main() -> int:
    parser = argparse.ArgumentParser(
        description="CDT Automated Experimentation and Pipeline Runner (Linux / Windows)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--check-env",
        action="store_true",
        help="Run environment pre-flight check for R, packages, and system dependencies.",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to YAML experiment configuration file.",
    )
    parser.add_argument(
        "--rscript",
        type=str,
        default=None,
        help="Optional custom path to Rscript binary.",
    )

    args = parser.parse_args()

    # If --check-env is specified or no arguments are given
    if args.check_env or (not args.config):
        env_status = check_system_environment()
        print_environment_report(env_status)
        if not env_status["is_ready"]:
            return 1
        if not args.config:
            print("To run an experiment batch, provide --config <path_to_yaml_file>.\n")
            return 0

    # Validate environment before running experiments
    env_status = check_system_environment()
    if not env_status["is_ready"]:
        print_environment_report(env_status)
        print("[!] Error: Environment is not ready. Aborting experiment execution.", file=sys.stderr)
        return 1

    config_path = Path(args.config)
    if not config_path.exists():
        print(f"[!] Error: Config file not found: {config_path}", file=sys.stderr)
        return 1

    try:
        runner = ExperimentRunner(config_path=config_path, rscript_path=args.rscript)
        results = runner.run_all_experiments()
        all_ok = all(res.get("status") == "SUCCESS" for res in results)
        return 0 if all_ok else 1
    except Exception as e:
        print(f"\n[!] Fatal Error during experiment execution: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
