import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.utils import resample
import shap
import functools
from concurrent.futures import ProcessPoolExecutor
import warnings
from tqdm import tqdm

from app.data_processor import KEEP_VARS, MULTILABEL_VARS
from app.error_handling import safe_process

warnings.filterwarnings('ignore')

NUMERICAL_VARS = [
    "userCentricity",
    "specificity",
    "deeperMotivationalDesire",
    "sellTheProductSellTheFilling",
    "videoLength",
    "slidesNumber",
]


class TrainModel:

    @safe_process(default_return={})
    def process_client(self, client, df):
        df = self.explode_multi_label(df, MULTILABEL_VARS)
        categorical_vars = list(
            set(KEEP_VARS)
            - (
                set(MULTILABEL_VARS)
                | set(NUMERICAL_VARS)
                | set(["metaGeomMScore1", "metaFBetaScore1"])
            )
        )
        df = self.get_dummies(df, categorical_vars)
        df = self.normalise(df, NUMERICAL_VARS)
        return self.train_model(df)
    
    def _train_single_model(self, i, X_processed, y, n_estimators):
        # Bootstrap sample (resampling with replacement)
        X_boot, y_boot = resample(X_processed, y, random_state=i)
        X_boot = np.array(X_boot)

        # Train a new Random Forest model
        model = RandomForestRegressor(n_estimators=n_estimators)
        model.fit(X_boot, y_boot)

        # Compute SHAP values
        explainer = shap.Explainer(model, X_boot)
        shap_values = explainer(X_boot, check_additivity=False)
        
        return shap_values.values

    def run(self, data):
        model_trained_data = {}
        for client, df in tqdm(data.items()):
            result = self.process_client(client, df)
            if result:
                model_trained_data[client] = result

        # Format data
        formatted_data = []
        for client, importance_dict in model_trained_data.items():
            formatted_data.append({"clientId": client, **importance_dict})

        return formatted_data

    def train_model(self, df_, n_models=50, n_estimators=10, max_workers=10):
        importance_scores = {}
        for metric in ["metaGeomMScore1", "metaFBetaScore1"]:

            df = df_.copy()
            X = df.drop(columns=["metaGeomMScore1", "metaFBetaScore1"])
            y = df[metric]
            X_processed = X.astype(
                {col: int for col in X.select_dtypes(include=["bool"]).columns}
            )

            # Use ProcessPoolExecutor for parallel processing
            with ProcessPoolExecutor(max_workers=max_workers) as executor:
                # Create a partial function with fixed arguments
                train_fn = functools.partial(self._train_single_model, 
                                            X_processed=X_processed, 
                                            y=y, 
                                            n_estimators=n_estimators)
                
                # Map the function to all model indices and collect results
                shap_values_list = list(executor.map(train_fn, range(n_models)))

            # Convert list to a 3D NumPy array
            shap_values_array = np.array(
                shap_values_list
            )  # Shape: (n_models, n_samples, n_features)

            # Average SHAP values across all models
            shap_values_avg = np.mean(shap_values_array, axis=(0, 1))
            shap_values_avg = np.tanh(
                shap_values_avg * (1 / (shap_values_avg.std() * 2))
            )

            eda_correlation = X_processed.corrwith(y)  # Take absolute correlation

            importance_scores[f"{metric}_blended_importance"] = (
                0.2 * shap_values_avg + 0.8 * eda_correlation
            )

        output = {
            "varNames": list(
                importance_scores["metaGeomMScore1_blended_importance"].index
            ),
            "geomMScoreImportance": importance_scores[
                "metaGeomMScore1_blended_importance"
            ].values.tolist(),
            "fBetaScoreImportance": importance_scores[
                "metaFBetaScore1_blended_importance"
            ].values.tolist(),
        }

        return output

    def explode_multi_label(self, df, columns):
        df_copy = df.copy()
        for column in columns:
            if column not in df_copy.columns:
                continue

            # Split and one-hot encode
            exploded_df = df.explode(column).reset_index()
            one_hot = pd.get_dummies(
                exploded_df[column], prefix=column, prefix_sep="::"
            )
            one_hot["index"] = exploded_df["index"]

            # Aggregate back to original indices
            aggregated = one_hot.groupby("index").sum()

            # Drop any duplicate columns that might exist
            duplicate_cols = [
                col for col in aggregated.columns if col in df_copy.columns
            ]
            if duplicate_cols:
                df_copy = df_copy.drop(columns=duplicate_cols)

            # Merge back into the main dataframe
            df_copy = df_copy.join(aggregated, how="left").fillna(0)

            # Drop the original multi-label column
            df_copy.drop(columns=[column], inplace=True)

        return df_copy

    def get_dummies(self, df, columns):
        df_copy = df.copy()
        cols = [col for col in columns if col in df_copy.columns]
        df_copy = pd.get_dummies(df_copy, columns=cols, prefix_sep="::")
        return df_copy

    def normalise(self, df, columns):
        df_copy = df.copy()
        for column in columns:
            if column not in df_copy.columns:
                continue
            df_copy[column] = (df_copy[column] - df_copy[column].min()) / (
                df_copy[column].max() - df_copy[column].min()
            )
        return df_copy
