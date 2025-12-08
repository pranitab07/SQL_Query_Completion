# Query-Pilot
 
An AI-powered SQL autocompletion assistant that helps developers write complex SQL queries faster and more efficiently using intelligent, context-aware suggestions.
 
## Overview
 
Query-Pilot is a desktop application that acts as your SQL copilot, providing real-time autocompletion suggestions while you work in MySQL Workbench or pgAdmin 4. By combining Retrieval-Augmented Generation (RAG) with Large Language Models and your actual database schema, it delivers accurate and contextually relevant SQL completions.
 
## Key Features
 
- **Intelligent SQL Autocompletion**: Real-time suggestion generation based on partial queries using advanced RAG architecture
- **Database Schema Integration**: Automatically extracts and incorporates your database schema with sample data for accurate suggestions
- **Multi-Database Support**: Works with both MySQL and PostgreSQL databases
- **Flexible Vector Store Options**: Choose between FAISS (local), Pinecone (cloud), or ChromaDB (persistent local)
- **Session Memory**: Remembers recent queries within your session for better context awareness
- **Non-Intrusive Interface**: Displays suggestions as SQL comments that you can accept or dismiss
- **Comprehensive Logging**: Tracks all interactions, acceptance rates, and performance metrics
- **MLflow Integration**: Monitors model performance and tracks key metrics over time
- **Keyboard-Driven Workflow**: Efficient hotkey-based interaction
 
## Architecture
 
Query-Pilot follows a modular architecture with the following workflow:
 
1. **Trigger**: User presses `Ctrl+C` to capture SQL text from clipboard
2. **Context Retrieval**: Searches vector store for similar SQL query examples
3. **Schema Extraction**: Fetches current database schema with sample data
4. **LLM Generation**: Sends combined context to Llama model via Groq API
5. **Suggestion Display**: Shows completion as a SQL comment
6. **User Action**: Accept with `Tab` or dismiss with any other key
7. **Logging**: Records interaction details for analysis and improvement
 
```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   User      │──────│  Clipboard   │──────│   Vector    │
│  Trigger    │      │   Capture    │      │   Store     │
└─────────────┘      └──────────────┘      └─────────────┘
                              │                     │
                              │                     │
                              ▼                     ▼
                     ┌─────────────────────────────────┐
                     │      Context Aggregation        │
                     │  (Query + Schema + Examples)    │
                     └─────────────────────────────────┘
                                    │
                                    ▼
                     ┌─────────────────────────────────┐
                     │      LLM (Groq/Llama 3.3)      │
                     └─────────────────────────────────┘
                                    │
                                    ▼
                     ┌─────────────────────────────────┐
                     │    Ghost Text Suggestion        │
                     └─────────────────────────────────┘
                                    │
                         ┌──────────┴──────────┐
                         ▼                     ▼
                  ┌────────────┐        ┌───────────┐
                  │   Accept   │        │  Dismiss  │
                  │   (Tab)    │        │ (Any Key) │
                  └────────────┘        └───────────┘
                         │                     │
                         └──────────┬──────────┘
                                    ▼
                         ┌─────────────────────┐
                         │  MLflow Logging     │
                         └─────────────────────┘
```
 
## Prerequisites
 
- Python 3.11 or higher
- MySQL Workbench or pgAdmin 4
- MySQL or PostgreSQL database (for schema extraction)
- Groq API key (for LLM access)
- Pinecone API key (optional, only if using Pinecone vector store)
 
## Installation
 
### 1. Clone the Repository
 
```bash
git clone https://github.com/yourusername/Query-Pilot.git
cd Query-Pilot
```
 
### 2. Create Virtual Environment
 
```bash
python -m venv venv
 
# On Windows
venv\Scripts\activate
 
# On Linux/Mac
source venv/bin/activate
```
 
### 3. Install Dependencies
 
```bash
pip install -r requirements.txt
```
 
### 4. Set Up Environment Variables

Copy the example environment file and configure it:

```bash
cp .env.example .env
```

Edit `.env` file with your credentials:

```env
GROQ_API_KEY=your_groq_api_key_here
DB_PASSWORD=your_database_password
DB_NAME=your_database_name
PINECONE_API_KEY=your_pinecone_api_key_here  # Optional, only for Pinecone
```

### 5. Configure Database Connection

Copy the example database config and configure it:

```bash
cp db_config.yaml.example db_config.yaml
```

The `db_config.yaml` file uses environment variables for sensitive data:

```yaml
db:
  type: mysql  # or postgres
  user: root
  password: ${DB_PASSWORD}  # Reads from .env
  host: localhost
  port: 3306  # 5432 for PostgreSQL
  name: ${DB_NAME}  # Reads from .env
  sample_rows: 2
```

