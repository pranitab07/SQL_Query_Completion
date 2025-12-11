import os
import yaml
import sqlalchemy
from sqlalchemy import create_engine, text

def read_db_config(path="db_config.yaml"):
    with open(path, "r") as f:
        config = yaml.safe_load(f)["db"]

    # Expand environment variables
    for key, value in config.items():
        if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
            env_var = value[2:-1]
            config[key] = os.getenv(env_var, value)

    return config

def create_connection(db_cfg):
    if db_cfg["type"] == "mysql":
        conn_str = f"mysql+pymysql://{db_cfg['user']}:{db_cfg['password']}@{db_cfg['host']}:{db_cfg['port']}/{db_cfg['name']}"
    elif db_cfg["type"] == "postgres":
        conn_str = f"postgresql://{db_cfg['user']}:{db_cfg['password']}@{db_cfg['host']}:{db_cfg['port']}/{db_cfg['name']}"
    else:
        raise ValueError("Unsupported DB type")
    return create_engine(conn_str)

def extract_schema_with_examples(engine, db_name, sample_rows=2):
    inspector = sqlalchemy.inspect(engine)
    schema_strs = []
    for table in inspector.get_table_names():
        columns = inspector.get_columns(table)
        col_str = ", ".join(f"{col['name']} ({col['type']})" for col in columns)
        schema_strs.append(f"Table: {table}\nColumns: {col_str}")

        try:
            with engine.connect() as conn:                     # ← get a Connection
                result = conn.execute(text(f"SELECT * FROM {table} LIMIT {sample_rows}"))
                rows = result.fetchall()
            if rows:
                schema_strs.append("Sample rows:")
                for row in rows:
                    schema_strs.append(str(dict(row._mapping)))
        except Exception as e:
            schema_strs.append(f"(Could not fetch rows: {e})")

        schema_strs.append("\n")

    return "\n".join(schema_strs)