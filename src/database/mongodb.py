from typing import Optional, Tuple, Dict, Any
import os
from bson import ObjectId
from pymongo import MongoClient
from pymongo.collection import Collection
from gridfs import GridFS
from dotenv import load_dotenv

load_dotenv()

class MongoDB:
    _instance = None
    _client = None
    _db = None
    _fs = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDB, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self._client is None:
            try:
                mongo_uri = os.getenv("MONGODB_URI", "mongodb://10.100.111.10:27017/")
                self._client = MongoClient(mongo_uri)
                self._db = self._client["AI_CALLING"]
                self._fs = GridFS(self._db)
            except Exception as e:
                raise

    @property
    def users(self) -> Collection:
        return self._db["user_details"]

    @property
    def documents(self) -> Collection:
        return self._db["documents"]

    # @property
    # def chat_history(self) -> Collection:
    #     return self._db["chat_history"]

    # @property
    # def unanswered_questions(self) -> Collection:
    #     return self._db["unanswered_questions"]

    def store_file(self, file_data: bytes, filename: str, metadata: Dict[str, Any] = None) -> str:
        """Store a file in GridFS and return its file_id."""
        try:
            file_id = self._fs.put(
                file_data,
                filename=filename,
                metadata=metadata
            )
            return str(file_id)
        except Exception as e:
            raise

    def get_file(self, file_id: str) -> Tuple[bytes, Dict[str, Any]]:
        """Retrieve a file from GridFS by its ID."""
        try:
            file_data = self._fs.get(ObjectId(file_id))
            return file_data.read(), file_data.metadata
        except Exception as e:
            raise

    def delete_file(self, file_id: str) -> bool:
        """Delete a file from GridFS by its ID."""
        try:
            self._fs.delete(ObjectId(file_id))
            return True
        except Exception as e:
            return False

    def close(self):
        if self._client:
            self._client.close()

# Create a singleton instance
db = MongoDB() 