"""
Build the searchable genome database from NCBI data files.

This script:
1. Creates the database schema
2. Parses gene_info.txt to load genes for selected species
3. Parses gene2go.txt to add GO term keywords
4. Builds the FTS5 full-text search index

Run download_data.py first to get the required data files.
"""

import os
import sqlite3
from collections import defaultdict

from schema import DATA_DIR, DATABASE, reset_database

# File paths - use FULL files (all species)
GENE_INFO_FILE = os.path.join(DATA_DIR, 'gene_info.txt')
GENE2GO_FILE = os.path.join(DATA_DIR, 'gene2go.txt')

# Popular model organisms and their taxonomy IDs
# Add or remove species as needed
SPECIES = {
    9606: {'name': 'Homo sapiens', 'common_name': 'Human'},
    10090: {'name': 'Mus musculus', 'common_name': 'Mouse'},
    10116: {'name': 'Rattus norvegicus', 'common_name': 'Rat'},
    7955: {'name': 'Danio rerio', 'common_name': 'Zebrafish'},
    7227: {'name': 'Drosophila melanogaster', 'common_name': 'Fruit fly'},
    6239: {'name': 'Caenorhabditis elegans', 'common_name': 'Roundworm'},
    9615: {'name': 'Canis lupus familiaris', 'common_name': 'Dog'},
    9685: {'name': 'Felis catus', 'common_name': 'Cat'},
    9913: {'name': 'Bos taurus', 'common_name': 'Cattle'},
    9823: {'name': 'Sus scrofa', 'common_name': 'Pig'},
    9031: {'name': 'Gallus gallus', 'common_name': 'Chicken'},
    559292: {'name': 'Saccharomyces cerevisiae S288C', 'common_name': 'Yeast'},
    3702: {'name': 'Arabidopsis thaliana', 'common_name': 'Thale cress'},
    9544: {'name': 'Macaca mulatta', 'common_name': 'Rhesus macaque'},
    9598: {'name': 'Pan troglodytes', 'common_name': 'Chimpanzee'},
}

# Set of tax_ids for quick lookup
SELECTED_TAX_IDS = set(SPECIES.keys())


def parse_gene_info(filepath):
    """
    Parse NCBI gene_info file for selected species.
    
    Columns (tab-separated):
    0: tax_id
    1: GeneID
    2: Symbol
    3: LocusTag
    4: Synonyms (pipe-separated)
    5: dbXrefs
    6: chromosome
    7: map_location
    8: description
    9: type_of_gene
    10: Symbol_from_nomenclature_authority
    11: Full_name_from_nomenclature_authority
    12: Nomenclature_status
    13: Other_designations (pipe-separated)
    14: Modification_date
    15: Feature_type
    """
    genes = []
    synonyms = defaultdict(list)
    species_counts = defaultdict(int)
    
    print(f"Parsing {filepath}...")
    print(f"  Filtering for {len(SELECTED_TAX_IDS)} species...")
    
    line_count = 0
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('#'):
                continue
            
            line_count += 1
            if line_count % 1000000 == 0:
                print(f"    Processed {line_count:,} lines...")
            
            parts = line.strip().split('\t')
            if len(parts) < 10:
                continue
            
            tax_id = int(parts[0])
            
            # Skip if not in our selected species
            if tax_id not in SELECTED_TAX_IDS:
                continue
            
            gene_id = int(parts[1])
            symbol = parts[2]
            synonym_list = parts[4].split('|') if parts[4] != '-' else []
            chromosome = parts[6] if parts[6] != '-' else None
            map_location = parts[7] if parts[7] != '-' else None
            description = parts[8] if parts[8] != '-' else None
            gene_type = parts[9] if parts[9] != '-' else None
            
            # Official full name (column 11) is often better than description
            full_name = parts[11] if len(parts) > 11 and parts[11] != '-' else None
            
            # Other designations provide additional searchable terms
            other_names = parts[13].split('|') if len(parts) > 13 and parts[13] != '-' else []
            
            genes.append({
                'gene_id': gene_id,
                'tax_id': tax_id,
                'symbol': symbol,
                'name': full_name or description,
                'chromosome': chromosome,
                'map_location': map_location,
                'description': description,
                'gene_type': gene_type
            })
            
            species_counts[tax_id] += 1
            
            # Collect all synonyms and other names
            for syn in synonym_list + other_names:
                if syn and syn != '-':
                    synonyms[gene_id].append(syn)
    
    print(f"  Parsed {len(genes):,} genes total")
    print("  Genes per species:")
    for tax_id, count in sorted(species_counts.items(), key=lambda x: -x[1]):
        species_info = SPECIES.get(tax_id, {'common_name': 'Unknown'})
        print(f"    {species_info['common_name']}: {count:,}")
    
    return genes, synonyms, species_counts


def parse_gene2go(filepath, gene_ids):
    """
    Parse NCBI gene2go file for GO term annotations.
    Only loads GO terms for genes we've already loaded.
    
    Columns (tab-separated):
    0: tax_id
    1: GeneID
    2: GO_ID
    3: Evidence
    4: Qualifier
    5: GO_term
    6: PubMed
    7: Category (Function/Process/Component)
    """
    go_terms = defaultdict(list)
    
    if not os.path.exists(filepath):
        print(f"  Warning: {filepath} not found, skipping GO terms")
        return go_terms
    
    print(f"Parsing {filepath}...")
    
    line_count = 0
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('#'):
                continue
            
            line_count += 1
            if line_count % 1000000 == 0:
                print(f"    Processed {line_count:,} lines...")
            
            parts = line.strip().split('\t')
            if len(parts) < 8:
                continue
            
            gene_id = int(parts[1])
            
            # Only include GO terms for genes we have
            if gene_id not in gene_ids:
                continue
            
            go_id = parts[2]
            go_term = parts[5]
            category = parts[7]
            
            go_terms[gene_id].append({
                'go_id': go_id,
                'go_term': go_term,
                'category': category
            })
    
    unique_genes = len(go_terms)
    total_terms = sum(len(terms) for terms in go_terms.values())
    print(f"  Parsed {total_terms:,} GO term associations for {unique_genes:,} genes")
    
    return go_terms


