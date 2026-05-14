import os
import sqlite3
import pandas as pd
import numpy as np

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
DB_PATH = os.path.join(DATA_DIR, 'genome.db')
RESULTS_DIR = os.path.join(os.path.dirname(__file__), 'results')

def get_bridge_enrichment():
    print("Running Bridge-Specific GO Enrichment...")
    npi_csv = os.path.join(RESULTS_DIR, 'normalized_pleiotropy_index.csv')
    if not os.path.exists(npi_csv):
        print(f"Error: {npi_csv} not found.")
        return

    df = pd.read_csv(npi_csv)
    
    # Exclude mega-hubs to focus on specific mechanisms
    df = df[df['Is_Novel'] == True]

    def has_bridge(domain_list_str, required_domains):
        if pd.isna(domain_list_str): return False
        return all(d in domain_list_str for d in required_domains)

    # To find the unique mechanism for these specific bridges, we must exclude the global
    # "8-domain" master hubs. Otherwise, the top 150 genes for both lists will just be 
    # the exact same top 8-domain genes! We restrict to genes that have EXACTLY 3 domains.
    df_specific = df[df['unique_domain_count'] <= 4]

    # Define Bridge A: Brain - Heart - Immune
    bridge_a = ['Neurological_and_Psychiatric', 'Cardiovascular', 'Immune_and_Autoimmune']
    bridge_a_genes = df_specific[df_specific['domain_list'].apply(lambda x: has_bridge(x, bridge_a))]
    
    # Define Bridge B: Metabolism - Cancer - Brain
    bridge_b = ['Metabolic_and_Lipid', 'Cancer_and_Neoplasm', 'Neurological_and_Psychiatric']
    bridge_b_genes = df_specific[df_specific['domain_list'].apply(lambda x: has_bridge(x, bridge_b))]

    # Take the top 150 NPI-scored genes for each bridge to keep the signal concentrated
    top_a = bridge_a_genes.head(150)['symbol'].tolist()
    top_b = bridge_b_genes.head(150)['symbol'].tolist()

    conn = sqlite3.connect(DB_PATH)
    query = '''
    SELECT g.symbol, go.go_term, go.category 
    FROM gene_go_terms go
    JOIN genes g ON go.gene_id = g.gene_id
    WHERE go.category = 'Process'
    '''
    go_df = pd.read_sql_query(query, conn)
    conn.close()

    bg_genes = go_df['symbol'].unique()
    M = len(bg_genes)
    term_to_genes = go_df.groupby('go_term')['symbol'].apply(lambda x: set(x.dropna())).to_dict()

    from scipy.stats import hypergeom

    def calculate_enrichment(target_genes, bridge_name):
        target_genes = set(target_genes).intersection(set(bg_genes))
        N = len(target_genes)
        records = []
        
        for term, geneset in term_to_genes.items():
            n = len(geneset)
            # Filter out overly generic terms (e.g. >2000 background genes) to force specificity
            if n > 2000 or n < 5: 
                continue
                
            k = len(geneset.intersection(target_genes))
            if k < 3: # Require at least 3 genes sharing the term
                continue
                
            pval = hypergeom.sf(k-1, M, n, N)
            
            # Calculate Fold Enrichment: (k/N) / (n/M)
            fold_enrichment = (k / N) / (n / M) if (n / M) > 0 else 0
            
            records.append((term, n, k, fold_enrichment, pval))

        res_df = pd.DataFrame(records, columns=['go_term', 'bg_count', 'top_count', 'fold_enrichment', 'p_value'])
        res_df = res_df.sort_values(by=['p_value', 'fold_enrichment'], ascending=[True, False])
        return res_df

    print(f"\n--- ENRICHMENT FOR BRIDGE A (Brain-Heart-Immune) ---")
    res_a = calculate_enrichment(top_a, "Bridge A")
    for idx, row in res_a.head(8).iterrows():
        print(f"[{row['fold_enrichment']:.1f}x Enriched] {row['go_term']} (p={row['p_value']:.2e})")

    print(f"\n--- ENRICHMENT FOR BRIDGE B (Metabolism-Cancer-Brain) ---")
    res_b = calculate_enrichment(top_b, "Bridge B")
    for idx, row in res_b.head(8).iterrows():
        print(f"[{row['fold_enrichment']:.1f}x Enriched] {row['go_term']} (p={row['p_value']:.2e})")

if __name__ == '__main__':
    get_bridge_enrichment()