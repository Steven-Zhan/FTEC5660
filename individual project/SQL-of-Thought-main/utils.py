import json, os, re
from openai import OpenAI
from typing import List, Dict, Optional
import sqlite3
from subprocess import Popen, PIPE
from datetime import datetime

# ==================== API Configuration ====================
# Read DeepSeek API key from environment variable (removed for security)
DEEPSEEK_API_KEY = ""

if not DEEPSEEK_API_KEY:
    print("="*80)
    print("Warning: DEEPSEEK_API_KEY environment variable is not set!")
    print("Please run the following command to set the API key:")
    print("  export DEEPSEEK_API_KEY='your_key_here'")
    print("="*80)

# Configure OpenAI client to use DeepSeek API
openai_client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com/v1"
)

print(f"[INFO] DeepSeek API configured")
# ==================== End of API Configuration ====================


def normalize_rows(rows):
    """Normalize query results for comparison"""
    return sorted([tuple(sorted(map(str, r))) for r in rows])


def query_execution(item, sql):
    """
    Execute SQL query and compare results with gold SQL
    Returns: (whether matched, error message)
    """
    sql = postprocess_sql(sql)
    gold_sql = postprocess_sql(item['query'])
    db_id = item['db_id']

    # Execute gold SQL and generated SQL
    gold_rows, gold_err = exec_query(f"../spider/database/{db_id}/{db_id}.sqlite", gold_sql)
    gen_rows, gen_err = exec_query(f"../spider/database/{db_id}/{db_id}.sqlite", sql)
    
    if gen_err is None and gold_err is None:
        gen_norm = normalize_rows(gen_rows)
        gold_norm = normalize_rows(gold_rows)
        exec_match = (gen_norm == gold_norm)
    else:
        exec_match = False
    
    return exec_match, gen_err


def call_agent(prompt: str, model="deepseek-chat", temperature: float = 0.0) -> str:
    """
    Call DeepSeek API
    
    Args:
        prompt: Prompt text
        model: Model name (default: deepseek-chat)
        temperature: Temperature parameter (default: 0.0, deterministic output)
    
    Returns:
        Model response text
    """
    try:
        resp = openai_client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=2048
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print(f"[ERROR] API call failed: {e}")
        return ""


def postprocess_sql(sql: str) -> str:
    """Postprocess SQL to remove redundant formatting"""
    sql_start_pattern = r'\b(select|insert)\b'
    match = re.search(sql_start_pattern, sql, re.IGNORECASE)
    if match:
        sql = sql[match.start():]
    sql = sql.strip().lower()
    sql = re.sub(r"```sql|```", "", sql)
    sql = re.sub(r"^sql[:\s]*", "", sql)
    sql = re.sub(r"```sql|```", "", sql)
    sql = sql.replace("`", "")
    sql = re.sub(r"\s+", " ", sql).strip()
    sql = re.sub(r"\s+,", ",", sql)
    if sql.endswith(";"):
        sql = sql[:-1].strip()
    return sql


def load_spider(dev: bool = True, testing=False) -> List[Dict]:
    """
    Load Spider dataset
    
    Args:
        dev: Load dev.json if True, train_spider.json if False
        testing: Whether to use test data
    
    Returns:
        List of data samples
    """
    path = "../spider/dev.json" if dev else "../spider/train_spider.json"
    if testing:
        path = "testing_limit.json"
    
    if not os.path.exists(path):
        print(f"[ERROR] Spider data file not found: {path}")
        print(f"Current working directory: {os.getcwd()}")
        print("Please ensure Spider dataset is in the correct location")
        return []
    
    with open(path) as f:
        data = json.load(f)
    
    print(f"[INFO] Successfully loaded {path}, total {len(data)} samples")
    return data


def exec_query(db_file: str, sql: str):
    """
    Execute SQL query
    
    Args:
        db_file: Database file path
        sql: SQL query statement
    
    Returns:
        (Query results, error message)
    """
    if not os.path.exists(db_file):
        return None, f"Database file does not exist: {db_file}"
    
    conn = sqlite3.connect(db_file)
    try:
        cur = conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        return rows, None
    except Exception as e:
        return None, str(e)
    finally:
        conn.close()


def load_schema(db_id: str) -> str:
    """
    Load database schema
    
    Args:
        db_id: Database ID
    
    Returns:
        Schema string
    """
    db_path = f"../spider/database/{db_id}/{db_id}.sqlite"
    
    if not os.path.exists(db_path):
        print(f"[ERROR] Database not found: {db_path}")
        return ""

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys=ON;")
    cur = conn.cursor()
    
    # Get all table names
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    tables = [row[0] for row in cur.fetchall()]

    schema_lines = []
    for tbl in tables:
        schema_lines.append(f"{tbl}:")
        
        # Get column information and primary keys
        cur.execute(f"PRAGMA table_info({tbl});")
        cols = cur.fetchall()
        col_names = [c[1] for c in cols]
        pks = [c[1] for c in cols if c[5] > 0]
        
        schema_lines.append(f"  Columns: {', '.join(col_names)}")
        if pks:
            schema_lines.append(f"  Primary Key: {', '.join(pks)}")
        
        # Get foreign keys
        cur.execute(f"PRAGMA foreign_key_list({tbl});")
        fks = cur.fetchall()
        if fks:
            schema_lines.append(f"  Foreign Keys:")
            for fk in fks:
                _, _, ref_tbl, from_col, to_col, *_ = fk
                schema_lines.append(f"    - {from_col} → {ref_tbl}.{to_col}")

    conn.close()
    return "\n".join(schema_lines)


