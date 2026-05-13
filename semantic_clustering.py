import sqlite3
import os
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
DB_PATH = os.path.join(DATA_DIR, 'genome.db')
RESULTS_DIR = os.path.join(os.path.dirname(__file__), 'results')

# Define semantic categories based on common GWAS keywords
DOMAIN_KEYWORDS = {
    'Cardiovascular': ['blood pressure', 'heart', 'cardiac', 'stroke', 'artery', 'myocardial', 'atherosclerosis', 'qt interval', 'ventricular', 'atrial'],
    'Metabolic_and_Lipid': ['cholesterol', 'triglyceride', 'lipid', 'obesity', 'bmi', 'body mass index', 'diabetes', 'insulin', 'glucose', 'metabolic', 'adipose', 'hdl', 'ldl', 'hba1c'],
    'Neurological_and_Psychiatric': ['schizophrenia', 'alzheimer', 'depression', 'cognitive', 'intelligence', 'brain', 'neuro', 'parkinson', 'bipolar', 'autism', 'sleep', 'epilepsy', 'anxiety', 'asmat'],
    'Immune_and_Autoimmune': ['asthma', 'arthritis', 'lupus', 'crohn', 'celiac', 'immune', 'allergy', 'multiple sclerosis', 'psoriasis', 'ibd', 'colitis', 'eosinophil', 'neutrophil', 'lymphocyte', 'white blood cell'],
    'Cancer_and_Neoplasm': ['cancer', 'carcinoma', 'melanoma', 'leukemia', 'lymphoma', 'neoplasm', 'tumor', 'sarcoma', 'adenoma', 'glioma'],
    'Hematological': ['erythrocyte', 'hemoglobin', 'platelet', 'blood count', 'corpuscular', 'hematocrit', 'red blood cell', 'mchc', 'reticulocyte'],
    'Anthropometric_and_Skeletal': ['height', 'weight', 'waist', 'hip', 'bone mineral', 'osteoporosis', 'fracture', 'balding', 'freckles', 'hair', 'pigmentation', 'heel'],
    'Hepatic_and_Renal': ['glomerular', 'creatinine', 'kidney', 'liver', 'bilirubin', 'urinary', 'egfr', 'cirrhosis', 'hepatic', 'renal']
}

def categorize_trait(trait_name):
    """Assigns a trait to a medical domain based on keyword matching."""
    if not trait_name:
        return 'Uncategorized'
        
    trait_lower = str(trait_name).lower()
    matched_domains = set()
    
    for domain, keywords in DOMAIN_KEYWORDS.items():
        if any(keyword in trait_lower for keyword in keywords):
            matched_domains.add(domain)
            
    if not matched_domains:
        return 'Other'
        
    # If it matches multiple (e.g. "cholesterol in cardiovascular disease"), 
    # we return a joined string or just count them all. 
    # Returning the first matched for simplicity, or expanding them later.
    # To be perfectly rigorous, we will return a comma-separated list of domains.
    return ",".join(list(matched_domains))

def run_semantic_clustering():
    print("Connecting to database...")
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        return
        
    conn = sqlite3.connect(DB_PATH)
    
    # Extract gene symbols and traits
    query = """
    SELECT 
        g.symbol,
        gt.reported_trait,
        gt.efo_trait
    FROM genes g
    JOIN gene_traits gt ON g.gene_id = gt.gene_id
    """
    print("Extracting associations...")
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if df.empty:
        print("No genes found with associations.")
        return

    print(f"Loaded {len(df)} trait associations. Categorizing by medical domain...")
    
    # Use reported_trait or efo_trait for categorization
    df['combined_trait'] = df['reported_trait'] + " " + df['efo_trait'].fillna('')
    
    # Apply categorization
    df['domains'] = df['combined_trait'].apply(categorize_trait)
    
    # Explode the comma-separated domains so each domain is its own row
    # e.g., "Metabolic,Cardiovascular" -> two rows
    # Ignore 'Other' and 'Uncategorized' to focus on strict cross-domain pleiotropy
    df_domains = df.assign(domain=df['domains'].str.split(',')).explode('domain')
    df_domains = df_domains[~df_domains['domain'].isin(['Other', 'Uncategorized'])]
    
    if df_domains.empty:
        print("No traits matched the categorization keywords.")
        return

    # Count unique domains per gene
    domain_counts = df_domains.groupby('symbol')['domain'].nunique().reset_index()
    domain_counts.columns = ['symbol', 'unique_domain_count']
    
    # Get the list of domains for each gene
    domain_lists = df_domains.groupby('symbol')['domain'].unique().reset_index()
    domain_lists['domain_list'] = domain_lists['domain'].apply(lambda x: ", ".join(x))
    
    # Count total distinct raw traits per gene (from original DataFrame)
    raw_trait_counts = df.groupby('symbol')['reported_trait'].nunique().reset_index()
    raw_trait_counts.columns = ['symbol', 'total_raw_traits']
    
    # Merge them together
    final_df = pd.merge(domain_counts, domain_lists[['symbol', 'domain_list']], on='symbol')
    final_df = pd.merge(final_df, raw_trait_counts, on='symbol')
    
    # Sort by Most Unique Domains, then by Total Raw Traits
    final_df = final_df.sort_values(by=['unique_domain_count', 'total_raw_traits'], ascending=[False, False])
    
    # Save the output
    if not os.path.exists(RESULTS_DIR):
        os.makedirs(RESULTS_DIR)
    csv_path = os.path.join(RESULTS_DIR, 'semantic_pleiotropy_hubs.csv')
    final_df.to_csv(csv_path, index=False)
    
    print(f"\nExported {len(final_df)} categorized genes to {csv_path}\n")
    print("--- Top 15 True Cross-Domain Pleiotropic Hubs ---")
    
    # Display the top 15 true hubs (Genes touching 6, 7, or 8 entirely distinct bodily systems)
    for index, row in final_df.head(15).iterrows():
        print(f"\nGene: {row['symbol']} | Unique Domains: {row['unique_domain_count']} / 8")
        print(f"Total Raw Traits: {row['total_raw_traits']}")
        print(f"Systems Involved: {row['domain_list']}")

if __name__ == '__main__':
    run_semantic_clustering()
