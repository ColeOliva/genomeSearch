import sqlite3
import os
import sys

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
DB_PATH = os.path.join(DATA_DIR, 'genome.db')
HMD_FILE = os.path.join(DATA_DIR, 'HMD_HumanPhenotype.rpt')
VOC_FILE = os.path.join(DATA_DIR, 'VOC_MammalianPhenotype.rpt')

def get_gene_id_map(conn):
    """Build mapping of human gene symbols and synonyms to gene_ids."""
    cursor = conn.cursor()
    cursor.execute('SELECT symbol, gene_id FROM genes WHERE tax_id = 9606')
    gene_map = {row[0].upper(): row[1] for row in cursor.fetchall()}
    
    cursor.execute('''
        SELECT s.synonym, s.gene_id 
        FROM gene_synonyms s
        JOIN genes g ON s.gene_id = g.gene_id
        WHERE g.tax_id = 9606
    ''')
    for synonym, gene_id in cursor.fetchall():
        syn = synonym.upper()
        if syn not in gene_map:
            gene_map[syn] = gene_id
            
    return gene_map

def import_vocabulary(conn):
    """Import Mammalian Phenotype (MP) dictionary."""
    cursor = conn.cursor()
    cursor.execute('DELETE FROM mouse_phenotype_terms')
    
    batch = []
    with open(VOC_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip('\n').split('\t')
            if len(parts) >= 3:
                mp_id, term_name, description = parts[0], parts[1], parts[2]
            elif len(parts) == 2:
                mp_id, term_name, description = parts[0], parts[1], None
            else:
                continue
                
            batch.append((mp_id, term_name, description))
            
    cursor.executemany('''
        INSERT INTO mouse_phenotype_terms (mp_id, term_name, description)
        VALUES (?, ?, ?)
    ''', batch)
    conn.commit()
    print(f"Imported {len(batch)} Mouse Phenotype vocabulary terms.")

def import_phenotypes(conn):
    """Import gene to mouse phenotype mapping."""
    gene_map = get_gene_id_map(conn)
    
    cursor = conn.cursor()
    cursor.execute('DELETE FROM mouse_phenotypes')
    
    batch = []
    matched = 0
    unmatched = 0
    
    with open(HMD_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip('\n').split('\t')
            # Look for lines that essentially have:
            # 0: Human Symbol, 1: Entrez, 2: Mouse Symbol, 3: MGI ID, 4: Phenotypes (optional)
            if len(parts) < 5 or not parts[4].strip():
                continue
                
            human_symbol = parts[0].upper()
            gene_id = gene_map.get(human_symbol)
            
            if not gene_id:
                # Try Entrez ID fallback
                entrez_id = parts[1].strip()
                if entrez_id.isdigit():
                    cursor.execute("SELECT gene_id FROM genes WHERE gene_id=? AND tax_id=9606", (int(entrez_id),))
                    row = cursor.fetchone()
                    if row:
                        gene_id = row[0]
            
            if not gene_id:
                unmatched += 1
                continue
                
            mouse_symbol = parts[2]
            mp_ids = [mp.strip() for mp in parts[4].split(',')]
            
            for mp_id in mp_ids:
                if mp_id:
                    batch.append((gene_id, mouse_symbol, mp_id))
            
            matched += 1
            
    cursor.executemany('''
        INSERT INTO mouse_phenotypes (gene_id, mouse_symbol, mp_id)
        VALUES (?, ?, ?)
    ''', batch)
    conn.commit()
    print(f"Imported {len(batch)} phenotype mappings spanning {matched} genes.")
    print(f"Skipped {unmatched} genes without known ID matches.")

def main():
    if not os.path.exists(VOC_FILE) or not os.path.exists(HMD_FILE):
        print("Required MGI data files are missing! Run download_mgi.py first.")
        sys.exit(1)
        
    print("=" * 50)
    print("Importing Mouse Phenotypes")
    print("=" * 50)
    
    # Run Schema Update explicitly in case `build_database` wasn't run
    import schema
    conn = sqlite3.connect(DB_PATH)
    schema.create_schema(conn)
    
    import_vocabulary(conn)
    import_phenotypes(conn)
    
    conn.close()
    print("=" * 50)
    print("Import complete!")

if __name__ == '__main__':
    main()
