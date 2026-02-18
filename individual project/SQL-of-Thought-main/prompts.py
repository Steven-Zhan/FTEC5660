import os
from string import Template

# API Key configuration (removed for security)
DEEPSEEK_API_KEY = ""

def alt_schema_linking_agent_prompt(question: str, table_schema: str) -> str:
    """Schema Linking Agent prompt"""
    return Template(
        """You are a Schema Linking Agent in an NL2SQL framework. Return the relevant schema links for generating SQL query for the question.

Given:
- A natural language question
- Database schemas with columns, primary keys (PK), and foreign keys (FK)

Cross-check your schema for:
- Missing or incorrect FK-PK relationships and add them
- Incomplete column selections (especially join keys)
- Table alias mismatches
- Linkage errors that would lead to incorrect joins or groupBy clauses

Question: $question

Table Schema:
$table_schema

Return the schema links in given format:

Table: primary_key_col, foreign_key_col, col1, col2, ... all other columns in Table

ONLY list relevant tables and columns and Foreign Keys in given format and no other extra characters.
"""
    ).substitute(question=question, table_schema=table_schema)


def subproblem_agent_prompt(question: str, schema: str) -> str:
    """Subproblem Agent prompt"""
    return Template(
        """You are a Subproblem Agent in an NL2SQL system. Break down the question into subproblems.

Question: $question

Schema:
$schema

Identify SQL clauses needed (SELECT, WHERE, JOIN, GROUP BY, HAVING, ORDER BY, LIMIT, etc.)

Return JSON format:
{
  "clauses": ["SELECT", "WHERE", "JOIN"],
  "subproblems": [
    {"clause": "SELECT", "description": "..."},
    {"clause": "WHERE", "description": "..."}
  ]
}

Return ONLY valid JSON, no extra text.
"""
    ).substitute(question=question, schema=schema)


def query_plan_agent_prompt(question: str, schema: str, subproblems: str) -> str:
    """Query Plan Agent prompt"""
    return Template(
        """You are a Query Plan Agent. Create a step-by-step natural language plan for SQL generation.

Question: $question

Schema:
$schema

Subproblems:
$subproblems

Create a clear plan with:
1. Which tables to use
2. What columns to select
3. Join conditions
4. Filter conditions
5. Grouping/aggregation if needed
6. Sorting/limiting if needed

Return a concise bullet-pointed plan. Do NOT write SQL code.
"""
    ).substitute(question=question, schema=schema, subproblems=subproblems)


def sql_agent_prompt(question: str, plan: str, schema: str) -> str:
    """SQL Agent prompt"""
    return Template(
        """You are a SQL Generation Agent. Generate SQL query based on the plan.

Question: $question

Schema:
$schema

Plan:
$plan

Generate a valid SQL query that:
- Follows standard SQL syntax
- Uses correct table and column names from schema
- Implements all steps in the plan
- Is executable on SQLite

Return ONLY the SQL query, no explanations.
"""
    ).substitute(question=question, plan=plan, schema=schema)


def correction_plan_agent_prompt(question: str, sql: str, schema: str, error: str) -> str:
    """Correction Plan Agent prompt"""
    return Template(
        """You are a SQL Correction Plan Agent. The generated SQL has an error.

Question: $question

Schema:
$schema

Current SQL:
$sql

Error:
$error

Analyze the error and create a correction plan. What needs to be fixed?

Return a concise correction plan.
"""
    ).substitute(question=question, sql=sql, schema=schema, error=str(error))


def correction_sql_agent_prompt(question: str, schema: str, correction_plan: str, old_sql: str) -> str:
    """Correction SQL Agent prompt"""
    return Template(
        """You are a SQL Correction Agent. Fix the SQL based on the correction plan.

Question: $question

Schema:
$schema

Old SQL (with error):
$old_sql

Correction Plan:
$correction_plan

Generate the corrected SQL query. Return ONLY the SQL, no explanations.
"""
    ).substitute(
        question=question,
        schema=schema,
        correction_plan=correction_plan,
        old_sql=old_sql
    )