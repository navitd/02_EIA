#import pandas as pd
#import numpy as np
import matplotlib.pyplot as plt


def plot_real_vs_predicted(output_real, output_pred, 
                           income_real, income_pred, 
                           gdp_real, gdp_pred, 
                           year1, year2, title):
    fig, axes = plt.subplots(3, 1, figsize=(6,8), sharex=True)
    
    fig.suptitle(title, fontsize=16)

    # Panel 1: Output
    axes[0].plot(output_real.index, output_real, label='Real Output', color='purple', marker='o')
    axes[0].plot(output_pred.index, output_pred, label='Predicted Output', color='red', marker='o')
    axes[0].set_title(f'Output {year2} Based on {year1}')
    axes[0].set_xlabel('Sectors')
    axes[0].set_ylabel('Million USD')
    axes[0].legend()

    # Panel 2: Income
    axes[1].plot(income_real.index, income_real, label='Real Income', color='purple', marker='o')
    axes[1].plot(income_pred.index, income_pred, label='Predicted Income', color='red', marker='o')
    axes[1].set_title(f'Income {year2} Based on {year1}')
    axes[1].set_xlabel('Sectors')
    axes[1].set_ylabel('Million USD')
    axes[1].legend()

    # Panel 3: GDP
    axes[2].plot(gdp_real.index, gdp_real, label='Real GDP', color='purple', marker='o')
    axes[2].plot(gdp_pred.index, gdp_pred, label='Predicted GDP', color='red', marker='o')
    axes[2].set_title(f'GDP {year2} Based on {year1}')
    axes[2].set_xlabel('Sectors')
    axes[2].set_ylabel('Million USD')
    axes[2].legend()
    for ax in axes:
        ax.tick_params(axis='x', rotation=45)
        ax.grid(True)

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.show()