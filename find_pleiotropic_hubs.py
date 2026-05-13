import sqlite3
import os
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
DB_PATH = os.path.join(DATA_DIR, 'genome.db')
RESULTS_DIR = os.path.join(os.path.dirname(__file__), 'results')

def find_pleiotropic_genes():
    print("Connecting to database...")
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        return
        
    conn = sqlite3.connect(DB_PATH)
    
    # Query to find genes with the most distinct traits in the GWAS catalog
    # We use GROUP_CONCAT to get a readable list of the traits for manual review
    query = """
    SELECT 
        g.symbol,
        COUNT(DISTINCT gt.reported_trait) as distinct_trait_count,
        GROUP_CONCAT(DISTINCT gt.reported_trait) as trait_list
    FROM genes g
    JOIN gene_traits gt ON g.gene_id = gt.gene_id
    GROUP BY g.gene_id
    HAVING distinct_trait_count > 10
    ORDER BY distinct_trait_count DESC
    """
    
    print("Executing query to find highly pleiotropic genes...")
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if df.empty:
        print("No genes found with multiple associations.")
        return
        
    # Ensure results directory exists
    if not os.path.exists(RESULTS_DIR):
        os.makedirs(RESULTS_DIR)
        
    # Export full dataset for reference
    csv_path = os.path.join(RESULTS_DIR, 'pleiotropic_hubs.csv')
    df.to_csv(csv_path, index=False)
    
    print(f"\nFound {len(df)} genes associated with >10 distinct traits.")
    print(f"Exported full list to: {csv_path}\n")
    
    print("--- Top 10 Most Pleiotropic Genes ---")
    for index, row in df.head(10).iterrows():
        print(f"\n{row['symbol']} (Traits: {row['distinct_trait_count']})")
        # Truncate the trait list for console output so it doesn't flood the terminal
        traits = row['trait_list'].split(',')
        display_traits = ", ".join(traits[:5])
        if len(traits) > 5:
            display_traits += f", ... (+ {len(traits)-5} more)"
        print(f"Example Traits: {display_traits}")

if __name__ == '__main__':
    find_pleiotropic_genes()