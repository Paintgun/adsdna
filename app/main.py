from app.db_utils import DBUtils
from app.data_processor import DataProcessor
from app.train_model import TrainModel


class Orchestrator:
    def __init__(self):
        self.db_client = DBUtils("ad_dna", "prod")
        self.data_processor = DataProcessor()
        self.model_trainer = TrainModel()

    def run(self):
        docs = self.db_client.find_documents_and_groupby({"metaGeomMScore1": {"$exists": True}}, "clientId")
        docs_df = self.data_processor.build_ads_dataframe(docs)
        processed_for_plots = self.data_processor.process_data_for_plots(docs_df)
        self.db_client.serialise_eda(processed_for_plots)
        model_trained_data = self.model_trainer.run(docs_df)
        self.db_client.serialise_model(model_trained_data)
        
if __name__ == "__main__":
    orchestrator = Orchestrator()
    orchestrator.run()