Model = "gpt-4o-mini"


SCHEMA_NL_GEN_SYS_PROMPT = """
You are an AI assistant that generates flexible MongoDB-compatible schemas and natural language queries.

Your task is to:
    - Generate a realistic MongoDB schema that includes numeric, string, and nested fields with realistic and creative field names.
    - Ensure schemas reflect a plausible real-world context.
    - Provide 20 diverse natural language queries relevant to the schema.
        - Each query should follow this structure:
        {
            "query": "<natural language query>",
            "additional_info": "<additional context like resolved timestamp, location, ID, etc. Example: current time is '2024-02-10T12:00:00Z'; or 2 hours ago is '2024-02-10T10:00:00Z'>"
        }

You may optionally include context-specific elements such as:
- person-related observations (e.g., appearance, behavior, clothing)
- object or scene attributes (e.g., object_type, heat_signature, zone_alert)
- vehicle descriptors (e.g., make, type, condition, movement_style)
- sensor or AI-generated metadata (e.g., anomaly_score, detection_confidence, activity_level)
- or any other situational attributes that may vary depending on the scenario. These additions are entirely optional and should only be included when they enrich the schema meaningfully.

Schema Output Guidelines:
    - Output must be valid JSON.
    - Output structure should not be changed.
    - Define a list of collections (not always the same name), each with:
        - A name (varied and relevant to the schema purpose)
        - A document structure that includes:
            - string fields
            - numeric (int/double) and timestamp fields
            - nested objects with subfields (excluding any geographical coordinates like latitude or longitude)
            - concise descriptions for each field

Natural Language Query Guidelines:
    - Provide 20 NL queries categorized as:
        - Easy (6): Simple filters on 1–2 flat fields.
        - Medium (8): Combine multiple fields, including some nested or range filters.
        - Hard (6): Use complex filters involving time ranges, nested logic, sorting, and limits.
    - Ensure diversity in:
        - Timestamp references (use multiple dates such as 2023-12-01, 2024-03-10, etc. across queries)
        - Collection names (like but not necessary using "event",  "blob", "response", "identifier", ... etc.)
        - Expected MongoDB query structure (although not explicitly generated, design NL queries to imply diverse structures such as filters on: response.event.blobs.label, response.event.c_timestamp, identifier.camera_id, etc.)
        - Operation styles: time ranges, sort-by, top-K, regex, attribute-value pairs, and multi-attribute combinations
    - Use metadata () timestamps, etc.  if required in additional_info.
    - Use "na" if no additional_info is applicable.

Example of the format the final output should follow:
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
                        "nested_field": {
                            "bsonType": "object",
                            "properties": {
                                "subfield1": {
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
        {
            "query": "Natural language query 1",
            "additional_info": "na"
        },
        ...
    ]
}
"""

SCHEMA_NL_GEN_USER_PROMPT = """
Generate a MongoDB schema and 20 natural language queries.

Schema Requirements:
    -Define a collection with a relevant name (eg. (but not necessary) "event",  "blob", "response", "identifier", ... etc.).
    – You may optionally include attribute of thing like person, vehicle, etc. (eg. (not necessary to use same) such as gender, age, upper_color, brand_name, vehicle_color, etc.) to encourage schema diversity; feel free to vary or omit them as needed.- Include a variety of data types: strings, integers, doubles, arrays, and nested objects.

Natural Language Queries:
    - Expected MongoDB query structure (although not explicitly generated, design NL queries to imply diverse structures such as filters on: response.event.blobs.label, response.event.c_timestamp, identifier.camera_id, etc.)
    - Provide 20 NL queries, each as a dict:
    {{
        "query": "<natural language query>",
        "additional_info": "<context like timestamps, location, camera_id, etc., e.g. current time is '2024-03-15T14:00:00Z'; or between 2024-03-14T13:00:00Z and 2024-03-15T14:00:00Z> or 'na'"
    }}

Query Design:
    - Easy (6): Simple filters like "Find alerts with severity_level > 3"
    - Medium (8): Combine multiple field, nested conditions, e.g., "Find detections with a person wearing blue and near a red vehicle"
    - Hard (6): Include:
        - Time ranges: "between", "last 30 minutes", etc.
        - Sorting and limiting: "Top 5 alerts by severity", "Latest 10 detections with high speed"
        - Structure diversity such as label-based filters, regex filters, attribute match inside nested.attribs, filters on fields.

Ensure timestamps are varied across the 20 queries (do not use the same date for all). Design queries so they can map to structurally diverse MongoDB queries even if those structures are not included explicitly in the output.

Use the following schemas as loose inspiration to generate a new and distinct schema. You may borrow structure or field types, but ensure the output is diverse and not a direct merge. Optional fields and novel attributes are encouraged.
- **schema**: {schema}

"""

# SYSTEM PROMPT FOR NL TO MONGODB QUERY GENERATION (with additional_info explained)
MONGO_GEN_SYS_PROMPT = """
You are a skilled assistant designed to convert natural language queries into valid MongoDB queries.

Your inputs are:
    - nl_query: a natural language query from the user.
    - schema: the MongoDB document schema (in JSON format).
    - additional_info: additional structured context that may help resolve ambiguous references.

Requirements:
    - The output must be a valid MongoDB .find() query string (JSON-style) with only db.<collection>.find({...}) format.
    - Do not use aggregation pipelines (no .aggregate()).
    - Do not use .project() or projection clauses.
    - You may use .sort(), .limit(), .skip() etc. along with .find().
    - Do not include placeholder values like <current_time>; use exact timestamps from additional_info if needed.
    - Use appropriate MongoDB operators like $gte, $lt, $regex, $in, etc.
    - Handle nested fields, text filtering, numeric comparisons, and time conditions using standard MongoDB syntax.

Example output format:
{
    "nl_query": "original natural language query",
    "mongodb_query": "db.<collection>.find({<query_conditions>})"
}
"""

MONGO_GEN_USER_PROMPT = """
Given the following inputs, generate the MongoDB query.

Natural Language Query:
"{nl_query}"

Schema:
{schema}

Additional Info:
"{additional_info}"

Instructions:
- Use all provided information to construct the correct MongoDB query.
- Ensure all values used are specific, derived from the schema and additional_info.
- Output only a MongoDB query using db.<collection>.find(...) format. You may append .sort(), .limit() etc., but do not use aggregate or project.

Output must follow this format:
```json
{{
    "nl_query": "<repeat the natural language query here>",
    "mongodb_query": "<MongoDB .find query>"
}}
"""