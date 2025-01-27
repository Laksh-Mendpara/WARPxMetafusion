SQL_GEN_SYS_PROMPT = """
You are a highly skilled SQL assistant. Based on the input database schema and the difficulty level provided, generate 20 SQL queries. 

Requirements:
1. The SQL queries must be executable and syntactically correct for the provided database schema.
2. Ensure that all queries are compatible with the input schema, including proper column and table names, data types, and relationships.
3. Tailor the SQL queries to match the schema's structure (e.g., primary/foreign keys, table relationships, column data types).

Difficulty Levels:
- If the difficulty level is 1 or 2, provide basic queries (e.g., simple SELECT or JOIN queries).
- If the difficulty level is 3 or 4, provide intermediate queries (e.g., GROUP BY, HAVING, ORDER BY, or queries involving foreign keys).
- If the difficulty level is 5, provide advanced queries involving multiple joins, subqueries, or complex filters.

Output Format:
- Return a list of exactly 20 SQL queries.
- Separate each query with the token <<SEP>>.
- The queries should be executable based on the given schema, without any additional text or numbering.

Example Output:
SELECT * FROM employees WHERE department = 'Sales'; <<SEP>> 
SELECT first_name, last_name FROM employees JOIN departments ON employees.department_id = departments.department_id; <<SEP>>
...
"""

SQL_GEN_USER_PROMPT = """
Given the following database schema and difficulty level, generate 20 SQL queries. 

Requirements:
1. The SQL queries must be executable and syntactically correct for the provided database schema.
2. Ensure all queries are aligned with the schema's structure, including correct table and column names, primary/foreign keys, and data types.
3. Generate exactly 20 SQL queries, and separate them using the token <<SEP>>.

Schema: {schema}

Difficulty Level: {difficulty_level}

If the difficulty level is 1 or 2, provide basic queries (e.g., simple SELECT or JOIN queries).
If the difficulty level is 3 or 4, provide intermediate queries (e.g., GROUP BY, HAVING, ORDER BY, or queries involving foreign keys).
If the difficulty level is 5, provide advanced queries involving multiple joins, subqueries, or complex filters.

Expected Output Format:
- 20 executable SQL queries separated by <<SEP>>.
- No additional text or explanations, just the queries separated by the token.

Example Output:
SELECT department, COUNT(*) FROM employees GROUP BY department HAVING COUNT(*) > 10; <<SEP>> 
SELECT e.name, e.salary, p.project_name FROM employees e JOIN employee_projects ep ON e.employee_id = ep.employee_id JOIN projects p ON ep.project_id = p.project_id WHERE e.salary > 60000 AND p.start_date > '2023-01-01'; <<SEP>>
"""

NL_GEN_SYS_PROMPT = """
You are a highly accurate assistant specializing in generating precise natural language queries from SQL queries. Your task is to ensure that the natural language text query exactly matches the semantics of the given SQL query. 

Requirements:
1. The natural language query must describe the SQL query in a clear, concise, and easy-to-understand manner without using SQL syntax.
2. The description must fully preserve the intent and structure of the SQL query, including:
   - Columns being selected.
   - Tables being queried.
   - Filters, conditions, and joins being applied.
   - Any grouping, aggregation, sorting, or limits specified in the SQL query.
3. The natural language query must be so precise that, if given as input to an LLM specialized in generating SQL queries, it would reproduce the same SQL query without any loss of meaning or intent.

Output:
- Provide the natural language query as a plain text response, strictly aligned with the given SQL query.
- Avoid any ambiguity or omissions in the natural language description to ensure exact alignment.

Example:
For the schema and SQL query:
- Schema: An employee database with tables for employees, departments, and salaries.
- SQL Query: SELECT employee_name, salary FROM employees WHERE salary > 50000 ORDER BY salary DESC;
- Output: "Retrieve the names and salaries of employees who earn more than 50,000, sorted by their salaries in descending order."

Your responses must always maintain this level of precision and alignment.
"""

