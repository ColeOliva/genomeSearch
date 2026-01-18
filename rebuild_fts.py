"""Rebuild the FTS5 full-text search index from existing gene data."""

import os
import sqlite3

DATABASE = os.path.join(os.path.dirname(__file__), 'data', 'genome.db')

def rebuild_fts():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    # Drop and recreate FTS table
    print('Dropping old FTS table...')
    c.execute('DROP TABLE IF EXISTS gene_fts')

    print('Creating new FTS table...')
    c.execute('''
        CREATE VIRTUAL TABLE gene_fts USING fts5(
            gene_id UNINDEXED,
            searchable_text,
            tokenize="porter unicode61"
        )
    ''')

    # Build searchable text from genes table + synonyms + go terms
    print('Building FTS index from existing data (this may take a few minutes)...')
    c.execute('''
        INSERT INTO gene_fts (gene_id, searchable_text)
        SELECT 
            g.gene_id,
            g.symbol || ' ' || 
            COALESCE(g.name, '') || ' ' || 
            COALESCE(g.description, '') || ' ' ||
            COALESCE((SELECT GROUP_CONCAT(synonym, ' ') FROM gene_synonyms WHERE gene_id = g.gene_id), '') || ' ' ||
            COALESCE((SELECT GROUP_CONCAT(go_term, ' ') FROM gene_go_terms WHERE gene_id = g.gene_id), '')
        FROM genes g
    ''')

    conn.commit()
    
    c.execute('SELECT COUNT(*) FROM gene_fts')
    count = c.fetchone()[0]
    print(f'FTS index rebuilt with {count:,} entries')

    # Test search
    print('\nTesting search...')
    c.execute("SELECT gene_id, substr(searchable_text, 1, 100) FROM gene_fts WHERE gene_fts MATCH 'BRCA' LIMIT 3")
    results = c.fetchall()
    print(f'Test search for "BRCA" found {len(results)} results:')
    for r in results:
        print(f'  Gene {r[0]}: {r[1]}...')
    
    conn.close()
    print('\nDone! Restart the Flask server to see the changes.')

if __name__ == '__main__':
    rebuild_fts()
