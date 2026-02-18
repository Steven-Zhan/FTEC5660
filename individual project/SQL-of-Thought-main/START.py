#!/usr/bin/env python3
"""
One-click Startup Script - SQL-of-Thought Evaluation
"""

import os
import sys
from pathlib import Path

def check_prerequisites():
    """Check prerequisites"""
    print("="*80)
    print("Checking prerequisites...")
    print("="*80)
    
    issues = []
    
    # 1. Check API key (removed for security)
    api_key = ""
    if not api_key:
        issues.append("DEEPSEEK_API_KEY environment variable is not set")
    else:
        print(f"✓ API Key configured (first 10 chars: {api_key[:10]}...)")
    
    # 2. Check required files
    required_files = [
        "utils.py",
        "prompts.py",
        "analyze_by_subproblems.py",
        "error_taxonomy.json"
    ]
    
    for file in required_files:
        if Path(file).exists():
            print(f"✓ {file}")
        else:
            issues.append(f"Missing file: {file}")
    
    # 3. Check Spider dataset
    spider_paths = ["../spider/dev.json", "../spider/database"]
    spider_ok = all(Path(p).exists() for p in spider_paths)
    
    if spider_ok:
        print("✓ Spider dataset")
    else:
        issues.append("Spider dataset not found")
    
    # 4. Check Python libraries
    try:
        from openai import OpenAI
        print("✓ openai library")
    except ImportError:
        issues.append("openai library not installed (pip install openai)")
    
    print("="*80)
    
    if issues:
        print("\n❌ Issues found:")
        for issue in issues:
            print(f"  - {issue}")
        print("\nPlease resolve these issues before running evaluation")
        return False
    else:
        print("\n✅ All checks passed!")
        return True


def show_menu():
    """Show menu"""
    print("\n" + "="*80)
    print("SQL-of-Thought Evaluation System")
    print("="*80)
    print("\nPlease select:")
    print("1. Run full evaluation (100 samples, ~15-20 minutes)")
    print("2. Quick test (10 samples, ~2-3 minutes)")
    print("3. Custom number of samples")
    print("4. Exit")
    print("="*80)


def run_evaluation(num_samples):
    """Run evaluation"""
    print(f"\nStarting evaluation ({num_samples} samples)...")
    print("Note: You can press Ctrl+C at any time to stop evaluation\n")
    
    try:
        # Import and run evaluation
        from run_eval import evaluate
        evaluate(num_samples=num_samples)
    except KeyboardInterrupt:
        print("\n\nEvaluation interrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main function"""
    print("\n" + "="*80)
    print("SQL-of-Thought One-click Startup Script")
    print("="*80)
    
    # Check prerequisites
    if not check_prerequisites():
        print("\nPlease run the following commands to resolve issues:")
        print("  export DEEPSEEK_API_KEY='your_key'")
        print("  python quick_fix.py")
        sys.exit(1)
    
    # Show menu
    while True:
        show_menu()
        choice = input("\nPlease select (1-4): ").strip()
        
        if choice == "1":
            run_evaluation(100)
            break
        elif choice == "2":
            run_evaluation(10)
            break
        elif choice == "3":
            try:
                num = int(input("Please enter number of samples (1-1034): "))
                if 1 <= num <= 1034:
                    run_evaluation(num)
                    break
                else:
                    print("Number of samples must be between 1-1034")
            except ValueError:
                print("Please enter a valid number")
        elif choice == "4":
            print("Exiting")
            sys.exit(0)
        else:
            print("Invalid selection, please enter 1-4")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCancelled by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()