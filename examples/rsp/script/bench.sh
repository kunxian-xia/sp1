#!/usr/bin/env bash
set -euo pipefail

BLOCK_NUMBER="${BLOCK_NUMBER:?BLOCK_NUMBER env var must be set}"
export BLOCK_NUMBER

echo "=== RSP Benchmark for block $BLOCK_NUMBER ==="

echo ""
echo "--- Step 1: Execute (get cycle count) ---"
SP1_PROVER=cuda RUST_LOG=info cargo run --release --bin rsp-script --features "cuda"

echo ""
echo "--- Step 2: GPU Core Prove ---"
SP1_PROVER=cuda RUST_LOG=debug cargo run --release --bin core_u64 --features "cuda"
