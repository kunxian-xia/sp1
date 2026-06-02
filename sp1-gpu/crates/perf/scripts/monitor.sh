#!/usr/bin/env bash
set -euo pipefail

INTERVAL=${MONITOR_INTERVAL:-1}
OUTPUT_DIR=${MONITOR_OUTPUT_DIR:-.}
GPU_LOG="$OUTPUT_DIR/gpu_usage.csv"
CPU_LOG="$OUTPUT_DIR/cpu_usage.csv"

mkdir -p "$OUTPUT_DIR"

# GPU monitor: utilization, memory, power, temperature
monitor_gpu() {
    echo "timestamp,gpu_util_%,mem_util_%,mem_used_MiB,mem_total_MiB,power_W,temp_C" > "$GPU_LOG"
    while true; do
        nvidia-smi --query-gpu=utilization.gpu,utilization.memory,memory.used,memory.total,power.draw,temperature.gpu \
            --format=csv,noheader,nounits 2>/dev/null | while IFS= read -r line; do
            echo "$(date +%s.%N),$line" >> "$GPU_LOG"
        done
        sleep "$INTERVAL"
    done
}

# CPU monitor: per-core utilization from /proc/stat
monitor_cpu() {
    local ncpu
    ncpu=$(nproc)
    # header
    header="timestamp,cpu_overall_%"
    for ((i=0; i<ncpu; i++)); do
        header+=",cpu${i}_%"
    done
    echo "$header" > "$CPU_LOG"

    # read initial snapshot
    declare -A prev_idle prev_total
    while IFS=' ' read -r cpu user nice system idle iowait irq softirq steal _ _; do
        if [[ "$cpu" =~ ^cpu ]]; then
            local total=$((user + nice + system + idle + iowait + irq + softirq + steal))
            prev_idle[$cpu]=$idle
            prev_total[$cpu]=$total
        fi
    done < /proc/stat

    while true; do
        sleep "$INTERVAL"
        local line
        line="$(date +%s.%N)"
        while IFS=' ' read -r cpu user nice system idle iowait irq softirq steal _ _; do
            if [[ "$cpu" =~ ^cpu ]]; then
                local total=$((user + nice + system + idle + iowait + irq + softirq + steal))
                local d_total=$((total - ${prev_total[$cpu]}))
                local d_idle=$((idle - ${prev_idle[$cpu]}))
                local usage=0
                if ((d_total > 0)); then
                    usage=$(awk "BEGIN {printf \"%.1f\", ($d_total - $d_idle) * 100.0 / $d_total}")
                fi
                line+=",$usage"
                prev_idle[$cpu]=$idle
                prev_total[$cpu]=$total
            fi
        done < /proc/stat
        echo "$line" >> "$CPU_LOG"
    done
}

cleanup() {
    kill "$GPU_PID" "$CPU_PID" 2>/dev/null || true
    wait "$GPU_PID" "$CPU_PID" 2>/dev/null || true
    echo ""
    echo "=== Monitoring stopped ==="
    echo "GPU log: $GPU_LOG ($(wc -l < "$GPU_LOG") samples)"
    echo "CPU log: $CPU_LOG ($(wc -l < "$CPU_LOG") samples)"
}

echo "=== Starting monitors (interval=${INTERVAL}s, output=$OUTPUT_DIR) ==="

monitor_gpu &
GPU_PID=$!
monitor_cpu &
CPU_PID=$!

trap cleanup EXIT

# Run the benchmark command (all remaining args)
echo "=== Running: $* ==="
"$@"
EXIT_CODE=$?

echo "=== Benchmark exited with code $EXIT_CODE ==="
exit $EXIT_CODE
