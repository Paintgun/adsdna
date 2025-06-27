import math
import numpy as np
import pandas as pd
from app.error_handling import safe_process


KEEP_VARS = [
    "narrativeType",
    "singleAssetFormatType",
    "singleAssetType",
    "singleAssetSubType",
    "languages",
    "layout",
    "assetRatio",
    "assetFormat",
    "slidesNumber",
    "videoLength",
    # GRAB ATTENTION
    "visualHookBranded",
    "visualHookFeatures",
    "visualHookUnusual",
    "visualHookRelevance",
    "copyHookFraming",
    "copyHookTypology",
    "copyHookRelevance",
    "popularFormats",
    "references",
    "trend",
    "sound",
    "aiContent",
    # HOLD ATTENTION
    "ugcCreators",
    "visualBranded",
    "visualFeatures",
    "painPoints",
    "locationSpecificity",
    #  'personas',
    "benefits",
    "productFeatures",
    "products",
    "valuePropositions",
    "educating",
    "educatingApp",
    "educatingAppWholeApp",
    "educatingAppService",
    "educatingBroadTopic",
    "userCentricity",
    "specificity",
    "statistics",
    "simpleLanguage",
    "legalDisclaimer",
    "subtitles",
    "entertaining",
    "anticipation",
    # EVOKE ACTION
    "financialBenefit",
    "instantValue",
    "socialProof",
    "authority",
    "lossAversion",
    "scarcity",
    "unity",
    "deeperMotivationalDesire",
    "sellTheProductSellTheFilling",
    "ctas",
    "ctaPlacement",
    # ROLES
    "creatorUserIds",
    # METRIC
    "metaGeomMScore1",
    "metaFBetaScore1",
]

MULTILABEL_VARS = [
    "languages",
    "visualHookFeatures",
    "visualHookRelevance",
    "copyHookFraming",
    "copyHookTypology",
    "copyHookRelevance",
    "popularFormats",
    "references",
    "trend",
    "sound",
    "ugcCreators",
    "visualFeatures",
    "painPoints",
    "personas",
    "benefits",
    "productFeatures",
    "products",
    "valuePropositions",
    "simpleLanguage",
    "financialBenefit",
    "instantValue",
    "socialProof",
    "authority",
    "lossAversion",
    "scarcity",
    "ctas",
    "creatorUserIds",
]

SCATTER_PLOTS = [
    "videoLength",
    "slidesNumber",
]


