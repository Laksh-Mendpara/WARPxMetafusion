# test_query_conversion.py

import pytest
from loguru import logger
from typing import Dict, Any

from .utils import (
    build_schema_maps,
    modified_to_actual_query,
    actual_to_modified_query,
    build_query_and_options,
)

# Setup logging
logger.add("test_log.log", rotation="500 KB", level="DEBUG", backtrace=True, diagnose=True)
logger.info("Initializing test suite for query conversion.")

# Define schema for testing
schema = {
    "collections": [{
        "name": "events",
        "document": {
            "properties": {
                "event_id": {"bsonType": "int"},
                "timestamp": {"bsonType": "int"},
                "severity_level": {"bsonType": "int"},
                "camera_id": {"bsonType": "int"},
                "vehicle_details": {"bsonType": "object", "properties": {
                    "license_plate_number": {"bsonType": "string"},
                    "vehicle_type": {"bsonType": "string"},
                    "color": {"bsonType": "string"}
                }},
                "person_details": {"bsonType": "object", "properties": {
                    "match_id": {"bsonType": "int"},
                    "age": {"bsonType": "int"},
                    "gender": {"bsonType": "string"},
                    "clothing_description": {"bsonType": "string"}
                }},
                "location": {"bsonType": "object", "properties": {
                    "latitude": {"bsonType": "double"},
                    "longitude": {"bsonType": "double"}
                }},
                "sensor_readings": {"bsonType": "object", "properties": {
                    "temperature": {"bsonType": "double"},
                    "speed": {"bsonType": "double"},
                    "distance": {"bsonType": "double"}
                }},
                "incident_type": {"bsonType": "string"}
            }
        }
    }],
    "version": 1
}

in2out, out2in = build_schema_maps(schema)


@pytest.mark.parametrize("flat_input, expected_filter", [
    (
        {"license_plate_number": {"$regex": "^MH12"}},
        {"vehicle_details": {"license_plate_number": {"$regex": "^MH12"}}}
    ),
    (
        {"timestamp": {"$gte": 100, "$lte": 200}},
        {"timestamp": {"$gte": 100, "$lte": 200}}
    ),
    (
        {"gender": "male", "clothing_description": "jacket"},
        {"person_details": {"gender": "male", "clothing_description": "jacket"}}
    ),
    (
        {"latitude": {"$gt": 19.0}, "longitude": {"$lt": 73.0}},
        {"location": {"latitude": {"$gt": 19.0}, "longitude": {"$lt": 73.0}}}
    ),
    (
        {"speed": 45.0, "distance": {"$lt": 100}},
        {"sensor_readings": {"speed": 45.0, "distance": {"$lt": 100}}}
    ),
    (
        {"incident_type": {"$in": ["accident", "fire"]}},
        {"incident_type": {"$in": ["accident", "fire"]}}
    ),
    (
        {"camera_id": 101, "event_id": 5001},
        {"camera_id": 101, "event_id": 5001}
    )
])
def test_modified_to_actual_query(flat_input: Dict[str, Any], expected_filter: Dict[str, Any]):
    logger.debug(f"Testing modified_to_actual_query with: {flat_input}")
    actual = modified_to_actual_query(flat_input, in2out)
    logger.debug(f"Expected: {expected_filter}, Got: {actual}")
    assert actual == expected_filter


@pytest.mark.parametrize("nested_query, expected_flat", [
    (
        {"vehicle_details": {"license_plate_number": {"$regex": "^MH12"}}},
        {"license_plate_number": {"$regex": "^MH12"}}
    ),
    (
        {"timestamp": {"$gte": 100, "$lte": 200}},
        {"timestamp": {"$gte": 100, "$lte": 200}}
    ),
    (
        {"sensor_readings": {"speed": 60.0}},
        {"speed": 60.0}
    ),
    (
        {"location": {"longitude": {"$lt": 73.9}}},
        {"longitude": {"$lt": 73.9}}
    ),
    (
        {"incident_type": "fire"},
        {"incident_type": "fire"}
    )
])
def test_actual_to_modified_query(nested_query: Dict[str, Any], expected_flat: Dict[str, Any]):
    logger.debug(f"Testing actual_to_modified_query with: {nested_query}")
    flat = actual_to_modified_query(nested_query, out2in)
    logger.debug(f"Expected: {expected_flat}, Got: {flat}")
    assert flat == expected_flat


def test_build_query_and_options():
    user_input = {
        "license_plate_number": {"$regex": "^MH12"},
        "timestamp": {"$gte": 1684080000, "$lte": 1684166400},
        "severity_level": 3,
        "limit": 50,
        "skip": 10,
        "sort": [("timestamp", -1)],
        "projection": {
            "vehicle_details.license_plate_number": 1,
            "timestamp": 1,
            "_id": 0
        }
    }

    logger.debug(f"Testing build_query_and_options with user input: {user_input}")
    query, options = build_query_and_options(user_input.copy(), in2out)

    expected_query = {
        "vehicle_details": {"license_plate_number": {"$regex": "^MH12"}},
        "timestamp": {"$gte": 1684080000, "$lte": 1684166400},
        "severity_level": 3
    }

    expected_options = {
        "limit": 50,
        "skip": 10,
        "sort": [("timestamp", -1)],
        "projection": {
            "vehicle_details.license_plate_number": 1,
            "timestamp": 1,
            "_id": 0
        }
    }

    logger.debug(f"Expected query: {expected_query}, Got: {query}")
    logger.debug(f"Expected options: {expected_options}, Got: {options}")

    assert query == expected_query
    assert options == expected_options


if __name__ == "__main__":
    import sys
    logger.info("Running tests from main.")
    retcode = pytest.main(sys.argv)
    logger.info(f"Test run complete. Exit code: {retcode}")
