from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")

db = client["rag_chatbot"]

users_collection = db["users"]
sessions_collection = db["sessions"]
chats_collection = db["chats"]