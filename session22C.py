import hashlib
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from bson import ObjectId  # For converting string IDs to ObjectId

class MongoDBHelper:
    def __init__(self, collection="users"):
        uri = "mongodb+srv://nainagupta9914:1234@cluster0.xmcswke.mongodb.net/?appName=Cluster0"
        self.client = MongoClient(uri, server_api=ServerApi('1'))

        try:
            self.client.admin.command('ping')
            print("Pinged your deployment. Successfully connected to MongoDB!")
        except Exception as e:
            print(f"Error connecting to MongoDB: {e}")

        self.db = self.client['election_system']
        self.collection = self.db[collection]

    @staticmethod
    def hash_password(password):
        return hashlib.sha256(password.encode()).hexdigest()

    def insert(self, collection_name, document):
     try:
        collection = self.db[collection_name]
        result = collection.insert_one(document)
        print(f"Document inserted with ID: {result.inserted_id}")
        return result.inserted_id
     except Exception as e:
        print(f"Error inserting document: {e}")
        return None

    def fetch(self, query=None, collection_name=None):
        if query is None:
            query = {}
        try:
            collection = self.db[collection_name] if collection_name else self.collection
            documents = collection.find(query)
            return list(documents)
        except Exception as e:
            print(f"Error fetching documents: {e}")
            return []

    def fetch_one(self, query=None, collection_name=None):
        if query is None:
            query = {}
        try:
            collection = self.db[collection_name] if collection_name else self.collection
            document = collection.find_one(query)
            return document
        except Exception as e:
            print(f"Error fetching document: {e}")
            return None

    def find_one(self, collection_name, query):
        collection = self.db[collection_name]
        return collection.find_one(query)

    def update(self, collection_name, query, updated_data):
        collection = self.db[collection_name]
        collection.update_one(query, updated_data)

    def delete(self, collection_name, query):
     try:
        collection = self.db[collection_name]
        result = collection.delete_one(query)  # Or delete_many(query) if needed
        if result.deleted_count > 0:
            return True  # Successfully deleted
        else:
            return False  # No document was deleted
     except Exception as e:
        print(f"Error deleting document: {e}")
        return False  # Return False in case of error
