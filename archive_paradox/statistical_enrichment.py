import sqlite3
import os
import pandas as pd
from scipy.stats import fisher_exact

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
DB_PATH = os.path.join(DATA_DIR, 'genome.db')
RESULTS_DIR = os.path.join(os.path.dirname(__file__), 'results')

def perform_fisher_sweep():
    print("Connecting to database...")
    conn = sqlite3.connect(DB_PATH)
    
    # We want ALL phenotype terms for ALL constrained genes.
    # By using INNER JOIN on mouse_phenotypes, we completely exclude genes that have no mouse data from the denominator.
    query = """
    SELECT 
        g.gene_id,
        g.symbol,
        CASE WHEN (cv.pathogenic_alleles IS NULL OR cv.pathogenic_alleles = 0) AND gt.gene_id IS NULL 
             THEN 1 ELSE 0 END as is_paradox,
        mpt.term_name
    FROM genes g
    JOIN gene_constraints gc ON g.gene_id = gc.gene_id
    JOIN mouse_phenotypes mp ON g.gene_id = mp.gene_id
    JOIN mouse_phenotype_terms mpt ON mp.mp_id = mpt.mp_id
    LEFT JOIN clinvar_gene_summary cv ON g.gene_id = cv.gene_id
    LEFT JOIN gene_traits gt ON g.gene_id = gt.gene_id
    WHERE 
        (gc.loeuf < 0.35 OR gc.pli > 0.9)
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()

    if df.empty:
        print("No genes found with mouse data.")
        return

    # Total genes in each group (that have mouse data at all)
    genes_df = df[['gene_id', 'is_paradox']].drop_duplicates()
    n_paradox = genes_df[genes_df['is_paradox'] == 1].shape[0]
    n_baseline = genes_df[genes_df['is_paradox'] == 0].shape[0]
    
    print(f"Total Paradox genes with known mouse data: {n_paradox} (Filtered out unstudied genes)")
    print(f"Total Baseline constrained genes with known mouse data: {n_baseline}")
    
    if n_paradox == 0 or n_baseline == 0:
        print("Not enough data in one of the groups to run statistics.")
        return

    results = []
    
    # We test every phenotype term that exists in the Paradox group to find what stands out
    paradox_terms = df[df['is_paradox'] == 1]['term_name'].unique()
    
    for term in paradox_terms:
        # Get unique genes with this explicit term
        genes_with_term = df[df['term_name'] == term][['gene_id', 'is_paradox']].drop_duplicates()
        
        paradox_w_term = genes_with_term[genes_with_term['is_paradox'] == 1].shape[0]
        baseline_w_term = genes_with_term[genes_with_term['is_paradox'] == 0].shape[0]
        
        paradox_wo_term = n_paradox - paradox_w_term
        baseline_wo_term = n_baseline - baseline_w_term
        
        table = [[paradox_w_term, paradox_wo_term], 
                 [baseline_w_term, baseline_wo_term]]
                 
        # Run test (Alternative = 'greater' meaning Enrichment in Paradox)
        odds_ratio, p_value = fisher_exact(table, alternative='greater')
        
        paradox_rate = (paradox_w_term / n_paradox) * 100
        baseline_rate = (baseline_w_term / n_baseline) * 100
        
        results.append({
            'Phenotype': term,
            'Paradox_Rate_%': round(paradox_rate, 1),
            'Baseline_Rate_%': round(baseline_rate, 1),
            'Odds_Ratio': round(odds_ratio, 2),
            'P_Value': p_value
        })
        
    results_df = pd.DataFrame(results)
    
    # Sort by how significant the enrichment is
    results_df = results_df.sort_values('P_Value', ascending=True)
    
    print("\n--- Top Enriched Phenotypes in Paradox Genes ---")
    print(results_df.head(15).to_string(index=False))
    
    csv_path = os.path.join(RESULTS_DIR, 'phenotype_enrichment_results.csv')
    results_df.to_csv(csv_path, index=False)
    print(f"\nFull sweep results exported to: {csv_path}")

if __name__ == '__main__':
    perform_fisher_sweep()