**Note**: The actual `db_config.yaml` file is gitignored for security. Always use the template file as a reference.
 
### 6. Download and Prepare Data
 
```bash
# Download SQL dataset from HuggingFace
python src/loading_data.py --config params.yaml
 
# Build vector store index
python src/build_vector_stores.py --config params.yaml
```
 
## Configuration
 
The main configuration file is `params.yaml`. Key sections include:
 
### Vector Store Configuration
 
Choose your preferred vector store by setting `vector_store.type`:
 
```yaml
vector_store:
  type: faiss  # Options: faiss, pinecone, chromadb
  top_k: 5     # Number of similar examples to retrieve
```
 
**FAISS** (recommended for local development):
```yaml
vector_store:
  type: faiss
  path_to_save: data/processed/sql_faiss_index.index
  metadata_path: data/processed/sql_metadata.pkl
```
 
**Pinecone** (for cloud-based scalability):
```yaml
vector_store:
  type: pinecone
  index_name: sql-index
  dimension: 384
  namespace: default
  metric: cosine
```
 
**ChromaDB** (for persistent local storage):
```yaml
vector_store:
  type: chromadb
  persist_directory: data/processed/chroma
  collection_name_chroma: sql_collection
```
 
### LLM Configuration
 
```yaml
llm:
  model_name: llama-3.3-70b-versatile  # Groq model
```
 
### Memory Configuration
 
```yaml
memory:
  enable: true
  limit: 3  # Remember last 3 queries in session
```
 
### Keyboard Shortcuts
 
```yaml
triggers:
  initiater: ctrl+c        # Trigger suggestion
  filler: tab              # Accept suggestion
  quiting: esc             # Quit application
  remove_ghost:
    c: ctrl
    key: z                 # Remove ghost text
```
 
## Usage
 
### Starting the Application
 
```bash
python src/sql_mcp.py --config params.yaml
```
 
### Workflow
 
1. **Open MySQL Workbench or pgAdmin 4**
2. **Write a partial SQL query**:
   ```sql
   SELECT * FROM users WHERE
   ```
3. **Press `Ctrl+C`** to trigger autocompletion
4. **Review the suggestion** (appears as SQL comment):
   ```sql
   SELECT * FROM users WHERE
   /* suggestion: email LIKE '%@example.com' ORDER BY created_at DESC */
   ```
5. **Accept or dismiss**:
   - Press `Tab` to accept and insert the suggestion
   - Press any other key to dismiss
6. **Clear session memory** (if needed): Press `Ctrl+Shift+C`
7. **Exit the application**: Press `Esc`
 
### Testing Database Connection
 
```bash
python test_schema.py
```
 
This will verify your database configuration and display the extracted schema.
 
### Running with Docker
 
```bash
# Build and run
docker-compose up --build
 
# Run in detached mode
docker-compose up -d
 
# Stop
docker-compose down
```
 
## Project Structure
 
```
Query-Pilot/
├── src/                          # Source code
│   ├── sql_mcp.py               # Main entry point - keyboard listener & orchestrator
│   ├── llm.py                   # LLM integration (Groq/Llama)
│   ├── retrieve_context.py      # Vector store retrieval logic
│   ├── build_vector_stores.py   # Vector store creation and management
│   ├── db_schema_utils.py       # Database schema extraction utilities
│   ├── loading_data.py          # Dataset loading from HuggingFace
│   └── mlflow_config.py         # MLflow experiment tracking
├── data/                         # Data directory
│   ├── raw/                     # Original dataset from HuggingFace
│   ├── processed/               # Vector store indexes and metadata
│   └── logs/                    # Application and suggestion logs
├── params.yaml                   # Main configuration file
├── db_config.yaml               # Database connection configuration
├── requirements.txt             # Python dependencies
├── docker-compose.yaml          # Docker deployment configuration
├── Makefile                     # Build automation commands
└── README.md                    # This file
```
 
## Technology Stack
 
### AI/ML
- **LLM**: Llama 3.3 (70B) via Groq API
- **Embeddings**: Sentence Transformers (all-MiniLM-L6-v2)
- **Vector Stores**: FAISS, Pinecone, ChromaDB
- **Framework**: LangChain
 
### Database
- **ORM**: SQLAlchemy 2.0+
- **Connectors**: PyMySQL (MySQL), psycopg2 (PostgreSQL)
 
### Desktop Integration
- **Keyboard Events**: keyboard library
- **Automation**: PyAutoGUI
- **Clipboard**: pyperclip
- **Window Detection**: pygetwindow
 
### Data Processing
- **Dataset**: HuggingFace Datasets (gretelai/synthetic_text_to_sql)
- **Manipulation**: pandas
 
### Monitoring
- **Experiment Tracking**: MLflow
- **Logging**: CSV-based suggestion logs
 
