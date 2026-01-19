"""
Import gene functional summaries from NCBI.
Downloads and imports detailed descriptions of gene function from RefSeq.
"""

import gzip
import os
import sqlite3

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
DATABASE = os.path.join(DATA_DIR, 'genome.db')
SUMMARY_FILE = os.path.join(DATA_DIR, 'gene_summary.gz')


def create_table(conn):
    """Create the gene_summaries table if it doesn't exist."""
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gene_summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gene_id INTEGER NOT NULL UNIQUE,
            summary TEXT NOT NULL,
            source TEXT,
            FOREIGN KEY (gene_id) REFERENCES genes(gene_id)
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_summaries_gene ON gene_summaries(gene_id)')
    conn.commit()


def import_summaries(conn):
    """Import gene summaries from the NCBI gene_summary.gz file."""
    cursor = conn.cursor()
    
    # Get all gene_ids we have in our database for faster lookup
    print("Loading existing gene IDs...")
    cursor.execute('SELECT gene_id FROM genes')
    existing_genes = set(row[0] for row in cursor.fetchall())
    print(f"Found {len(existing_genes):,} genes in database")
    
    # Clear existing data
    cursor.execute('DELETE FROM gene_summaries')
    conn.commit()
    
    print(f"Reading summaries from {SUMMARY_FILE}...")
    
    batch = []
    batch_size = 10000
    imported = 0
    skipped = 0
    
    with gzip.open(SUMMARY_FILE, 'rt', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            # Skip header lines
            if line.startswith('#'):
                continue
            
            parts = line.strip().split('\t')
            if len(parts) < 4:
                continue
            
            tax_id = parts[0]
            gene_id = int(parts[1])
            source = parts[2]  # RefSeq, Alliance of Genome Resources, etc.
            summary = parts[3]
            
            # Only import if gene exists in our database
            if gene_id not in existing_genes:
                skipped += 1
                continue
            
            # Skip very short summaries (often just "Predicted to...")
            if len(summary) < 50:
                skipped += 1
                continue
            
            batch.append((gene_id, summary, source))
            
            if len(batch) >= batch_size:
                cursor.executemany('''
                    INSERT OR REPLACE INTO gene_summaries (gene_id, summary, source)
                    VALUES (?, ?, ?)
                ''', batch)
                conn.commit()
                imported += len(batch)
                print(f"  Imported {imported:,} summaries...")
                batch = []
    
    # Insert remaining batch
    if batch:
        cursor.executemany('''
            INSERT OR REPLACE INTO gene_summaries (gene_id, summary, source)
            VALUES (?, ?, ?)
        ''', batch)
        conn.commit()
        imported += len(batch)
    
    print(f"\nImport complete!")
    print(f"  Imported: {imported:,} gene summaries")
    print(f"  Skipped: {skipped:,} (not in database or too short)")


def main():
    """Main entry point."""
    if not os.path.exists(SUMMARY_FILE):
        print(f"Error: {SUMMARY_FILE} not found!")
        print("Please download it first:")
        print("  curl -O https://ftp.ncbi.nlm.nih.gov/gene/DATA/gene_summary.gz")
        return
    
    conn = sqlite3.connect(DATABASE)
    
    try:
        create_table(conn)
        import_summaries(conn)
        
        # Show sample
        cursor = conn.cursor()
        cursor.execute('''
            SELECT g.symbol, gs.summary 
            FROM gene_summaries gs
            JOIN genes g ON gs.gene_id = g.gene_id
            WHERE g.symbol IN ('BRCA1', 'TP53', 'EGFR')
            LIMIT 3
        ''')
        print("\nSample summaries:")
        for row in cursor.fetchall():
            print(f"\n{row[0]}:")
            print(f"  {row[1][:200]}...")
            
    finally:
        conn.close()
        # Bump the database modification time so caches that rely on db_mtime() expire
        try:
            os.utime(DATABASE, None)
        except Exception:
            pass


if __name__ == '__main__':
    main()
