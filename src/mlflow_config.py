import mlflow
import pandas as pd
import yaml
import os
from retrieve_context import read_param
import argparse
# Set up MLflow tracking
mlflow.set_tracking_uri("http://localhost:5000")
mlflow.set_experiment("sql-copilot-acceptance-metrics")

def log_acceptance_metrics(config_path, csv_path="logs/suggestions_log.csv"):
    # Load the configuration file
    config = read_param(config_path)

    # Normalize the CSV path
    csv_path = os.path.normpath(csv_path)

    # Load the suggestion data
    df = pd.read_csv(csv_path)

    # Calculate metrics
    total_suggestions = len(df)
    accepted_suggestions = len(df[df['status'] == 'ACCEPTED'])
    rejected_suggestions = len(df[df['status'] == 'DISMISSED'])

    # Calculate rates
    acceptance_rate = accepted_suggestions / total_suggestions if total_suggestions > 0 else 0
    rejection_rate = rejected_suggestions / total_suggestions if total_suggestions > 0 else 0

    # Latency metrics (assuming 'latency_ms' column exists)
    avg_latency = df["latency_ms"].mean() if "latency_ms" in df.columns else None
    max_latency = df["latency_ms"].max() if "latency_ms" in df.columns else None
    min_latency = df["latency_ms"].min() if "latency_ms" in df.columns else None

    # Start MLflow run
    with mlflow.start_run():
        # Log parameters
        mlflow.log_param("model_name", config["llm"]["model_name"])
        mlflow.log_param("data_size", total_suggestions)

        # Log metrics
        mlflow.log_metric("acceptance_rate", acceptance_rate)
        mlflow.log_metric("rejection_rate", rejection_rate)
        mlflow.log_metric("accepted_count", accepted_suggestions)
        mlflow.log_metric("rejected_count", rejected_suggestions)
        mlflow.log_metric("total_count", total_suggestions)

        # Log latency if available
        if avg_latency is not None:
            mlflow.log_metric("avg_latency_ms", avg_latency)
            mlflow.log_metric("min_latency_ms", min_latency)
            mlflow.log_metric("max_latency_ms", max_latency)

        # Log the CSV file as an artifact
        mlflow.log_artifact(csv_path)

    return {
        "acceptance_rate": acceptance_rate,
        "rejection_rate": rejection_rate,
        "accepted_count": accepted_suggestions,
        "rejected_count": rejected_suggestions,
        "avg_latency_ms": avg_latency,
        "min_latency_ms": min_latency,
        "max_latency_ms": max_latency
    }


# Example usage

if __name__ == "__main__":
    args = argparse.ArgumentParser()
    args.add_argument("--config", default="params.yaml")
    parsed_args = args.parse_args()
    metrics = log_acceptance_metrics(config_path=parsed_args.config)
    print(f"SQL Copilot Acceptance Rate: {metrics['acceptance_rate']:.2%}")
    print(f"SQL Copilot Rejection Rate: {metrics['rejection_rate']:.2%}")