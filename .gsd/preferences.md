---
version: 1
models:
  research:
    # Long-context, high-quality research + retrieval
    model: moonshotai/kimi-k2.5
    fallbacks:
      - qwen/qwen3.5-397b-a17b

  planning:
    # Deep, careful reasoning for plans; V3 as fast/reliable backup
    model: deepseek/deepseek-r1-0528
    fallbacks:
      - moonshotai/kimi-k2.5
      - deepseek/deepseek-v3.2

  execution:
    # Primary coding workhorse, with high-success fallback ladder
    model: qwen/qwen3-coder
    fallbacks:
      - qwen/qwen3-coder-next
      - minimax/minimax-m2.5

  completion:
    # High-frequency summarization/UX completions; strong but not frontier overkill
    model: qwen/qwen3-next-80b-a3b-instruct
    fallbacks:
      - deepseek/deepseek-v3.2
      - qwen/qwen-plus-2025-07-28

---