def build_searchable_text(gene, synonyms, go_terms):
    """
    Build combined searchable text for a gene.
    This gets indexed in FTS5 for full-text search.
    """
    parts = []
    
    # Symbol (weighted heavily by repetition)
    parts.append(gene['symbol'])
    parts.append(gene['symbol'])  # Repeat for higher weight
    
    # Name
    if gene['name']:
        parts.append(gene['name'])
    
    # Description
    if gene['description']:
        parts.append(gene['description'])
    
    # Synonyms
    for syn in synonyms:
        parts.append(syn)
    
    # GO terms (biological process keywords)
    for term in go_terms:
        parts.append(term['go_term'])
    
    # Chromosome
    if gene['chromosome']:
        parts.append(f"chromosome {gene['chromosome']}")
    
    return ' '.join(parts)


def insert_species(conn, species_counts):
    """Insert species information."""
    cursor = conn.cursor()
    
    print("Inserting species...")
    for tax_id, info in SPECIES.items():
        count = species_counts.get(tax_id, 0)
        cursor.execute('''
            INSERT INTO species (tax_id, name, common_name, gene_count)
            VALUES (?, ?, ?, ?)
        ''', (tax_id, info['name'], info['common_name'], count))
    
    conn.commit()
    print(f"  Inserted {len(SPECIES)} species")


def insert_data(conn, genes, synonyms, go_terms):
    """Insert all gene data into the database."""
    cursor = conn.cursor()
    
    print("Inserting genes...")
    cursor.executemany('''
        INSERT INTO genes (gene_id, tax_id, symbol, name, chromosome, map_location, description, gene_type)
        VALUES (:gene_id, :tax_id, :symbol, :name, :chromosome, :map_location, :description, :gene_type)
    ''', genes)
    print(f"  Inserted {len(genes):,} genes")
    
    print("Inserting synonyms...")
    synonym_rows = []
    for gene_id, syns in synonyms.items():
        for syn in syns:
            synonym_rows.append({'gene_id': gene_id, 'synonym': syn})
    
    cursor.executemany('''
        INSERT INTO gene_synonyms (gene_id, synonym)
        VALUES (:gene_id, :synonym)
    ''', synonym_rows)
    print(f"  Inserted {len(synonym_rows):,} synonyms")
    
    print("Inserting GO terms...")
    go_rows = []
    for gene_id, terms in go_terms.items():
        for term in terms:
            go_rows.append({
                'gene_id': gene_id,
                'go_id': term['go_id'],
                'go_term': term['go_term'],
                'category': term['category']
            })
    
    cursor.executemany('''
        INSERT INTO gene_go_terms (gene_id, go_id, go_term, category)
        VALUES (:gene_id, :go_id, :go_term, :category)
    ''', go_rows)
    print(f"  Inserted {len(go_rows):,} GO term associations")
    
    conn.commit()


def build_fts_index(conn, genes, synonyms, go_terms):
    """Build the FTS5 full-text search index."""
    cursor = conn.cursor()
    
    print("Building full-text search index...")
    
    fts_rows = []
    for gene in genes:
        gene_id = gene['gene_id']
        searchable = build_searchable_text(
            gene, 
            synonyms.get(gene_id, []), 
            go_terms.get(gene_id, [])
        )
        fts_rows.append((gene_id, searchable))
    
    cursor.executemany('''
        INSERT INTO gene_fts (gene_id, searchable_text)
        VALUES (?, ?)
    ''', fts_rows)
    
    conn.commit()
    print(f"  Indexed {len(fts_rows):,} genes for full-text search")


def main():
    """Build the complete database."""
    print("=" * 60)
    print("Genome Database Builder (Multi-Species)")
    print("=" * 60)
    print()
    print("Including species:")
    for tax_id, info in SPECIES.items():
        print(f"  - {info['common_name']} ({info['name']})")
    print()
    
    # Check for required files
    if not os.path.exists(GENE_INFO_FILE):
        print(f"ERROR: {GENE_INFO_FILE} not found!")
        print("Run 'python download_data.py' first to download the data.")
        return
    
    # Parse data files
    genes, synonyms, species_counts = parse_gene_info(GENE_INFO_FILE)
    
    # Get set of gene_ids for filtering GO terms
    gene_ids = {g['gene_id'] for g in genes}
    go_terms = parse_gene2go(GENE2GO_FILE, gene_ids)
    
    print()
    
    # Create fresh database
    reset_database()
    
    # Connect and populate
    conn = sqlite3.connect(DATABASE)
    
    insert_species(conn, species_counts)
    insert_data(conn, genes, synonyms, go_terms)
    print()
    
    build_fts_index(conn, genes, synonyms, go_terms)
    print()
    
    conn.close()
    
    # Report database size
    db_size = os.path.getsize(DATABASE) / (1024 * 1024)
    print("=" * 60)
    print(f"Database built successfully!")
    print(f"  Location: {DATABASE}")
    print(f"  Size: {db_size:.1f} MB")
    print(f"  Species: {len(SPECIES)}")
    print(f"  Total genes: {len(genes):,}")
    print()
    print("Next step: Run 'python app.py' to start the web server.")
    print("=" * 60)


if __name__ == '__main__':
    main()
