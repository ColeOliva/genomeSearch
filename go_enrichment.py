import os
import sqlite3
import pandas as pd
import numpy as np
from math import comb

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
DB_PATH = os.path.join(DATA_DIR, 'genome.db')
RESULTS_DIR = os.path.join(os.path.dirname(__file__), 'results')

TOP_N = 1000


def benjamini_hochberg(pvals):
    """Return BH FDR q-values in the same order as input pvals."""
    pvals = np.array(pvals)
    n = len(pvals)
    order = np.argsort(pvals)
    ranks = np.empty(n, int)
    ranks[order] = np.arange(1, n+1)
    qvals = pvals * n / ranks
    # enforce monotonicity
    qvals_corrected = np.minimum.accumulate(qvals[order[::-1]])[::-1]
    # put back in original order
    qvals_final = np.empty(n)
    qvals_final[order] = qvals_corrected
    qvals_final = np.minimum(qvals_final, 1.0)
    return qvals_final


def run_enrichment(top_n=TOP_N):
    print(f"Running GO enrichment for top {top_n} NPI genes...")
    if not os.path.exists(RESULTS_DIR):
        os.makedirs(RESULTS_DIR)

    npi_csv = os.path.join(RESULTS_DIR, 'normalized_pleiotropy_index.csv')
    if not os.path.exists(npi_csv):
        print(f"Error: {npi_csv} not found. Run scoring_metric.py first.")
        return

    df = pd.read_csv(npi_csv)
    top_genes = df.head(top_n)['symbol'].tolist()

    if not os.path.exists(DB_PATH):
        print(f"Error: database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    # gene_go_terms stores gene_id; join to genes to get gene symbols
    query = '''
    SELECT g.gene_id, g.symbol as symbol, go.go_term, go.category
    FROM gene_go_terms go
    JOIN genes g ON go.gene_id = g.gene_id
    '''
    go_df = pd.read_sql_query(query, conn)
    conn.close()

    # Background: unique genes with GO annotations
    bg_genes = go_df['symbol'].unique()
    M = len(bg_genes)
    print(f"Background genes with GO annotations: {M}")

    # Map GO term -> set of genes
    term_to_genes = go_df.groupby('go_term')['symbol'].apply(lambda x: set(x.dropna())).to_dict()

    # Count k, n for each term
    N = len(set(top_genes).intersection(set(bg_genes)))
    print(f"Top genes found in background: {N}")

    records = []
    for term, geneset in term_to_genes.items():
        n = len(geneset)
        k = len(geneset.intersection(top_genes))
        if k == 0:
            continue
        # compute hypergeometric p-value: probability of >= k successes
        # use survival function: sum_{i=k}^{min(n,N)} [C(n,i)*C(M-n, N-i)] / C(M,N)
        # try to use scipy if available for numeric stability
        try:
            from scipy.stats import hypergeom
            pval = hypergeom.sf(k-1, M, n, N)
        except Exception:
            # fallback: compute directly (may be slow/unstable)
            # compute cumulative tail
            denom = comb(M, N)
            tail = 0
            max_i = min(n, N)
            for i in range(k, max_i+1):
                num = comb(n, i) * comb(M-n, N-i)
                tail += num
            pval = tail / denom if denom > 0 else 1.0
        records.append((term, n, k, pval))

    if not records:
        print("No GO terms enriched in top gene set.")
        return

    res_df = pd.DataFrame(records, columns=['go_term', 'bg_count', 'top_count', 'p_value'])
    res_df['q_value'] = benjamini_hochberg(res_df['p_value'].values)
    res_df = res_df.sort_values('p_value')

    out_csv = os.path.join(RESULTS_DIR, f'go_enrichment_top{top_n}.csv')
    res_df.to_csv(out_csv, index=False)
    print(f"Saved enrichment results to {out_csv}")

    # Print top 10
    print('\nTop 10 enriched GO terms:')
    for idx, row in res_df.head(10).iterrows():
        print(f"- {row['go_term']} (bg={row['bg_count']}, top={row['top_count']}, p={row['p_value']:.2e}, q={row['q_value']:.2e})")

    # Try plotting if matplotlib available
    try:
        import matplotlib.pyplot as plt
        top_plot = res_df.head(10).iloc[::-1]
        plt.figure(figsize=(8,6))
        plt.barh(range(len(top_plot)), -np.log10(top_plot['p_value']), color='C0')
        plt.yticks(range(len(top_plot)), top_plot['go_term'])
        plt.xlabel('-log10(p-value)')
        plt.tight_layout()
        fig_path = os.path.join(RESULTS_DIR, f'go_enrichment_top{top_n}.png')
        plt.savefig(fig_path, dpi=300)
        plt.close()
        print(f"Saved barplot to {fig_path}")
    except Exception:
        print("matplotlib not available or plotting failed; skipping figure generation.")

if __name__ == '__main__':
    run_enrichment()
