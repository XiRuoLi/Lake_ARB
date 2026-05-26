import os
import glob
import joblib
import numpy as np
import pandas as pd
import re
from sklearn.utils import resample
from joblib import Parallel, delayed
from sklearn.preprocessing import OrdinalEncoder
from sklearn.base import clone
import argparse
import sys
import warnings

# 0. Define the batch prediction and uncertainty estimation function for a single table
# If no valid lakes are available for this month, save an empty table and skip processing
def predict_and_evaluate(file_path, output_dir, target_col, target_features, expert_committee, n_bootstraps):
    file_name = os.path.basename(file_path)
    df_pred = pd.read_csv(file_path)

    if len(df_pred) == 0:
        df_empty = pd.DataFrame(columns=['Hylak', f'{target_col}_Mean', f'{target_col}_Uncertainty_IQR', f'{target_col}_Relative_IQR'])
        df_empty.to_csv(os.path.join(output_dir, file_name), index=False)
        return file_name
    
    # Extract features for prediction
    X_pred = df_pred[target_features].values
    
    # Generate predictions for all lakes using the bootstrap ensemble
    predictions_matrix = np.zeros((len(df_pred), n_bootstraps))

    for i, expert in enumerate(expert_committee):
        predictions_matrix[:, i] = expert.predict(X_pred)
    
    # Calculate prediction mean and IQR from the valid prediction matrix
    df_pred[f'{target_col}_Mean'] = np.mean(predictions_matrix, axis=1)
    q75 = np.percentile(predictions_matrix, 75, axis=1)
    q25 = np.percentile(predictions_matrix, 25, axis=1)
    df_pred[f'{target_col}_Uncertainty_IQR'] = q75 - q25
    
    # Calculate relative IQR
    df_pred[f'{target_col}_Relative_IQR'] = df_pred[f'{target_col}_Uncertainty_IQR'] / df_pred[f'{target_col}_Mean'].replace({0: np.nan})

    cols_to_keep = ['Hylak', f'{target_col}_Mean', f'{target_col}_Uncertainty_IQR', f'{target_col}_Relative_IQR']
    df_slim = df_pred[cols_to_keep]

    out_path = os.path.join(output_dir, file_name)
    df_slim.to_csv(out_path, index=False)
    
    return file_name


def main():
# 1. Configure command-line arguments
    parser = argparse.ArgumentParser(description="Bootstrap-based prediction and automatic aggregation framework")

    class Args:
        pass

    args = Args()

    args.train_data = r"ML_table.xlsx"
    args.base_model = r"XGBoost_best_model.pkl"
    args.feature_cols = r"Training_Feature_Columns.joblib"
    args.input_dir = r"Factor_data"
    args.output_dir = r"predict_output"
    args.target_col = "ARB_abundance"

    N_BOOTSTRAPS = 99
    N_JOBS = 32
    
    # Directory configuration
    output_dir = args.output_dir
    results_dir = os.path.join(output_dir, 'results')
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(results_dir, exist_ok=True)

    print(f"Launching the 99-bootstrap prediction and automatic aggregation framework ({args.target_col})")


# 2. Load the base model and original training data
    print("\n Loading and globally encoding the original training dataset...")
    df_train = pd.read_excel(args.train_data)
    target_features = joblib.load(args.feature_cols)

    encoder_country = OrdinalEncoder(categories='auto')
    df_train[['country']] = encoder_country.fit_transform(df_train[['country']])

    # Extract target features (X) and target variable (y)
    X_train = df_train[target_features].values
    y_train = df_train[args.target_col].values

    base_model = joblib.load(args.base_model)
    model_type = type(base_model).__name__


# 3. Train 99 bootstrap expert models
    print(f"\n Performing {N_BOOTSTRAPS} bootstrap resamplings to build the ensemble committee...")
    expert_committee = []

    for i in range(N_BOOTSTRAPS):
        if (i+1) % 20 == 0:
            print(f"    - Trained {i+1}/{N_BOOTSTRAPS} bootstrap models...")

        X_res, y_res = resample(X_train, y_train, random_state=i)

        clone_model = clone(base_model)
        clone_model.fit(X_res, y_res)
        
        expert_committee.append(clone_model)


# 4. Perform parallel prediction across all input tables
    input_files = glob.glob(os.path.join(args.input_dir, '*.csv'))
    
    if not input_files:
        print(f"Error: No CSV files were found in {args.input_dir} ")
        sys.exit(1)

    Parallel(n_jobs=N_JOBS, verbose=10)(
        delayed(predict_and_evaluate)(
            f, output_dir, args.target_col, target_features, expert_committee, N_BOOTSTRAPS
        ) for f in input_files
    )


# 5. Post-processing: generate three summary tables
    print("\n Prediction completed. Generating the summary tables")

    output_files = glob.glob(os.path.join(output_dir, '*.csv'))
    all_months_data = []

    for f in output_files:
        df_temp = pd.read_csv(f)
        if len(df_temp) > 0:
            year_match = re.search(r'\d{4}', os.path.basename(f))
            if year_match:
                df_temp['Year'] = year_match.group()
                all_months_data.append(df_temp)

    df_master = pd.concat(all_months_data, ignore_index=True)

    # Table 1
    print("    Generating [Table 1] global mean relative uncertainty table")
    df_rel_iqr = df_master.groupby('Hylak')[f'{args.target_col}_Relative_IQR'].mean().reset_index()
    df_rel_iqr.rename(columns={f'{args.target_col}_Relative_IQR': 'Overall_Mean_Relative_IQR'}, inplace=True)
    df_rel_iqr.to_csv(os.path.join(results_dir, f'Summary_Table1_Mean_Relative_IQR_{args.target_col}.csv'), index=False)

    # Table 2
    print("    Generating [Table 2] global historical mean prediction table")
    df_overall_mean = df_master.groupby('Hylak')[f'{args.target_col}_Mean'].mean().reset_index()
    df_overall_mean.rename(columns={f'{args.target_col}_Mean': 'Overall_Mean_Prediction'}, inplace=True)
    df_overall_mean.to_csv(os.path.join(results_dir, f'Summary_Table2_Overall_Mean_{args.target_col}.csv'), index=False)

    # Table 3
    print("    Generating [Table 3] annual spatiotemporal matrix")
    df_annual = df_master.groupby(['Hylak', 'Year'])[f'{args.target_col}_Mean'].mean().reset_index()
    df_annual_pivot = df_annual.pivot(index='Hylak', columns='Year', values=f'{args.target_col}_Mean').reset_index()
    df_annual_pivot.to_csv(os.path.join(results_dir, f'Summary_Table3_Annual_Matrix_{args.target_col}.csv'), index=False)

    print(f"-> Prediction and summary table generation completed ({model_type})")
    print(f"-> Monthly prediction tables saved in: {output_dir}")
    print(f"-> Summary tables archived in: {results_dir}")

if __name__ == "__main__":
    main()