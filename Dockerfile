# GDB — Goal Displacement Benchmark
# Reproduces all paper analysis results without GPU or external API calls.
#
# Build:
#   docker build -t gdb .
#
# Run all six analysis scripts:
#   docker run --rm gdb
#
# Run a specific script:
#   docker run --rm gdb python code/headline_table.py
#
# Evaluate a new model (requires API key):
#   docker run --rm \
#     -e OPENAI_API_KEY=sk-... \
#     -v $(pwd)/responses:/gdb/responses \
#     gdb python code/generate_responses.py --model gpt-4o --provider openai

FROM python:3.12-slim

LABEL org.opencontainers.image.description="GDB: Goal Displacement Benchmark analysis environment"
LABEL org.opencontainers.image.licenses="CC-BY-4.0 (data), MIT (code)"

WORKDIR /gdb

# Install Python dependencies first (cached layer unless requirements change)
COPY requirements_locked.txt .
RUN pip install --no-cache-dir -r requirements_locked.txt

# Copy the full repository
COPY . .

# Verify the data files are present and scripts import cleanly
RUN python -c "import sys; sys.path.insert(0,'code'); from _paths import DATA; assert DATA.exists(), f'unified_dataset not found at {DATA}'; print('Data path OK:', DATA)"

# Default: run all six analysis scripts in order
CMD ["sh", "-c", "\
  echo '=== Table 4: per-model displacement ===' && python code/headline_table.py && \
  echo '' && echo '=== Table 3: reliability statistics ===' && python code/reliability.py && \
  echo '' && echo '=== Tier chi-squared and LRT ===' && python code/tier_test.py && \
  echo '' && echo '=== Arena Elo correlation ===' && python code/arena_correlation.py && \
  echo '' && echo '=== 2x2 discriminant probe ===' && python code/discriminant_2x2.py && \
  echo '' && echo '=== Post-training probe (probe1) ===' && python code/probe1_stages.py \
"]
