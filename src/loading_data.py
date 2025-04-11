from datasets import load_dataset
import argparse
import yaml

def read_param(config_path):
    with open(config_path) as yaml_file:
        config = yaml.safe_load(yaml_file)
        return config

def get_data(config_path):
    config = read_param(config_path)
    dataset = load_dataset(config["data"]["source"], split="train")
    df = dataset.to_pandas()
    data_path = config["data"]["loc"]
    df.to_csv(data_path, index=False)
    print(f"Dataset saved at {data_path}")
    return df

if __name__ == "__main__":
    args = argparse.ArgumentParser()
    args.add_argument("--config",default="params.yaml")
    parsed_args = args.parse_args()
    data = get_data(config_path=parsed_args.config)