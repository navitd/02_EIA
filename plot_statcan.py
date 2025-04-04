import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('TkAgg')  # Use TkAgg backend for interactive plotting
import matplotlib.pyplot as plt
import traceback
import time

# ...existing code...

# Replace the plotting section with:
plt.figure(figsize=(10, 6))

# Group by Transaction and plot each group
for transaction, group in df2.groupby("Transaction"):
    plt.plot(group["TIME_PERIOD"], group["OBS_VALUE"], label=transaction)

# Formatting
plt.xlabel("TIME_PERIOD")
plt.ylabel("OBS_VALUE")
plt.title("OBS_VALUE vs. TIME_PERIOD grouped by Transaction")
plt.legend(title="Transaction", bbox_to_anchor=(1.05, 1), loc='upper left')
plt.xticks(rotation=45)
plt.grid(True)

# Show plot interactively
plt.tight_layout()
plt.show()