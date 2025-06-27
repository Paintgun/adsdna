import datetime
import numpy as np
import pymongo
from bson import json_util
import json
import os
import dotenv

dotenv.load_dotenv()


class DBUtils:
    def __init__(self, collection, database="dev"):
        self.client = pymongo.MongoClient(os.getenv("MONGODB_URI"))
        self.db = self.client.get_database(database)
        self.collection = self.db[collection]

    def find_documents_and_groupby(self, filter_query=None, group_field=None):
        """
        Find documents in the collection based on filter criteria and group them by a specified field
        Returns documents with _id converted to string format
        """

        if filter_query is None:
            filter_query = {}

        if group_field is None:
            raise ValueError("group_field must be specified")

        pipeline = [
            {"$match": filter_query},
            {"$group": {"_id": f"${group_field}", "documents": {"$push": "$$ROOT"}}},
        ]

        cursor = self.collection.aggregate(pipeline, allowDiskUse=True)
        # Use json_util to handle MongoDB-specific types like ObjectId
        documents = json.loads(json_util.dumps(list(cursor)))
        documents = {doc["_id"]: doc["documents"] for doc in documents}
        return documents

    def find_documents(self, filter_query=None):
        """
        Find documents in the collection based on filter criteria
        Returns documents with _id converted to string format
        """
        if filter_query is None:
            filter_query = {}

        cursor = self.collection.find(filter_query)
        # Use json_util to handle MongoDB-specific types like ObjectId
        documents = json.loads(json_util.dumps(list(cursor)))
        return documents

    def get_distinct_values(self, field, filter_query=None):
        """
        Return a list of distinct values for a given field, constrained by an optional filter.
        This is useful for batching work per unique key (e.g., clientId) to avoid large BSON
        responses and excessive memory use.
        """
        if filter_query is None:
            filter_query = {}
        return self.collection.distinct(field, filter_query)

    def convert_to_numpy(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return obj

    def serialise_eda(self, data: list[dict]):
        client_eda_collection = self.db["client_eda"]

        # First convert numpy types to Python native types
        data = json.loads(json.dumps(data, default=self.convert_to_numpy))

        # Then handle MongoDB specific types
        as_json = json.loads(json_util.dumps(data))

        lastModifiedDate = datetime.datetime.now()

        # Prepare bulk operations
        bulk_operations = []
        for doc in as_json:
            doc["lastModifiedDate"] = lastModifiedDate
            bulk_operations.append(
                pymongo.UpdateOne(
                    {"clientId": doc["clientId"]}, {"$set": doc}, upsert=True
                )
            )

        # Execute all operations in a single bulk write
        if bulk_operations:
            client_eda_collection.bulk_write(bulk_operations)

    def serialise_model(self, data: list[dict]):
        client_model_collection = self.db["client_model"]

        # Convert numpy types to Python native types
        data = json.loads(json.dumps(data, default=self.convert_to_numpy))

        # Handle MongoDB specific types
        as_json = json.loads(json_util.dumps(data))

        lastModifiedDate = datetime.datetime.now()

        # Prepare bulk operations
        bulk_operations = []
        for doc in as_json:
            doc["lastModifiedDate"] = lastModifiedDate
            bulk_operations.append(
                pymongo.UpdateOne(
                    {"clientId": doc["clientId"]}, {"$set": doc}, upsert=True
                )
            )

        # Execute all operations in a single bulk write
        if bulk_operations:
            client_model_collection.bulk_write(bulk_operations)
