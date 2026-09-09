import os
import requests
import pandas as pd
import time

def query_qlever(sparql_query, endpoint="https://qlever.cs.uni-freiburg.de/api/dbpedia"):
    
    try:
        response = requests.post(
            endpoint,
            data={'query': sparql_query},
            headers={'Accept': 'application/sparql-results+json'}
        )
        response.raise_for_status()
        
        results = response.json()
        bindings = results['results']['bindings']
        
        # convert to dataframe
        rows = [{k: v['value'] for k, v in b.items()} for b in bindings]
        return pd.DataFrame(rows)

    except requests.exceptions.RequestException as e:
        print(f"Error querying QLever: {e}")
        return pd.DataFrame()  # return empty DataFrame on error

def get_sameAs_entities():

    df = pd.read_csv('data/filtered_entity_ids.csv')

    if os.path.exists(f'results/last_id_entity_batch_to_qlever.txt'):
        with open(f'results/last_id_entity_batch_to_qlever.txt', 'r') as f:

            last_id = f.read().strip()

        if last_id == '':
            last_id = 0
    else:
        last_id = 0

    if last_id:
        
        last_id_idx = df[df['entity_id'] == int(last_id)].index + 1
        if not last_id_idx.empty:
            df = df.iloc[last_id_idx[0]:, :].copy()
        else:
            last_id = 0
    else:
        last_id = 0

    df['wikidata_uri'] = df['entity_id'].apply(lambda x: f'<http://www.wikidata.org/entity/Q{x}>')

    wikidata_ids = df['wikidata_uri'].tolist()

    batch_size = 100000

    for i in range(last_id, len(wikidata_ids), batch_size):

        batch_ids = wikidata_ids[i:i+batch_size]

        print(f"Processing batch {i//batch_size + 1} with {len(batch_ids)} Wikidata IDs")

        values_str = ' '.join(batch_ids)
        query = f"""
            PREFIX owl: <http://www.w3.org/2002/07/owl#>
            
            SELECT ?dbpedia ?wikidata WHERE {{
                VALUES ?wikidata {{ {values_str} }}
                ?dbpedia owl:sameAs ?wikidata .
            }}
        """

        # ------

        df_sameAs = query_qlever(query)

        df_sameAs['wikidata_id'] = df_sameAs['wikidata'].str.replace('http://www.wikidata.org/entity/Q', '').str.replace('<', '').str.replace('>', '').astype(int)

        df_sameAs['dbpedia_id'] = df_sameAs['dbpedia'].str.replace('http://dbpedia.org/resource/', '').str.replace('<', '').str.replace('>', '')

        df_slice = df.iloc[i:i+batch_size, :].copy()
        df_merge = df_slice.merge(df_sameAs, how='left', left_on='entity_id', right_on='wikidata_id')

        df_merge[['entity_id', "entity_label","entity_type","type_numeric_id", 'dbpedia_id', 'dbpedia', 'wikidata']].to_csv(f'results/sameAs_links.csv', index=False, mode='a', header=False)

        last_id = df_merge.iloc[-1]['entity_id']  # get the last Wikidata id because the query returns those found, but not necessarily the last one I asked for

        print(f"Finished processing batch {i//batch_size + 1}. Last Wikidata ID: {last_id}")

        with open(f'results/last_id_entity_batch_to_qlever.txt', 'w') as f:
            f.write(str(last_id))


        time.sleep(50) 
    
    
if __name__ == "__main__":
    get_sameAs_entities()