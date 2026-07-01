import argparse
import json

from src.agent.intent_parser import build_execution_plan, parse_command


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse instruksi natural untuk AI Agent SIGA.")
    parser.add_argument("command", help="Instruksi user, contoh: input data implant 10 orang dari desa ambulu rt.2 rw.6")
    args = parser.parse_args()

    intent = parse_command(args.command)
    output = {
        "intent": intent.to_dict(),
        "execution_plan": build_execution_plan(intent),
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
