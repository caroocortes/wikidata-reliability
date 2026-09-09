import json
import yaml

import pandas as pd
from sqlalchemy import create_engine

from os.path import abspath, dirname

CONSTRAINTS = {
    "range_constraint": ['property_id', 'minimum_value', 'maximum_value', 'constraint_status_label'],
    # "required_qualifier_constraint",
    # "single_value_constraint",
    "integer_constraint": ['property_id', 'constraint_status_label'],
}

if __name__ == "__main__":

    current_script_file = abspath(__file__)
    root_folder = dirname(dirname(current_script_file))
    
    with open(f"{root_folder}/set_up.yaml") as stream:
        try:
            config = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)

    with open(f"{root_folder}/{config['db_config_path']}") as f:
        db_config = json.load(f)

    for cstr, columns in CONSTRAINTS.items():
        csv_file_path = f'{root_folder}/property_constraints/{cstr}.csv'
        df = pd.read_csv(csv_file_path, usecols=columns)

        engine = create_engine(f"postgresql+psycopg2://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}")

        df.to_sql(cstr,
                con=engine,
                index=False,
                if_exists='replace')
    
