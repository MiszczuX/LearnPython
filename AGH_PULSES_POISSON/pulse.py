#!/usr/bin/env python3

###############################################################################
# The script generates the set of include files to provide current pulses with
# poissonian distribution for Virtuoso ADE-L / Spectre simulator.
#
# Python reimplementation of original Perl generator.
#
# Features:
# - Poisson distributed hits
# - PWL current source generation
# - Spectre include file generation
# - PNG visualization
# - Strictly monotonic timestamps for Spectre compatibility
#
###############################################################################

import re
import numpy as np
from pathlib import Path
from collections import defaultdict
import matplotlib.pyplot as plt

# =============================================================================
# USER VARIABLES
# =============================================================================

numberOfHits = 2000

chargePulseWidth = 1e-9

avgHitRate = [
    5e6,
    10e6,
    15e6,
    20e6,
    25e6,
    30e6,
    35e6,
    40e6,
    45e6,
    50e6,
    60e6,
    70e6,
    80e6,
    90e6,
    100e6,
    200e6,
    300e6,
    400e6
]

seed = 61

mainIncludeFileName = "vpoissonInclude.scs"

extraTranTime = 200e-9

tranOptions = (
    'errpreset=moderate '
    'write="spectre.ic" '
    'writefinal="spectre.fc" '
    'annotate=status '
    'maxiters=5'
)

# =============================================================================
# INTERNAL SETTINGS
# =============================================================================

precision = 100e-12

pulseWidthRaw = chargePulseWidth

slopeRaw = 10e-12

rangeRaw = int(1.0 / precision)

# IMPORTANT:
# keep as FLOATS
# identical behavior to Perl implementation

pulseWidth = pulseWidthRaw / precision

slope = slopeRaw / precision

# Minimal timestep increment
# needed for Spectre strictly increasing timestamps

epsilonTime = 1e-18

# =============================================================================
# RANDOM GENERATOR
# =============================================================================

rng = np.random.default_rng(seed)

# =============================================================================
# OUTPUT DIRECTORIES
# =============================================================================

base = Path("vpoisson_clean")

data_dir = base / "data"
png_dir = base / "png"

data_dir.mkdir(parents=True, exist_ok=True)
png_dir.mkdir(parents=True, exist_ok=True)

# =============================================================================
# STORAGE
# =============================================================================

hitRate2File = {}

tranTimeDict = {}

# =============================================================================
# IDEAL PULSE PLOT
# =============================================================================

ideal_time = [
    0,
    0,
    chargePulseWidth,
    chargePulseWidth,
    2 * chargePulseWidth
]

ideal_current = [
    0,
    1,
    1,
    0,
    0
]

plt.figure(figsize=(6, 3))

plt.plot(
    ideal_time,
    ideal_current
)

plt.title("Ideal Pulse Shape")

plt.xlabel("Time [s]")
plt.ylabel("Amplitude")

plt.grid(True)

plt.savefig(
    png_dir / "ideal_pulse.png",
    dpi=200
)

plt.close()

# =============================================================================
# MAIN LOOP
# =============================================================================

