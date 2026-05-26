import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import AgglomerativeClustering
import matplotlib.pyplot as plt

# Load data
data_path = 'predictions.csv'
df = pd.read_csv(data_path)

# Feature scaling
X = df[['ARG', 'MGE', 'VF']]
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Hierarchical clustering
n_clusters = 3
clustering = AgglomerativeClustering(
    n_clusters=n_clusters,
    linkage='ward',
    metric='euclidean'
)

cluster_labels = clustering.fit_predict(X_scaled)
df['Cluster_Label'] = cluster_labels

# Save cluster results
output_path = 'cluster_results.csv'
df.to_csv(output_path, index=False)
print(f"Results saved to {output_path}")

# Plot using functional gene counts
X_plot = df[['ARG', 'MGE', 'VF']].values

fig = plt.figure(figsize=(9, 7))
ax = fig.add_subplot(111, projection='3d')

fig.patch.set_facecolor('white')
ax.set_facecolor('white')

sc = ax.scatter(
    X_plot[:, 0],
    X_plot[:, 1],
    X_plot[:, 2],
    c=cluster_labels,
    cmap='Set1',
    s=80,
    edgecolor='k',
    depthshade=False
)

# Plotting parameters
for axis in [ax.xaxis, ax.yaxis, ax.zaxis]:
    axis.pane.set_facecolor((1, 1, 1, 0))
    axis.pane.set_edgecolor('white')

ax.grid(True)
for axis in [ax.xaxis, ax.yaxis, ax.zaxis]:
    axis._axinfo["grid"]['color'] = (0, 0, 0, 0.25)
    axis._axinfo["grid"]['linewidth'] = 0.8

ax.set_xlabel("ARG")
ax.set_ylabel("MGE")
ax.set_zlabel("VF")

fig.colorbar(sc, label='Cluster Label')

plt.title('3D Scatter: ARG vs MGE vs VF')
plt.tight_layout()
plt.show()
