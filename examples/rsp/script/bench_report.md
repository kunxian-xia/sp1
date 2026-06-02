# RSP Benchmark Report

**Date:** 2026-06-02
**SP1 Version:** v6.2.1
**Proof Mode:** Core (GPU/CUDA)
**Hardware:** RTX 3090

## Results

| Metric | Block 21740137 | Block 21740164 |
|--------|---------------|----------------|
| Cycles | 594,565,681 | 295,162,512 |
| Execution Time | 8.75s | 5.26s |
| Core Prove Time (GPU) | ~216s | ~109s |
| Block Hash | `0xb3366f..695b90` | `0x27947d..dfd62` |

## Precompile Usage (Block 21740137)

| Precompile | Invocations |
|------------|-------------|
| KECCAK_PERMUTE | 88,559 |
| SECP256K1_ADD | 105,732 |
| SECP256K1_DOUBLE | 211,968 |
| SHA_EXTEND | 1 |
| SHA_COMPRESS | 1 |

## How to Reproduce

```bash
cd examples/rsp/script
BLOCK_NUMBER=21740137 ./bench.sh
BLOCK_NUMBER=21740164 ./bench.sh
```
