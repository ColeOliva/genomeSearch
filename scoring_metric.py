import sqlite3
import os
import pandas as pd
import numpy as np

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
DB_PATH = os.path.join(DATA_DIR, 'genome.db')
RESULTS_DIR = os.path.join(os.path.dirname(__file__), 'results')

def build_pleiotropy_index():
    print("Building Normalized Pleiotropy Index (NPI)...")
    
    # 1. Load the semantic dataset we generated
    semantic_csv = os.path.join(RESULTS_DIR, 'semantic_pleiotropy_hubs.csv')
    if not os.path.exists(semantic_csv):
        print(f"Error: {semantic_csv} not found.")
        return
        
    df_hubs = pd.read_csv(semantic_csv)
    
    # 2. Extract constraint data from database to capture evolutionary constraint
    conn = sqlite3.connect(DB_PATH)
    query = """
    SELECT 
        gene_symbol as symbol,
        pli,
        loeuf,
        oe_lof
    FROM gene_constraints
    """
    df_constraints = pd.read_sql_query(query, conn)
    conn.close()
    
    # 3. Merge datasets
    # Merge constraints with our hub data
    df = pd.merge(df_hubs, df_constraints, on='symbol', how='left')
    
    # 4. Formulate the Pleiotropy Index
    # We want to reward:
    #   - High unique domain count (max 8) -> Heavily weighted
    #   - Trait diversity (total raw traits) -> Log scaled to prevent publication bias inflation
    #   - Evolutionary constraint (pLI > 0.9 means highly essential/constrained) -> Bonus weight
    
    # Fill NAs in constraint data with median values to avoid dropping genes
    df['pli'] = df['pli'].fillna(df['pli'].median())
    
    # Log scale the raw traits to compress publication bias
    df['log_traits'] = np.log1p(df['total_raw_traits'])
    
    # Normalize components to 0-1 scale for fair indexing
    max_domains = 8.0 # We know this is our cap
    max_log_traits = df['log_traits'].max()
    
    # Score Formula:
    # 50% Domain Diversity + 25% Trait Volume (Log Scaled) + 25% Evolutionary Essentiality (pLI)
    df['domain_score'] = (df['unique_domain_count'] / max_domains) * 50
    df['trait_score'] = (df['log_traits'] / max_log_traits) * 25
    df['constraint_score'] = df['pli'] * 25 # pLI is already 0 to 1
    
    # Final Index (Out of 100)
    df['Pleiotropy_Index'] = df['domain_score'] + df['trait_score'] + df['constraint_score']
    
    # Clean up and sort
    df = df.sort_values('Pleiotropy_Index', ascending=False)
    
    # Flag our known "Mega Hubs" to see if our novel ones compete
    mega_hubs = ['APOE', 'ABO']
    df['Is_Novel'] = ~df['symbol'].isin(mega_hubs) & ~df['symbol'].str.startswith('HLA-')

    # Save
    out_path = os.path.join(RESULTS_DIR, 'normalized_pleiotropy_index.csv')
    df.to_csv(out_path, index=False)
    
    print("\n--- TOP 10 OVERALL GENES BY PLEIOTROPY INDEX ---")
    columns_to_show = ['symbol', 'Pleiotropy_Index', 'unique_domain_count', 'total_raw_traits', 'pli', 'Is_Novel']
    print(df.head(10)[columns_to_show].to_string(index=False))
    
    print("\n--- TOP 10 NOVEL GENES BY PLEIOTROPY INDEX ---")
    novel_df = df[df['Is_Novel']]
    print(novel_df.head(10)[columns_to_show].to_string(index=False))

    print(f"\nSaved full index to {out_path}")

if __name__ == "__main__":
    build_pleiotropy_index()
