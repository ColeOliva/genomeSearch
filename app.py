"""
Genome Search Application
A searchable database of human genes with keyword search and chromosome visualization.
"""

import os
import sqlite3

from flask import Flask, jsonify, render_template, request, send_from_directory

app = Flask(__name__)
DATABASE = os.path.join(os.path.dirname(__file__), 'data', 'genome.db')


@app.route('/favicon.ico')
def favicon():
    """Return empty favicon to avoid 404."""
    return '', 204


def get_db():
    """Get database connection."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/')
def index():
    """Main search page."""
    return render_template('index.html')


@app.route('/search')
def search():
    """Search genes by keyword, optionally filtered by species and other criteria."""
    query = request.args.get('q', '').strip()
    species = request.args.get('species', '').strip()
    chromosome = request.args.get('chromosome', '').strip()
    constraint = request.args.get('constraint', '').strip()
    clinical = request.args.get('clinical', '').strip()
    gene_type = request.args.get('gene_type', '').strip()
    go_category = request.args.get('go_category', '').strip()
    
    if not query:
        return jsonify({'results': [], 'query': query})
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Use FTS5 full-text search
    safe_query = query.replace('"', '""')
    fts_query = f'"{safe_query}"*'
    
    # Build dynamic WHERE clause for filters
    filters = []
    params = [fts_query]
    
    if species:
        filters.append("g.tax_id = ?")
        params.append(int(species))
    
    if chromosome:
        filters.append("g.chromosome = ?")
        params.append(chromosome)
    
    if constraint == 'essential':
        filters.append("EXISTS (SELECT 1 FROM gene_constraints gc WHERE gc.gene_id = g.gene_id AND gc.pli > 0.9)")
    elif constraint == 'constrained':
        filters.append("EXISTS (SELECT 1 FROM gene_constraints gc WHERE gc.gene_id = g.gene_id AND gc.loeuf < 0.35)")
    elif constraint == 'tolerant':
        filters.append("NOT EXISTS (SELECT 1 FROM gene_constraints gc WHERE gc.gene_id = g.gene_id AND gc.pli > 0.5)")
    
    if clinical == 'pathogenic':
        filters.append("EXISTS (SELECT 1 FROM clinvar_gene_summary cv WHERE cv.gene_id = g.gene_id AND cv.pathogenic_alleles > 0)")
    elif clinical == 'gwas':
        filters.append("(SELECT COUNT(*) FROM gene_traits gt WHERE gt.gene_id = g.gene_id) > 0")
    elif clinical == 'disease':
        filters.append("(EXISTS (SELECT 1 FROM clinvar_gene_summary cv WHERE cv.gene_id = g.gene_id AND cv.pathogenic_alleles > 0) OR (SELECT COUNT(*) FROM gene_traits gt WHERE gt.gene_id = g.gene_id) > 0)")
    
    if gene_type == 'protein-coding':
        filters.append("g.gene_type = 'protein-coding'")
    elif gene_type == 'pseudo':
        filters.append("g.gene_type LIKE '%pseudo%'")
    elif gene_type == 'ncRNA':
        filters.append("(g.gene_type LIKE '%RNA%' OR g.gene_type LIKE '%ncRNA%')")
    elif gene_type == 'other':
        filters.append("g.gene_type NOT IN ('protein-coding') AND g.gene_type NOT LIKE '%pseudo%' AND g.gene_type NOT LIKE '%RNA%'")
    
    if go_category == 'function':
        filters.append("EXISTS (SELECT 1 FROM gene_go_terms ggo WHERE ggo.gene_id = g.gene_id AND ggo.category = 'Function')")
    elif go_category == 'process':
        filters.append("EXISTS (SELECT 1 FROM gene_go_terms ggo WHERE ggo.gene_id = g.gene_id AND ggo.category = 'Process')")
    elif go_category == 'component':
        filters.append("EXISTS (SELECT 1 FROM gene_go_terms ggo WHERE ggo.gene_id = g.gene_id AND ggo.category = 'Component')")
    elif go_category == 'any':
        filters.append("EXISTS (SELECT 1 FROM gene_go_terms ggo WHERE ggo.gene_id = g.gene_id)")
    
    where_clause = "gene_fts MATCH ?"
    if filters:
        where_clause += " AND " + " AND ".join(filters)
    
    try:
        cursor.execute(f'''
            SELECT g.gene_id, g.tax_id, g.symbol, g.name, g.chromosome, 
                   g.map_location, g.description, g.gene_type,
                   s.common_name as species_name,
                   snippet(gene_fts, 1, '<mark>', '</mark>', '...', 32) as matched_text,
                   (SELECT COUNT(*) FROM gene_traits gt WHERE gt.gene_id = g.gene_id) as trait_count,
                   (SELECT MAX(pli) FROM gene_constraints gc WHERE gc.gene_id = g.gene_id) as pli,
                   (SELECT MIN(loeuf) FROM gene_constraints gc WHERE gc.gene_id = g.gene_id) as loeuf,
                   (SELECT MAX(pathogenic_alleles) FROM clinvar_gene_summary cv WHERE cv.gene_id = g.gene_id) as clinvar_pathogenic
            FROM gene_fts
            JOIN genes g ON gene_fts.gene_id = g.gene_id
            JOIN species s ON g.tax_id = s.tax_id
            WHERE {where_clause}
            ORDER BY rank
            LIMIT 100
        ''', params)
        
        results = [dict(row) for row in cursor.fetchall()]
    except sqlite3.OperationalError:
        # Fallback to simple LIKE search if FTS fails
        cursor.execute('''
            SELECT g.gene_id, g.tax_id, g.symbol, g.name, g.chromosome, 
                   g.map_location, g.description, g.gene_type,
                   s.common_name as species_name
            FROM genes g
            JOIN species s ON g.tax_id = s.tax_id
            WHERE g.symbol LIKE ? OR g.name LIKE ? OR g.description LIKE ?
            LIMIT 100
        ''', (f'%{query}%', f'%{query}%', f'%{query}%'))
        results = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return jsonify({'results': results, 'query': query})


@app.route('/gene/<int:gene_id>')
def gene_detail(gene_id):
    """Get detailed info for a specific gene."""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT g.*, s.common_name as species_name, s.name as species_scientific
        FROM genes g
        JOIN species s ON g.tax_id = s.tax_id
        WHERE g.gene_id = ?
    ''', (gene_id,))
    gene = cursor.fetchone()
    
    if not gene:
        return jsonify({'error': 'Gene not found'}), 404
    
    # Get synonyms
    cursor.execute('SELECT synonym FROM gene_synonyms WHERE gene_id = ?', (gene_id,))
    synonyms = [row['synonym'] for row in cursor.fetchall()]
    
    # Get functional summary from NCBI RefSeq
    cursor.execute('SELECT summary, source FROM gene_summaries WHERE gene_id = ?', (gene_id,))
    summary_row = cursor.fetchone()
    functional_summary = {
        'text': summary_row['summary'],
        'source': summary_row['source']
    } if summary_row else None
    
    # Get trait associations (GWAS data)
    cursor.execute('''
        SELECT reported_trait, p_value, snp_id, risk_allele, odds_ratio, pubmed_id
        FROM gene_traits
        WHERE gene_id = ?
        ORDER BY p_value ASC
        LIMIT 20
    ''', (gene_id,))
    traits = [dict(row) for row in cursor.fetchall()]
    
    # Get count of total traits for this gene
    cursor.execute('SELECT COUNT(*) as cnt FROM gene_traits WHERE gene_id = ?', (gene_id,))
    trait_count = cursor.fetchone()['cnt']
    
    # Get constraint data (gnomAD)
    cursor.execute('''
        SELECT pli, loeuf, oe_lof, oe_mis, mis_z, gnomad_version
        FROM gene_constraints
        WHERE gene_id = ?
        ORDER BY 
            CASE gnomad_version 
                WHEN 'v4.1' THEN 1 
                WHEN 'v2.1.1' THEN 2 
                ELSE 3 
            END
        LIMIT 1
    ''', (gene_id,))
    constraint_row = cursor.fetchone()
    constraint = dict(constraint_row) if constraint_row else None
    
    # Get ClinVar summary for this gene
    cursor.execute('''
        SELECT pathogenic_alleles, uncertain_alleles, conflicting_alleles, 
               total_alleles, gene_mim_number
        FROM clinvar_gene_summary
        WHERE gene_id = ?
    ''', (gene_id,))
    clinvar_summary_row = cursor.fetchone()
    clinvar_summary = dict(clinvar_summary_row) if clinvar_summary_row else None
    
    # Get top pathogenic variants from ClinVar
    cursor.execute('''
        SELECT allele_id, variant_name, variant_type, clinical_significance,
               review_status, phenotype_list, chromosome, start_pos, rs_id
        FROM clinvar_variants
        WHERE gene_id = ?
        ORDER BY 
            CASE review_status
                WHEN 'practice guideline' THEN 1
                WHEN 'reviewed by expert panel' THEN 2
                WHEN 'criteria provided, multiple submitters, no conflicts' THEN 3
                WHEN 'criteria provided, single submitter' THEN 4
                ELSE 5
            END,
            clinical_significance
        LIMIT 20
    ''', (gene_id,))
    clinvar_variants = [dict(row) for row in cursor.fetchall()]
    
    # Get Gene Ontology (GO) terms
    cursor.execute('''
        SELECT go_id, go_term, category
        FROM gene_go_terms
        WHERE gene_id = ?
        ORDER BY category, go_term
    ''', (gene_id,))
    go_terms = [dict(row) for row in cursor.fetchall()]
    
    # Group GO terms by category
    go_by_category = {
        'Function': [],
        'Process': [],
        'Component': []
    }
    for term in go_terms:
        cat = term['category']
        if cat in go_by_category:
            go_by_category[cat].append({
                'go_id': term['go_id'],
                'go_term': term['go_term']
            })
    
    conn.close()
    
    result = dict(gene)
    result['synonyms'] = synonyms
    result['functional_summary'] = functional_summary
    result['traits'] = traits
    result['trait_count'] = trait_count
    result['constraint'] = constraint
    result['clinvar_summary'] = clinvar_summary
    result['clinvar_variants'] = clinvar_variants
    result['go_terms'] = go_by_category
    return jsonify(result)


@app.route('/species')
def list_species():
    """Get list of all species in the database."""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT tax_id, name, common_name, gene_count
        FROM species
        WHERE gene_count > 0
        ORDER BY gene_count DESC
    ''')
    
    species = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify({'species': species})


@app.route('/chromosome/<chrom>')
def chromosome_genes(chrom):
    """Get all genes on a specific chromosome for a species."""
    tax_id = request.args.get('species', 9606, type=int)  # Default to human
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT gene_id, symbol, name, map_location, description, gene_type
        FROM genes
        WHERE chromosome = ? AND tax_id = ?
        ORDER BY map_location
    ''', (chrom, tax_id))
    
    genes = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify({'chromosome': chrom, 'genes': genes, 'tax_id': tax_id})


@app.route('/chromosomes')
def list_chromosomes():
    """Get list of all chromosomes for a species with gene counts."""
    tax_id = request.args.get('species', 9606, type=int)  # Default to human
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT chromosome, COUNT(*) as gene_count
        FROM genes
        WHERE tax_id = ? AND chromosome IS NOT NULL AND chromosome != ''
        GROUP BY chromosome
        ORDER BY 
            CASE 
                WHEN chromosome GLOB '[0-9]*' THEN CAST(chromosome AS INTEGER)
                WHEN chromosome = 'X' THEN 23
                WHEN chromosome = 'Y' THEN 24
                WHEN chromosome = 'MT' THEN 25
                ELSE 26
            END
    ''', (tax_id,))
    
    chromosomes = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify({'chromosomes': chromosomes, 'tax_id': tax_id})


@app.route('/chromosome/<chrom>/region')
def chromosome_region(chrom):
    """Get genes in a specific cytogenetic region (e.g., 1p22)."""
    tax_id = request.args.get('species', 9606, type=int)
    region = request.args.get('region', '')
    
    conn = get_db()
    cursor = conn.cursor()
    
    if region:
        cursor.execute('''
            SELECT gene_id, symbol, name, map_location, description, gene_type
            FROM genes
            WHERE chromosome = ? AND tax_id = ? AND map_location LIKE ?
            ORDER BY map_location
            LIMIT 500
        ''', (chrom, tax_id, f'{chrom}{region}%'))
    else:
        cursor.execute('''
            SELECT gene_id, symbol, name, map_location, description, gene_type
            FROM genes
            WHERE chromosome = ? AND tax_id = ?
            ORDER BY map_location
            LIMIT 500
        ''', (chrom, tax_id))
    
    genes = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify({'chromosome': chrom, 'region': region, 'genes': genes})


if __name__ == '__main__':
    app.run(debug=True, port=5000)
