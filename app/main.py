from app.db_utils import DBUtils
from app.data_processor import DataProcessor
from app.train_model import TrainModel
import time
from datetime import datetime, timezone
from logtail import LogtailHandler
import logging
import os

handler = LogtailHandler(
    source_token=os.getenv("LOGTAIL_SOURCE_TOKEN"),
    host=os.getenv("LOGTAIL_HOST"),
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.handlers = []
logger.addHandler(handler)


class Orchestrator:
    def __init__(self):
        self.db_client = DBUtils("ad_dna", "prod")
        self.data_processor = DataProcessor()
        self.model_trainer = TrainModel()

    def run(self):
        while True:
            if datetime.now(tz=timezone.utc).minute == 00:
                self.process_data()
            # wait a minute to ensure we don't run the same tick twice
            time.sleep(60)

    def process_data(self):
        """
        Process data client-by-client to avoid large BSON responses.

        Steps:
        1. Fetch distinct clientIds that have scoring fields.
        2. For each clientId, pull that client’s docs, run EDA + model, and
           serialise results immediately.
        """
        base_filter = {"metaGeomMScore1": {"$exists": True}}

        # 1. Get all relevant clientIds
        client_ids = self.db_client.get_distinct_values(
            "clientId", base_filter)

        for client_id in client_ids:

            # 2. Pull docs only for this client
            docs_list = self.db_client.find_documents(
                {**base_filter, "clientId": client_id}
            )
            if not docs_list:
                continue

            # Build structure expected by downstream code: {clientId: docs}
            docs_dict = {client_id: docs_list}
            docs_df = self.data_processor.build_ads_dataframe(docs_dict)

            # --- EDA ---
            processed_for_plots = self.data_processor.process_data_for_plots(
                docs_df
            )
            self.db_client.serialise_eda(processed_for_plots)

            # --- Model ---
            model_trained_data = self.model_trainer.run(docs_df)
            self.db_client.serialise_model(model_trained_data)


if __name__ == "__main__":
    orchestrator = Orchestrator()
    orchestrator.run()
