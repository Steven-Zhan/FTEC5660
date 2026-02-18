"""
SQL-of-Thought Evaluation Script (Final Version)
Reproduce paper results using DeepSeek API
"""

import json
import os
from datetime import datetime
from utils import *
from prompts import *
from analyze_by_subproblems import *

# Configuration
MAX_CRITIC_ATTEMPTS = 3  # Maximum correction attempts
MODEL = "deepseek-chat"   # Model to use

def evaluate(num_samples=100, output_file=None):
    """
    Evaluation function
    
    Args:
        num_samples: Number of evaluation samples (default: 100)
        output_file: Output file name (default: auto-generated)
    """
    print("="*80)
    print("SQL-of-Thought Evaluation System")
    print("="*80)
    print(f"Model: {MODEL}")
    print(f"Number of samples: {num_samples}")
    print(f"Maximum correction attempts: {MAX_CRITIC_ATTEMPTS}")
    print("="*80)
    
    # Load data and taxonomy
    dev = load_spider(dev=True)
    if not dev:
        print("[ERROR] Failed to load Spider dataset, exiting")
        return
    
    # Limit number of samples
    dev = dev[:num_samples]
    
    # Load error taxonomy
    try:
        taxonomy = json.load(open("error_taxonomy.json"))
    except FileNotFoundError:
        print("[WARNING] error_taxonomy.json not found, error classification will not be used")
        taxonomy = {}
    
    # Initialize metrics
    total, exact_match, valid_sql, exec_correct = 0, 0, 0, 0
    results = []
    
    # Record start time
    start_time = datetime.now()
    
    # Iterate through samples
    for idx, item in enumerate(dev):
        print(f"\n{'='*80}")
        print(f"Sample {idx + 1}/{num_samples}")
        print(f"{'='*80}")
        
        question = item['question']
        gold_sql = item['query']
        db_id = item['db_id']

        print(f"Question: {question}")
        print(f"Database: {db_id}")

        # Load database schema
        schema = load_schema(db_id)
        if not schema:
            print(f"[ERROR] Failed to load schema, skipping this sample")
            continue

        entry = {
            "sample_id": idx + 1,
            "question": question,
            "db_id": db_id,
            "gold_sql": gold_sql,
        }

        try:
            # ===== Agent 1: Schema Linking Agent =====
            print("\n[1/5] Schema Linking Agent...")
            schema_prompt = alt_schema_linking_agent_prompt(question, schema)
            corrected_schema = call_agent(schema_prompt, MODEL)
            if not corrected_schema:
                print("[ERROR] Schema Agent failed")
                corrected_schema = schema
            print(f"[Completed] Output length: {len(corrected_schema)} characters")

            # ===== Agent 2: Subproblem Agent =====
            print("\n[2/5] Subproblem Agent...")
            subproblem_prompt = subproblem_agent_prompt(question, corrected_schema)
            sub_json_raw = call_agent(subproblem_prompt, MODEL)
            if not sub_json_raw:
                print("[ERROR] Subproblem Agent failed")
                sub_json = "{}"
            else:
                sub_json = clean_json(sub_json_raw)
            print(f"[Completed] Output: {sub_json[:100]}...")

            # Parse SQL clauses from subproblems
            subproblem_specific_clauses = list(set(parse_subproblems(sub_json)))
            print(f"[Identified SQL clauses]: {subproblem_specific_clauses}")
            subprob_plan, subprob_sql = clause_specific_prompts(subproblem_specific_clauses)

            # ===== Agent 3: Query Plan Agent =====
            print("\n[3/5] Query Plan Agent...")
            plan_prompt = query_plan_agent_prompt(question, corrected_schema, sub_json)
            plan = call_agent(plan_prompt, MODEL)
            if not plan:
                print("[ERROR] Query Plan Agent failed")
                plan = "Generate SQL based on the question"
            print(f"[Completed] Plan: {plan[:150]}...")

            # ===== Agent 4: SQL Generating Agent =====
            print("\n[4/5] SQL Agent...")
            sql_prompt = sql_agent_prompt(question, plan, corrected_schema)
            sql = call_agent(sql_prompt, MODEL)
            if not sql:
                print("[ERROR] SQL Agent failed")
                entry["gen_sql"] = ""
                entry["exact_match"] = False
                entry["valid_sql"] = False
                entry["exec_match"] = False
                results.append(entry)
                total += 1
                continue
            
            sql = postprocess_sql(sql)
            print(f"[Generated SQL]: {sql}")

            # Execute SQL and check
            exec_match, error = query_execution(item, sql)
            exec_failed = not exec_match
            attempts = 0

            # ===== Agent 5: Correction Loop =====
            if exec_failed:
                print(f"\n[5/5] SQL correction loop (Error: {error})")
            
            while exec_failed and attempts < MAX_CRITIC_ATTEMPTS:
                print(f"\n  Correction attempt {attempts + 1}/{MAX_CRITIC_ATTEMPTS}")
                
                # Generate correction plan
                correction_plan_prompt = correction_plan_agent_prompt(
                    question, sql, corrected_schema, error
                )
                correction_plan = call_agent(correction_plan_prompt, MODEL)
                if correction_plan:
                    print(f"  [Correction plan]: {correction_plan[:100]}...")
                
                # Generate corrected SQL
                correction_sql_prompt = correction_sql_agent_prompt(
                    question, corrected_schema, correction_plan, sql
                )
                corrected_sql = call_agent(correction_sql_prompt, MODEL)
                if not corrected_sql:
                    print("  [ERROR] Correction failed")
                    break
                
                sql = postprocess_sql(corrected_sql)
                print(f"  [Corrected SQL]: {sql}")
                
                # Re-execute
                exec_match, error = query_execution(item, sql)
                exec_failed = not exec_match
                attempts += 1
                
                if exec_match:
                    print(f"  ✓ Correction successful!")
                elif attempts >= MAX_CRITIC_ATTEMPTS:
                    print(f"  ✗ Maximum attempts reached")

            # ===== Calculate Metrics =====
            
            # Metric 1: Exact Match
            gold_sql_processed = postprocess_sql(gold_sql)
            entry["gen_sql"] = sql
            
            if sql.strip().lower() == gold_sql_processed.strip().lower():
                exact_match += 1
                entry["exact_match"] = True
                print("\n✓ Exact Match")
            else:
                entry["exact_match"] = False
                print("\n✗ Exact Match")

            # Metric 2: Valid SQL
            gen_rows, gen_err = exec_query(
                f"../spider/database/{db_id}/{db_id}.sqlite", sql
            )
            entry["valid_sql"] = (gen_err is None)
            if gen_err is None:
                valid_sql += 1
                print("✓ Valid SQL")
            else:
                print(f"✗ Valid SQL: {gen_err}")

            # Metric 3: Execution Accuracy
            entry["exec_match"] = exec_match
            if exec_match:
                exec_correct += 1
                print("✓ Execution Accuracy")
            else:
                print("✗ Execution Accuracy")

            total += 1
            results.append(entry)

            # Print current statistics
            print(f"\n--- Progress ({total}/{num_samples}) ---")
            print(f"Exact Match:        {exact_match}/{total} = {exact_match/total*100:.1f}%")
            print(f"Valid SQL:          {valid_sql}/{total} = {valid_sql/total*100:.1f}%")
            print(f"Execution Accuracy: {exec_correct}/{total} = {exec_correct/total*100:.1f}%")
        
        except Exception as e:
            print(f"\n[ERROR] Error processing sample: {e}")
            import traceback
            traceback.print_exc()
            
            entry["gen_sql"] = ""
            entry["error"] = str(e)
            entry["exact_match"] = False
            entry["valid_sql"] = False
            entry["exec_match"] = False
            results.append(entry)
            total += 1
            continue
    
    # Calculate total time
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    # ===== Generate Final Report =====
    summary = {
        "model": MODEL,
        "total_samples": total,
        "exact_match": exact_match,
        "valid_sql": valid_sql,
        "execution_accuracy": exec_correct,
        "exact_match_rate": round(exact_match / total, 4) if total > 0 else 0,
        "valid_sql_rate": round(valid_sql / total, 4) if total > 0 else 0,
        "execution_accuracy_rate": round(exec_correct / total, 4) if total > 0 else 0,
        "duration_seconds": duration,
        "avg_time_per_sample": round(duration / total, 2) if total > 0 else 0,
        "timestamp": datetime.now().isoformat()
    }

    output = {
        "summary": summary,
        "results": results
    }

    # Save results
    os.makedirs("results", exist_ok=True)
    
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"results/eval_{num_samples}samples_{timestamp}.json"
    else:
        output_file = f"results/{output_file}"
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # Print final report
    print("\n" + "="*80)
    print("Evaluation completed!")
    print("="*80)
    print(f"\nTotal time: {duration:.1f} seconds ({duration/60:.1f} minutes)")
    print(f"Average time per sample: {duration/total:.1f} seconds")
    print("\nFinal results:")
    print(f"  Exact Match:        {exact_match}/{total} = {exact_match/total*100:.2f}%")
    print(f"  Valid SQL:          {valid_sql}/{total} = {valid_sql/total*100:.2f}%")
    print(f"  Execution Accuracy: {exec_correct}/{total} = {exec_correct/total*100:.2f}%")
    print(f"\nResults saved to: {output_file}")
    
    # Compare with original paper (if available)
    print("\n" + "="*80)
    print("Comparison Analysis")
    print("="*80)
    print("Note: Results may differ due to using DeepSeek instead of GPT-4o-mini")
    print("\nExpected comparison:")
    print("  Original paper (GPT-4o-mini): Execution Accuracy ~68%")
    print(f"  This run (DeepSeek):          Execution Accuracy {exec_correct/total*100:.1f}%")
    
    if exec_correct/total >= 0.60:
        print("\n✓ Results within reasonable range (60%+)")
    elif exec_correct/total >= 0.50:
        print("\n⚠️  Results slightly low but acceptable (50-60%)")
    else:
        print("\n❌ Results low (<50%), please check configuration")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='SQL-of-Thought Evaluation Script')
    parser.add_argument('--samples', type=int, default=100,
                       help='Number of evaluation samples (default: 100)')
    parser.add_argument('--output', type=str, default=None,
                       help='Output file name (default: auto-generated)')
    
    args = parser.parse_args()
    
    print(f"\nStarting evaluation...")
    print(f"Number of samples: {args.samples}")
    
    evaluate(num_samples=args.samples, output_file=args.output)