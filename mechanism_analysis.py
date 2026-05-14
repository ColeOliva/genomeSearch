import sqlite3
import os
import pandas as pd
from collections import Counter

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
DB_PATH = os.path.join(DATA_DIR, 'genome.db')
RESULTS_DIR = os.path.join(os.path.dirname(__file__), 'results')

def run_mechanism_analysis():
    print("Connecting to database...")
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        return
        
    conn = sqlite3.connect(DB_PATH)
    
    # Top 5 novel robust genes spanning all 8 domains + exact 3 domains
    target_genes = ['FADS2', 'CFH', 'GCKR', 'ARHGEF3', 'SARM1']
    
    query = """
    SELECT 
        g.symbol,
        go.go_term,
        go.category
    FROM genes g
    JOIN gene_go_terms go ON g.gene_id = go.gene_id
    WHERE g.symbol IN ({})
    """.format(','.join(['?'] * len(target_genes)))
    
    df = pd.read_sql_query(query, conn, params=target_genes)
    conn.close()
    
    if df.empty:
        print("No GO terms found for the target genes.")
        return

    print(f"Found {len(df)} Gene Ontology (GO) terms for the target genes.")
    
    # Analyze by category (Process, Function, Component)
    # Most interested in Biological Process and Molecular Function
    df_mech = df[df['category'].isin(['Process', 'Function'])]
    
    # Count frequency of GO terms across these 5 genes
    # We want to see if any specific biological process is shared among these diverse genes
    term_counts = df_mech.groupby('go_term')['symbol'].nunique().reset_index()
    term_counts.columns = ['go_term', 'gene_count']
    
    # Get the list of genes sharing each term
    term_genes = df_mech.groupby('go_term')['symbol'].unique().reset_index()
    term_genes['shared_by'] = term_genes['symbol'].apply(lambda x: ", ".join(x))
    
    merged = pd.merge(term_counts, term_genes[['go_term', 'shared_by']], on='go_term')
    merged = merged.sort_values(by=['gene_count', 'go_term'], ascending=[False, True])
    
    print("\n--- SHARED BIOLOGICAL MECHANISMS AMONG NOVEL HUBS ---")
    print(f"Analyzing: {', '.join(target_genes)}")
    
    # Show terms shared by 2 or more of these 5 specific hubs
    shared_terms = merged[merged['gene_count'] >= 2]
    
    if shared_terms.empty:
        print("Surprisingly, no shared GO Process/Function terms among these 5 genes! Highly distinct pleiotropy.")
    else:
        for idx, row in shared_terms.head(15).iterrows():
            print(f"- {row['go_term']} (Shared by {row['gene_count']}/5: {row['shared_by']})")
    
    # Now output individual distinct mechanisms to see the individual flavor
    print("\n--- INDIVIDUAL HUB HIGHLIGHTS (Top Processes) ---")
    for gene in target_genes:
        gene_terms = df_mech[(df_mech['symbol'] == gene) & (df_mech['category'] == 'Process')]['go_term'].tolist()
        # Just show first 5 processes
        print(f"\n{gene}:")
        for t in gene_terms[:5]:
            print(f"  * {t}")

    # Save output
    out_path = os.path.join(RESULTS_DIR, 'mechanism_go_analysis.csv')
    merged.to_csv(out_path, index=False)
    print(f"\nExported mechanism overlap data to {out_path}")

if __name__ == '__main__':
    run_mechanism_analysis()