## Keyboard Shortcuts Reference
 
| Shortcut | Action |
|----------|--------|
| `Ctrl+C` | Trigger SQL autocompletion |
| `Tab` | Accept suggested completion |
| `Esc` | Quit the application |
| `Ctrl+Z` | Remove ghost text suggestion |
| `Ctrl+Shift+C` | Clear session memory |
 
## Logging and Metrics
 
Query-Pilot logs all interactions to CSV files in the `data/logs/` directory:
 
**Log Fields**:
- Timestamp
- Model name
- Status (ACCEPTED/DISMISSED)
- Latency (ms)
- User query
- LLM suggestion
- Retrieved context
- Database schema
 
### MLflow Tracking
 
Track model performance metrics:
 
```bash
# Start MLflow UI
mlflow ui
 
# Access dashboard
# Open browser to http://127.0.0.1:5000
```
 
**Tracked Metrics**:
- Acceptance rate
- Average latency
- Min/Max latency
- Total suggestions generated
 
## Development
 
### Code Quality
 
```bash
# Run linting
make lint
 
# Format code
flake8 src/
```
 
### Running Tests
 
```bash
# Test database connection
python test_schema.py
 
# Test vector store retrieval
python src/retrieve_context.py --config params.yaml
```
 
### Makefile Commands
 
```bash
make requirements    # Install dependencies
make data           # Download and prepare dataset
make clean          # Remove compiled files and cache
make lint           # Run code quality checks
```
 
## Troubleshooting
 
### Issue: Vector store not found
 
**Solution**: Run the vector store build script:
```bash
python src/build_vector_stores.py --config params.yaml
```
 
### Issue: Database connection failed
 
**Solution**:
1. Check credentials in `db_config.yaml`
2. Ensure database server is running
3. Verify network connectivity and port accessibility
4. Test connection: `python test_schema.py`
 
### Issue: Groq API errors
 
**Solution**:
1. Verify `GROQ_API_KEY` in `.env` file
2. Check API key validity on Groq console
3. Monitor rate limits and quotas
 
### Issue: Keyboard shortcuts not working
 
**Solution**:
1. Ensure MySQL Workbench or pgAdmin 4 is the active window
2. Check if another application is capturing the same hotkeys
3. Run application with administrator/sudo privileges (for keyboard access)
4. Verify `params.yaml` trigger configuration
 
### Issue: Ghost text not appearing
 
**Solution**:
1. Check clipboard contains valid SQL text
2. Verify window detection: ensure you're in MySQL Workbench or pgAdmin 4
3. Check application logs in `data/logs/`
4. Increase `sleep_time` in `params.yaml` if timing issues occur
 
### Issue: Pinecone connection errors
 
**Solution**:
1. Verify `PINECONE_API_KEY` and `PINECONE_ENVIRONMENT` in `.env`
2. Ensure Pinecone index exists: check Pinecone console
3. Verify index dimension matches embedding model (384 for all-MiniLM-L6-v2)
4. Consider switching to FAISS for local development
 
## Performance Optimization

- **Vector Store**: Use FAISS for fastest local performance, Pinecone for scalability
- **Top-K Setting**: Reduce `vector_store.top_k` for faster retrieval (default: 5)
- **Memory Limit**: Adjust `memory.limit` based on query complexity needs
- **LLM Temperature**: Currently set to 0.3 for deterministic output (configured in `llm.py`)
 
## Contributing
 
Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Follow PEP 8 style guidelines
4. Add tests for new functionality
5. Update documentation as needed
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## Security Considerations

- **API Keys**: Never commit `.env` file to version control
- **Database Credentials**: Use environment variables or secure vaults for production
- **SQL Injection**: Review all LLM-generated SQL before execution
- **Rate Limiting**: Monitor Groq API usage to avoid quota exhaustion

## Known Limitations

- Currently supports only MySQL Workbench and pgAdmin 4
- Requires clipboard access for query capture
- Windows-specific paths in default configuration (update `params.yaml` for Linux/Mac)
- LLM suggestions should be reviewed before execution in production environments

## Future Enhancements

- Support for additional SQL clients (DBeaver, DataGrip, etc.)
- Multi-language support
- Custom fine-tuned models
- Query optimization suggestions
- Syntax error detection and fixing
- Integration with additional LLM providers

## License

This project is based on the [Cookiecutter Data Science](https://drivendata.github.io/cookiecutter-data-science/) project template.

## Acknowledgments

- **Dataset**: [gretelai/synthetic_text_to_sql](https://huggingface.co/datasets/gretelai/synthetic_text_to_sql)
- **LLM Provider**: Groq API (Llama 3.3)
- **Embedding Model**: Sentence Transformers

## Support

For issues, questions, or feature requests, please open an issue on the GitHub repository.
