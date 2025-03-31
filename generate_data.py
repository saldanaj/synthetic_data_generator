import yaml
import pandas as pd
import uuid
import random
from faker import Faker
from datetime import datetime
import argparse
import os

# Initialize Faker
fake = Faker()

# Directory where synthetic data will be stored
DATA_DIR = "./synthetic_data"
os.makedirs(DATA_DIR, exist_ok=True)

# Load YAML schema (your format)
def load_schema(schema_file):
    with open(schema_file, 'r') as file:
        return yaml.safe_load(file)

# Map schema data types to fake data generators
def generate_field(data_type, column_name=None):
    if column_name == "PATIENT_ID":
        return str(uuid.uuid4())
    if column_name == "MRN":
        return fake.unique.bothify(text="??####")

    dtype = data_type.lower()
    if dtype == "string":
        if "first_name" in column_name.lower():
            return fake.first_name()
        elif "last_name" in column_name.lower():
            return fake.last_name()
        elif "email" in column_name.lower():
            return fake.email()
        elif "phone" in column_name.lower():
            return fake.phone_number()
        elif "address" in column_name.lower():
            return fake.street_address()
        elif "city" in column_name.lower():
            return fake.city()
        elif "state" in column_name.lower():
            return fake.state_abbr()
        elif "zip" in column_name.lower():
            return fake.zipcode()
        elif "sex" in column_name.lower():
            return random.choice(["Male", "Female"])
        elif "gender" in column_name.lower():
            return random.choice(["Male", "Female", "Non-binary", "Other"])
        elif "race" in column_name.lower():
            return random.choice(["White", "Black", "Asian", "Hispanic", "Other"])
        elif "ethnicity" in column_name.lower():
            return random.choice(["Not Hispanic or Latino", "Hispanic or Latino"])
        elif "language" in column_name.lower():
            return random.choice(["English", "Spanish", "Creole", "Chinese", "Other"])
        else:
            return fake.word()
    elif dtype == "boolean":
        return random.choice([True, False])
    elif dtype == "datetime":
        return datetime.now()
    elif dtype == "date":
        return fake.date_of_birth(minimum_age=0, maximum_age=100)
    else:
        return fake.word()  # Default fallback

# Create a row of synthetic data
def generate_row(schema):
    return {
        col["column_name"]: generate_field(col["data_type"], col["column_name"])
        for col in schema
    }

# Evolve the dataset for Day > 1
def evolve_data(df, schema, new_count):
    df = df.copy()
    update_cols = [col for col in schema if col["data_type"].lower() in ["string", "boolean"]]

    # Update 20% of existing records
    updated_indices = df.sample(frac=0.2).index
    for idx in updated_indices:
        for col in update_cols:
            col_name = col["column_name"]
            if random.random() < 0.5:
                df.at[idx, col_name] = generate_field(col["data_type"], col_name)
        df.at[idx, "LAST_UPDATED"] = datetime.now()

    # Generate new rows
    new_rows = [generate_row(schema) for _ in range(new_count)]
    return pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)

# Script entry point
def main():
    parser = argparse.ArgumentParser(description="YAML-based Synthetic Data Generator")
    parser.add_argument("--day", type=int, required=True, help="Day number to generate data for (starting from 1)")
    parser.add_argument("--schema", type=str, required=True, help="Path to YAML schema file")
    args = parser.parse_args()

    # Load schema and metadata
    meta = load_schema(args.schema)
    table_name = meta["table_name"]
    schema = meta["schema"]

    # File paths
    file_day_prev = f"{DATA_DIR}/{table_name}_day{args.day - 1}.csv"
    file_day = f"{DATA_DIR}/{table_name}_day{args.day}.csv"

    # Generate or evolve dataset
    if args.day == 1 or not os.path.exists(file_day_prev):
        df = pd.DataFrame([generate_row(schema) for _ in range(100)])
    else:
        df_prev = pd.read_csv(file_day_prev, parse_dates=["DATE_CREATED", "LAST_UPDATED"])
        df = evolve_data(df_prev, schema, new_count=20)

    # Save to CSV
    df.to_csv(file_day, index=False)
    print(f"Data saved to: {file_day}")

if __name__ == "__main__":
    main()
