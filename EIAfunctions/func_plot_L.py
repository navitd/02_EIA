import matplotlib.pyplot as plt

def plot_matrix_columns(matrix, sectors, sector_code_to_name, title):
    """
    Plots selected columns of a matrix as individual line plots.

    Parameters:
    - matrix: pd.DataFrame with labeled rows and columns.
    - sectors: list of sector codes (columns of the matrix) to plot.
    - sector_code_to_name: dict mapping sector code to descriptive name.
    - title: overall plot title.
    """
    n_sectors = len(sectors)
    nrows = (n_sectors + 1) // 2
    fig, axes = plt.subplots(nrows, 2, figsize=(14, 4 * nrows), sharey=True)
    axes = axes.flatten()

    x_labels = matrix.index.tolist()

    for i, sector in enumerate(sectors):
        ax = axes[i]
        if sector in matrix.columns:
            y = matrix[sector].reindex(x_labels)
            ax.plot(x_labels, y, marker='o')
            sector_name = sector_code_to_name.get(sector, 'Unknown')
            ax.set_title(f'{sector_name} ({sector})')
            ax.set_xlabel('Input Sector (rows)')
            ax.set_ylabel('Value')
            ax.tick_params(axis='x', rotation=90)
            ax.legend(fontsize='small')
            ax.grid(True) 
        else:
            ax.set_title(f'{sector} not found')
            ax.axis('off')

    # Hide unused subplots if any
    for j in range(i + 1, len(axes)):
        axes[j].axis('off')

    fig.suptitle(title, fontsize=16)
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.show()
