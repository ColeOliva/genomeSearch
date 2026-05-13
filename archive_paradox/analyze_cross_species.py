import sqlite3
import os
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
DB_PATH = os.path.join(DATA_DIR, 'genome.db')
RESULTS_DIR = os.path.join(os.path.dirname(__file__), 'results')

def analyze_cross_species():
    conn = sqlite3.connect(DB_PATH)
    
    # Check what happens to the 36 Paradox Genes when they are knocked out in mice!
    query = """
    SELECT 
        g.symbol, 
        gc.loeuf, 
        gc.pli,
        mp.mouse_symbol,
        mpt.term_name AS mouse_phenotype
    FROM genes g
    JOIN gene_constraints gc ON g.gene_id = gc.gene_id
    LEFT JOIN clinvar_gene_summary cv ON g.gene_id = cv.gene_id
    LEFT JOIN gene_traits gt ON g.gene_id = gt.gene_id
    JOIN mouse_phenotypes mp ON g.gene_id = mp.gene_id
    JOIN mouse_phenotype_terms mpt ON mp.mp_id = mpt.mp_id
    WHERE 
        (gc.loeuf < 0.35 OR gc.pli > 0.9)
        AND (cv.pathogenic_alleles IS NULL OR cv.pathogenic_alleles = 0)
        AND gt.gene_id IS NULL
    ORDER BY gc.loeuf ASC, g.symbol
    """
    
    df = pd.read_sql_query(query, conn)
    
    csv_path = os.path.join(RESULTS_DIR, 'paradox_genes_mouse_phenotypes.csv')
    df.to_csv(csv_path, index=False)
    
    print(f"Discovered {len(df)} mouse phenotypes across your 'Dark Matter' genes!")
    print(f"Exported to {csv_path}")
    
    conn.close()

if __name__ == '__main__':
    analyze_cross_species()