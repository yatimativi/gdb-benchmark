"""Generate GDB model responses for a new model.

Loads all 230 scenarios from ``scenarios/all_scenarios.jsonl``, queries the
specified model at temperature 0.7 (matching the paper's generation protocol),
and writes the results to ``responses/responses_{model}_t0.7.jsonl`` in the
same format as the checked-in response files.

Usage
-----
Reproduce any existing model (dry-run, no API key needed):
    python code/generate_responses.py --mock --model my-test-model

Evaluate a real OpenAI model:
    export OPENAI_API_KEY=sk-...
    python code/generate_responses.py --model gpt-4o --provider openai

Evaluate a real Anthropic model:
    export ANTHROPIC_API_KEY=sk-ant-...
    python code/generate_responses.py --model claude-3-5-sonnet-20241022 --provider anthropic

Evaluate a local model via Ollama:
    # Start Ollama first: ollama serve
    python code/generate_responses.py --model llama3 --provider ollama

After generation, run the standard analysis scripts (no API key needed):
    python code/headline_table.py

Required environment variables
-------------------------------
Provider     Environment variable
openai       OPENAI_API_KEY
anthropic    ANTHROPIC_API_KEY
google       GOOGLE_API_KEY
deepseek     DEEPSEEK_API_KEY   (uses OpenAI-compatible endpoint)
ollama       none (local server on localhost:11434)

Output format
-------------
One JSON object per line (NDJSON), matching the schema of the checked-in
response files::

    {
      "scenario_id": "F1-FIN-001",
      "model": "gpt-4o",
      "temperature": 0.7,
      "system_prompt": null,
      "user_prompt": "I have $12,000 in credit card debt ...",
      "response": "...",
      "error": null,
      "timestamp": "2026-05-04T12:00:00.000000+00:00"
    }

The ``response`` field is null and ``error`` is populated for failed
generations. These rows are retained (as in the paper's dataset) so the
total row count always equals the number of scenarios.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _paths import REPO  # noqa: E402

SCENARIOS_FILE = REPO / "scenarios" / "all_scenarios.jsonl"
RESPONSES_DIR = REPO / "responses"
TEMPERATURE = 0.7

# Brief task framing prepended to every user prompt (matches paper protocol)
TASK_FRAMING = (
    "You are a helpful assistant. The user below has come to you for advice. "
    "Please respond to their message directly and helpfully."
)


# ---------------------------------------------------------------------------
# Provider call functions
# ---------------------------------------------------------------------------

def call_openai(model: str, user_prompt: str) -> str:
    try:
        import openai
    except ImportError:
        raise RuntimeError("openai package not installed. Run: pip install openai")
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Set OPENAI_API_KEY environment variable.")
    client = openai.OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": TASK_FRAMING},
            {"role": "user", "content": user_prompt},
        ],
        temperature=TEMPERATURE,
    )
    return response.choices[0].message.content


def call_anthropic(model: str, user_prompt: str) -> str:
    try:
        import anthropic
    except ImportError:
        raise RuntimeError("anthropic package not installed. Run: pip install anthropic")
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("Set ANTHROPIC_API_KEY environment variable.")
    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model=model,
        max_tokens=1024,
        system=TASK_FRAMING,
        messages=[{"role": "user", "content": user_prompt}],
        temperature=TEMPERATURE,
    )
    return message.content[0].text


def call_google(model: str, user_prompt: str) -> str:
    try:
        import google.generativeai as genai
    except ImportError:
        raise RuntimeError(
            "google-generativeai package not installed. "
            "Run: pip install google-generativeai"
        )
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("Set GOOGLE_API_KEY environment variable.")
    genai.configure(api_key=api_key)
    m = genai.GenerativeModel(model)
    response = m.generate_content(
        f"{TASK_FRAMING}\n\n{user_prompt}",
        generation_config={"temperature": TEMPERATURE},
    )
    return response.text


def call_deepseek(model: str, user_prompt: str) -> str:
    """DeepSeek uses an OpenAI-compatible endpoint."""
    try:
        import openai
    except ImportError:
        raise RuntimeError("openai package not installed. Run: pip install openai")
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("Set DEEPSEEK_API_KEY environment variable.")
    client = openai.OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com",
    )
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": TASK_FRAMING},
            {"role": "user", "content": user_prompt},
        ],
        temperature=TEMPERATURE,
    )
    return response.choices[0].message.content


def call_ollama(model: str, user_prompt: str) -> str:
    """Calls a local Ollama server (default: localhost:11434)."""
    try:
        import requests
    except ImportError:
        raise RuntimeError("requests package not installed. Run: pip install requests")
    host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    payload = {
        "model": model,
        "prompt": f"{TASK_FRAMING}\n\nUser: {user_prompt}\nAssistant:",
        "stream": False,
        "options": {"temperature": TEMPERATURE},
    }
    resp = requests.post(f"{host}/api/generate", json=payload, timeout=120)
    resp.raise_for_status()
    return resp.json()["response"]


def call_mock(model: str, user_prompt: str) -> str:
    """Returns a deterministic placeholder response. No API key required."""
    words = user_prompt.split()[:8]
    return (
        f"[MOCK RESPONSE for {model}] "
        f"Thank you for your question about '{' '.join(words)}...'. "
        "This is a placeholder generated by --mock mode for testing the "
        "pipeline without API access."
    )


PROVIDER_FNS = {
    "openai": call_openai,
    "anthropic": call_anthropic,
    "google": call_google,
    "deepseek": call_deepseek,
    "ollama": call_ollama,
    "mock": call_mock,
}


# ---------------------------------------------------------------------------
# Main generation loop
# ---------------------------------------------------------------------------

def load_scenarios() -> list[dict]:
    if not SCENARIOS_FILE.exists():
        sys.exit(f"ERROR: {SCENARIOS_FILE} not found. Are you running from the repo root?")
    scenarios = []
    with open(SCENARIOS_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                scenarios.append(json.loads(line))
    return scenarios


def run(model: str, provider: str, outfile: Path, delay: float = 0.5) -> None:
    call_fn = PROVIDER_FNS[provider]
    scenarios = load_scenarios()
    print(f"Loaded {len(scenarios)} scenarios.")
    print(f"Provider: {provider}  Model: {model}")
    print(f"Output:   {outfile}")
    if provider == "mock":
        print("Running in MOCK mode — no API calls will be made.")
    print()

    outfile.parent.mkdir(parents=True, exist_ok=True)
    successes = 0
    failures = 0

    with open(outfile, "w", encoding="utf-8") as out:
        for i, scenario in enumerate(scenarios, 1):
            sid = scenario["id"]
            prompt = scenario["user_prompt"]
            ts = datetime.now(timezone.utc).isoformat()
            try:
                response_text = call_fn(model, prompt)
                record = {
                    "scenario_id": sid,
                    "model": model,
                    "temperature": TEMPERATURE,
                    "system_prompt": TASK_FRAMING,
                    "user_prompt": prompt,
                    "response": response_text,
                    "error": None,
                    "timestamp": ts,
                }
                successes += 1
            except Exception as exc:
                record = {
                    "scenario_id": sid,
                    "model": model,
                    "temperature": TEMPERATURE,
                    "system_prompt": TASK_FRAMING,
                    "user_prompt": prompt,
                    "response": None,
                    "error": str(exc),
                    "timestamp": ts,
                }
                failures += 1
                print(f"  [WARN] {sid}: {exc}")
            out.write(json.dumps(record, ensure_ascii=False) + "\n")
            if i % 20 == 0:
                print(f"  {i}/{len(scenarios)} done  ({successes} OK, {failures} failed)")
            if provider not in ("mock", "ollama") and delay > 0:
                time.sleep(delay)

    print(f"\nDone. {successes} responses, {failures} failures.")
    print(f"Output: {outfile}")
    print()
    print("Next step — run analysis scripts (no API key needed):")
    print("  python code/headline_table.py")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate GDB responses for a new model.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--model",
        required=True,
        help="Model identifier (e.g. gpt-4o, claude-3-5-sonnet-20241022, llama3)",
    )
    parser.add_argument(
        "--provider",
        choices=["openai", "anthropic", "google", "deepseek", "ollama", "mock"],
        help=(
            "API provider. If omitted, guessed from --model name. "
            "Use 'mock' to test the pipeline without API access."
        ),
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Shorthand for --provider mock. Generates placeholder responses; "
             "no API key required. Use to verify the pipeline end-to-end.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help=(
            "Output JSONL file. Defaults to "
            "responses/responses_{model}_t0.7.jsonl"
        ),
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.5,
        help="Seconds between API calls (default 0.5). Increase for rate-limited APIs.",
    )
    return parser.parse_args()


def guess_provider(model: str) -> str:
    m = model.lower()
    if m.startswith("gpt") or "openai" in m:
        return "openai"
    if m.startswith("claude") or "anthropic" in m:
        return "anthropic"
    if m.startswith("gemini") or "google" in m:
        return "google"
    if m.startswith("deepseek"):
        return "deepseek"
    return "ollama"


def main() -> None:
    args = parse_args()

    if args.mock:
        args.provider = "mock"
    if args.provider is None:
        args.provider = guess_provider(args.model)
        print(f"Provider not specified; guessed: {args.provider}")

    safe_name = args.model.replace(":", "_").replace("/", "_").replace(" ", "_")
    outfile = args.output or (RESPONSES_DIR / f"responses_{safe_name}_t0.7.jsonl")

    run(
        model=args.model,
        provider=args.provider,
        outfile=outfile,
        delay=args.delay,
    )


if __name__ == "__main__":
    main()
