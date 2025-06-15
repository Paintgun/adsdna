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
            time.sleep(60)  # wait a minute to ensure we don't run the same tick twice

    def process_data(self):
        docs = self.db_client.find_documents_and_groupby(
            {"metaGeomMScore1": {"$exists": True}}, "clientId"
        )
        docs_df = self.data_processor.build_ads_dataframe(docs)
        processed_for_plots = self.data_processor.process_data_for_plots(docs_df)
        self.db_client.serialise_eda(processed_for_plots)
        model_trained_data = self.model_trainer.run(docs_df)
        self.db_client.serialise_model(model_trained_data)


if __name__ == "__main__":
    orchestrator = Orchestrator()
    orchestrator.run()
