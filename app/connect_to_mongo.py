import logging
from typing import Optional

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, DuplicateKeyError, PyMongoError

logger = logging.getLogger(__name__)


class MongoJsonInserter:
    """Simple wrapper to insert/replace JSON documents in a MongoDB collection.

    Notes:
    - The constructor attempts to connect (ping) and will raise RuntimeError on failure.
    - The collection will have a unique index on `job_id` (created if missing).
    - Use `close()` to explicitly close the MongoDB client or use the class as a context manager.
    """

    def __init__(self, uri: str, db_name: str = "FuturScam", collection_name: str = "RFP"):
        self.uri = uri
        self.db_name = db_name
        self.collection_name = collection_name

        # attempt to connect and ping the server; raise a clear error on failure
        try:
            self.client = MongoClient(self.uri, serverSelectionTimeoutMS=5000)
            self.client.admin.command("ping")
            logger.info("Connected to MongoDB")
        except ConnectionFailure as exc:
            raise RuntimeError(f"Unable to connect to MongoDB: {exc}") from exc

        self.db = self.client[self.db_name]
        self.collection = self.db[self.collection_name]

        # Ensure unique index on job_id; log a warning if index creation fails
        try:
            self.collection.create_index("job_id", unique=True)
            logger.debug("Ensured unique index on 'job_id'")
        except PyMongoError as exc:
            logger.warning("Could not create index on 'job_id': %s", exc)

    def insert_json(self, data: dict) -> str:
        """Insert or replace a document by its 'job_id'.

        Returns the job_id inserted/updated. Raises ValueError for invalid input and
        RuntimeError for database errors.
        """
        if not isinstance(data, dict):
            raise ValueError("data must be a dict")

        job_id = data.get("job_id")
        if not job_id:
            raise ValueError("data must contain a non-empty 'job_id'")

        try:
            result = self.collection.replace_one({"job_id": job_id}, data, upsert=True)
        except DuplicateKeyError as exc:
            # This should be rare with replace_one+upsert, but handle explicitly
            logger.error("Duplicate key error for job_id=%s: %s", job_id, exc)
            raise
        except PyMongoError as exc:
            logger.exception("MongoDB error while upserting job_id=%s", job_id)
            raise RuntimeError(f"MongoDB error: {exc}") from exc

        if result.matched_count > 0:
            logger.info("Replaced existing document with job_id=%s", job_id)
        else:
            logger.info("Inserted new document with job_id=%s", job_id)

        return job_id

