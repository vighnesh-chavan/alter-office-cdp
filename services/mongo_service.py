import os
import copy
from datetime import datetime
from pymongo import MongoClient

# Global variable to hold MongoDB client
_mongo_client = None


def connect_to_mongo():
    """
    Connects to MongoDB using the MONGO_URI environment variable.
    Caches the connection to avoid reconnecting.

    Returns:
        MongoClient: A connected MongoClient instance.
    """
    global _mongo_client
    if _mongo_client is None:
        mongo_uri = os.getenv("MONGO_URI")
        if not mongo_uri:
            raise EnvironmentError("MONGO_URI not set in environment variables.")
        _mongo_client = MongoClient(mongo_uri)
        print("Connected to MongoDB Successfully")

    return _mongo_client


def fetch_from_mongo(collection_name, query, sort=None):
    """
    Fetches documents from MongoDB based on a given query.

    Args:
        collection_name (str): Name of the collection.
        query (dict): MongoDB query dictionary.
        sort (list of tuples, optional): List of (field, direction) pairs for sorting.
            E.g., [("publishDate", -1)]

    Returns:
        list: A list of matching documents.
    """
    client = connect_to_mongo()
    db = client.get_default_database()

    if db is None:
        raise ValueError(
            "No default database specified in MONGO_URI. Please ensure your URI is in the format 'mongodb://host:port/defaultdb'."
        )

    collection = db[collection_name]

    cursor = collection.find(query)
    if sort:
        cursor = cursor.sort(sort)

    return list(cursor)


def insert_into_mongo(collection_name, data):
    """
    Inserts data into a specified MongoDB collection within the default database.
    Automatically adds 'created_at' and 'updated_at' timestamps.

    Args:
        collection_name (str): The name of the collection to insert into.
        data (dict or list of dict): The document(s) to insert.
                                     Can be a single dictionary for one document
                                     or a list of dictionaries for multiple documents.

    Returns:
        pymongo.results.InsertOneResult or pymongo.results.InsertManyResult:
            The result object from the insert operation.
    """
    client = connect_to_mongo()
    db = client.get_default_database()

    if db is None:
        raise ValueError(
            "No default database specified in MONGO_URI. Please ensure your URI is in the format 'mongodb://host:port/defaultdb'."
        )

    collection = db[collection_name]
    current_time = datetime.now()

    if isinstance(data, list):
        # Work on a copy of the original list
        documents = []
        for doc in data:
            doc_copy = copy.deepcopy(doc)
            doc_copy["created_at"] = current_time
            doc_copy["updated_at"] = current_time
            doc_copy["deleted_at"] = None
            documents.append(doc_copy)
        result = collection.insert_many(documents)
        print(
            f"Inserted {len(result.inserted_ids)} documents into '{collection_name}'."
        )
    elif isinstance(data, dict):
        doc_copy = copy.deepcopy(data)
        doc_copy["created_at"] = current_time
        doc_copy["updated_at"] = current_time
        doc_copy["deleted_at"] = None
        result = collection.insert_one(doc_copy)
        print(
            f"Inserted document with _id: {result.inserted_id} into '{collection_name}'."
        )
    else:
        raise TypeError(
            "Data to insert must be a dictionary or a list of dictionaries."
        )

    return result


def update_in_mongo(collection_name, match_query, update_query):
    """
    Updates documents in MongoDB based on a match query and update query.
    Automatically updates the 'updated_at' timestamp.

    Args:
        collection_name (str): Name of the collection to update.
        match_query (dict): Query to match documents that need to be updated.
        update_query (dict): The update operations to perform on matched documents.
                            Should use MongoDB update operators like $set, $inc, etc.

    Returns:
        pymongo.results.UpdateResult: The result object containing information about the update operation.
    """
    client = connect_to_mongo()
    db = client.get_default_database()

    if db is None:
        raise ValueError(
            "No default database specified in MONGO_URI. Please ensure your URI is in the format 'mongodb://host:port/defaultdb'."
        )

    collection = db[collection_name]

    # Add updated_at timestamp to the update query
    if "$set" in update_query:
        update_query["$set"]["updated_at"] = datetime.now()
    else:
        update_query["$set"] = {"updated_at": datetime.now()}

    result = collection.update_many(match_query, update_query)
    print(
        f"Updated {result.modified_count} documents in '{collection_name}' "
        f"(matched {result.matched_count} documents)."
    )

    return result


def delete_from_mongo(collection_name, query):
    """
    Deletes documents from a specified MongoDB collection based on a query.

    Args:
        collection_name (str): The name of the collection to delete from.
        query (dict): MongoDB query dictionary to match documents for deletion.

    Returns:
        pymongo.results.DeleteResult: The result object from the delete operation.
    """
    client = connect_to_mongo()
    db = client.get_default_database()

    if db is None:
        raise ValueError(
            "No default database specified in MONGO_URI. Please ensure your URI is in the format 'mongodb://host:port/defaultdb'."
        )

    collection = db[collection_name]
    result = collection.delete_many(query)
    print(f"Deleted {result.deleted_count} documents from '{collection_name}'.")
    return result
