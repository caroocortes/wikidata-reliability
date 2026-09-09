from sqlalchemy import create_engine
import pandas as pd
import argparse


if __name__ == "__main__":

    parser = argparse.ArgumentParser("table_name")
    parser.add_argument("table_name", help="Name of the table to query.", type=str)

    # parser = argparse.ArgumentParser("property_type")
    # parser.add_argument("property_type", help="Type of the property to query.", type=str)
    args = parser.parse_args()

    engine = create_engine("postgresql+psycopg2://postgres:postgres@10.130.31.43/:5433/wikidata_changes_new")
    
    batch_size = 1000000
    offset = 0
    while True:
        query = f'select * from {args.table_name} where num_value_changes > 20 LIMIT {batch_size} OFFSET {offset}'
        df = pd.read_sql_query(query, con=engine)
        if df.empty:
            break
        df.to_csv(f'data/{args.table_name}_{offset}.csv', index=False)
        offset += batch_size