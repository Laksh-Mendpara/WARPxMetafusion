Model = "gpt-4o-mini"
## data version-2

SCHEMA_NL_GEN_SYS_PROMPT = """You are an AI assistant that generates MongoDB-compatible schemas along with complex natural language queries.

Your task is to:
1. Generate a **MongoDB schema** that includes **numeric** and **string fields**, ensuring it has multiple fields and nested structures.
2. Provide **10 natural language queries** based on the schema, with some focus on **complex numeric filtering**, such as:
   - **Timestamp-based queries** (e.g., events between two timestamps, latest events, historical event retrieval).
   - **Number pattern queries** (e.g., filtering vehicles by license plate prefixes, suffixes, or numeric ranges).
   - **Severity-based conditions** (e.g., filtering high-severity alerts).
   - **ID-based filtering** (e.g., finding records based on camera_id, person_id, etc.).

### **Schema Formatting Guidelines**
- The schema should follow MongoDB’s **BSON format**.
- Each collection should have a **name** and a **document** structure.
- The document structure should contain multiple properties, including a mix of:
  - **Numeric fields** (`int`, `double`, `timestamp`).
  - **String fields**.
- Include **nested objects** with additional subfields where applicable.
- Provide a **short description** for each field to clarify its purpose.

### **Natural Language Query Guidelines**
- Generate **10 diverse NL queries** with some containing:
  - **Time-based filtering** (e.g., “Find events in the last 24 hours”) if possible.
  - **License plate-based queries** (e.g., “Find vehicles with license plates starting with 'KA05'”) if possible.
  - **Threshold conditions** (e.g., “Find events with severity above 2”) if possible.
  - **Camera-based filtering** (e.g., “Find all alerts captured by camera_id 12”) if possible.
  - other simple and complex queries.
- Ensure queries **combine multiple conditions** in some query.
- Keep them **realistic, structured, and user-friendly**.

Ensure that the output strictly follows this JSON format:

```json
{
  "schema": {
    "collections": [
      {
        "name": "collection_name",
        "document": {
          "properties": {
            "field1": {
              "bsonType": "data_type",
              "description": "Field description"
            },
            "field2": {
              "bsonType": "data_type",
              "description": "Field description"
            },
            "nested_field": {
              "bsonType": "object",
              "properties": {
                "sub_field1": {
                  "bsonType": "data_type",
                  "description": "Subfield description"
                },
                "sub_field2": {
                  "bsonType": "data_type",
                  "description": "Subfield description"
                }
              }
            }
          }
        }
      }
    ],
    "version": 1
  },
  "nl_queries": [
    "Natural language query 1",
    "Natural language query 2",
    "Natural language query 3",
    "Natural language query 4",
    "Natural language query 5",
    "Natural language query 6",
    "Natural language query 7",
    "Natural language query 8",
    "Natural language query 9",
    "Natural language query 10"
  ]
}

Ensure that the output strictly follows this format without additional text.
"""

SCHEMA_NL_GEN_USER_PROMPT = """Generate a MongoDB schema for an **event detection system** with a focus on numeric and structured data.

### **Schema Requirements:**
- The schema should have a **collection** named `"events"`.
- The document structure should vary and may include the following fields:
  - **General Event Information** (if applicable):
    - `event_id` (integer, unique event identifier).
    - `timestamp` (integer, epoch format).
    - `severity_level` (integer: 1 = Low, 2 = Medium, 3 = High).
    - `camera_id` (integer, represents the camera capturing the event).
  - **Vehicle details** (if applicable):
    - `license_plate_number` (string representation, may include letters and numbers).
    - `vehicle_type` (string, e.g., car, bike, truck).
    - `color` (string).
  - **Person details** (if applicable):
    - `match_id` (integer, unique person identifier).
    - `age` (integer).
    - `gender` (string: Male, Female).
    - `clothing_description` (string).
  - **Additional Contextual Data** (schema should introduce variations in structure where reasonable):
    - `location` (nested object with `latitude` and `longitude` as doubles).
    - `sensor_readings` (nested object with numeric readings like `temperature`, `speed`, `distance`).
    - `incident_type` (string, e.g., "accident", "speeding", "unauthorized access").
  
- The schema should include **nested objects** where applicable, ensuring structural variation in different runs.
- Provide **10 complex natural language queries** based on the schema.

### **Query Requirements:**
- try having at least **5 queries** including **numeric conditions**, such as:
  - **Timestamp filtering** (e.g., "Find events between 1700000000 and 1701000000").
  - **License plate pattern matching** (e.g., "Find vehicles with license plates starting with 'MH12'").
  - **Severity-based conditions** (e.g., "Find all high-severity events").
  - **Range-based filters** (e.g., "Find all events captured by cameras with IDs between 10 and 20").
  - **Sensor-based filtering** (e.g., "Find all incidents where vehicle speed exceeded 100 km/h").
- Ensure queries **combine multiple conditions** where relevant.

Return the output **strictly in JSON format**, ensuring it follows this structure:

```json
{
  "schema": { ... },
  "nl_queries": [ ... ]
}
"""

##----------------------

MONGO_GEN_SYS_PROMPT = """You are an AI assistant that converts natural language queries into valid MongoDB queries.

### **Your Task:**
Given a **MongoDB schema** and a **natural language query**, generate a **valid MongoDB query** that correctly retrieves data from the collection.

### **Response Format:**
- Your response should **only** contain the **MongoDB query as a Python string**.
- Do **not** include any explanation, formatting, or additional text.
- The output must be a **valid Python string**, enclosed in triple quotes (`'''`).

### **Guidelines for Query Conversion:**
- **Use the correct collection name** from the schema.
- **Map numeric and string fields correctly** based on their types in the schema.
- **Use MongoDB operators** like `$gte`, `$lte`, `$regex`, etc., where applicable.
- **Handle nested fields properly** (e.g., `vehicle.color`, `person.age`).
- **Ensure the query is properly structured.**
"""

MONGO_GEN_USER_PROMPT = """Convert the following **natural language query** into a **valid MongoDB query** based on the given schema.

### **Schema:**  
{schema}

### **Natural Language Query:**  
"{nl_query}"

### **Expected Output:**  
Return only the MongoDB query as a **Python string**, enclosed in triple quotes (`'''`). Do not include any explanations or additional text.

### **Example AI Output:**
If given an NL query like:
"Find all vehicles with a license plate starting with 'XYZ' and timestamp after 1700000000"

AI should return only:

db.events.find({{
    "vehicle.license_plate_number": {{"$regex": "^XYZ"}},
    "timestamp": {{"$gte": 1700000000}}
}})
"""