for hitRate in avgHitRate:

    # =========================================================================
    # TIME MODEL
    # =========================================================================

    hitRateTranTime = (
        numberOfHits
        / hitRate
        / precision
    )

    tranTimeDict[hitRate] = (
        numberOfHits / hitRate
        + extraTranTime
    )

    hitRateTimeScale = (
        hitRateTranTime
        / rangeRaw
    )

    # =========================================================================
    # GENERATE POISSON TIMES
    # =========================================================================

    randValues = rng.integers(
        0,
        rangeRaw,
        size=numberOfHits
    )

    hitTime = np.sort(
        hitRateTimeScale
        * randValues.astype(float)
    )

    # =========================================================================
    # CURRENT MODIFICATIONS
    # =========================================================================

    iMod = defaultdict(int)

    for t in hitTime:

        iMod[t] += 1

        iMod[t + pulseWidth] -= 1

    # =========================================================================
    # FILE NAME GENERATION
    # =========================================================================

    if hitRate >= 1e9:

        fileName = f"{hitRate/1e9:.2f}Gcps"

    elif hitRate >= 1e6:

        fileName = f"{hitRate/1e6:.2f}Mcps"

    elif hitRate >= 1e3:

        fileName = f"{hitRate/1e3:.2f}kcps"

    else:

        fileName = f"{hitRate:.2f}cps"

    if numberOfHits > 1e3:

        fileName += (
            f"_{numberOfHits/1e3:.2f}kHits"
        )

    else:

        fileName += (
            f"_{numberOfHits:.2f}Hits"
        )

    # identical regex behavior to Perl

    fileName = re.sub(
        r"\.?0+([GMkcH])",
        r"\1",
        fileName
    )

    # =========================================================================
    # DATA FILE
    # =========================================================================

    data_file = (
        data_dir
        / f"vpoisson_{fileName}.data"
    )

    abs_data_file = str(
        data_file.resolve()
    )

    hitRate2File[hitRate] = abs_data_file

    print(f"Writing: {abs_data_file}")

    # =========================================================================
    # WRITE PWL DATA FILE
    # =========================================================================

    iCurrent = 0
    iCurrentPrev = 0

    t_plot = []
    i_plot = []

    with open(data_file, "w") as f:

        last_time = -1.0

        for t in sorted(iMod.keys()):

            iCurrent += iMod[t]

            # -----------------------------------------------------------------
            # POINT BEFORE EDGE
            # -----------------------------------------------------------------

            t1 = t * precision

            # Force strictly increasing timestamps

            if t1 <= last_time:
                t1 = last_time + epsilonTime

            f.write(
                f"{t1:.16e} "
                f"{iCurrentPrev}*vps_amp\n"
            )

            t_plot.append(t1)
            i_plot.append(iCurrentPrev)

            last_time = t1

            # -----------------------------------------------------------------
            # POINT AFTER EDGE
            # -----------------------------------------------------------------

            t2 = (
                (t + slope)
                * precision
            )

            # Force strictly increasing timestamps

            if t2 <= last_time:
                t2 = last_time + epsilonTime

            f.write(
                f"{t2:.16e} "
                f"{iCurrent}*vps_amp\n"
            )

            t_plot.append(t2)
            i_plot.append(iCurrent)

            last_time = t2

            iCurrentPrev = iCurrent

    # =========================================================================
    # PNG PLOT
    # =========================================================================

    png_file = (
        png_dir
        / f"vpoisson_{fileName}.png"
    )

    plt.figure(figsize=(10, 4))

    plt.step(
        t_plot,
        i_plot,
        where="post"
    )

    plt.title(
        f"Poisson Pulse {fileName}"
    )

    plt.xlabel("Time [s]")
    plt.ylabel("Current")

    plt.grid(True)

    plt.savefig(
        png_file,
        dpi=200
    )

    plt.close()

# =============================================================================
# MAIN INCLUDE FILE
# =============================================================================

mainIncludeFile = (
    base
    / mainIncludeFileName
)

print(
    f"\nWriting MAIN INCLUDE FILE: {mainIncludeFile}"
)

with open(mainIncludeFile, "w") as f:

    # =========================================================================
    # PARAMETERS
    # =========================================================================

    f.write(
        "parameters "
        f"vps_time={pulseWidthRaw} "
        "vps_amp="
        "vps_charge_e*1.60217662e-19/"
        "vps_time\n\n"
    )

    # =========================================================================
    # CONDITIONAL BLOCKS
    # =========================================================================

    prefix = ""

    for hitRate in sorted(hitRate2File.keys()):

        f.write(
            f"{prefix}"
            f"if( vps_freq == {int(hitRate)} ) {{\n"
        )

        f.write(
            "IpoissonPulse "
            "(0 ipoissonIn) "
            "isource "
            "type=pwl "
            f'file="{hitRate2File[hitRate]}"\n'
        )

        f.write(
            "tran tran "
            f"stop={tranTimeDict[hitRate]:e} "
            f"{tranOptions}\n"
        )

        prefix = "} else "

    f.write("}\n")

# =============================================================================
# SUMMARY
# =============================================================================

print("\nDONE")
print(f"Generated DATA files : {data_dir}")
print(f"Generated PNG files  : {png_dir}")
print(f"Generated SCS file   : {mainIncludeFile}")