def clean_json(text: str) -> str:
    """
    Extract JSON object from text
    """
    start = text.find('{')
    if start == -1:
        raise ValueError("No JSON object found")
    end = text.rfind('}')
    if end == -1:
        raise ValueError("No closing '}' found")
    json_str = text[start:end+1]
    json_str = json_str.strip("`\n\r ")
    return json_str


def clean_json_prefix(text: str) -> str:
    """
    Remove all characters before JSON
    """
    match = re.search(r'\{', text)
    if not match:
        raise ValueError("No JSON object found in critic response")
    trimmed = text[match.start():]
    trimmed = re.sub(r'^```+', '', trimmed)
    trimmed = re.sub(r"^['\"]+", '', trimmed)
    end = text.rfind('}')
    json_str = trimmed[:end+1]
    json_str = json_str.strip("`\n\r ")
    return json_str


def clause_specific_prompts(clauses):
    """
    Generate prompts for specific SQL clauses
    """
    plan, sql = "", ""
    for clause in clauses:
        clause = clause.upper()
        if clause in ["HAVING", "GROUPBY", "GROUP BY"]:
            plan += """
    GROUP BY detected:
    - All non-aggregated SELECT columns must be in GROUP BY.
    - GROUP BY should appear after WHERE but before HAVING/ORDER BY.

    If HAVING is present:
    - Use HAVING to filter on aggregates, not WHERE.
    """
            sql += """
    Ensure:
    - All non-aggregated SELECT columns are in GROUP BY.
    - HAVING filters only aggregated expressions.
    - HAVING appears after GROUP BY.
    - Use WHERE for pre-aggregation filters only.
    """

        if clause in ["ORDERBY", "ORDER BY"]:
            plan += """
    ORDER BY detected:
    - Specify column(s) to sort on with direction (ASC/DESC).
    - ORDER BY should be planned after WHERE/ GROUP BY / HAVING steps.
    - If LIMIT or OFFSET is present, ORDER BY must come before them.
    """
            sql += """
    Ensure:
    - ORDER BY references valid columns (or aliases defined in SELECT/grouping).
    - ORDER BY is placed after GROUP BY or HAVING if those exist.
    - If LIMIT is used, ORDER BY must guarantee deterministic results.
    """

        if clause == "LIMIT":
            plan += """
    LIMIT detected:
    - Decide which rows are returned: use ORDER BY to define which subset is used.
    - Plan ORDER BY step before LIMIT to ensure consistent results.
    """
            sql += """
    Ensure:
    - Use ORDER BY before LIMIT for deterministic row selection.
    - LIMIT appears as the final clause after ORDER BY.
    """

        if clause == "JOIN":
            plan += """
    JOIN detected:
    - Plan all necessary JOINs between tables, listing each table and ON condition.
    - Each JOIN must reference valid foreign key paths from schema.
    - Avoid Cartesian products: every JOIN must include a precise ON clause.
    """
            sql += """
    Ensure:
    - Include all tables referenced in the plan via JOINS.
    - Each JOIN uses correct foreign key column(s) in ON clause.
    - Do not introduce unintended full joins or missing JOIN conditions.
    """

        if clause == "UNION":
            plan += """
    UNION detected:
    - Both subqueries must select the same number of columns with compatible types.
    - Specify UNION vs UNION ALL depending on whether duplicates should be removed.
    - Plan ORDER BY / LIMIT after the entire UNION block.
    """
            sql += """
    Ensure:
    - Each UNION branch has identical column count and data types.
    - Use DISTINCT (default UNION) or ALL explicitly.
    - If ORDER BY or LIMIT is applied, apply it only at the end of the UNION output.
    """

        if clause == "INTERSECT":
            plan += """
    INTERSECT detected:
    - Both queries must select the same number and type of columns.
    - Plan for duplicates: INTERSECT removes duplicates unless INTERSECT ALL is specified.
    - ORDER BY / LIMIT clauses apply after the intersect.
    """
            sql += """
    Ensure:
    - Each INTERSECT branch selects same number and types of columns.
    - Use INTERSECT or INTERSECT ALL as needed.
    - Place ORDER BY and LIMIT after the intersect expression.
    """

        if clause == "EXCEPT":
            plan += """
    EXCEPT detected:
    - Both queries must select the same number and type of columns.
    - Plan which side to apply EXCEPT (left - right rows).
    - ORDER BY / LIMIT should be planned after the EXCEPT block.
    """
            sql += """
    Ensure:
    - EXCEPT branches share identical column count/types.
    - Use EXCEPT or EXCEPT ALL appropriately.
    - Apply ORDER BY and LIMIT only to the final output of the EXCEPT.
    """

    return plan, sql