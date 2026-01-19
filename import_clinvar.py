#!/usr/bin/env python3
"""
Import ClinVar data into the genome search database.

Imports:
1. Gene-specific summary: Pathogenic variant counts per gene
2. Variant summary: Individual pathogenic/likely pathogenic variants
"""

import csv
import os
import sqlite3
from collections import defaultdict

DATA_DIR = "data"
DATABASE = os.path.join(DATA_DIR, "genome.db")

# Only import pathogenic variants to keep database size manageable
PATHOGENIC_TERMS = {
    'Pathogenic',
    'Likely pathogenic', 
    'Pathogenic/Likely pathogenic',
    'Pathogenic, low penetrance',
    'Likely pathogenic, low penetrance',
}


def create_tables_if_not_exists(conn):
    """Create ClinVar tables if they don't exist."""
    cursor = conn.cursor()
    
    # Gene-level summary
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clinvar_gene_summary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gene_id INTEGER,
            gene_symbol TEXT NOT NULL,
            total_submissions INTEGER DEFAULT 0,
            total_alleles INTEGER DEFAULT 0,
            pathogenic_alleles INTEGER DEFAULT 0,
            uncertain_alleles INTEGER DEFAULT 0,
            conflicting_alleles INTEGER DEFAULT 0,
            gene_mim_number TEXT,
            
            FOREIGN KEY (gene_id) REFERENCES genes(gene_id)
        )
    ''')
    
    # Individual variants
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clinvar_variants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            allele_id INTEGER NOT NULL,
            variation_id INTEGER,
            gene_id INTEGER,
            gene_symbol TEXT,
            variant_name TEXT,
            variant_type TEXT,
            clinical_significance TEXT,
            review_status TEXT,
            phenotype_list TEXT,
            chromosome TEXT,
            start_pos INTEGER,
            stop_pos INTEGER,
            reference_allele TEXT,
            alternate_allele TEXT,
            rs_id INTEGER,
            last_evaluated TEXT,
            origin TEXT,
            assembly TEXT,
            
            FOREIGN KEY (gene_id) REFERENCES genes(gene_id)
        )
    ''')
    
    # Indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_clinvar_summary_gene ON clinvar_gene_summary(gene_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_clinvar_summary_symbol ON clinvar_gene_summary(gene_symbol)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_clinvar_summary_pathogenic ON clinvar_gene_summary(pathogenic_alleles)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_clinvar_variants_gene ON clinvar_variants(gene_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_clinvar_variants_symbol ON clinvar_variants(gene_symbol)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_clinvar_variants_allele ON clinvar_variants(allele_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_clinvar_variants_chr ON clinvar_variants(chromosome)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_clinvar_variants_significance ON clinvar_variants(clinical_significance)')
    
    conn.commit()


def get_gene_id_map(conn):
    """Build a mapping of gene symbols to gene IDs (human genes only)."""
    cursor = conn.cursor()
    # Human tax_id = 9606
    cursor.execute("SELECT gene_id, symbol FROM genes WHERE tax_id = 9606")
    return {row[1].upper(): row[0] for row in cursor.fetchall()}


def clear_existing_data(conn):
    """Clear existing ClinVar data."""
    cursor = conn.cursor()
    cursor.execute("DELETE FROM clinvar_gene_summary")
    cursor.execute("DELETE FROM clinvar_variants")
    conn.commit()
    print("Cleared existing ClinVar data.")


