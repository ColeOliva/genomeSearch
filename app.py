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
    """Search genes by keyword, optionally filtered by species."""
    query = request.args.get('q', '').strip()
    species = request.args.get('species', '').strip()  # tax_id or empty for all
    
    if not query:
        return jsonify({'results': [], 'query': query})
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Use FTS5 full-text search
    # Escape special FTS5 characters and add prefix matching
    safe_query = query.replace('"', '""')
    fts_query = f'"{safe_query}"*'
    
    try:
        if species:
            cursor.execute('''
                SELECT g.gene_id, g.tax_id, g.symbol, g.name, g.chromosome, 
                       g.map_location, g.description, g.gene_type,
                       s.common_name as species_name,
                       snippet(gene_fts, 1, '<mark>', '</mark>', '...', 32) as matched_text,
                       (SELECT COUNT(*) FROM gene_traits gt WHERE gt.gene_id = g.gene_id) as trait_count,
                       gc.pli, gc.loeuf
                FROM gene_fts
                JOIN genes g ON gene_fts.gene_id = g.gene_id
                JOIN species s ON g.tax_id = s.tax_id
                LEFT JOIN gene_constraints gc ON g.gene_id = gc.gene_id
                WHERE gene_fts MATCH ? AND g.tax_id = ?
                ORDER BY rank
                LIMIT 100
            ''', (fts_query, int(species)))
        else:
            cursor.execute('''
                SELECT g.gene_id, g.tax_id, g.symbol, g.name, g.chromosome, 
                       g.map_location, g.description, g.gene_type,
                       s.common_name as species_name,
                       snippet(gene_fts, 1, '<mark>', '</mark>', '...', 32) as matched_text,
                       (SELECT COUNT(*) FROM gene_traits gt WHERE gt.gene_id = g.gene_id) as trait_count,
                       gc.pli, gc.loeuf
                FROM gene_fts
                JOIN genes g ON gene_fts.gene_id = g.gene_id
                JOIN species s ON g.tax_id = s.tax_id
                LEFT JOIN gene_constraints gc ON g.gene_id = gc.gene_id
                WHERE gene_fts MATCH ?
                ORDER BY rank
                LIMIT 100
            ''', (fts_query,))
        
        results = [dict(row) for row in cursor.fetchall()]
    except sqlite3.OperationalError:
        # Fallback to simple LIKE search if FTS fails
        if species:
            cursor.execute('''
                SELECT g.gene_id, g.tax_id, g.symbol, g.name, g.chromosome, 
                       g.map_location, g.description, g.gene_type,
                       s.common_name as species_name
                FROM genes g
                JOIN species s ON g.tax_id = s.tax_id
                WHERE (g.symbol LIKE ? OR g.name LIKE ? OR g.description LIKE ?)
                AND g.tax_id = ?
                LIMIT 100
            ''', (f'%{query}%', f'%{query}%', f'%{query}%', int(species)))
        else:
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
    
    conn.close()
    
    result = dict(gene)
    result['synonyms'] = synonyms
    result['traits'] = traits
    result['trait_count'] = trait_count
    result['constraint'] = constraint
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
