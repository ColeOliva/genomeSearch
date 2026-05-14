import os
import pandas as pd

RESULTS_DIR = os.path.join(os.path.dirname(__file__), 'results')
CSV_PATH = os.path.join(RESULTS_DIR, 'semantic_pleiotropy_hubs.csv')

def analyze_domain_bridges():
    if not os.path.exists(CSV_PATH):
        print(f"Error: Could not find {CSV_PATH}. Run semantic_clustering.py first.")
        return

    df = pd.read_csv(CSV_PATH)
    
    # 1. Filter out the "Famous Mega-Hubs" to find novel targets
    famous_hubs = ['APOE', 'ABO']
    # Also exclude HLA genes as they are universally pleiotropic due to general immune function
    novel_df = df[
        (~df['symbol'].isin(famous_hubs)) & 
        (~df['symbol'].str.startswith('HLA-'))
    ].copy()

    # 2. Define specific disparate bridges that are biologically interesting
    # Bridge A: The "Brain-Body-Immune" Axis
    bridge_a_domains = ['Neurological_and_Psychiatric', 'Cardiovascular', 'Immune_and_Autoimmune']
    
    # Bridge B: The "Metabolic-Cancer-Brain" Axis
    bridge_b_domains = ['Metabolic_and_Lipid', 'Cancer_and_Neoplasm', 'Neurological_and_Psychiatric']

    def has_bridge(domain_list_str, required_domains):
        if pd.isna(domain_list_str):
            return False
        # Check if all required domains are in the string
        return all(d in domain_list_str for d in required_domains)

    print("--- UNDERRATED PLEIOTROPIC HUBS (Excluding APOE, ABO, HLA) ---")
    top_novel = novel_df.head(10)
    for idx, row in top_novel.iterrows():
        print(f"\nGene: {row['symbol']} (Domains: {row['unique_domain_count']}, Traits: {row['total_raw_traits']})")
        print(f"Systems: {row['domain_list']}")

    print("\n\n--- SPECIFIC BRIDGE ANALYSIS ---")
    
    # Analyze Bridge A
    bridge_a_genes = novel_df[novel_df['domain_list'].apply(lambda x: has_bridge(x, bridge_a_domains))]
    # Sort by total raw traits to find the most robust ones
    bridge_a_genes = bridge_a_genes.sort_values('total_raw_traits', ascending=False)
    
    print(f"\nBridge A: Brain-Body-Immune Axis ({' + '.join(bridge_a_domains)})")
    print(f"Found {len(bridge_a_genes)} novel genes spanning these exact three domains. Top 5:")
    for idx, row in bridge_a_genes.head(5).iterrows():
        print(f"  - {row['symbol']} ({row['total_raw_traits']} traits)")

    # Analyze Bridge B
    bridge_b_genes = novel_df[novel_df['domain_list'].apply(lambda x: has_bridge(x, bridge_b_domains))]
    bridge_b_genes = bridge_b_genes.sort_values('total_raw_traits', ascending=False)
    
    print(f"\nBridge B: Metabolic-Cancer-Brain Axis ({' + '.join(bridge_b_domains)})")
    print(f"Found {len(bridge_b_genes)} novel genes spanning these exact three domains. Top 5:")
    for idx, row in bridge_b_genes.head(5).iterrows():
        print(f"  - {row['symbol']} ({row['total_raw_traits']} traits)")

    # Save filtered "Underrated Hubs" for Phase 2 (Mechanism analysis)
    novel_out_path = os.path.join(RESULTS_DIR, 'underrated_bridge_genes.csv')
    novel_df.to_csv(novel_out_path, index=False)
    print(f"\nSaved {len(novel_df)} underrated hubs to {novel_out_path}")

if __name__ == '__main__':
    analyze_domain_bridges()
