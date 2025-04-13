import mlflow
import pandas as pd
import yaml
import os
# Set up MLflow tracking
mlflow.set_tracking_uri("http://localhost:5000")
mlflow.set_experiment("sql-copilot-acceptance-metrics")

def log_acceptance_metrics(csv_path="logs/suggestions_log.csv", config_path="params.yaml"):
    # Load the configuration file
    with open(config_path) as yaml_file:
        config = yaml.safe_load(yaml_file)

    # Normalize the CSV path
    csv_path = os.path.normpath(csv_path)

    # Load the suggestion data
    df = pd.read_csv(csv_path)

    # Calculate metrics
    total_suggestions = len(df)
    accepted_suggestions = len(df[df['status'] == 'ACCEPTED'])
    rejected_suggestions = len(df[df['status'] == 'DISMISSED'])  # fixed logic

    # Calculate rates
    acceptance_rate = accepted_suggestions / total_suggestions if total_suggestions > 0 else 0
    rejection_rate = rejected_suggestions / total_suggestions if total_suggestions > 0 else 0

    # Start MLflow run
    with mlflow.start_run():
        # Log parameters
        mlflow.log_param("model_name", config["llm"]["model_name"])  # now logs the actual model name
        mlflow.log_param("data_size", total_suggestions)

        # Log metrics
        mlflow.log_metric("acceptance_rate", acceptance_rate)
        mlflow.log_metric("rejection_rate", rejection_rate)
        mlflow.log_metric("accepted_count", accepted_suggestions)
        mlflow.log_metric("rejected_count", rejected_suggestions)
        mlflow.log_metric("total_count", total_suggestions)

        # Log the CSV file as an artifact (corrected usage)
        mlflow.log_artifact(csv_path)

    return {
        "acceptance_rate": acceptance_rate,
        "rejection_rate": rejection_rate,
        "accepted_count": accepted_suggestions,
        "rejected_count": rejected_suggestions
    }

# Example usage
if __name__ == "__main__":
    metrics = log_acceptance_metrics()
    print(f"SQL Copilot Acceptance Rate: {metrics['acceptance_rate']:.2%}")
    print(f"SQL Copilot Rejection Rate: {metrics['rejection_rate']:.2%}")




######################################################################################################################
import os, time, yaml, requests
import pandas as pd
import mlflow
from tqdm import tqdm

def get_similar_context(user_input, config_path, top_k=5):
    with open(config_path, "r") as f:
        params = yaml.safe_load(f)
    df = pd.read_csv(params.get("vector_store", {}).get("path", "data/raw/sql_text_to_sql.csv"))
    user_tokens = set(user_input.lower().split())
    matches = [(i, row, len(user_tokens & set(str(row["sql_prompt"]).lower().split())))
               for i, row in df.iterrows()]
    matches.sort(key=lambda x: x[2], reverse=True)
    return [row for _, row, _ in matches[:top_k]]

def format_context(rows):
    return "\n".join(
        f"Example {i+1}:\nQuestion: {r['sql_prompt']}\nSQL: {r['sql']}" for i, r in enumerate(rows)
    )

def query_llama(prompt, context, config):
    api_key = os.getenv("GROQ_API_KEY")
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    data = {
        "model": config["llm"]["model_name"],
        "messages": [
            {"role": "system", "content": "You are a SQL assistant. Generate only the SQL.\n" + context},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.0,
        "max_tokens": 300
    }

    for i in range(3):
        time.sleep(config.get("api_delay", 5))
        res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data)
        if res.status_code == 429:
            time.sleep(config.get("rate_limit_delay", 60))
            continue
        if res.ok:
            return res.json()["choices"][0]["message"]["content"].strip()
        time.sleep(10 * (i + 1))
    return ""

def run_sample_eval(csv_path, output_path, config):
    df = pd.read_csv("data\\raw\\sql_text_to_sql.csv").sample(config.get("sample_size", 100), random_state=42).reset_index(drop=True)
    df["predicted_sql"], df["context_used"] = None, None

    for i, row in tqdm(df.iterrows(), total=len(df), desc="Generating SQL"):
        context_rows = get_similar_context(row["sql_prompt"], config["config_path"], config["vector_store"]["top_k"])
        context = format_context(context_rows)
        pred = query_llama(row["sql_prompt"], context, config).strip().lower()
        df.at[i, "predicted_sql"], df.at[i, "context_used"] = pred, context
        if (i + 1) % 5 == 0 or i == len(df) - 1:
            df.to_csv("data\\raw\\sql_text_to_sql_predicted.csv", index=False)

    valid = df["predicted_sql"].notna() & (df["predicted_sql"] != "")
    matches = df.loc[valid, "predicted_sql"].str.strip().str.lower() == df.loc[valid, "sql"].str.strip().str.lower()
    acc = (matches.sum() / valid.sum() * 100) if valid.sum() else 0
    context_ratio = (df["context_used"] != "").sum() / len(df) * 100

    with mlflow.start_run():
        mlflow.log_metric("exact_match_accuracy", acc)
        mlflow.log_metric("processed_queries", valid.sum())
        mlflow.log_metric("total_sample_size", len(df))
        mlflow.log_metric("context_usage_ratio", context_ratio)

    ci_low = max(0, acc - 1.96 * (acc * (100 - acc) / valid.sum()) ** 0.5)
    ci_high = min(100, acc + 1.96 * (acc * (100 - acc) / valid.sum()) ** 0.5)

    report = f"""
    SQL Evaluation Report
    =====================
    Sample Size: {len(df)}
    Processed: {valid.sum()}
    Exact Match Accuracy: {acc:.2f}%
    Context Used: {context_ratio:.2f}%
    95% CI: {ci_low:.2f}% - {ci_high:.2f}%
    """
    print(report)
    with open(output_path.replace(".csv", "_report.txt"), "w") as f:
        f.write(report)
    return df

if __name__ == "__main__":
    config = {
        "llm": {"model_name": "meta-llama/llama-4-scout-17b-16e-instruct"},
        "api_delay": 5,
        "rate_limit_delay": 60,
        "sample_size": 100,
        "config_path": "params.yaml",
        "vector_store": {"top_k": 5}
    }
    run_sample_eval("data/raw/sql_text_to_sql.csv", "sql_sample_results.csv", config)

