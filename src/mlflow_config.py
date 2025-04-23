import mlflow
import pandas as pd
from retrieve_context import read_param
import argparse

# Set up MLflow tracking
mlflow.set_tracking_uri("http://localhost:5000")
mlflow.set_experiment("sql-copilot-acceptance-metrics")

def log_acceptance_metrics_per_model(config_path, csv_path="logs/suggestions_log.csv"):
    # Load the configuration
    config = read_param(config_path)

    # Load the full CSV
    df = pd.read_csv(csv_path)

    # Get unique models
    unique_models = df['model'].unique()

    summary = {}

    for model_name in unique_models:
        # Filter dataframe for this model
        df_model = df[df['model'] == model_name]

        # Calculate metrics
        total_suggestions = len(df_model)
        accepted = len(df_model[df_model['status'] == 'ACCEPTED'])
        rejected = len(df_model[df_model['status'] == 'DISMISSED'])
        acceptance_rate = accepted / total_suggestions if total_suggestions > 0 else 0
        rejection_rate = rejected / total_suggestions if total_suggestions > 0 else 0

        avg_latency = df_model["latency_ms"].mean() if "latency_ms" in df_model else None
        max_latency = df_model["latency_ms"].max() if "latency_ms" in df_model else None
        min_latency = df_model["latency_ms"].min() if "latency_ms" in df_model else None

        # Grab optional columns if available
        embedding_model = df_model['embedding_model'].iloc[0] if 'embedding_model' in df_model else "N/A"
        vector_store = df_model['vector_store'].iloc[0] if 'vector_store' in df_model else "N/A"

        # Start MLflow run
        with mlflow.start_run(run_name=f"{model_name}_run"):
            mlflow.log_param("model_name", model_name)
            mlflow.log_param("data_size", total_suggestions)
            mlflow.log_param("embedding_model", embedding_model)
            mlflow.log_param("vector_store", vector_store)

            mlflow.log_metric("acceptance_rate", acceptance_rate)
            mlflow.log_metric("rejection_rate", rejection_rate)
            mlflow.log_metric("accepted_count", accepted)
            mlflow.log_metric("rejected_count", rejected)
            mlflow.log_metric("total_count", total_suggestions)

            if avg_latency is not None:
                mlflow.log_metric("avg_latency_ms", avg_latency)
                mlflow.log_metric("min_latency_ms", min_latency)
                mlflow.log_metric("max_latency_ms", max_latency)

            # Log filtered data per model as artifact
            model_csv_path = f"logs/{model_name.replace('/', '_')}_log.csv"
            df_model.to_csv(model_csv_path, index=False)
            mlflow.log_artifact(model_csv_path)

        # Store for printing or reporting
        summary[model_name] = {
            "acceptance_rate": acceptance_rate,
            "rejection_rate": rejection_rate,
            "accepted_count": accepted,
            "rejected_count": rejected,
            "avg_latency_ms": avg_latency,
            "min_latency_ms": min_latency,
            "max_latency_ms": max_latency
        }

    return summary



# Example usage
if __name__ == "__main__":
    args = argparse.ArgumentParser()
    args.add_argument("--config", default="params.yaml")
    parsed_args = args.parse_args()

    results = log_acceptance_metrics_per_model(config_path=parsed_args.config)

    print("\n📊 Model-wise Acceptance Metrics:")
    for model, metrics in results.items():
        print(f"\n🔹 Model: {model}")
        print(f"  - Acceptance Rate: {metrics['acceptance_rate']:.2%}")
        print(f"  - Rejection Rate: {metrics['rejection_rate']:.2%}")
        print(f"  - Avg Latency: {metrics['avg_latency_ms']:.2f} ms")