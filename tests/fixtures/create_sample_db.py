"""Create a small sample SQLite database used for CI lightweight tests.
This avoids downloading the full genome DB in CI.
"""
import sqlite3
import os

DB = os.path.join(os.path.dirname(__file__), 'sample.db')

if os.path.exists(DB):
    print(f"Sample DB already exists at {DB}")
    exit(0)

conn = sqlite3.connect(DB)
cur = conn.cursor()

# Minimal schema to satisfy tests
cur.executescript('''
CREATE TABLE species (tax_id INTEGER PRIMARY KEY, name TEXT, common_name TEXT, gene_count INTEGER);
CREATE TABLE genes (gene_id INTEGER PRIMARY KEY, tax_id INTEGER, symbol TEXT, name TEXT, chromosome TEXT, map_location TEXT, description TEXT, gene_type TEXT);
CREATE TABLE gene_synonyms (id INTEGER PRIMARY KEY, gene_id INTEGER, synonym TEXT);
CREATE VIRTUAL TABLE IF NOT EXISTS gene_fts USING fts5(gene_id UNINDEXED, searchable_text);

CREATE TABLE gene_traits (
    id INTEGER PRIMARY KEY,
    gene_id INTEGER,
    gene_symbol TEXT,
    reported_trait TEXT,
    p_value REAL,
    study_id TEXT,
    snp_id TEXT,
    risk_allele TEXT,
    odds_ratio REAL,
    pubmed_id TEXT
);
CREATE TABLE gene_constraints (id INTEGER PRIMARY KEY, gene_id INTEGER, gene_symbol TEXT, pli REAL, loeuf REAL, gnomad_version TEXT);
CREATE TABLE clinvar_variants (id INTEGER PRIMARY KEY, allele_id INTEGER, variation_id INTEGER, gene_id INTEGER, gene_symbol TEXT, variant_name TEXT, clinical_significance TEXT, phenotype_list TEXT, chromosome TEXT, start_pos INTEGER, rs_id INTEGER);
CREATE TABLE clinvar_gene_summary (id INTEGER PRIMARY KEY, gene_id INTEGER, gene_symbol TEXT, pathogenic_alleles INTEGER);
CREATE TABLE gene_summaries (id INTEGER PRIMARY KEY, gene_id INTEGER, summary TEXT, source TEXT);
''')

# Insert sample species
cur.execute("INSERT INTO species (tax_id, name, common_name, gene_count) VALUES (9606, 'Homo sapiens', 'Human', 2)")
cur.execute("INSERT INTO species (tax_id, name, common_name, gene_count) VALUES (10090, 'Mus musculus', 'Mouse', 1)")

# Insert sample genes (BRCA1 human, TP53 human, Gnai2 mouse)
cur.execute("INSERT INTO genes (gene_id, tax_id, symbol, name, chromosome, map_location, description, gene_type) VALUES (1, 9606, 'BRCA1', 'Breast cancer type 1 susceptibility protein', '17', '17q21.31', 'Tumor suppressor', 'protein-coding')")
cur.execute("INSERT INTO genes (gene_id, tax_id, symbol, name, chromosome, map_location, description, gene_type) VALUES (2, 9606, 'TP53', 'Tumor protein p53', '17', '17p13.1', 'Guardian of the genome', 'protein-coding')")
cur.execute("INSERT INTO genes (gene_id, tax_id, symbol, name, chromosome, map_location, description, gene_type) VALUES (3, 10090, 'Gnai2', 'Guanine nucleotide-binding protein', '3', '3q', 'Signal transduction', 'protein-coding')")

# FTS entries
cur.execute("INSERT INTO gene_fts (gene_id, searchable_text) VALUES (1, 'BRCA1 tumor suppressor breast cancer')")
cur.execute("INSERT INTO gene_fts (gene_id, searchable_text) VALUES (2, 'TP53 tumor suppressor p53')")
cur.execute("INSERT INTO gene_fts (gene_id, searchable_text) VALUES (3, 'Gnai2 G protein signaling')")

# Synonyms
cur.execute("INSERT INTO gene_synonyms (gene_id, synonym) VALUES (1, 'BRCC1')")
cur.execute("INSERT INTO gene_synonyms (gene_id, synonym) VALUES (2, 'P53')")

# Traits
cur.execute("INSERT INTO gene_traits (gene_id, gene_symbol, reported_trait, p_value, study_id, snp_id, risk_allele, odds_ratio, pubmed_id) VALUES (1, 'BRCA1', 'breast cancer', 1e-8, 'GCST0001', 'rs123', 'A', 2.1, '12345678')")
cur.execute("INSERT INTO gene_traits (gene_id, gene_symbol, reported_trait, p_value, study_id, snp_id, risk_allele, odds_ratio, pubmed_id) VALUES (2, 'TP53', 'lung cancer', 2e-5, 'GCST0002', 'rs456', 'G', 1.5, '87654321')")

# Constraints
cur.execute("INSERT INTO gene_constraints (gene_id, gene_symbol, pli, loeuf, gnomad_version) VALUES (1, 'BRCA1', 0.95, 0.2, 'v4.1')")
cur.execute("INSERT INTO gene_constraints (gene_id, gene_symbol, pli, loeuf, gnomad_version) VALUES (2, 'TP53', 0.99, 0.15, 'v4.1')")

# ClinVar
cur.execute("INSERT INTO clinvar_variants (allele_id, variation_id, gene_id, gene_symbol, variant_name, clinical_significance, phenotype_list, chromosome, start_pos, rs_id) VALUES (1001, 5001, 1, 'BRCA1', 'c.68_69del', 'Pathogenic', 'Breast cancer', '17', 43044295, 123456)")
cur.execute("INSERT INTO clinvar_gene_summary (gene_id, gene_symbol, pathogenic_alleles) VALUES (1, 'BRCA1', 5)")
# gene_summaries: minimal row for BRCA1 (gene_id=1) -- required for CI tests
cur.execute("INSERT INTO gene_summaries (gene_id, summary, source) VALUES (1, 'BRCA1 is a tumor suppressor gene involved in DNA repair.', 'NCBI RefSeq')")

conn.commit()
conn.close()
print(f"Created sample DB at {DB}")
