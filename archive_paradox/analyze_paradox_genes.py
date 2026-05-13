import sqlite3
import os
import pandas as pd
import matplotlib.pyplot as plt

# Paths
DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'genome.db')
RESULTS_DIR = os.path.join(os.path.dirname(__file__), 'results')

def ensure_results_dir():
    if not os.path.exists(RESULTS_DIR):
        os.makedirs(RESULTS_DIR)

def get_paradox_genes(conn):
    """
    Find highly constrained genes (LOEUF < 0.35 or pLI > 0.9)
    that have NO pathogenic variants in ClinVar and NO GWAS traits.
    """
    query = """
    SELECT 
        g.symbol, 
        g.name, 
        gc.loeuf, 
        gc.pli,
        gc.transcript
    FROM genes g
    JOIN gene_constraints gc ON g.gene_id = gc.gene_id
    LEFT JOIN clinvar_gene_summary cv ON g.gene_id = cv.gene_id
    LEFT JOIN gene_traits gt ON g.gene_id = gt.gene_id
    WHERE 
        (gc.loeuf < 0.35 OR gc.pli > 0.9)
        AND (cv.pathogenic_alleles IS NULL OR cv.pathogenic_alleles = 0)
        AND gt.gene_id IS NULL
    GROUP BY g.gene_id
    ORDER BY gc.loeuf ASC
    """
    return pd.read_sql_query(query, conn)

def get_disease_genes(conn):
    """
    For comparison: Find highly constrained genes that DO have 
    known diseases (ClinVar pathogenic hits) or GWAS traits.
    """
    query = """
    SELECT 
        g.symbol, 
        gc.loeuf, 
        gc.pli
    FROM genes g
    JOIN gene_constraints gc ON g.gene_id = gc.gene_id
    LEFT JOIN clinvar_gene_summary cv ON g.gene_id = cv.gene_id
    LEFT JOIN gene_traits gt ON g.gene_id = gt.gene_id
    WHERE 
        (gc.loeuf < 0.35 OR gc.pli > 0.9)
        AND (cv.pathogenic_alleles > 0 OR gt.gene_id IS NOT NULL)
    GROUP BY g.gene_id
    """
    return pd.read_sql_query(query, conn)

def run_analysis():
    ensure_results_dir()
    print("Connecting to database...")
    
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        return
        
    conn = sqlite3.connect(DB_PATH)
    
    # 1. Fetch data
    print("Fetching Paradox Genes (Highly Constrained, No Disease)...")
    paradox_df = get_paradox_genes(conn)
    print(f"Found {len(paradox_df)} Paradox Genes.")
    
    print("Fetching Disease-Associated Constrained Genes (For comparison)...")
    disease_df = get_disease_genes(conn)
    print(f"Found {len(disease_df)} Known Disease/Trait Constrained Genes.")
    
    # 2. Export to CSV
    csv_path = os.path.join(RESULTS_DIR, 'paradox_genes.csv')
    paradox_df.to_csv(csv_path, index=False)
    print(f"\nExported Paradox Genes list to: {csv_path}")
    
    # 3. Plotting
    print("Generating LOEUF Distribution Plot...")
    plt.figure(figsize=(10, 6))
    
    # Histogram comparing the two groups
    plt.hist(disease_df['loeuf'].dropna(), bins=30, alpha=0.5, label='Known Disease/Trait Genes', color='blue', density=True)
    plt.hist(paradox_df['loeuf'].dropna(), bins=30, alpha=0.5, label='Paradox Genes (No Disease)', color='red', density=True)
    
    plt.axvline(x=0.35, color='black', linestyle='--', label='Severe Constraint Threshold (0.35)')
    
    plt.title('Distribution of LOEUF Constraint Scores')
    plt.xlabel('LOEUF (Lower means more intolerant to mutation)')
    plt.ylabel('Density')
    plt.legend(loc='upper right')
    plt.grid(axis='y', alpha=0.3)
    
    plot_path = os.path.join(RESULTS_DIR, 'loeuf_distribution.png')
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Exported plot to: {plot_path}")
    conn.close()
    print("\nAnalysis complete! You can now review the CSV and PNG files in the 'results' folder.")

if __name__ == "__main__":
    run_analysis()
