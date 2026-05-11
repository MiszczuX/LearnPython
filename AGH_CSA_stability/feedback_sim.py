import numpy as np
import matplotlib.pyplot as plt
import itertools
import os

# =========================================================
# CZĘSTOTLIWOŚĆ
# =========================================================

f = np.logspace(3, 12, 5000)

omega = 2 * np.pi * f
s = 1j * omega

# =========================================================
# PARAMETRY DO SWEEPU
# Każdy parametr może mieć:
# - jedną wartość
# - wiele wartości
# =========================================================

params = {

    "RF":   [10e6],

    "CT":   [50e-15],

    "CF":   [1e-15, 2.4e-15, 5e-15],

    "GM1":  [1.4e-6, 5e-6],

    "GM3":  [2.5e-6],

    "GDS4": [20e-9],

    "CD":   [7.5e-15],

    "CX":   [117.5e-15]
}

# =========================================================
# PLOT
# =========================================================

plt.figure(figsize=(14, 8))

# =========================================================
# GENEROWANIE WSZYSTKICH KOMBINACJI
# =========================================================

keys = params.keys()

all_combinations = itertools.product(
    *(params[key] for key in keys)
)

# =========================================================
# PĘTLA PO KOMBINACJACH
# =========================================================

for values in all_combinations:

    p = dict(zip(keys, values))

    # ==========================================
    # PARAMETRY
    # ==========================================

    RF   = p["RF"]
    CT   = p["CT"]
    CF   = p["CF"]

    GM1  = p["GM1"]
    GM3  = p["GM3"]

    GDS4 = p["GDS4"]

    CD   = p["CD"]
    CX   = p["CX"]

    # ==========================================
    # PARAMETRY POCHODNE
    # ==========================================

    LX = 2 * CX / (GM1 * GM3)

    L  = 2 * CD / (GM1 * GM3)

    RL = 2 * GDS4 / (GM1 * GM3)

    R  = 2 / GM1

    # ==========================================
    # TRANSMITANCJA
    # ==========================================

    ZF = 1 / (
        (1 / R)
        + (s * CF)
        + (1 / (RL + s * L))
    )

    ZT = 1 / (s * CT)

    M = 1 + ZF / ZT

    # ==========================================
    # dB
    # ==========================================

    M_dB = 20 * np.log10(np.abs(M))

    # ==========================================
    # LABEL
    # ==========================================

    label = (
        f"CF={CF*1e15:.1f}fF | "
        f"GM1={GM1*1e6:.1f}uS | "
        f"CT={CT*1e15:.1f}fF"
    )

    # ==========================================
    # PLOT
    # ==========================================

    plt.semilogx(
        f,
        M_dB,
        linewidth=2,
        label=label
    )

# =========================================================
# CSV
# =========================================================

script_dir = os.path.dirname(os.path.abspath(__file__))

csv_files = [
    os.path.join(script_dir, "gain5u.csv")
]

for file in csv_files:

    if os.path.exists(file):

        data = np.loadtxt(
            file,
            delimiter=',',
            skiprows=1
        )

        f_csv = data[:, 0]
        y_csv = data[:, 1]

        plt.semilogx(
            f_csv,
            y_csv,
            linestyle='--',
            linewidth=3,
            label=os.path.basename(file)
        )

    else:
        print(f"Plik {file} nie istnieje!")

# =========================================================
# OPIS
# =========================================================

plt.xlabel("Frequency [Hz]", fontsize=12)

plt.ylabel("|H(jω)| [dB]", fontsize=12)

plt.title(
    "Parametric sweep",
    fontsize=14
)

plt.grid(
    True,
    which='both',
    linestyle='--',
    alpha=0.7
)

plt.legend(fontsize=8)

plt.xlim(1e3, 1e11)

plt.ylim(-20, 50)

plt.tight_layout()

plt.show()