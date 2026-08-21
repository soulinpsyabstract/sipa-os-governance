#!/usr/bin/env bash
# Known-working launch for nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-NVFP4 via vLLM
# on a single L40S. This is the recipe from EXP-030 (2026-08-13) -- 10 failed attempts
# preceded this (6 in EXP-028 via transformers/unsloth/llama.cpp, 4 in EXP-030 via vLLM
# itself). Run this instead of re-deriving the flags from scratch.
#
# Two blockers below are NOT flags -- they must be fixed on the box BEFORE this script
# will get past model load. Run the fix commands once per fresh GPU instance.
set -euo pipefail

echo "=== Blocker 1/2: gcc/g++ version match (flashinfer JIT needs matching versions) ==="
if ! g++-12 --version >/dev/null 2>&1; then
  sudo apt-get update -qq
  sudo apt-get install -y g++-12
  sudo update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-12 100
fi
rm -rf /ephemeral/cache/flashinfer 2>/dev/null || true

echo "=== Blocker 2/2: flashinfer array.array[int] crash (invalid subscript at this Python version) ==="
FD_EXCHANGE="$(python3 -c 'import flashinfer.comm as m, os; print(os.path.dirname(m.__file__) + "/fd_exchange.py")' 2>/dev/null || true)"
if [ -n "$FD_EXCHANGE" ] && [ -f "$FD_EXCHANGE" ]; then
  if ! head -1 "$FD_EXCHANGE" | grep -q "from __future__ import annotations"; then
    sed -i '1i from __future__ import annotations' "$FD_EXCHANGE"
    echo "Patched: $FD_EXCHANGE"
  else
    echo "Already patched: $FD_EXCHANGE"
  fi
  python3 -c "import flashinfer.comm" && echo "Verified: import flashinfer.comm OK"
else
  echo "flashinfer.comm not found yet -- pip install vllm first, then re-run this script."
fi

echo "=== Launching vLLM ==="
vllm serve nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-NVFP4 \
  --moe-backend humming \
  --linear-backend humming \
  --quantization modelopt_fp4 \
  --mamba-backend flashinfer \
  --mamba-ssm-cache-dtype float16 \
  --mamba-cache-mode align \
  --mamba-ssu-algorithm simple \
  --enforce-eager \
  --max-model-len 8192

# Notes from EXP-030, not flags to change lightly:
# - --mamba-ssu-algorithm simple, NOT horizontal: `horizontal` is NVIDIA's own H100
#   (Hopper/SM90) recipe. L40S is Ada Lovelace (SM89) -- `horizontal` passes /health
#   but crashes the engine on the FIRST real generation request. Always verify with
#   a real curl to /v1/chat/completions after /health passes, not /health alone.
# - --enforce-eager is required to skip vLLM's compilation-pass import of
#   flashinfer.comm (a separate crash from the kernel_warmup one patched above --
#   two different import paths hit the same broken module).
# - max_tokens for actual requests: this is a reasoning model (visible <think> block).
#   EXP-030's max_tokens=800 left 24/30 rows truncated mid-reasoning, never reaching
#   a final answer. Use a substantially larger budget (or a system prompt that caps
#   reasoning length) before treating any output as a completed answer.
