from pymongo import MongoClient

MONGO_URI = "mongodb://pasin:s6810545794@localhost:27017/"

def get_db():
    try:
        # --- Task: Database Connection ---
        # TODO: Connect to MongoDB using the 'pymongo' library.
        # TODO: The connection string should use 'localhost' and port 27017.
        # TODO: Authentication may be required (check docker-compose.yml).
        # TODO: Assign the MongoClient instance to a variable named 'client'.

        client = MongoClient(MONGO_URI)
        client.admin.command('ping')
        print("\n\n >> Connected to MongoDB successfully!\n\n")

        # Select the 'instagram_db' database assignment
        db = client['instagram_db']
        return db
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        return None
