import asyncio
import os
import statistics
import time
from typing import Dict, List, Optional

from backend.config import settings
from backend.providers.llm.gemini_provider import GeminiProvider


def _summary(latencies: List[float]) -> Dict[str, float]:
    ordered = sorted(latencies)
    p95_index = max(0, min(len(ordered) - 1, int(round(0.95 * (len(ordered) - 1)))))
    return {
        "runs": float(len(ordered)),
        "avg_s": statistics.mean(ordered),
        "median_s": statistics.median(ordered),
        "p95_s": ordered[p95_index],
        "min_s": ordered[0],
        "max_s": ordered[-1],
    }


async def _bench_model(
    model_name: str,
    prompt: str,
    runs: int,
    warmup: int,
    temperature: float,
    max_tokens: int,
) -> Dict[str, object]:
    provider = GeminiProvider(model_name=model_name)

    for i in range(warmup):
        _ = await provider.generate_text(
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        print(f"[{model_name}] warmup {i + 1}/{warmup} done")

    latencies: List[float] = []
    output_lengths: List[int] = []

    for i in range(runs):
        start = time.perf_counter()
        text = await provider.generate_text(
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        elapsed = time.perf_counter() - start
        latencies.append(elapsed)
        output_lengths.append(len((text or "").strip()))
        print(
            f"[{model_name}] run {i + 1}/{runs}: {elapsed:.3f}s | chars={output_lengths[-1]}"
        )

    return {
        "model": model_name,
        "latencies": latencies,
        "summary": _summary(latencies),
        "avg_output_chars": statistics.mean(output_lengths) if output_lengths else 0,
    }


async def main() -> None:
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY is empty in environment. Cannot run benchmark.")

    gemma_model = os.getenv("BENCH_GEMMA_MODEL", "gemma-4-26b-a4b-it")
    flash_model = os.getenv("BENCH_FLASH_MODEL", "gemini-2.5-flash")

    runs = int(os.getenv("BENCH_RUNS", "5"))
    warmup = int(os.getenv("BENCH_WARMUP", "1"))
    temperature = float(os.getenv("BENCH_TEMPERATURE", "0.2"))
    max_tokens = int(os.getenv("BENCH_MAX_TOKENS", "220"))

    prompt = os.getenv("BENCH_PROMPT") or (
        "Write a concise 3-bullet summary of how retrieval augmented generation works, "
        "then add a one-sentence practical caveat."
    )

    print("Benchmark configuration")
    print(f"gemma_model={gemma_model}")
    print(f"flash_model={flash_model}")
    print(f"runs={runs}, warmup={warmup}, temperature={temperature}, max_tokens={max_tokens}")
    print(f"prompt_chars={len(prompt)}")
    print("-" * 70)

    results: List[Dict[str, object]] = []
    errors: Dict[str, str] = {}

    for model in (gemma_model, flash_model):
        try:
            result = await _bench_model(
                model_name=model,
                prompt=prompt,
                runs=runs,
                warmup=warmup,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            results.append(result)
        except Exception as exc:
            errors[model] = str(exc)
            print(f"[{model}] ERROR: {exc}")

    print("-" * 70)

    for result in results:
        model = result["model"]
        summary = result["summary"]
        print(f"Summary for {model}:")
        print(
            "  avg={avg:.3f}s median={med:.3f}s p95={p95:.3f}s min={minv:.3f}s max={maxv:.3f}s avg_chars={chars:.1f}".format(
                avg=summary["avg_s"],
                med=summary["median_s"],
                p95=summary["p95_s"],
                minv=summary["min_s"],
                maxv=summary["max_s"],
                chars=float(result["avg_output_chars"]),
            )
        )

    if len(results) == 2:
        a = results[0]
        b = results[1]
        a_avg = float(a["summary"]["avg_s"])
        b_avg = float(b["summary"]["avg_s"])
        faster = a if a_avg < b_avg else b
        slower = b if a_avg < b_avg else a
        delta = abs(a_avg - b_avg)
        ratio = (float(slower["summary"]["avg_s"]) / float(faster["summary"]["avg_s"])) if float(faster["summary"]["avg_s"]) > 0 else float("inf")

        print("-" * 70)
        print(
            "Faster model by average latency: {fast} ({fast_avg:.3f}s) vs {slow} ({slow_avg:.3f}s)".format(
                fast=faster["model"],
                fast_avg=float(faster["summary"]["avg_s"]),
                slow=slower["model"],
                slow_avg=float(slower["summary"]["avg_s"]),
            )
        )
        print(f"Absolute delta: {delta:.3f}s | Speed ratio: {ratio:.2f}x")

    if errors:
        print("-" * 70)
        print("Errors:")
        for model, message in errors.items():
            print(f"  {model}: {message}")


if __name__ == "__main__":
    asyncio.run(main())
