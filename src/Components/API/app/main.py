import os
from fastapi import FastAPI, Body, HTTPException, status, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field, EmailStr
from bson import ObjectId
from typing import Optional, List
import datetime
from app import serializers
from app import schemas
import pymongo
import json

app = FastAPI()

# Add the CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:9080"],  # Replace with your own allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

router = APIRouter()

# Load the project echo credentials into a dictionary
try:
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'echo_config.json')
    with open(file_path, 'r') as f:
        echo_config = json.load(f)
    print(f"Echo API echo_config successfully loaded", flush=True)
except:
    print(f"Could not API echo_config : {file_path}") 

connection_string=f"mongodb://{echo_config['DB_USERNAME']}:{echo_config['DB_PASSWORD']}@{echo_config['DB_HOSTNAME']}/EchoNet"
client = pymongo.MongoClient(connection_string)
db = client['EchoNet']

print(f" database names: {client.list_database_names()}")

@app.get("/", response_description="api-root")
def show_home():
    return 'Welcome to echo api, move to /docs for more'


@app.get("/events_time", response_description="Get detection events within certain duration")
def show_event_from_time(start: str, end: str):
    datetime_start = datetime.datetime.fromtimestamp(int(start), datetime.timezone.utc)
    datetime_end = datetime.datetime.fromtimestamp(int(end), datetime.timezone.utc)
    print(datetime_start)
    print(datetime_end)
    aggregate = [
        {
            '$match':{'timestamp': {'$lt' : datetime_end, '$gte' : datetime_start }}
            
        },
        {
            '$lookup': {
                'from': 'species',
                'localField': 'species',
                'foreignField': '_id',
                'as': 'info'
            }
        },
        {
            "$replaceRoot": { "newRoot": { "$mergeObjects": [ { "$arrayElemAt": [ "$info", 0 ] }, "$$ROOT" ] } }
        },
        {
            '$project': { "audioClip": 0, "sampleRate": 0, "fileFormat": 0}
        },
        {
            "$addFields": {
            "timestamp": { "$toLong": "$timestamp" }}
        }       

    ]
    events = serializers.eventSpeciesListEntity(db["events"].aggregate(aggregate))
    return events

@app.get("/audio", response_description="returns audio given ID")
def show_audio(id: str):
    aggregate = [
        {
            '$match':{'_id': ObjectId(id)}
        },
        {
            '$project': { "audioClip": 1}
        }
    ]
    results = list(db["events"].aggregate(aggregate))
    audio = serializers.audioListEntity(results)[0]
    return audio

@app.get("/movement_time", response_description="Get true animal movement data within certain duration")
def show_event_from_time(start: str, end: str):
    datetime_start = datetime.datetime.fromtimestamp(int(start), datetime.timezone.utc)
    datetime_end = datetime.datetime.fromtimestamp(int(end), datetime.timezone.utc)
    aggregate = [
        {
            '$match':{'timestamp': {'$lt' : datetime_end, '$gte' : datetime_start }}
        },
        {
            '$lookup': {
                'from': 'species',
                'localField': 'species',
                'foreignField': '_id',
                'as': 'info'
            }
        },
        {
            "$replaceRoot": { "newRoot": { "$mergeObjects": [ { "$arrayElemAt": [ "$info", 0 ] }, "$$ROOT" ] } }
        },
        { "$project": { "info": 0 } },
        {
            "$addFields":
            {
            "timestamp": { "$toLong": "$timestamp" }
            }
        }       

    ]
    events = serializers.movementSpeciesListEntity(db["movements"].aggregate(aggregate))
    return events

@app.get("/microphones", response_description="returns location of all microphones")
def list_microphones():
    aggregate = [
        {
            "$group":
            {
            "_id": "$sensorId",
            "microphoneLLA": { "$first": "$microphoneLLA" }
            }
        }
    ]
    results = list(db["events"].aggregate(aggregate))
    microphones = serializers.microphoneListEntity(results)
    return microphones

@app.post("/event", status_code=status.HTTP_201_CREATED)
def create_event(event: schemas.EventSchema):

    result = db["events"].insert_one(event.dict())
    pipeline = [
            {'$match': {'_id': result.inserted_id}},
        ]
    new_post = serializers.eventListEntity(db["events"].aggregate(pipeline))[0]
    return new_post

@app.post("/movement", status_code=status.HTTP_201_CREATED)
def create_movement(movement: schemas.MovementSchema):

    result = db["movements"].insert_one(movement.dict())
    pipeline = [
            {'$match': {'_id': result.inserted_id}},
        ]
    new_post = serializers.movementListEntity(db["movements"].aggregate(pipeline))[0]
    return new_post