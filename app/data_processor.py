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
                    # Filter out NaN values
                    client_obj["plotData"].append(
                        {
                            "varName": var,
                            "varValue": ads[var][mask].values,
                            "plotType": "scatter",
                            "geomMScore": ads["metaGeomMScore1"][mask].values,
                            "fBetaScore": ads["metaFBetaScore1"][mask].values,
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
                    client_obj["plotData"].append(
                        {
                            "varName": var,
                            "varValue": geomMLongFormat["Factor"].values,
                            "plotType": "box",
                            "geomMScore": geomMLongFormat["metaGeomMScore1"].values,
                            "fBetaScore": fbetaLongFormat["metaFBetaScore1"].values,
                        }
                    )
                    continue

                client_obj["plotData"].append(
                    {
                        "varName": var,
                        "varValue": ads[var][mask].values,
                        "plotType": "box",
                        "geomMScore": ads["metaGeomMScore1"][mask].values,
                        "fBetaScore": ads["metaFBetaScore1"][mask].values,
                    }
                )

        return client_obj

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
        long_df = long_df[long_df["Indicator"] == 1].drop(columns=["Indicator"])

        return long_df
