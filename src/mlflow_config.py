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