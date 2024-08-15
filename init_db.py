from datasets import load_dataset
from pymongo import MongoClient

# Load the Amharic corpus dataset
print("Loading the dataset...")
ds = load_dataset("faristechnology/amharic_corpus")

# Initialize MongoDB connection
print("Connecting to MongoDB...")
client = MongoClient('mongodb://localhost:27017')

# Select the database (it will be created if it doesn't exist)
db = client['stt']

# Select the collection (it will be created if it doesn't exist)
coll = db['datasets']

# Initialize a counter for the index
index = 0

# Insert each entry in the dataset into the MongoDB collection
print("Inserting documents into MongoDB...")
for item in ds['train']:  # Assuming the dataset has a 'train' split
    sentence = item.get('text')  # Replace 'text' with the actual key containing the sentence
    
    if sentence:
        # Prepare the document for insertion
        document = {
            "index": index,
            "sentence": sentence,
            "audio": []  # Initialize an empty list for audio files
        }
        
        # Insert the document into the collection
        coll.insert_one(document)
        
        # Increment the index
        index += 1

print(f"Inserted {index} documents into MongoDB.")

# Verify the data in MongoDB by fetching and printing a few documents
print("Fetching a few documents to verify insertion:")
documents = coll.find().limit(5)  # Limit to the first 5 documents

for doc in documents:
    print(doc)
