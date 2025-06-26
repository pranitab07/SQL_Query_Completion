# test_schema.py
from src.db_schema_utils import read_db_config, create_connection, extract_schema_with_examples

def main():
    cfg = read_db_config("db_config.yaml")
    engine = create_connection(cfg)
    schema_str = extract_schema_with_examples(engine, cfg["name"], sample_rows=cfg.get("sample_rows", 2))
    print("=== Extracted Schema & Samples ===")
    print(schema_str)

if __name__ == "__main__":
    main()