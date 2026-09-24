import os
import joblib
import numpy as np
import pandas as pd
from scipy.stats import chi2
from scipy.spatial.distance import cdist
import warnings

warnings.filterwarnings('ignore')

# 1. Paths and configuration (specify the prediction file to be evaluated)
train_data_path = 'ML_table5.txt'
feature_cols_path = 'Training_Feature_Columns.joblib'
predict_file_path = 'predict_factor.csv'  # Replace with your actual prediction file
output_evaluation_path = 'Single_Time2022_Mahalanobis_Mask.csv'  # Output file

print(">>> Starting Nature-standard AOA assessment using Mahalanobis distance for a single time point <<<")

# 2. Load data and extract environmental predictors only
df_train = pd.read_csv(train_data_path, sep='\t')
df_pred = pd.read_csv(predict_file_path)
target_features = joblib.load(feature_cols_path)

# Remove technical variables and retain only environmental predictors
tech_factors = ['size_group', 'depth_group', 'PLATFORM']
env_features = [f for f in target_features if f not in tech_factors]

X_train_env = df_train[env_features].values
X_pred_env = df_pred[env_features].values

# 3. Calculate Mahalanobis distance parameters and the 90% chi-square threshold
# Calculate the centroid of the training environmental space
centroid = np.mean(X_train_env, axis=0)

# Calculate covariance matrix and its pseudo-inverse
# Pseudo-inverse is used to avoid errors caused by singular matrices
cov_matrix = np.cov(X_train_env, rowvar=False)
inv_cov_matrix = np.linalg.pinv(cov_matrix)

# The squared Mahalanobis distance follows a chi-square distribution
# with degrees of freedom equal to the number of variables
df_degrees = len(env_features)
chi2_threshold_sq = chi2.ppf(0.90, df_degrees)
mahalanobis_threshold = np.sqrt(chi2_threshold_sq)

print(f"\n[Step 1] Defining the 90% chi-square boundary:")
print(f"    - Degrees of freedom: {df_degrees}")
print(f"    - Mahalanobis distance threshold (90% chi-square): {mahalanobis_threshold:.4f}")

# 4. Calculate Mahalanobis distance and classify prediction validity
print("\n[Step 2] Calculating Mahalanobis distance for all lakes...")

# Efficient distance calculation
dists = cdist(
    X_pred_env,
    [centroid],
    metric='mahalanobis',
    VI=inv_cov_matrix
).flatten()

# Classification:
# <= threshold → 1 (within AOA / valid prediction)
# > threshold  → 0 (outside AOA / environmental extrapolation)
is_valid = (dists <= mahalanobis_threshold).astype(int)

# Export results including Mahalanobis distance and validity flag
df_result = pd.DataFrame({
    'Hylak_id': df_pred['Hylak_id'],
    'Mahalanobis_Distance': dists,
    'Is_Valid': is_valid
})

df_result.to_csv(output_evaluation_path, index=False)

# 5. Summary statistics and output
total_lakes = len(df_result)
valid_lakes = is_valid.sum()
outlier_ratio = (1 - valid_lakes / total_lakes) * 100

print(f"\n==================================================")
print(f"AOA assessment completed!")
print(f"-> Total lakes evaluated: {total_lakes}")
print(f"-> Lakes within AOA (Is_Valid = 1): {valid_lakes}")
print(f"-> Lakes outside AOA (%): {outlier_ratio:.2f}%")
print(f"-> Results saved to: {output_evaluation_path}")
print(f"==================================================")