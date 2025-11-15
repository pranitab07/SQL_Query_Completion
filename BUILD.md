# Building Query-Pilot Executable

This guide explains how to build a standalone executable (`.exe`) for Query-Pilot using PyInstaller.

## Prerequisites

1. Python 3.8 or higher installed
2. All dependencies installed: `pip install -r requirements.txt`
3. PyInstaller installed: `pip install pyinstaller`
4. Configured `.env` and `db_config.yaml` files (see README.md)

## Important Notes

- The `sql_mcp.spec` file is gitignored to allow for local customization
- You need to create your own `sql_mcp.spec` file locally before building
- Make sure your `.env` and `db_config.yaml` files are properly configured before building

## Step 1: Create the Spec File

Create a file named `sql_mcp.spec` in the project root with the following content:

```python
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['src/sql_mcp.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('params.yaml', '.'),
        ('.env', '.'),
        ('db_config.yaml', '.'),
        ('data/raw/*', 'data/raw'),
        ('data/processed/*', 'data/processed'),
        ('logs/*', 'logs'),
        ('src/', 'src')
    ],
    hiddenimports=[
        'faiss',
        'sentence_transformers',
        'openai',
        'fastapi',
        'uvicorn',
        'httpx',
        'requests',
        'langchain',
        'tiktoken',
        'pydantic',
        'transformers',
        'pyperclip',
        'watchdog',
        'typer',
        'pandas',
        'datasets',
        'dotenv',
        'keyboard',
        'pyautogui',
        'pygetwindow',
        'yaml',
        'sqlalchemy',
        'pymysql',
        'psycopg2',
        'pinecone',
        'chromadb'
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='QueryPilot',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True
)
```

## Step 2: Prepare Your Environment

Before building, ensure:

1. `.env` file exists and contains all required API keys:
   ```bash
   cp .env.example .env
   # Edit .env with your actual credentials
   ```

2. `db_config.yaml` exists with your database configuration:
   ```bash
   cp db_config.yaml.example db_config.yaml
   # The file uses environment variables from .env
   ```

3. Data and models are prepared:
   ```bash
   python src/loading_data.py --config params.yaml
   python src/build_vector_stores.py --config params.yaml
   ```

## Step 3: Build the Executable

Run PyInstaller with the spec file:

```bash
pyinstaller sql_mcp.spec
```

The build process will:
- Create a `build/` directory with temporary files
- Create a `dist/` directory with the final executable
- Include all data files, configuration files, and dependencies

## Step 4: Test the Executable

The executable will be located at:
- **Windows**: `dist/QueryPilot.exe`
- **Linux/Mac**: `dist/QueryPilot`

Test it by running:
```bash
./dist/QueryPilot.exe  # Windows
./dist/QueryPilot      # Linux/Mac
```

## Troubleshooting

### Missing Dependencies
If you get import errors, add the missing module to `hiddenimports` in the spec file.

### Missing Data Files
If data files are missing, ensure they're listed in the `datas` section of the spec file.

### Configuration Issues
- Ensure `.env` file is in the same directory as the executable
- Ensure `db_config.yaml` is in the same directory as the executable
- The executable looks for these files relative to its location

### Database Connection Errors
- Verify your database is running
- Check credentials in `.env` file
- Ensure `DB_PASSWORD` and `DB_NAME` environment variables are set

## Distribution

When distributing the executable:

1. **Include these files with the executable:**
   - `.env.example` (not the actual `.env` - users should create their own)
   - `db_config.yaml.example` (not the actual config)
   - `params.yaml`
   - README.md with setup instructions

2. **Users need to:**
   - Copy `.env.example` to `.env` and fill in their credentials
   - Copy `db_config.yaml.example` to `db_config.yaml`
   - Set up their database connection
   - Run the data preparation scripts (if needed)

## Notes on Security

- **NEVER** distribute your actual `.env` or `db_config.yaml` files
- **NEVER** commit these files to version control (they're gitignored)
- Always use the `.example` template files for reference
- Users must create their own configuration files with their own credentials
