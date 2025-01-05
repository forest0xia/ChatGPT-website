# app/database/db_config.py
import os
from pymongo import MongoClient
from flask import current_app

from ..config.settings import DB_PASS

# Create the Mongo client and references to collections

db_connection_string = (
    f"mongodb+srv://dota2bot:{DB_PASS}"
    "@cluster0-dota2bots.lmt2r85.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0-dota2bots"
)

mongo_client = MongoClient(db_connection_string)
database = mongo_client['dota2bot-gamedata']

db_collection_player = database['player-data']
db_collection_chat = database['player-chat']
db_collection_tracking = database['post-game-tracking']

# For example, expire documents after 90 days = 60 * 24 * 60 * 60 seconds
tracking_expire_after_seconds = 90 * 24 * 60 * 60
# Create or ensure a TTL index exists on 'createdTime'
db_collection_tracking.create_index(
    [("createdTime", 1)],
    expireAfterSeconds=tracking_expire_after_seconds
)

# indexes = db_collection_tracking.list_indexes()
# print('indexes for post-game-tracking:')
# for idx in indexes:
#     print(idx)
