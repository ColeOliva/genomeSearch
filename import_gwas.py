"""
Import GWAS Catalog data into the genome database.
Adds gene-trait associations from published GWAS studies.
"""

import csv
import os
import sqlite3
from collections import defaultdict

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
DATABASE = os.path.join(DATA_DIR, 'genome.db')
GWAS_FILE = os.path.join(DATA_DIR, 'gwas_catalog.tsv')


def create_gwas_tables(conn):
    """Create tables for GWAS data."""
    cursor = conn.cursor()
    
    # Drop existing tables if they exist
    cursor.execute('DROP TABLE IF EXISTS gene_traits')
    cursor.execute('DROP TABLE IF EXISTS traits')
    cursor.execute('DROP TABLE IF EXISTS gwas_studies')
    
    # Studies table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gwas_studies (
            study_id TEXT PRIMARY KEY,
            pubmed_id TEXT,
            first_author TEXT,
            publication_date TEXT,
            journal TEXT,
            title TEXT,
            initial_sample_size TEXT,
            replication_sample_size TEXT
        )
    ''')
    
    # Traits table (EFO-based)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS traits (
            trait_id INTEGER PRIMARY KEY AUTOINCREMENT,
            efo_trait TEXT,
            reported_trait TEXT UNIQUE,
            trait_category TEXT
        )
    ''')
    
    # Gene-trait associations
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gene_traits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gene_id INTEGER,
            gene_symbol TEXT NOT NULL,
            trait_id INTEGER,
            reported_trait TEXT,
            efo_trait TEXT,
            p_value REAL,
            p_value_text TEXT,
            risk_allele TEXT,
            risk_allele_freq REAL,
            odds_ratio REAL,
            beta_coefficient REAL,
            ci_text TEXT,
            chromosome TEXT,
            position INTEGER,
            snp_id TEXT,
            study_id TEXT,
            pubmed_id TEXT,
            sample_description TEXT,
            FOREIGN KEY (gene_id) REFERENCES genes(gene_id),
            FOREIGN KEY (trait_id) REFERENCES traits(trait_id)
        )
    ''')
    
    # Indexes for performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_gene_traits_gene_id ON gene_traits(gene_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_gene_traits_symbol ON gene_traits(gene_symbol)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_gene_traits_trait ON gene_traits(reported_trait)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_traits_efo ON traits(efo_trait)')
    
    conn.commit()
    print("GWAS tables created.")


def get_gene_id_map(conn):
    """Get mapping of gene symbols to gene_ids for human genes."""
    cursor = conn.cursor()
    cursor.execute('''
        SELECT symbol, gene_id FROM genes WHERE tax_id = 9606
    ''')
    return {row[0].upper(): row[1] for row in cursor.fetchall()}


def parse_p_value(p_str):
    """Parse p-value string to float."""
    if not p_str or p_str == '':
        return None
    try:
        return float(p_str)
    except:
        return None


def parse_float(val):
    """Parse float value safely."""
    if not val or val == '' or val == 'NR':
        return None
    try:
        return float(val)
    except:
        return None


def import_gwas_data(conn):
    """Import GWAS catalog data."""
    cursor = conn.cursor()
    
    # Get gene symbol to ID mapping
    print("Loading gene ID mappings...")
    gene_map = get_gene_id_map(conn)
    print(f"  Loaded {len(gene_map):,} human gene symbols")
    
    # Track traits
    traits = {}
    trait_id_counter = 0
    
    # Track studies
    studies_seen = set()
    
    # Stats
    stats = {
        'total_rows': 0,
        'associations': 0,
        'matched_genes': 0,
        'unmatched_genes': set(),
        'studies': 0,
        'traits': 0
    }
    
    print(f"Reading GWAS catalog: {GWAS_FILE}")
    
    # Process in batches for better memory and commit reliability
    batch_size = 10000
    associations_batch = []
    studies_batch = []
    traits_batch = []
    
    with open(GWAS_FILE, 'r', encoding='utf-8', errors='replace') as f:
        reader = csv.DictReader(f, delimiter='\t')
        
        for row in reader:
            stats['total_rows'] += 1
            
            if stats['total_rows'] % 50000 == 0:
                print(f"  Processed {stats['total_rows']:,} rows...")
                conn.commit()  # Commit periodically
            
            # Get gene symbols (can be multiple, separated by various delimiters)
            gene_field = row.get('REPORTED GENE(S)', '') or row.get('MAPPED_GENE', '')
            if not gene_field or gene_field == 'NR':
                continue
            
            # Split on common delimiters
            gene_symbols = []
            for delim in [', ', ' - ', '; ', ' x ']:
                if delim in gene_field:
                    gene_symbols = [g.strip() for g in gene_field.split(delim)]
                    break
            if not gene_symbols:
                gene_symbols = [gene_field.strip()]
            
            # Get trait info
            reported_trait = row.get('DISEASE/TRAIT', '')
            efo_trait = row.get('MAPPED_TRAIT', '') or reported_trait
            
            if not reported_trait:
                continue
            
            # Track trait
            if reported_trait not in traits:
                trait_id_counter += 1
                traits[reported_trait] = {
                    'trait_id': trait_id_counter,
                    'efo_trait': efo_trait,
                    'reported_trait': reported_trait
                }
                traits_batch.append(traits[reported_trait])
                
                # Insert traits in batches
                if len(traits_batch) >= batch_size:
                    cursor.executemany('''
                        INSERT OR IGNORE INTO traits (trait_id, efo_trait, reported_trait)
                        VALUES (:trait_id, :efo_trait, :reported_trait)
                    ''', traits_batch)
                    traits_batch = []
            
            trait_id = traits[reported_trait]['trait_id']
            
            # Study info
            study_id = row.get('STUDY ACCESSION', '')
            pubmed_id = row.get('PUBMEDID', '')
            
            if study_id and study_id not in studies_seen:
                studies_seen.add(study_id)
                study_data = {
                    'study_id': study_id,
                    'pubmed_id': pubmed_id,
                    'first_author': row.get('FIRST AUTHOR', ''),
                    'publication_date': row.get('DATE', ''),
                    'journal': row.get('JOURNAL', ''),
                    'title': row.get('STUDY', ''),
                    'initial_sample_size': row.get('INITIAL SAMPLE SIZE', ''),
                    'replication_sample_size': row.get('REPLICATION SAMPLE SIZE', '')
                }
                studies_batch.append(study_data)
                
                # Insert studies in batches
                if len(studies_batch) >= batch_size:
                    cursor.executemany('''
                        INSERT OR IGNORE INTO gwas_studies 
                        (study_id, pubmed_id, first_author, publication_date, journal, title, 
                         initial_sample_size, replication_sample_size)
                        VALUES (:study_id, :pubmed_id, :first_author, :publication_date, :journal, 
                                :title, :initial_sample_size, :replication_sample_size)
                    ''', studies_batch)
                    studies_batch = []
            
            # Parse association data
            p_value = parse_p_value(row.get('P-VALUE', ''))
            risk_allele = row.get('STRONGEST SNP-RISK ALLELE', '')
            risk_allele_freq = parse_float(row.get('RISK ALLELE FREQUENCY', ''))
            odds_ratio = parse_float(row.get('OR or BETA', ''))
            ci_text = row.get('95% CI (TEXT)', '')
            chromosome = row.get('CHR_ID', '')
            position = parse_float(row.get('CHR_POS', ''))
            snp_id = row.get('SNPS', '')
            sample_desc = row.get('INITIAL SAMPLE SIZE', '')
            
            # Create association for each gene
            for symbol in gene_symbols:
                symbol = symbol.strip().upper()
                if not symbol or symbol == 'NR' or symbol == 'INTERGENIC':
                    continue
                
                gene_id = gene_map.get(symbol)
                
                if gene_id:
                    stats['matched_genes'] += 1
                else:
                    stats['unmatched_genes'].add(symbol)
                
                associations_batch.append({
                    'gene_id': gene_id,
                    'gene_symbol': symbol,
                    'trait_id': trait_id,
                    'reported_trait': reported_trait,
                    'efo_trait': efo_trait,
                    'p_value': p_value,
                    'p_value_text': row.get('P-VALUE', ''),
                    'risk_allele': risk_allele,
                    'risk_allele_freq': risk_allele_freq,
                    'odds_ratio': odds_ratio,
                    'beta_coefficient': None,
                    'ci_text': ci_text,
                    'chromosome': chromosome,
                    'position': int(position) if position else None,
                    'snp_id': snp_id,
                    'study_id': study_id,
                    'pubmed_id': pubmed_id,
                    'sample_description': sample_desc
                })
                stats['associations'] += 1
                
                # Insert associations in batches
                if len(associations_batch) >= batch_size:
                    cursor.executemany('''
                        INSERT INTO gene_traits 
                        (gene_id, gene_symbol, trait_id, reported_trait, efo_trait, p_value, p_value_text,
                         risk_allele, risk_allele_freq, odds_ratio, beta_coefficient, ci_text,
                         chromosome, position, snp_id, study_id, pubmed_id, sample_description)
                        VALUES (:gene_id, :gene_symbol, :trait_id, :reported_trait, :efo_trait, :p_value, 
                                :p_value_text, :risk_allele, :risk_allele_freq, :odds_ratio, :beta_coefficient, 
                                :ci_text, :chromosome, :position, :snp_id, :study_id, :pubmed_id, :sample_description)
                    ''', associations_batch)
                    associations_batch = []
    
    # Insert remaining batches
    if traits_batch:
        cursor.executemany('''
            INSERT OR IGNORE INTO traits (trait_id, efo_trait, reported_trait)
            VALUES (:trait_id, :efo_trait, :reported_trait)
        ''', traits_batch)
    
    if studies_batch:
        cursor.executemany('''
            INSERT OR IGNORE INTO gwas_studies 
            (study_id, pubmed_id, first_author, publication_date, journal, title, 
             initial_sample_size, replication_sample_size)
            VALUES (:study_id, :pubmed_id, :first_author, :publication_date, :journal, 
                    :title, :initial_sample_size, :replication_sample_size)
        ''', studies_batch)
    
    if associations_batch:
        cursor.executemany('''
            INSERT INTO gene_traits 
            (gene_id, gene_symbol, trait_id, reported_trait, efo_trait, p_value, p_value_text,
             risk_allele, risk_allele_freq, odds_ratio, beta_coefficient, ci_text,
             chromosome, position, snp_id, study_id, pubmed_id, sample_description)
            VALUES (:gene_id, :gene_symbol, :trait_id, :reported_trait, :efo_trait, :p_value, 
                    :p_value_text, :risk_allele, :risk_allele_freq, :odds_ratio, :beta_coefficient, 
                    :ci_text, :chromosome, :position, :snp_id, :study_id, :pubmed_id, :sample_description)
        ''', associations_batch)
    
    conn.commit()
    
    print(f"  Total rows: {stats['total_rows']:,}")
    print(f"  Associations: {stats['associations']:,}")
    print(f"  Matched to genes: {stats['matched_genes']:,}")
    print(f"  Unmatched symbols: {len(stats['unmatched_genes']):,}")
    print(f"  Studies: {len(studies_seen):,}")
    print(f"  Traits: {len(traits):,}")
    
    return stats


def update_fts_index(conn):
    """Update FTS index to include trait terms."""
    cursor = conn.cursor()
    
    print("Updating full-text search index with trait data...")
    
    # Get genes with traits (use subquery to get distinct traits first)
    cursor.execute('''
        SELECT gene_id, GROUP_CONCAT(reported_trait, ' ') as traits
        FROM (
            SELECT DISTINCT g.gene_id, gt.reported_trait
            FROM genes g
            JOIN gene_traits gt ON g.gene_id = gt.gene_id
            WHERE g.tax_id = 9606
        )
        GROUP BY gene_id
    ''')
    
    trait_data = {row[0]: row[1] for row in cursor.fetchall()}
    print(f"  Found {len(trait_data):,} genes with trait associations")
    
    # Get all current FTS entries for these genes in one query
    gene_ids = list(trait_data.keys())
    placeholders = ','.join(['?'] * len(gene_ids))
    cursor.execute(f'SELECT gene_id, searchable_text FROM gene_fts WHERE gene_id IN ({placeholders})', gene_ids)
    current_fts = {row[0]: row[1] or '' for row in cursor.fetchall()}
    
    # Prepare batch updates
    updates = []
    for gene_id, traits in trait_data.items():
        if gene_id in current_fts:
            new_text = current_fts[gene_id] + ' ' + traits
            updates.append((gene_id, new_text))
    
    print(f"  Updating {len(updates):,} FTS entries...")
    
    # Delete and re-insert in batches
    batch_size = 1000
    for i in range(0, len(updates), batch_size):
        batch = updates[i:i+batch_size]
        batch_ids = [u[0] for u in batch]
        placeholders = ','.join(['?'] * len(batch_ids))
        cursor.execute(f'DELETE FROM gene_fts WHERE gene_id IN ({placeholders})', batch_ids)
        cursor.executemany('INSERT INTO gene_fts (gene_id, searchable_text) VALUES (?, ?)', batch)
        if (i + batch_size) % 5000 == 0 or i + batch_size >= len(updates):
            print(f"    Processed {min(i + batch_size, len(updates)):,} / {len(updates):,}")
    
    conn.commit()
    print("  FTS index updated.")


def main():
    """Import GWAS data into the database."""
    print("=" * 60)
    print("GWAS Catalog Importer")
    print("=" * 60)
    print()
    
    # Check for GWAS file
    if not os.path.exists(GWAS_FILE):
        print(f"ERROR: GWAS catalog not found: {GWAS_FILE}")
        print("Run 'python download_gwas.py' first to download the data.")
        return
    
    # Check for database
    if not os.path.exists(DATABASE):
        print(f"ERROR: Database not found: {DATABASE}")
        print("Run 'python build_database.py' first to create the gene database.")
        return
    
    file_size = os.path.getsize(GWAS_FILE) / (1024 * 1024)
    print(f"GWAS file: {GWAS_FILE} ({file_size:.1f} MB)")
    print(f"Database: {DATABASE}")
    print()
    
    # Connect to database
    conn = sqlite3.connect(DATABASE)
    
    # Create tables
    create_gwas_tables(conn)
    print()
    
    # Import data
    stats = import_gwas_data(conn)
    print()
    
    # Update FTS index
    update_fts_index(conn)
    print()
    
    # Final stats
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM gene_traits')
    total_assoc = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(DISTINCT gene_id) FROM gene_traits WHERE gene_id IS NOT NULL')
    genes_with_traits = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(DISTINCT reported_trait) FROM gene_traits')
    unique_traits = cursor.fetchone()[0]
    
    conn.close()
    
    # Bump database mtime so cache invalidation based on db_mtime() happens immediately
    try:
        os.utime(DATABASE, None)
    except Exception:
        pass

    print("=" * 60)
    print("Import complete!")
    print(f"  Total associations: {total_assoc:,}")
    print(f"  Genes with traits: {genes_with_traits:,}")
    print(f"  Unique traits: {unique_traits:,}")
    print()
    print("You can now search for traits like 'diabetes', 'heart disease', etc.")
    print("Restart the Flask server to see the changes.")
    print("=" * 60)


if __name__ == '__main__':
    main()