class DataProcessor:

    def build_ads_dataframe(self, data):
        """
        Build a dataframe from the data
        """
        for client, ads in data.items():
            data[client] = pd.DataFrame(ads)
            cols = data[client].columns
            cols_in_keep_vars = [col for col in cols if col in KEEP_VARS]
            data[client] = data[client][cols_in_keep_vars]
        return data

    def process_data_for_plots(self, data):
        """
        We will eventually store data as:
        {
            "clientId": string,
            "plotData": {
                varName: string,
                varValue: (string|number)[], # this is x
                plotType: string
                geomMScore: number[], # this is a choice for y
                fBetaScore: number[] # this is the other choice for y
                geomMStats: dict,
                fBetaStats: dict
            }[],
        }

        This function will take the data and convert it to the above format
        """
        plot_data = []
        for client, ads in data.items():
            client_result = self.process_client_for_plots(client, ads)
            if client_result:
                plot_data.append(client_result)
        return plot_data

    @safe_process(default_return=None)
    def process_client_for_plots(self, client, ads):
        """
        Process a single client's data for plots
        """
        client_obj = {
            "clientId": client,
            "plotData": [],
        }

        for var in ads.columns:
            if var not in ["metaGeomMScore1", "metaFBetaScore1"]:
                mask = ~pd.isna(ads[var])
                if var in SCATTER_PLOTS:

                    stats = self.calculate_stats_by_group(
                        ads, var, ["metaGeomMScore1", "metaFBetaScore1"], mask
                    )

                    client_obj["plotData"].append(
                        {
                            "varName": var,
                            "varValue": ads[var][mask].values,
                            "plotType": "scatter",
                            "geomMScore": ads["metaGeomMScore1"][mask].values,
                            "fBetaScore": ads["metaFBetaScore1"][mask].values,
                            "geomMStats": stats["metaGeomMScore1"],
                            "fBetaStats": stats["metaFBetaScore1"],
                        }
                    )
                    continue

                if var in MULTILABEL_VARS:
                    geomMLongFormat = self.create_long_format_dataframe(
                        client, ads, var, "metaGeomMScore1"
                    )
                    fbetaLongFormat = self.create_long_format_dataframe(
                        client, ads, var, "metaFBetaScore1"
                    )

                    # Group by Factor and calculate stats for each group
                    geom_stats = self.get_grouped_iqr_stats(
                        geomMLongFormat, "Factor", "metaGeomMScore1"
                    )
                    fbeta_stats = self.get_grouped_iqr_stats(
                        fbetaLongFormat, "Factor", "metaFBetaScore1"
                    )

                    client_obj["plotData"].append(
                        {
                            "varName": var,
                            "varValue": geomMLongFormat["Factor"].values,
                            "plotType": "box",
                            "geomMScore": geomMLongFormat["metaGeomMScore1"].values,
                            "fBetaScore": fbetaLongFormat["metaFBetaScore1"].values,
                            "geomMStats": geom_stats,
                            "fBetaStats": fbeta_stats,
                        }
                    )
                    continue

                # For regular categorical variables, group by unique values
                if pd.api.types.is_categorical_dtype(
                    ads[var]
                ) or pd.api.types.is_object_dtype(ads[var]):

                    stats = self.calculate_stats_by_group(
                        ads, var, ["metaGeomMScore1", "metaFBetaScore1"], mask
                    )

                    client_obj["plotData"].append(
                        {
                            "varName": var,
                            "varValue": ads[var][mask].values,
                            "plotType": "box",
                            "geomMScore": ads["metaGeomMScore1"][mask].values,
                            "fBetaScore": ads["metaFBetaScore1"][mask].values,
                            "geomMStats": stats["metaGeomMScore1"],
                            "fBetaStats": stats["metaFBetaScore1"],
                        }
                    )
                else:
                    # For numerical variables, compute stats for each unique value
                    unique_vals = ads[var][mask].unique()
                    geomMStats = {}
                    fBetaStats = {}
                    for val in unique_vals:
                        submask = (ads[var] == val) & mask
                        geomMStats[str(val)] = self.get_iqr_data(
                            ads["metaGeomMScore1"][submask].values
                        )
                        fBetaStats[str(val)] = self.get_iqr_data(
                            ads["metaFBetaScore1"][submask].values
                        )

                    client_obj["plotData"].append(
                        {
                            "varName": var,
                            "varValue": ads[var][mask].values,
                            "plotType": "box",
                            "geomMScore": ads["metaGeomMScore1"][mask].values,
                            "fBetaScore": ads["metaFBetaScore1"][mask].values,
                            "geomMStats": geomMStats,
                            "fBetaStats": fBetaStats,
                        }
                    )

        return client_obj

    @safe_process(default_return={})
    def calculate_stats_by_group(self, df, group_var, score_vars, mask=None):
        """
        Calculate statistics for each unique value in group_var for each score variable

        Args:
            df: DataFrame containing the data
            group_var: Column to group by
            score_vars: List of columns containing score values
            mask: Boolean mask to filter rows (optional)

        Returns:
            Dictionary with score variables as keys, each containing a dictionary
            of group values as keys and IQR statistics as values
        """
        if mask is None:
            mask = pd.Series(True, index=df.index)

        result = {}
        unique_values = df[group_var][mask].unique()

        for score_var in score_vars:
            stats = {}
            for val in unique_values:
                val_mask = (df[group_var] == val) & mask
                scores = df[score_var][val_mask].values

                if len(scores) > 0:
                    stats[str(val)] = self.get_iqr_data(scores)

            result[score_var] = stats

        return result

    @safe_process(default_return={})
    def get_iqr_data(self, data: list):
        if len(data) == 0:
            return {}

        # If there's only one data point, return simplified stats
        if len(data) == 1:
            value = data[0]
            return {
                "lower_fence": value,
                "min": value,
                "q1": value,
                "median": value,
                "q3": value,
                "upper_fence": value,
                "max": value,
                "iqr": 0,
            }

        def get_percentile(data, p):
            data.sort()
            n = len(data)
            x = n * p + 0.5

            #  If integer, return
            if x.is_integer():
                return round(data[int(x - 1)], 2)  # account for zero-indexing

            #  If not an integer, get the interpolated value of the values of floor and ceiling indices
            x1, x2 = math.floor(x), math.ceil(x)
            y1, y2 = data[x1 - 1], data[x2 - 1]  # account for zero-indexing
            return round(np.interp(x=x, xp=[x1, x2], fp=[y1, y2]), 2)

        # calculate all boxplot statistics
        q1, median, q3 = (
            get_percentile(data, 0.25),
            get_percentile(data, 0.50),
            get_percentile(data, 0.75),
        )
        iqr = q3 - q1
        # Lower fence value is the minimum of y values that is more than the calculated lower limit
        lower_limit = q1 - 1.5 * iqr
        lower_fence = round(
            min([i for i in data.tolist() if i >= lower_limit]), 2)
        # Upper fence value is the maximum of y values that is less than the calculated upper limit
        upper_limit = q3 + 1.5 * iqr
        upper_fence = round(
            max([i for i in data.tolist() if i <= upper_limit]), 2)

        return {
            "lower_fence": lower_fence,
            "min": min(data.tolist()),
            "q1": q1,
            "median": median,
            "q3": q3,
            "upper_fence": upper_fence,
            "max": max(data.tolist()),
            "iqr": iqr,
        }

    @safe_process(default_return={})
    def get_grouped_iqr_stats(self, df, group_col, value_col):
        """
        Calculate IQR statistics for each group in the dataframe

        Args:
            df: DataFrame containing the data
            group_col: Column to group by
            value_col: Column containing values to calculate statistics for

        Returns:
            Dictionary with group values as keys and IQR statistics as values
        """
        stats = {}
        for group_val in df[group_col].unique():
            group_data = df[df[group_col] == group_val][value_col].values
            if len(group_data) > 0:
                stats[str(group_val)] = self.get_iqr_data(group_data)
        return stats

    @safe_process(default_return=pd.DataFrame())
    def create_long_format_dataframe(
        self, client, df, categorical_column, target_variable
    ):
        """
        Transforms a DataFrame where a categorical column contains lists of categories.
        Converts to a long-format DataFrame for plotting.

        Parameters:
        df (pd.DataFrame): Input DataFrame.
        categorical_column (str): Name of the column containing lists of categories.
        target_variable (str): Name of the target variable column.

        Returns:
        pd.DataFrame: Long-format DataFrame with category-value pairs.
        """

        # Ensure that all entries in categorical_column are lists (handle potential NaNs)
        df = df.copy()
        df[categorical_column] = df[categorical_column].apply(
            lambda x: x if isinstance(x, list) else []
        )

        # Explode lists into separate rows
        exploded_df = df.explode(categorical_column).reset_index()

        # One-hot encode the unique categories
        one_hot = pd.get_dummies(exploded_df[categorical_column])
        one_hot["index"] = exploded_df["index"]

        # Aggregate back to original indices
        aggregated = one_hot.groupby("index").sum()

        # Include the target variable
        aggregated[target_variable] = (
            df[target_variable].iloc[aggregated.index].reset_index(drop=True)
        )

        # Convert to long format
        long_df = aggregated.melt(
            id_vars=[target_variable], var_name="Factor", value_name="Indicator"
        )

        # Filter rows where Indicator == 1
        long_df = long_df[long_df["Indicator"]
                          == 1].drop(columns=["Indicator"])

        return long_df
