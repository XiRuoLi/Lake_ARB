import os
import pandas as pd
import matplotlib.pyplot as plt
import geopandas as gpd
from matplotlib.colors import LinearSegmentedColormap, LogNorm
import numpy as np

# 1. Parameter settings
input_file = r"Summary_Table3_Annual_Matrix_ARB_abundance.csv"
output_folder = r"map_predict"
shp_file = r"ne_110m_admin_0_countries.shp"

years = ["2022"]
point_size = 2
fig_width = 16
fig_height = 8
dpi = 300

os.makedirs(output_folder, exist_ok=True)

# 2. Load data
df_all = pd.read_csv(input_file)

required_cols = ["lat", "long"] + years
for col in required_cols:
    if col not in df_all.columns:
        raise ValueError(f"Missing required columns: {col}")

# 3. Calculate unified color scale range (across years)
global_min = np.inf
global_max = -np.inf

for year in years:
    values = df_all[year]
    positive_values = values[values > 0]

    if len(positive_values) == 0:
        continue
    global_min = min(global_min, positive_values.min())
    global_max = max(global_max, positive_values.max())

if not np.isfinite(global_min):
    raise ValueError("No valid positive data available")

print(f"Unified color scale range: vmin={global_min:.6f}, vmax={global_max:.6f}")

# 4. Load map
world = gpd.read_file(shp_file)
world = world[world.geometry.notnull()].copy()
world = world.explode(index_parts=False)

# 5. Customize colors
colors = ["#2558a0", "#fae5a9", "#ca3423"]
custom_cmap = LinearSegmentedColormap.from_list("blue_yellow_red", colors)

# 6. Latitude and longitude label function
def format_lon(x):
    if x == 0:
        return "0°"
    return f"{abs(int(x))}°{'E' if x > 0 else 'W'}"

def format_lat(y):
    if y == 0:
        return "0°"
    return f"{abs(int(y))}°{'N' if y > 0 else 'S'}"

# 7. Plot
for year in years:
    print(f"\nGenerating plot: {year}")

    df = df_all[["lat", "long", year]].copy()
    df = df.dropna()
    df = df[df[year] > 0]

    if len(df) == 0:
        print(f" {year} No valid data available")
        continue

    fig, ax = plt.subplots(figsize=(fig_width, fig_height))

    fig.patch.set_alpha(0)
    ax.set_facecolor("none")

    world.boundary.plot(ax=ax, color="#5b5b5b", linewidth=0.8, zorder=3)

    sc = ax.scatter(
        df["long"],
        df["lat"],
        c=df[year],
        cmap=custom_cmap,
        norm=LogNorm(vmin=global_min, vmax=global_max),
        s=point_size,
        alpha=0.9,
        linewidths=0,
        zorder=2
    )

    ax.set_xlim(-180, 180)
    ax.set_ylim(-60, 90)

    xticks = np.arange(-180, 181, 90)
    yticks = np.arange(-60, 91, 30)

    ax.set_xticks(xticks)
    ax.set_yticks(yticks)
    ax.set_xticklabels([format_lon(x) for x in xticks], fontsize=10)
    ax.set_yticklabels([format_lat(y) for y in yticks], fontsize=10)
    ax.grid(True, linestyle='-', linewidth=0.6, alpha=0.6, zorder=1)

    for spine in ax.spines.values():
        spine.set_visible(False)

    ax.set_title(year, fontsize=20, fontweight="bold", pad=20)

    cbar = plt.colorbar(sc, ax=ax, fraction=0.03, pad=0.02)
    cbar.set_label(year, fontsize=12)
    cbar.ax.tick_params(labelsize=10)
    cbar.outline.set_visible(False)

    # 8. Output
    output_file = os.path.join(output_folder, f"{year}_map.pdf")

    plt.tight_layout()
    plt.savefig(output_file, dpi=dpi, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close(fig)

    print(f"save: {output_file}")

print("\nCompleted successfully")