def import_gene_summary(conn, gene_map):
    """Import gene-specific summary with pathogenic variant counts."""
    filepath = os.path.join(DATA_DIR, "gene_specific_summary.txt")
    
    if not os.path.exists(filepath):
        print(f"  {filepath} not found. Run download_clinvar.py first.")
        return 0
    
    print("Importing gene-specific summary...")
    
    cursor = conn.cursor()
    batch = []
    batch_size = 5000
    count = 0
    matched = 0
    
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        reader = csv.reader(f, delimiter='\t')
        header = next(reader)
        
        # Find column indices
        col_map = {col: idx for idx, col in enumerate(header)}
        
        for row in reader:
            if len(row) < len(header):
                continue
            
            symbol = row[col_map.get('Symbol', 0)]
            gene_ncbi_id = row[col_map.get('GeneID', 1)]
            total_subs = row[col_map.get('Total_submissions', 2)] or '0'
            total_alleles = row[col_map.get('Total_alleles', 3)] or '0'
            pathogenic = row[col_map.get('Alleles_reported_Pathogenic_Likely_pathogenic', 5)] or '0'
            uncertain = row[col_map.get('Number_Uncertain', 7)] or '0'
            conflicts = row[col_map.get('Number_with_conflicts', 8)] or '0'
            mim_num = row[col_map.get('Gene_MIM_Number', 6)] if col_map.get('Gene_MIM_Number') else ''
            
            # Try to match to our genes table
            gene_id = None
            if symbol:
                gene_id = gene_map.get(symbol.upper())
            
            # Also try by NCBI gene ID
            if not gene_id and gene_ncbi_id and gene_ncbi_id != '-1':
                try:
                    gene_id = int(gene_ncbi_id)
                except ValueError:
                    pass
            
            if gene_id:
                matched += 1
            
            batch.append((
                gene_id,
                symbol,
                int(total_subs) if total_subs.isdigit() else 0,
                int(total_alleles) if total_alleles.isdigit() else 0,
                int(pathogenic) if pathogenic.isdigit() else 0,
                int(uncertain) if uncertain.isdigit() else 0,
                int(conflicts) if conflicts.isdigit() else 0,
                mim_num if mim_num and mim_num != '-' else None,
            ))
            
            if len(batch) >= batch_size:
                cursor.executemany('''
                    INSERT INTO clinvar_gene_summary 
                    (gene_id, gene_symbol, total_submissions, total_alleles, 
                     pathogenic_alleles, uncertain_alleles, conflicting_alleles, gene_mim_number)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', batch)
                conn.commit()
                count += len(batch)
                print(f"  Processed {count:,} genes...", end='\r')
                batch = []
    
    # Insert remaining
    if batch:
        cursor.executemany('''
            INSERT INTO clinvar_gene_summary 
            (gene_id, gene_symbol, total_submissions, total_alleles, 
             pathogenic_alleles, uncertain_alleles, conflicting_alleles, gene_mim_number)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', batch)
        conn.commit()
        count += len(batch)
    
    print(f"  Imported {count:,} gene summaries ({matched:,} linked to genes)")
    return count


def import_variants(conn, gene_map):
    """Import pathogenic/likely pathogenic variants from variant_summary.txt."""
    filepath = os.path.join(DATA_DIR, "variant_summary.txt")
    
    if not os.path.exists(filepath):
        print(f"  {filepath} not found. Run download_clinvar.py first.")
        return 0
    
    print("Importing pathogenic variants (this may take a few minutes)...")
    
    cursor = conn.cursor()
    batch = []
    batch_size = 10000
    count = 0
    total_rows = 0
    
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        reader = csv.reader(f, delimiter='\t')
        header = next(reader)
        
        # Build column map
        col_map = {col: idx for idx, col in enumerate(header)}
        
        for row in reader:
            total_rows += 1
            if total_rows % 500000 == 0:
                print(f"  Scanned {total_rows:,} rows, found {count:,} pathogenic variants...", end='\r')
            
            if len(row) < 20:
                continue
            
            # Check clinical significance
            clin_sig = row[col_map.get('ClinicalSignificance', 6)] if col_map.get('ClinicalSignificance') else ''
            
            # Only import pathogenic variants
            is_pathogenic = any(term in clin_sig for term in PATHOGENIC_TERMS)
            if not is_pathogenic:
                continue
            
            # Parse fields
            allele_id = row[col_map.get('AlleleID', 0)]
            var_type = row[col_map.get('Type', 1)]
            name = row[col_map.get('Name', 2)]
            gene_ncbi = row[col_map.get('GeneID', 3)]
            symbol = row[col_map.get('GeneSymbol', 4)]
            review_status = row[col_map.get('ReviewStatus', 24)] if col_map.get('ReviewStatus') else ''
            phenotypes = row[col_map.get('PhenotypeList', 13)] if col_map.get('PhenotypeList') else ''
            chromosome = row[col_map.get('Chromosome', 18)] if col_map.get('Chromosome') else ''
            start = row[col_map.get('Start', 19)] if col_map.get('Start') else ''
            stop = row[col_map.get('Stop', 20)] if col_map.get('Stop') else ''
            ref_allele = row[col_map.get('ReferenceAllele', 21)] if col_map.get('ReferenceAllele') else ''
            alt_allele = row[col_map.get('AlternateAllele', 22)] if col_map.get('AlternateAllele') else ''
            rs_num = row[col_map.get('RS# (dbSNP)', 9)] if col_map.get('RS# (dbSNP)') else ''
            last_eval = row[col_map.get('LastEvaluated', 8)] if col_map.get('LastEvaluated') else ''
            origin = row[col_map.get('Origin', 14)] if col_map.get('Origin') else ''
            assembly = row[col_map.get('Assembly', 16)] if col_map.get('Assembly') else ''
            var_id = row[col_map.get('VariationID', 30)] if col_map.get('VariationID') and len(row) > 30 else ''
            
            # Match gene
            gene_id = None
            if symbol:
                gene_id = gene_map.get(symbol.upper())
            if not gene_id and gene_ncbi and gene_ncbi != '-1':
                try:
                    gene_id = int(gene_ncbi)
                except ValueError:
                    pass
            
            batch.append((
                int(allele_id) if allele_id.isdigit() else 0,
                int(var_id) if var_id and var_id.isdigit() else None,
                gene_id,
                symbol if symbol and symbol != '-' else None,
                name[:500] if name else None,  # Truncate long names
                var_type if var_type else None,
                clin_sig[:200] if clin_sig else None,
                review_status[:100] if review_status else None,
                phenotypes[:500] if phenotypes else None,  # Truncate
                chromosome if chromosome and chromosome != '-1' else None,
                int(start) if start and start.isdigit() else None,
                int(stop) if stop and stop.isdigit() else None,
                ref_allele[:100] if ref_allele and ref_allele != 'na' else None,
                alt_allele[:100] if alt_allele and alt_allele != 'na' else None,
                int(rs_num) if rs_num and rs_num.isdigit() else None,
                last_eval if last_eval and last_eval != '-' else None,
                origin if origin else None,
                assembly if assembly else None,
            ))
            
            if len(batch) >= batch_size:
                cursor.executemany('''
                    INSERT INTO clinvar_variants 
                    (allele_id, variation_id, gene_id, gene_symbol, variant_name, 
                     variant_type, clinical_significance, review_status, phenotype_list,
                     chromosome, start_pos, stop_pos, reference_allele, alternate_allele,
                     rs_id, last_evaluated, origin, assembly)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', batch)
                conn.commit()
                count += len(batch)
                print(f"  Imported {count:,} pathogenic variants...", end='\r')
                batch = []
    
    # Insert remaining
    if batch:
        cursor.executemany('''
            INSERT INTO clinvar_variants 
            (allele_id, variation_id, gene_id, gene_symbol, variant_name, 
             variant_type, clinical_significance, review_status, phenotype_list,
             chromosome, start_pos, stop_pos, reference_allele, alternate_allele,
             rs_id, last_evaluated, origin, assembly)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', batch)
        conn.commit()
        count += len(batch)
    
    print(f"\n  Scanned {total_rows:,} total variants")
    print(f"  Imported {count:,} pathogenic/likely pathogenic variants")
    return count


def print_stats(conn):
    """Print summary statistics."""
    cursor = conn.cursor()
    
    print("\n" + "=" * 50)
    print("ClinVar Import Statistics")
    print("=" * 50)
    
    # Gene summary stats
    cursor.execute("SELECT COUNT(*) FROM clinvar_gene_summary")
    total_genes = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM clinvar_gene_summary WHERE gene_id IS NOT NULL")
    matched_genes = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM clinvar_gene_summary WHERE pathogenic_alleles > 0")
    genes_with_path = cursor.fetchone()[0]
    
    cursor.execute("SELECT SUM(pathogenic_alleles) FROM clinvar_gene_summary")
    total_path_alleles = cursor.fetchone()[0] or 0
    
    print(f"\nGene Summaries:")
    print(f"  Total genes: {total_genes:,}")
    print(f"  Linked to database: {matched_genes:,}")
    print(f"  Genes with pathogenic variants: {genes_with_path:,}")
    print(f"  Total pathogenic alleles (from summary): {total_path_alleles:,}")
    
    # Variant stats
    cursor.execute("SELECT COUNT(*) FROM clinvar_variants")
    total_variants = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT gene_symbol) FROM clinvar_variants WHERE gene_symbol IS NOT NULL")
    genes_in_variants = cursor.fetchone()[0]
    
    cursor.execute('''
        SELECT clinical_significance, COUNT(*) as cnt 
        FROM clinvar_variants 
        GROUP BY clinical_significance 
        ORDER BY cnt DESC 
        LIMIT 5
    ''')
    sig_counts = cursor.fetchall()
    
    cursor.execute('''
        SELECT variant_type, COUNT(*) as cnt 
        FROM clinvar_variants 
        GROUP BY variant_type 
        ORDER BY cnt DESC 
        LIMIT 5
    ''')
    type_counts = cursor.fetchall()
    
    print(f"\nPathogenic Variants:")
    print(f"  Total imported: {total_variants:,}")
    print(f"  Unique genes: {genes_in_variants:,}")
    
    print(f"\n  By Clinical Significance:")
    for sig, cnt in sig_counts:
        print(f"    {sig}: {cnt:,}")
    
    print(f"\n  By Variant Type:")
    for vtype, cnt in type_counts:
        print(f"    {vtype}: {cnt:,}")
    
    # Top genes by pathogenic variants
    cursor.execute('''
        SELECT gene_symbol, pathogenic_alleles 
        FROM clinvar_gene_summary 
        WHERE pathogenic_alleles > 0
        ORDER BY pathogenic_alleles DESC 
        LIMIT 10
    ''')
    top_genes = cursor.fetchall()
    
    print(f"\nTop 10 Genes by Pathogenic Variants:")
    for symbol, count in top_genes:
        print(f"    {symbol}: {count:,}")


def main():
    """Main import function."""
    if not os.path.exists(DATABASE):
        print(f"Database not found: {DATABASE}")
        print("Please run build_database.py first.")
        return
    
    conn = sqlite3.connect(DATABASE)
    
    try:
        print("ClinVar Data Import")
        print("=" * 50)
        
        # Create tables
        create_tables_if_not_exists(conn)
        
        # Clear existing data
        clear_existing_data(conn)
        
        # Get gene mapping
        print("\nBuilding gene symbol map...")
        gene_map = get_gene_id_map(conn)
        print(f"  Loaded {len(gene_map):,} human gene symbols")
        
        # Import gene summary
        print()
        import_gene_summary(conn, gene_map)
        
        # Import pathogenic variants
        print()
        import_variants(conn, gene_map)
        
        # Print statistics
        print_stats(conn)
        
    finally:
        conn.close()
        # Touch DB to bump mtime so caches will observe the updated database
        try:
            os.utime(DATABASE, None)
        except Exception:
            pass
    
    print("\n" + "=" * 50)
    print("ClinVar import complete!")


if __name__ == "__main__":
    main()
