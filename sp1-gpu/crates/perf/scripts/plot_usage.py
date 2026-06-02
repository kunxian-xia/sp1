#!/usr/bin/env python3
"""Plot CPU and GPU usage from monitor.sh CSV logs."""

import argparse
import csv
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker


def read_csv(path):
    with open(path) as f:
        reader = csv.DictReader(f)
        rows = [row for row in reader]
    return rows


def plot(gpu_path, cpu_path, output):
    gpu_rows = read_csv(gpu_path)
    cpu_rows = read_csv(cpu_path)

    if not gpu_rows or not cpu_rows:
        print("Error: empty CSV file(s)", file=sys.stderr)
        sys.exit(1)

    # Use the earlier start time as t=0
    t0 = min(float(gpu_rows[0]["timestamp"]), float(cpu_rows[0]["timestamp"]))

    gpu_t = [float(r["timestamp"]) - t0 for r in gpu_rows]
    gpu_util = [float(r["gpu_util_%"]) for r in gpu_rows]
    gpu_mem = [float(r["mem_used_MiB"]) for r in gpu_rows]
    gpu_power = [float(r["power_W"]) for r in gpu_rows]
    gpu_temp = [float(r["temp_C"]) for r in gpu_rows]

    cpu_t = [float(r["timestamp"]) - t0 for r in cpu_rows]
    cpu_overall = [float(r["cpu_overall_%"]) for r in cpu_rows]

    ncpu = sum(1 for k in cpu_rows[0] if k.startswith("cpu") and k != "cpu_overall_%")

    fig, axes = plt.subplots(4, 1, figsize=(14, 12), sharex=True)
    fig.suptitle("SP1 GPU Perf — Resource Usage", fontsize=14, fontweight="bold")

    # 1) GPU + CPU utilization
    ax = axes[0]
    ax.plot(gpu_t, gpu_util, color="tab:red", linewidth=1.5, label="GPU Util %")
    ax.plot(cpu_t, cpu_overall, color="tab:blue", linewidth=1.5, label="CPU Overall %")
    ax.set_ylabel("Utilization (%)")
    ax.set_ylim(-5, 105)
    ax.legend(loc="upper right")
    ax.grid(True, alpha=0.3)

    # 2) GPU memory
    ax = axes[1]
    gpu_total = float(gpu_rows[0]["mem_total_MiB"])
    ax.plot(gpu_t, gpu_mem, color="tab:orange", linewidth=1.5)
    ax.axhline(gpu_total, color="tab:orange", linestyle="--", alpha=0.5, label=f"Total {gpu_total:.0f} MiB")
    ax.set_ylabel("GPU Memory (MiB)")
    ax.set_ylim(0, gpu_total * 1.1)
    ax.legend(loc="upper right")
    ax.grid(True, alpha=0.3)

    # 3) GPU power + temperature
    ax = axes[2]
    ax.plot(gpu_t, gpu_power, color="tab:green", linewidth=1.5, label="Power (W)")
    ax.set_ylabel("Power (W)")
    ax.grid(True, alpha=0.3)
    ax2 = ax.twinx()
    ax2.plot(gpu_t, gpu_temp, color="tab:purple", linewidth=1.2, linestyle="--", label="Temp (°C)")
    ax2.set_ylabel("Temperature (°C)")
    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, loc="upper right")

    # 4) Per-core CPU heatmap
    ax = axes[3]
    per_core = []
    for r in cpu_rows:
        core_vals = [float(r[f"cpu{i}_%"]) for i in range(ncpu)]
        per_core.append(core_vals)
    if per_core:
        im = ax.imshow(
            list(zip(*per_core)),
            aspect="auto",
            cmap="YlOrRd",
            vmin=0,
            vmax=100,
            extent=[cpu_t[0], cpu_t[-1], ncpu - 0.5, -0.5],
            interpolation="nearest",
        )
        cbar = fig.colorbar(im, ax=ax, label="Usage %", pad=0.01)
        ax.set_ylabel("CPU Core")
        ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))

    axes[-1].set_xlabel("Time (s)")

    plt.tight_layout()
    plt.savefig(output, dpi=150, bbox_inches="tight")
    print(f"Saved plot to {output}")


def main():
    parser = argparse.ArgumentParser(description="Plot CPU/GPU usage from monitor.sh logs")
    parser.add_argument("--gpu", default="gpu_usage.csv", help="Path to gpu_usage.csv")
    parser.add_argument("--cpu", default="cpu_usage.csv", help="Path to cpu_usage.csv")
    parser.add_argument("-o", "--output", default="usage_plot.png", help="Output image path")
    args = parser.parse_args()

    plot(args.gpu, args.cpu, args.output)


if __name__ == "__main__":
    main()
