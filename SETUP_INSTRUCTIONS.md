# QueryPilot Setup Instructions

Thank you for downloading QueryPilot! Follow these simple steps to get started.

## Prerequisites

Before you begin, make sure you have:

- ✅ Windows 10 or higher
- ✅ MySQL Workbench or pgAdmin 4 installed
- ✅ An active database (MySQL or PostgreSQL)
- ✅ Groq API key (free at https://console.groq.com)
- ✅ Pinecone API key (optional, only if using Pinecone vector store)

## Quick Start (5 minutes)

### Step 1: Configure Environment Variables

1. Locate the file named `.env.example` in this folder
2. Rename it to `.env` (remove the `.example` extension)
3. Open `.env` with a text editor (Notepad, VS Code, etc.)
4. Fill in your credentials:

```env
GROQ_API_KEY=your_groq_api_key_here
DB_PASSWORD=your_database_password
DB_NAME=your_database_name
PINECONE_API_KEY=your_pinecone_key_here  # Only if using Pinecone
```

**Where to get API keys:**
- **Groq API Key**: Sign up at https://console.groq.com (free tier available)
- **Pinecone API Key**: Sign up at https://www.pinecone.io (only if using Pinecone vector store)

### Step 2: Configure Database Connection

1. Locate the file named `db_config.yaml.example`
2. Rename it to `db_config.yaml`
3. Open `db_config.yaml` and verify the settings:

```yaml
db:
  type: mysql  # Change to 'postgres' if using PostgreSQL
  user: root   # Your database username
  password: ${DB_PASSWORD}  # Uses value from .env
  host: localhost
  port: 3306  # Use 5432 for PostgreSQL
  name: ${DB_NAME}  # Uses value from .env
  sample_rows: 2
```

**Note**: The `${DB_PASSWORD}` and `${DB_NAME}` placeholders will automatically use the values you set in the `.env` file.

### Step 3: Run QueryPilot

1. Double-click `QueryPilot.exe`
2. You should see: `👀 Listening for Ctrl+C and Tab... (press Esc to quit)`
3. **Success!** QueryPilot is now running.

## How to Use QueryPilot

### Step 1: Open Your SQL Editor

Open MySQL Workbench or pgAdmin 4 (must be one of these)

### Step 2: Ask Query using comments

Ask your question:

```sql
-- Fetch me the data for employees having more than 20LPA CTC 
```

### Step 3: Get AI Suggestions

1. Select your question (comment)
2. Press **Ctrl+C** to trigger QueryPilot
3. Wait a moment for the AI suggestion to appear

### Step 4: Accept or Dismiss

- Press **Tab** to accept and insert the suggestion
- Press any other key to dismiss it

### Other Hotkeys

- **Ctrl+Z**: Remove ghost text
- **Ctrl+Shift+C**: Clear session memory
- **Esc**: Quit QueryPilot

## Example Workflow

```sql
-- 1. Ask your question
-- Fetch me the data for employees having more than 20LPA CTC 

-- 2. Select the statement and press Ctrl+C

-- 3. QueryPilot shows suggestion:
/* suggestion: SELECT * FROM Employees WHERE CTC > 2000000; */

-- 4. Press Tab to accept, or any other key to dismiss
```

## Configuration (Optional)

You can customize QueryPilot by editing `params.yaml`:

### Change Vector Store

```yaml
vector_store:
  type: faiss  # Options: faiss, pinecone, chromadb
```

### Adjust Session Memory

```yaml
memory:
  enable: true
  limit: 3  # Remember last 3 queries
```

### Change Hotkeys

```yaml
triggers:
  initiater: ctrl+c  # Change trigger key
  filler: tab        # Change accept key
```

## Troubleshooting

### Problem: "Cannot find .env file"

**Solution:**
- Make sure you renamed `.env.example` to `.env`
- Ensure `.env` is in the same folder as `QueryPilot.exe`
- Check that the file extension is `.env` (not `.env.txt`)

### Problem: "Database connection failed"

**Solution:**
1. Verify your database is running
2. Check credentials in `.env` file
3. Make sure the database name exists
4. Test connection with MySQL Workbench/pgAdmin 4 first

### Problem: "API key invalid"

**Solution:**
1. Verify your Groq API key at https://console.groq.com
2. Make sure there are no extra spaces in the `.env` file
3. Check that you copied the entire key

### Problem: "Vector store not found"

**Solution:**

If you see errors about missing vector store files, you need to prepare the data:

**Option A - Use Pre-built Data (if provided):**
- Check if `data/processed/` folder exists with vector store files
- If not, see Option B

**Option B - Build Vector Store Yourself:**

This requires Python 3.8+. In a terminal:

```bash
# Install Python dependencies
pip install -r requirements.txt

# Download SQL dataset
python src/loading_data.py --config params.yaml

# Build vector store
python src/build_vector_stores.py --config params.yaml
```

### Problem: Antivirus is blocking QueryPilot.exe

**Solution:**
- This is a false positive (common with packaged Python apps)
- Add an exception for `QueryPilot.exe` in your antivirus settings
- The exe is safe - it's just Python code packaged with PyInstaller

### Problem: Suggestions are not appearing

**Solution:**
1. Make sure MySQL Workbench or pgAdmin 4 is the active window
2. Check that you pressed Ctrl+C (not just C)
3. Verify QueryPilot terminal shows "SQL Captured"
4. Try again with a different SQL query

### Problem: "Missing DLL" errors

**Solution:**
- Install Visual C++ Redistributable: https://aka.ms/vs/17/release/vc_redist.x64.exe
- Restart your computer after installation

## Performance Tips

- **Faster suggestions**: Use FAISS vector store (default)
- **Better suggestions**: Increase `vector_store.top_k` in `params.yaml`
- **More context**: Increase `memory.limit` to remember more queries

## Need More Help?

- **Full Documentation**: See `README.md` in this folder
- **Report Issues**: Contact the developer or check the project repository

---

**Enjoy using QueryPilot! Happy querying! 🚀**
