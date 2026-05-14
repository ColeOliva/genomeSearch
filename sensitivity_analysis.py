import sqlite3
import os
import pandas as pd
import numpy as np

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
DB_PATH = os.path.join(DATA_DIR, 'genome.db')
RESULTS_DIR = os.path.join(os.path.dirname(__file__), 'results')

def calculate_npi(df, domain_w, trait_w, constraint_w, transform='log1p'):
    # Create a copy so we don't modify the shared dataframe directly
    df_calc = df.copy()
    
    if transform == 'log1p':
        trait_val = np.log1p(df_calc['total_raw_traits'])
    elif transform == 'sqrt':
        trait_val = np.sqrt(df_calc['total_raw_traits'])
    elif transform == 'none':
        trait_val = df_calc['total_raw_traits']
    else:
        trait_val = df_calc['total_raw_traits'] # fallback
        
    max_domains = 8.0
    max_trait_val = trait_val.max()
    
    domain_score = (df_calc['unique_domain_count'] / max_domains) * domain_w
    trait_score = (trait_val / max_trait_val) * trait_w
    constraint_score = df_calc['pli'] * constraint_w
    
    return domain_score + trait_score + constraint_score

def run_sensitivity_analysis():
    print("Running Sensitivity Analysis on NPI...")
    
    semantic_csv = os.path.join(RESULTS_DIR, 'semantic_pleiotropy_hubs.csv')
    if not os.path.exists(semantic_csv):
        print(f"Error: {semantic_csv} not found.")
        return
        
    df_hubs = pd.read_csv(semantic_csv)
    
    conn = sqlite3.connect(DB_PATH)
    query = "SELECT gene_symbol as symbol, pli, loeuf, oe_lof FROM gene_constraints"
    df_constraints = pd.read_sql_query(query, conn)
    conn.close()
    
    df = pd.merge(df_hubs, df_constraints, on='symbol', how='left')
    df['pli'] = df['pli'].fillna(df['pli'].median())
    
    # Define our test scenarios
    # Tuples of (Domain Weight, Trait Weight, Constraint Weight, Transform Name)
    scenarios = [
        # Baseline
        (50, 25, 25, 'log1p'),
        # High Domain Dependence
        (70, 15, 15, 'log1p'),
        # Low Domain Dependence
        (30, 35, 35, 'log1p'),
        # Different Transforms (to test publication bias handling)
        (50, 25, 25, 'sqrt'),
        (50, 25, 25, 'none'),
    ]
    
    # Track the ranks of specific highly interesting exploratory signals and benchmark genes
    novel_targets = ['FADS2', 'JMJD1C', 'CELSR2']
    benchmarks = ['APOE', 'ABO', 'TCF7L2', 'SH2B3']
    all_targets = novel_targets + benchmarks
    
    results = {target: [] for target in all_targets}
    
    for (d_w, t_w, c_w, trans) in scenarios:
        scenario_name = f"D{d_w}_T{t_w}_C{c_w}_{trans}"
        df[scenario_name] = calculate_npi(df, d_w, t_w, c_w, trans)
        
        # Rank them
        df['rank_' + scenario_name] = df[scenario_name].rank(ascending=False, method='min')
        
        for target in all_targets:
            # Get rank for target gene
            target_rank = df[df['symbol'] == target]['rank_' + scenario_name].values
            if len(target_rank) > 0:
                results[target].append(int(target_rank[0]))
            else:
                results[target].append(None)
                
    # Display Sensitivity Matrix
    print(f"\n{'Gene Role':<15} | {'Gene':<10} | {'Base Rank':<10} | {'D70':<10} | {'D30':<10} | {'Sqrt':<10} | {'NoScale':<10}")
    print("-" * 80)
    for target in novel_targets:
        r = results[target]
        print(f"{'Novel Signal':<15} | {target:<10} | {r[0]:<10} | {r[1]:<10} | {r[2]:<10} | {r[3]:<10} | {r[4]:<10}")
        
    print("-" * 80)
    for target in benchmarks:
        r = results[target]
        print(f"{'Benchmark':<15} | {target:<10} | {r[0]:<10} | {r[1]:<10} | {r[2]:<10} | {r[3]:<10} | {r[4]:<10}")

    # Evaluate Stability
    print("\n--- Stability Conclusion ---")
    fads2_ranks = results['FADS2']
    if all(r is not None and r <= 15 for r in fads2_ranks):
        print("-> FADS2 is highly stable and robust across all weighting and scaling assumptions.")
    else:
        print("-> FADS2's rank fluctuates depending on assumptions. It is highly sensitive to the metric.")

if __name__ == "__main__":
    run_sensitivity_analysis()