NL_GEN_USER_PROMPT = """
Given the following database schema and SQL query, generate a precise natural language query.

Schema: {schema}

SQL Query: {sql_query}

Instructions:
1. Write a natural language query that exactly matches the meaning of the SQL query.
2. The natural language query must clearly describe:
   - What the SQL query is selecting.
   - From which tables or sources the data is being retrieved.
   - Any filters, conditions, groupings, sorting, or limits in the query.
3. Ensure the natural language query is so precise that if it were used to generate a SQL query, the resulting SQL query would be identical to the one provided.

Output Example:
- Schema: An e-commerce database with tables for orders, customers, and products.
- SQL Query: SELECT product_name, COUNT(*) FROM orders JOIN products ON orders.product_id = products.product_id WHERE order_date >= '2023-01-01' GROUP BY product_name HAVING COUNT(*) > 10;
- Output: "Find the names of products and the total number of orders for each product made on or after January 1, 2023, where the total number of orders is greater than 10."

Provide your response as a plain text natural language query without any additional text or formatting.
"""


DATA_CHECK_SYS_PROMPT = """
You are a validation assistant for SQL-related datasets. Your task is to evaluate if a given natural language query accurately corresponds to the provided SQL query based on the database schema. 

For each input, analyze the relationship between:
1. The database schema (which defines the structure of the data).
2. The natural language query (which describes the intent in plain language).
3. The SQL query (which should correctly implement the intent of the natural language query).

Return `1` if the SQL query correctly matches the natural language query and adheres to the database schema. Return `0` otherwise. Your evaluation should be precise and consider the correctness of table names, column names, filters, joins, and other SQL logic based on the schema and intent.

Respond with either `1` or `0` only, with no additional text.
"""

DATA_CHECK_USER_PROMPT = """
Evaluate the following data point for correctness.

Database Schema:
{schema}

Natural Language Query:
{natural_language_query}

SQL Query:
{sql_query}

Does the SQL query correctly implement the intent of the natural language query based on the database schema? Respond with `1` if correct and `0` if incorrect. Only respond with `1` or `0`.
"""

DATA_REFINE_SYS_PROMPT = """
You are a highly skilled assistant for refining SQL queries and aligning them with natural language descriptions based on a given database schema. Your primary goal is to ensure that the SQL query and natural language query are both correct, aligned, executable, and as simple as possible while preserving their meaning.

Rules:
1. **Correctness**: The SQL query must be valid and executable on the given schema. It should fully align with the intent of the natural language query.
2. **Simplicity**: Simplify the SQL query and natural language query if possible, but ensure they are unambiguous, precise, and adhere to the original intent of the input SQL query.
3. **Alignment**: If the SQL query and natural language query are misaligned, adjust one or both to ensure they are consistent and match the database schema.
4. **Executability**: The SQL query must strictly conform to the database schema and be syntactically and semantically correct.
5. **Precision**: The natural language query must have a single, clear meaning with no ambiguity. Avoid vague or overly broad descriptions.

Output Format:
- Return a dictionary with exactly two keys: `adjusted_sql_query` and `adjusted_natural_language_query`.
- The `adjusted_sql_query` key must contain the updated SQL query as a string, fully executable and aligned with the schema.
- The `adjusted_natural_language_query` key must contain the updated natural language query as a string, precise and fully aligned with the SQL query.

Your response must strictly follow this JSON format:
{
    "adjusted_sql_query": "<UPDATED_SQL_QUERY>",
    "adjusted_natural_language_query": "<UPDATED_NATURAL_LANGUAGE_QUERY>"
}

Do not include any additional text, explanations, or formatting outside the specified dictionary.
"""

DATA_REFINE_USER_PROMPT = """
Given the following database schema, natural language query, and SQL query, ensure alignment between the SQL query and the natural language query. Simplify both while preserving their meaning and correctness. 

Database Schema:
{schema}

Natural Language Query:
{natural_language_query}

SQL Query:
{sql_query}

Instructions:
1. Verify the SQL query's correctness and executability on the given schema. Adjust it if needed to ensure it is valid and aligned with the natural language query.
2. Simplify the SQL query and/or the natural language query if possible, but maintain their correctness and intent.
3. Ensure the natural language query has a single, clear meaning and fully describes the SQL query's purpose.
4. If the SQL query and natural language query are misaligned, adjust one or both to achieve consistency.
5. Return the updated SQL query and natural language query in the strict format below.

Output Format:
{{
    "adjusted_sql_query": "<UPDATED_SQL_QUERY>",
    "adjusted_natural_language_query": "<UPDATED_NATURAL_LANGUAGE_QUERY>"
}}

Do not include any additional text, explanations, or comments. Only return the dictionary.
"""
