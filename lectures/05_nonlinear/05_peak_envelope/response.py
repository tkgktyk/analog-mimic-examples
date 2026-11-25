# SPDX-License-Identifier: MIT
"""Peak hold and envelope follower in time: a sine whose amplitude falls from 1 to 0.5
after 4 periods; the peak hold keeps 1, the envelope follower (decay time 1 period)
comes down with ripple."""
import sys
import pathlib

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools"))
from figures import save  # noqa: E402

t = np.linspace(0, 10, 4001)            # time in periods
amp = np.where(t < 4, 1.0, 0.5)
x = amp * np.sin(2 * np.pi * t)
dt = t[1] - t[0]
hold, env = np.empty_like(t), np.empty_like(t)
h = e = 0.0
for n, v in enumerate(np.maximum(x, 0)):
    h = max(h, v)
    e = v if v > e else e * np.exp(-dt / 1.0)
    hold[n], env[n] = h, e
fig, ax = plt.subplots(figsize=(6.5, 3.2))
ax.plot(t, x, color="gray", lw=1, label="input")
ax.plot(t, hold, lw=2, label="peak hold")
ax.plot(t, env, lw=2, label="envelope (decay 1 period)")
ax.axhline(0, color="gray", ls=":", lw=1)
ax.set_xlim(0, 10)
ax.set_ylim(-1.15, 1.35)
ax.set_xlabel("Time [periods]")
ax.set_ylabel("Input / output - Vref")
ax.legend(loc="upper right", fontsize=9, ncol=3)
fig.tight_layout()
save(fig, pathlib.Path(__file__).with_name("response.svg"))
