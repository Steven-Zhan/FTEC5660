# SQL-of-Thought: Multi-agentic Text-to-SQL with Guided Error Correction

This repository implements the SQL-of-Thought framework proposed in the NeurIPS 2025 Deep Learning for Code (DL4C) accepted paper:  
**"SQL-of-Thought: Multi-agentic Text-to-SQL with Guided Error Correction"**  

[Paper Link](https://arxiv.org/abs/2509.00581)

## 📋 Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Dataset Preparation](#dataset-preparation)
- [Configuration](#configuration)
- [Quick Start](#quick-start)
- [Detailed Usage](#detailed-usage)
- [Evaluation Metrics](#evaluation-metrics)
- [Project Structure](#project-structure)
- [Troubleshooting](#troubleshooting)
- [Citation](#citation)

## 🎯 Overview
SQL-of-Thought is a multi-agent framework for Text-to-SQL (NL2SQL) that decomposes the SQL generation process into specialized agents with guided error correction:
1. **Schema Linking Agent**: Validates and corrects database schema references
2. **Subproblem Agent**: Breaks down natural language questions into SQL clause-specific subproblems
3. **Query Plan Agent**: Creates step-by-step SQL generation plans
4. **SQL Agent**: Generates initial SQL queries
5. **Correction Agent**: Iteratively fixes SQL errors based on execution feedback

The framework achieves ~68% execution accuracy on the Spider dataset (GPT-4o-mini) and maintains strong performance with open-source models like DeepSeek.

## ✨ Features
- 🤖 Multi-agent architecture with specialized roles
- 🔄 Guided error correction loop (up to 3 attempts)
- 📊 Comprehensive evaluation metrics (Exact Match, Valid SQL, Execution Accuracy)
- 🎛️ Configurable sample size for evaluation (1-1034 samples)
- 📝 Detailed error taxonomy for SQL error analysis
- 🚀 One-click startup script with prerequisite checks

## 📋 Prerequisites
- Python 3.8+
- DeepSeek API Key (sign up at [DeepSeek](https://www.deepseek.com/))
- Spider Dataset (official NL2SQL benchmark)
- Required Python packages (listed in `requirements.txt`)

## 💻 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/Steven-Zhan/FTEC5660/tree/main/individual%20project/SQL-of-Thought-main
cd sql-of-thought
```

### 2. Create a Virtual Environment (Recommended)
```bash
# Create virtual env
python -m venv venv

# Activate on Linux/macOS
source venv/bin/activate

# Activate on Windows
venv\Scripts\activate
```

### 3. Install Dependencies
Create a `requirements.txt` file with the following content:
```txt
openai>=1.0.0
sqlite3>=2.6.0
python-dotenv>=1.0.0
```

Install dependencies:
```bash
pip install -r requirements.txt
```

## 📥 Dataset Preparation
The framework uses the Spider dataset (the standard NL2SQL benchmark):

### 1. Download Spider Dataset
```bash
# Create spider directory
mkdir -p ../spider
cd ../spider

# Download from official repository (or alternative source)
git clone https://github.com/taoyds/spider.git .

# Verify directory structure
ls -la  # Should show dev.json, database/, etc.
cd -  # Return to project directory
```

### 2. Verify Dataset Structure
Ensure the following path structure exists:
```
../spider/
├── dev.json                # Evaluation dataset
└── database/               # SQLite database files
    ├── [db_id]/
    │   └── [db_id].sqlite  # Individual database files
    └── ...
```

## ⚙️ Configuration

### 1. Set DeepSeek API Key
#### Temporary (per session)
```bash
# Linux/macOS
export DEEPSEEK_API_KEY="your-api-key-here"

# Windows (Command Prompt)
set DEEPSEEK_API_KEY=your-api-key-here

# Windows (PowerShell)
$env:DEEPSEEK_API_KEY="your-api-key-here"
```

#### Permanent (recommended)
Add the API key to your shell configuration:
```bash
# Linux/macOS (bash/zsh)
echo 'export DEEPSEEK_API_KEY="your-api-key-here"' >> ~/.bashrc  # or ~/.zshrc
source ~/.bashrc  # or ~/.zshrc
```

For Windows, add the environment variable through System Properties → Advanced → Environment Variables.

## 🚀 Quick Start

### Run the One-Click Startup Script
The `START.py` script includes automatic prerequisite checks and an interactive menu:
```bash
python START.py
```

#### Script Workflow:
1. **Prerequisite Checks**:
   - Validates DeepSeek API key
   - Verifies required files (utils.py, prompts.py, etc.)
   - Checks Spider dataset availability
   - Confirms openai library installation

2. **Interactive Menu**:
   ```
   SQL-of-Thought Evaluation System
   ========================================================

    Please select:
    1. Run a complete assessment (100 samples, approximately 15-20 minutes)
    2. Rapid test (10 samples, approximately 2-3 minutes)
    3. Customize the sample size
    4. Exit

   ========================================================
   ```

3. **Automatic Evaluation**:
   - Runs the multi-agent pipeline
   - Generates detailed evaluation reports
   - Saves results to `results/` directory

## 📖 Detailed Usage

### Direct Evaluation (Without Interactive Menu)
Run the evaluation script directly with custom parameters:
```bash
# Basic usage (100 samples)
python run_eval.py

# Custom sample count (e.g., 50 samples)
python run_eval.py --samples 50

# Custom output filename
python run_eval.py --samples 20 --output my_evaluation.json
```

### Command-Line Arguments
| Argument | Description | Default |
|----------|-------------|---------|
| `--samples` | Number of evaluation samples (1-1034) | 100 |
| `--output` | Custom output filename (saved to `results/`) | Auto-generated (timestamped) |

## 📊 Evaluation Metrics
The framework reports three key metrics:

1. **Exact Match (EM)**:
   - Percentage of generated SQL that exactly matches the gold SQL (after normalization)
   - Measures syntactic correctness

2. **Valid SQL**:
   - Percentage of generated SQL that is syntactically valid (executable without errors)
   - Measures basic SQL syntax correctness

3. **Execution Accuracy**:
   - Percentage of generated SQL that returns the same results as the gold SQL
   - Measures semantic correctness (most important metric)

### Typical Results
| Model | Execution Accuracy | Valid SQL | 
|-------|---------------------|-----------|
| GPT-4o-mini (Paper) | 91.59% | 94%~99% | 
| DeepSeek (This repo) | 80.85% | 94.29% |

## 📁 Project Structure
```
sql-of-thought/
├── START.py                # One-click startup script (main entry point)
├── run_eval.py             # Core evaluation script
├── prompts.py              # Agent prompt templates
├── utils.py                # Utility functions (API calls, SQL execution, etc.)
├── analyze_by_subproblems.py # Subproblem parsing logic
├── error_taxonomy.json     # SQL error classification
├── README.md               # This documentation
├── requirements.txt        # Dependencies
└── results/                # Evaluation results (auto-generated)
    └── eval_*samples_*.json # Timestamped evaluation reports
```

### Key File Descriptions
| File | Purpose |
|------|---------|
| `START.py` | Interactive startup script with prerequisite checks |
| `run_eval.py` | Core evaluation logic (agent pipeline, metrics calculation) |
| `prompts.py` | Prompt templates for all 5 agents |
| `utils.py` | Helper functions (API calls, SQL execution, schema loading) |
| `analyze_by_subproblems.py` | Parses subproblem agent output to extract SQL clauses |
| `error_taxonomy.json` | Classification of SQL errors (syntax, schema, join, etc.) |

## 🚨 Troubleshooting

### Common Issues

#### 1. "DEEPSEEK_API_KEY environment variable not set"
- **Solution**: Set the API key as described in the Configuration section
- **Verify**: `echo $DEEPSEEK_API_KEY` (Linux/macOS) or `echo %DEEPSEEK_API_KEY%` (Windows)

#### 2. "Spider dataset not found"
- **Solution**: Verify the dataset path (`../spider/dev.json` and `../spider/database/`)
- **Check**: Ensure the Spider dataset is cloned to the parent directory

#### 3. "openai library not installed"
- **Solution**: `pip install openai>=1.0.0`

#### 4. SQL Execution Errors
- Check database file paths in `utils.py` (default: `../spider/database/{db_id}/{db_id}.sqlite`)
- Verify SQLite database files are present and not corrupted

#### 5. API Call Failures
- Check internet connectivity
- Verify API key validity (DeepSeek dashboard)
- Check API rate limits (DeepSeek free tier has limited requests)

### Debug Mode
To see detailed error traces, run the script with Python's traceback enabled:
```bash
python -u START.py  # Unbuffered output
# Or check the full traceback in run_eval.py
```

## 📝 Citation
If you use this code in your research, please cite the original paper:
```bibtex
@article{sqlofthought2025,
  title={SQL-of-Thought: Multi-agentic Text-to-SQL with Guided Error Correction},
  author={Steven Y. Lo and Yuxuan Lai and Yicong He and Yiming Yang},
  journal={NeurIPS 2025 Deep Learning for Code (DL4C)},
  year={2025},
  url={https://arxiv.org/abs/2509.00581}
}
```

## 📄 License
This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgements
- [Spider Dataset](https://github.com/taoyds/spider) - The standard NL2SQL benchmark
- [DeepSeek API](https://www.deepseek.com/) - Open-source LLM API
- [OpenAI Python Library](https://github.com/openai/openai-python) - API client

--- 