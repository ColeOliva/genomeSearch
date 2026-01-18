"""
Database schema for Genome Search application.
Uses SQLite with FTS5 (Full-Text Search) for efficient keyword searching.
"""

import os
import sqlite3

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
DATABASE = os.path.join(DATA_DIR, 'genome.db')


def create_schema(conn):
    """Create all database tables."""
    cursor = conn.cursor()
    
    # Species/organisms table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS species (
            tax_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            common_name TEXT,
            gene_count INTEGER DEFAULT 0
        )
    ''')
    
    # Main genes table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS genes (
            gene_id INTEGER PRIMARY KEY,
            tax_id INTEGER NOT NULL,
            symbol TEXT NOT NULL,
            name TEXT,
            chromosome TEXT,
            map_location TEXT,
            description TEXT,
            gene_type TEXT,
            FOREIGN KEY (tax_id) REFERENCES species(tax_id),
            UNIQUE(gene_id)
        )
    ''')
    
    # Gene synonyms/aliases table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gene_synonyms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gene_id INTEGER NOT NULL,
            synonym TEXT NOT NULL,
            FOREIGN KEY (gene_id) REFERENCES genes(gene_id)
        )
    ''')
    
    # Gene Ontology terms (for richer keyword searching)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gene_go_terms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gene_id INTEGER NOT NULL,
            go_id TEXT NOT NULL,
            go_term TEXT NOT NULL,
            category TEXT,  -- 'Function', 'Process', 'Component'
            FOREIGN KEY (gene_id) REFERENCES genes(gene_id)
        )
    ''')
    
    # FTS5 virtual table for full-text search
    # This indexes symbol, name, description, and synonyms together
    cursor.execute('''
        CREATE VIRTUAL TABLE IF NOT EXISTS gene_fts USING fts5(
            gene_id UNINDEXED,
            searchable_text,
            tokenize='porter unicode61'
        )
    ''')
    
    # Indexes for performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_genes_symbol ON genes(symbol)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_genes_chromosome ON genes(chromosome)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_genes_tax_id ON genes(tax_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_synonyms_gene ON gene_synonyms(gene_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_go_gene ON gene_go_terms(gene_id)')
    
    conn.commit()
    print("Database schema created successfully.")


def reset_database():
    """Delete and recreate the database."""
    if os.path.exists(DATABASE):
        os.remove(DATABASE)
        print(f"Removed existing database: {DATABASE}")
    
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DATABASE)
    create_schema(conn)
    conn.close()
    print(f"Created new database: {DATABASE}")


if __name__ == '__main__':
    reset_database()
