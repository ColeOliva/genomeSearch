#!/usr/bin/env python3
"""
Import gnomAD gene constraint metrics into the genome database.

Constraint metrics tell us how tolerant/intolerant genes are to mutations:
- pLI (Probability of LoF Intolerance): >0.9 means the gene is likely essential
- LOEUF (LoF Observed/Expected Upper Fraction): <0.35 means strongly constrained

Data source: gnomAD (Genome Aggregation Database)
https://gnomad.broadinstitute.org/
"""

import csv
import os
import sqlite3

DATA_DIR = 'data'
DATABASE = os.path.join(DATA_DIR, 'genome.db')

# Input files
V4_CONSTRAINT_FILE = os.path.join(DATA_DIR, 'gnomad_v4_constraint.tsv')
V2_LOF_FILE = os.path.join(DATA_DIR, 'gnomad_v2_lof_metrics.txt')


def create_table_if_not_exists(conn):
    """Create the gene_constraints table if it doesn't exist."""
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gene_constraints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gene_id INTEGER,
            gene_symbol TEXT NOT NULL,
            transcript TEXT,
            
            -- Loss-of-function constraint metrics
            pli REAL,
            loeuf REAL,
            loeuf_lower REAL,
            loeuf_upper REAL,
            oe_lof REAL,
            
            -- Missense constraint metrics
            oe_mis REAL,
            oe_mis_lower REAL,
            oe_mis_upper REAL,
            mis_z REAL,
            
            -- Synonymous metrics
            oe_syn REAL,
            syn_z REAL,
            
            -- Metadata
            gnomad_version TEXT,
            
            FOREIGN KEY (gene_id) REFERENCES genes(gene_id)
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_constraints_gene ON gene_constraints(gene_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_constraints_symbol ON gene_constraints(gene_symbol)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_constraints_pli ON gene_constraints(pli)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_constraints_loeuf ON gene_constraints(loeuf)')
    conn.commit()


def get_gene_id_map(conn):
    """Build a mapping from gene symbols to gene_ids (for human genes)."""
    cursor = conn.cursor()
    # Get human genes (tax_id 9606)
    cursor.execute('''
        SELECT gene_id, UPPER(symbol) FROM genes WHERE tax_id = 9606
    ''')
    return {row[1]: row[0] for row in cursor.fetchall()}


def parse_float(value):
    """Parse a float value, returning None for empty/NA values."""
    if value is None or value == '' or value == 'NA' or value == 'NaN':
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def import_v4_constraints(conn, gene_map):
    """Import gnomAD v4.1 constraint metrics."""
    if not os.path.exists(V4_CONSTRAINT_FILE):
        print(f"  File not found: {V4_CONSTRAINT_FILE}")
        print("  Run 'python download_gnomad.py' first")
        return 0
    
    print(f"  Importing from {V4_CONSTRAINT_FILE}")
    cursor = conn.cursor()
    
    # Clear existing v4 data
    cursor.execute("DELETE FROM gene_constraints WHERE gnomad_version = 'v4.1'")
    
    batch = []
    batch_size = 1000
    count = 0
    matched = 0
    
    with open(V4_CONSTRAINT_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        
        # Debug: print available columns
        if reader.fieldnames:
            print(f"    Found columns: {len(reader.fieldnames)}")
        
        for row in reader:
            count += 1
            
            # Get gene symbol - try different column names
            gene_symbol = row.get('gene', row.get('symbol', row.get('gene_symbol', '')))
            if not gene_symbol:
                continue
            
            gene_symbol_upper = gene_symbol.upper()
            gene_id = gene_map.get(gene_symbol_upper)
            
            if gene_id:
                matched += 1
            
            # Extract constraint metrics - column names vary by version
            batch.append((
                gene_id,
                gene_symbol,
                row.get('transcript', row.get('canonical_transcript', '')),
                parse_float(row.get('pLI', row.get('pli'))),
                parse_float(row.get('lof.oe_ci.upper', row.get('oe_lof_upper', row.get('loeuf')))),
                parse_float(row.get('lof.oe_ci.lower', row.get('oe_lof_lower'))),
                parse_float(row.get('lof.oe_ci.upper', row.get('oe_lof_upper'))),
                parse_float(row.get('lof.oe', row.get('oe_lof'))),
                parse_float(row.get('mis.oe', row.get('oe_mis'))),
                parse_float(row.get('mis.oe_ci.lower', row.get('oe_mis_lower'))),
                parse_float(row.get('mis.oe_ci.upper', row.get('oe_mis_upper'))),
                parse_float(row.get('mis.z_score', row.get('mis_z'))),
                parse_float(row.get('syn.oe', row.get('oe_syn'))),
                parse_float(row.get('syn.z_score', row.get('syn_z'))),
                'v4.1'
            ))
            
            if len(batch) >= batch_size:
                cursor.executemany('''
                    INSERT INTO gene_constraints 
                    (gene_id, gene_symbol, transcript, pli, loeuf, loeuf_lower, loeuf_upper,
                     oe_lof, oe_mis, oe_mis_lower, oe_mis_upper, mis_z, oe_syn, syn_z, gnomad_version)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', batch)
                conn.commit()
                batch = []
                print(f"\r    Processed {count:,} rows, matched {matched:,} to genes...", end='', flush=True)
    
    # Insert remaining
    if batch:
        cursor.executemany('''
            INSERT INTO gene_constraints 
            (gene_id, gene_symbol, transcript, pli, loeuf, loeuf_lower, loeuf_upper,
             oe_lof, oe_mis, oe_mis_lower, oe_mis_upper, mis_z, oe_syn, syn_z, gnomad_version)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', batch)
        conn.commit()
    
    print(f"\r    Processed {count:,} rows, matched {matched:,} to genes")
    return count


def import_v2_lof_metrics(conn, gene_map):
    """Import gnomAD v2.1.1 pLoF metrics (alternative data source with pLI)."""
    if not os.path.exists(V2_LOF_FILE):
        print(f"  File not found: {V2_LOF_FILE}")
        print("  Run 'python download_gnomad.py' first")
        return 0
    
    print(f"  Importing from {V2_LOF_FILE}")
    cursor = conn.cursor()
    
    # Clear existing v2 data
    cursor.execute("DELETE FROM gene_constraints WHERE gnomad_version = 'v2.1.1'")
    
    batch = []
    batch_size = 1000
    count = 0
    matched = 0
    
    with open(V2_LOF_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        
        for row in reader:
            count += 1
            
            gene_symbol = row.get('gene', '')
            if not gene_symbol:
                continue
            
            gene_symbol_upper = gene_symbol.upper()
            gene_id = gene_map.get(gene_symbol_upper)
            
            if gene_id:
                matched += 1
            
            batch.append((
                gene_id,
                gene_symbol,
                row.get('transcript', ''),
                parse_float(row.get('pLI')),
                parse_float(row.get('oe_lof_upper')),  # LOEUF
                parse_float(row.get('oe_lof_lower_bin')),  # Lower bound
                parse_float(row.get('oe_lof_upper')),
                parse_float(row.get('oe_lof')),
                parse_float(row.get('oe_mis')),
                parse_float(row.get('oe_mis_lower')),
                parse_float(row.get('oe_mis_upper')),
                parse_float(row.get('mis_z')),
                parse_float(row.get('oe_syn')),
                parse_float(row.get('syn_z')),
                'v2.1.1'
            ))
            
            if len(batch) >= batch_size:
                cursor.executemany('''
                    INSERT INTO gene_constraints 
                    (gene_id, gene_symbol, transcript, pli, loeuf, loeuf_lower, loeuf_upper,
                     oe_lof, oe_mis, oe_mis_lower, oe_mis_upper, mis_z, oe_syn, syn_z, gnomad_version)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', batch)
                conn.commit()
                batch = []
                print(f"\r    Processed {count:,} rows, matched {matched:,} to genes...", end='', flush=True)
    
    # Insert remaining
    if batch:
        cursor.executemany('''
            INSERT INTO gene_constraints 
            (gene_id, gene_symbol, transcript, pli, loeuf, loeuf_lower, loeuf_upper,
             oe_lof, oe_mis, oe_mis_lower, oe_mis_upper, mis_z, oe_syn, syn_z, gnomad_version)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', batch)
        conn.commit()
    
    print(f"\r    Processed {count:,} rows, matched {matched:,} to genes")
    return count


def main():
    print("=" * 60)
    print("Importing gnomAD Gene Constraint Metrics")
    print("=" * 60)
    print()
    
    if not os.path.exists(DATABASE):
        print(f"Error: Database not found at {DATABASE}")
        print("Run 'python build_database.py' first")
        return
    
    conn = sqlite3.connect(DATABASE)
    
    # Create table if needed
    print("Creating/updating schema...")
    create_table_if_not_exists(conn)
    
    # Build gene symbol -> gene_id mapping
    print("Building gene ID mapping...")
    gene_map = get_gene_id_map(conn)
    print(f"  Found {len(gene_map):,} human genes in database")
    print()
    
    # Import data - try v4 first, then v2 as fallback
    total = 0
    
    print("Importing gnomAD v4.1 constraint metrics...")
    total += import_v4_constraints(conn, gene_map)
    print()
    
    print("Importing gnomAD v2.1.1 pLoF metrics (includes pLI scores)...")
    total += import_v2_lof_metrics(conn, gene_map)
    print()
    
    # Summary statistics
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM gene_constraints")
    total_rows = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM gene_constraints WHERE gene_id IS NOT NULL")
    linked_rows = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM gene_constraints WHERE pli > 0.9")
    high_pli = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM gene_constraints WHERE loeuf < 0.35")
    constrained = cursor.fetchone()[0]
    
    conn.close()
    
    print("=" * 60)
    print("Import complete!")
    print("=" * 60)
    print(f"  Total constraint records: {total_rows:,}")
    print(f"  Linked to genes: {linked_rows:,}")
    print(f"  High pLI (>0.9) genes: {high_pli:,} (essential/intolerant)")
    print(f"  Low LOEUF (<0.35) genes: {constrained:,} (strongly constrained)")
    print()
    print("Interpretation:")
    print("  - High pLI (>0.9): Gene is likely essential, mutations are harmful")
    print("  - Low LOEUF (<0.35): Gene is strongly constrained against LoF variants")
    print("  - These metrics help prioritize variants for clinical significance")


if __name__ == '__main__':
    main()
