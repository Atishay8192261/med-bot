import os
from app.langgraph_agent import run_turn


def main():
    session = os.getenv("SESSION_ID", "demo")
    print("MedBot Agent REPL. Type 'exit' to quit.")
    while True:
        try:
            text = input("> ").strip()
        except EOFError:
            break
        if not text or text.lower() in {"exit", "quit"}:
            break
        res = run_turn(session, text)
        print(f"[intent={res['intent']}] brand={res['brand']} sig={res['signature']}")
        print(res["answer"])
        print()
    print("bye.")


if __name__ == "__main__":
    main()
