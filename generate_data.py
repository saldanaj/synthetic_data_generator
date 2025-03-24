import yaml
import pandas as pd
import uuid
import random
from faker import Faker
from datetime import datetime
import argparse
import os

# Initialize the Faker library for generating fake data
fake = Faker()

# Define where to store generated data files
DATA_DIR = "./synthetic_data"
os.makedirs(DATA_DIR, exist_ok=True)

# Load table schema from a YAML file
def load_schema(schema_file):
    with open(schema_file, 'r') as file:
        return yaml.safe_load(file)

# Function to generate a single field's value based on its type
def generate_field(field_def):
    field_type = field_def["type"]
    if field_type == "uuid":
        return str(uuid.uuid4())
    elif field_type == "mrn":
        return fake.unique.bothify(text="??####")
    elif field_type == "first_name":
        return fake.first_name()
    elif field_type == "last_name":
        return fake.last_name()
    elif field_type == "email":
        return fake.email()
    elif field_type == "datetime":
        return datetime.now()
    elif field_type == "date_of_birth":
        return fake.date_of_birth(minimum_age=0, maximum_age=100)
    elif field_type == "choice":
        return random.choice(field_def["values"])
    else:
        # Default to a fake word if unknown type
        return fake.word()

# Generate a single row of synthetic data using the schema
def generate_row(columns):
    return {col["name"]: generate_field(col) for col in columns}

# Update existing data and add new rows to simulate changes on Day > 1
def evolve_data(df, columns, new_count):
    df = df.copy()

    # Select 20% of rows to update
    updated_indices = df.sample(frac=0.2).index

    for idx in updated_indices:
        for col in columns:
            # Only update fields that make sense to change
            if col['type'] in ['first_name', 'last_name', 'email', 'choice'] and random.random() < 0.5:
                df.at[idx, col['name']] = generate_field(col)
        # Always update the last modified timestamp
        df.at[idx, 'LAST_UPDATED'] = datetime.now()

    # Generate new patients to simulate growth
    new_rows = [generate_row(columns) for _ in range(new_count)]
    return pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)

# Entry point for the script
def main():
    parser = argparse.ArgumentParser(description="YAML-based Synthetic Data Generator")
    parser.add_argument("--day", type=int, required=True, help="Day number to generate data for (starting from 1)")
    parser.add_argument("--schema", type=str, required=True, help="Path to YAML schema file")
    args = parser.parse_args()

    # Load the YAML schema
    schema = load_schema(args.schema)
    table = schema["table"]
    columns = schema["columns"]
    initial_rows = schema.get("rows", 100)

    # File paths for current and previous days
    file_day_prev = f"{DATA_DIR}/{table}_day{args.day - 1}.csv"
    file_day = f"{DATA_DIR}/{table}_day{args.day}.csv"

    # For Day 1, generate from scratch
    if args.day == 1 or not os.path.exists(file_day_prev):
        df = pd.DataFrame([generate_row(columns) for _ in range(initial_rows)])
    else:
        # For Day > 1, load previous data and simulate updates
        df_prev = pd.read_csv(file_day_prev, parse_dates=["DATE_CREATED", "LAST_UPDATED"])
        df = evolve_data(df_prev, columns, new_count=20)

    # Save generated data to CSV
    df.to_csv(file_day, index=False)
    print(f"✅ Data saved: {file_day}")

# Run the script when executed from the command line
if __name__ == "__main__":
    main()
