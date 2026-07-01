import argparse
import json
from dataclasses import asdict

from src.agent.orchestrator import run_job


def main() -> None:
    parser = argparse.ArgumentParser(description="Dry-run AI agent input data SIGA.")
    parser.add_argument("--input", required=True, help="Path file CSV input.")
    parser.add_argument(
        "--mapping",
        default="config/field_mapping.example.json",
        help="Path file mapping field.",
    )
    parser.add_argument(
        "--config",
        default="config/agent.config.example.json",
        help="Path konfigurasi agent.",
    )
    parser.add_argument(
        "--target",
        default=None,
        help="Target menu, contoh: yankb_pelkon.tempat_pelayanan_kb.",
    )
    parser.add_argument(
        "--approved",
        action="store_true",
        help="Tandai job sudah di-approve. Tidak berpengaruh jika dry_run masih true.",
    )

    args = parser.parse_args()
    result = run_job(
        input_path=args.input,
        mapping_path=args.mapping,
        config_path=args.config,
        target_key=args.target,
        approved=args.approved,
    )
    print(json.dumps(asdict(result), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
