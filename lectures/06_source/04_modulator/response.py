# SPDX-License-Identifier: MIT
"""AM (m = 0.5) and ring (DSB) modulation in time with the envelope (left, middle), and
their spectra (right): the carrier fc with the sidebands fc - fm and fc + fm."""
import sys
import pathlib

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools"))
from figures import save  # noqa: E402

t = np.linspace(0, 2, 8001)            # time in periods of the signal
fc = 12                                 # carrier periods per signal period
sig = np.sin(2 * np.pi * t)
car = np.sin(2 * np.pi * fc * t)
fig, axes = plt.subplots(1, 3, figsize=(11, 3.0), gridspec_kw=dict(width_ratios=[1, 1, 0.8]))
for ax, (title, env) in zip(axes, (("AM, m = 0.5", 1 + 0.5 * sig), ("Ring (DSB)", sig))):
    ax.plot(t, env * car, lw=1)
    ax.plot(t, env, color="C3", lw=1.5, ls="--", label="envelope")
    ax.plot(t, -env, color="C3", lw=1.5, ls="--")
    ax.set_title(title)
    ax.set_xlim(0, 2)
    ax.set_ylim(-1.7, 1.9)
    ax.set_xlabel("Time [signal periods]")
    ax.legend(loc="upper right", fontsize=8)
axes[0].set_ylabel("Output - Vref")
ax = axes[2]
ax.stem([-1, 0, 1], [0.25, 1, 0.25], linefmt="C0-", markerfmt="C0o", basefmt=" ", label="AM")
ax.stem([-0.9, 1.1], [0.5, 0.5], linefmt="C1--", markerfmt="C1s", basefmt=" ", label="ring")
ax.set_xticks([-1, 0, 1], ["fc - fm", "fc", "fc + fm"])
ax.set_xlim(-2, 2)
ax.set_ylim(0, 1.2)
ax.set_yticks([])
ax.set_title("Spectrum")
ax.legend(loc="upper right", fontsize=8)
fig.tight_layout()
save(fig, pathlib.Path(__file__).with_name("response.svg"))
