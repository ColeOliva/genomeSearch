"""
Test suite for the Genome Search Flask application.
"""

import json
import os
import sqlite3
import sys

import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import DATABASE, app, get_db


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def db_path():
    """Return the database path for direct database queries."""
    return DATABASE


@pytest.fixture
def sample_gene_id():
    """Get a sample gene ID from the database for testing."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT gene_id FROM genes LIMIT 1')
    result = cursor.fetchone()
    conn.close()
    return result['gene_id'] if result else None


class TestDatabaseConnection:
    """Tests for database connectivity and integrity."""
    
    def test_database_exists(self):
        """Test that the database file exists."""
        assert os.path.exists(DATABASE), f"Database not found at {DATABASE}"
    
    def test_database_connection(self):
        """Test that we can connect to the database."""
        conn = get_db()
        assert conn is not None
        conn.close()
    
    def test_database_has_genes(self):
        """Test that the genes table has data."""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM genes')
        result = cursor.fetchone()
        conn.close()
        assert result['count'] > 0, "No genes found in database"
    
    def test_database_has_species(self):
        """Test that the species table has data."""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM species')
        result = cursor.fetchone()
        conn.close()
        assert result['count'] > 0, "No species found in database"
    
    def test_fts_index_exists(self):
        """Test that the FTS5 full-text search index exists and has data."""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM gene_fts')
        result = cursor.fetchone()
        conn.close()
        assert result['count'] > 0, "FTS index is empty"


class TestIndexRoute:
    """Tests for the main index page."""
    
    def test_index_returns_200(self, client):
        """Test that the index page loads successfully."""
        response = client.get('/')
        assert response.status_code == 200
    
    def test_index_returns_html(self, client):
        """Test that the index page returns HTML content."""
        response = client.get('/')
        assert b'<!DOCTYPE html>' in response.data or b'<html' in response.data
    
    def test_index_contains_search_form(self, client):
        """Test that the index page contains the search input."""
        response = client.get('/')
        assert b'search-input' in response.data


class TestSpeciesEndpoint:
    """Tests for the /species endpoint."""
    
    def test_species_returns_200(self, client):
        """Test that the species endpoint returns successfully."""
        response = client.get('/species')
        assert response.status_code == 200
    
    def test_species_returns_json(self, client):
        """Test that the species endpoint returns valid JSON."""
        response = client.get('/species')
        data = json.loads(response.data)
        assert 'species' in data
    
    def test_species_has_data(self, client):
        """Test that the species list is not empty."""
        response = client.get('/species')
        data = json.loads(response.data)
        assert len(data['species']) > 0
    
    def test_species_has_required_fields(self, client):
        """Test that each species has required fields."""
        response = client.get('/species')
        data = json.loads(response.data)
        for species in data['species']:
            assert 'tax_id' in species
            assert 'name' in species
            assert 'common_name' in species
            assert 'gene_count' in species
    
    def test_species_includes_human(self, client):
        """Test that human (tax_id 9606) is in the species list."""
        response = client.get('/species')
        data = json.loads(response.data)
        tax_ids = [sp['tax_id'] for sp in data['species']]
        assert 9606 in tax_ids, "Human (tax_id 9606) not found in species"


class TestSearchEndpoint:
    """Tests for the /search endpoint."""
    
    def test_search_returns_200(self, client):
        """Test that search endpoint returns successfully."""
        response = client.get('/search?q=BRCA')
        assert response.status_code == 200
    
    def test_search_returns_json(self, client):
        """Test that search returns valid JSON."""
        response = client.get('/search?q=cancer')
        data = json.loads(response.data)
        assert 'results' in data
        assert 'query' in data
    
    def test_search_empty_query(self, client):
        """Test that empty search returns empty results."""
        response = client.get('/search?q=')
        data = json.loads(response.data)
        assert data['results'] == []
    
    def test_search_finds_results(self, client):
        """Test that a common search term returns results."""
        response = client.get('/search?q=cancer')
        data = json.loads(response.data)
        assert len(data['results']) > 0, "No results for 'cancer' search"
    
    def test_search_result_has_required_fields(self, client):
        """Test that search results have required fields."""
        response = client.get('/search?q=BRCA')
        data = json.loads(response.data)
        if len(data['results']) > 0:
            result = data['results'][0]
            assert 'gene_id' in result
            assert 'symbol' in result
            assert 'species_name' in result
    
    def test_search_with_species_filter(self, client):
        """Test search with species filter."""
        response = client.get('/search?q=cancer&species=9606')
        data = json.loads(response.data)
        assert response.status_code == 200
        # All results should be human (tax_id 9606)
        for result in data['results']:
            assert result['tax_id'] == 9606
    
    def test_search_with_chromosome_filter(self, client):
        """Test search with chromosome filter."""
        response = client.get('/search?q=gene&species=9606&chromosome=1')
        data = json.loads(response.data)
        assert response.status_code == 200
        for result in data['results']:
            assert result['chromosome'] == '1'
    
    def test_search_with_constraint_filter_essential(self, client):
        """Test search with essential gene filter (pLI > 0.9)."""
        response = client.get('/search?q=gene&species=9606&constraint=essential')
        data = json.loads(response.data)
        assert response.status_code == 200
        # Results should have high pLI scores
        for result in data['results']:
            if result.get('pli') is not None:
                assert result['pli'] > 0.9
    
    def test_search_with_constraint_filter_constrained(self, client):
        """Test search with constrained gene filter (LOEUF < 0.35)."""
        response = client.get('/search?q=gene&species=9606&constraint=constrained')
        data = json.loads(response.data)
        assert response.status_code == 200
        for result in data['results']:
            if result.get('loeuf') is not None:
                assert result['loeuf'] < 0.35
    
    def test_search_with_clinical_filter_pathogenic(self, client):
        """Test search with pathogenic variants filter."""
        response = client.get('/search?q=gene&species=9606&clinical=pathogenic')
        data = json.loads(response.data)
        assert response.status_code == 200
        for result in data['results']:
            assert result.get('clinvar_pathogenic', 0) > 0
    
    def test_search_with_gene_type_filter(self, client):
        """Test search with gene type filter."""
        response = client.get('/search?q=gene&species=9606&gene_type=protein-coding')
        data = json.loads(response.data)
        assert response.status_code == 200
        for result in data['results']:
            assert result['gene_type'] == 'protein-coding'
    
    def test_search_multiple_filters(self, client):
        """Test search with multiple filters combined."""
        response = client.get('/search?q=cancer&species=9606&chromosome=17&clinical=pathogenic')
        data = json.loads(response.data)
        assert response.status_code == 200
        for result in data['results']:
            assert result['tax_id'] == 9606
            assert result['chromosome'] == '17'
            assert result.get('clinvar_pathogenic', 0) > 0
    
    def test_search_returns_constraint_data(self, client):
        """Test that search results include gnomAD constraint data."""
        response = client.get('/search?q=BRCA1&species=9606')
        data = json.loads(response.data)
        assert response.status_code == 200
        # BRCA1 should have constraint data
        if len(data['results']) > 0:
            result = data['results'][0]
            assert 'pli' in result
            assert 'loeuf' in result
    
    def test_search_returns_clinvar_data(self, client):
        """Test that search results include ClinVar pathogenic count."""
        response = client.get('/search?q=BRCA1&species=9606')
        data = json.loads(response.data)
        assert response.status_code == 200
        if len(data['results']) > 0:
            result = data['results'][0]
            assert 'clinvar_pathogenic' in result
    
    def test_search_special_characters(self, client):
        """Test that search handles special characters safely."""
        response = client.get('/search?q=test"quote')
        assert response.status_code == 200
    
    def test_search_limit(self, client):
        """Test that search results are limited."""
        response = client.get('/search?q=gene')
        data = json.loads(response.data)
        assert len(data['results']) <= 100


class TestGeneDetailEndpoint:
    """Tests for the /gene/<gene_id> endpoint."""
    
    def test_gene_detail_returns_200(self, client, sample_gene_id):
        """Test that gene detail endpoint returns successfully."""
        if sample_gene_id:
            response = client.get(f'/gene/{sample_gene_id}')
            assert response.status_code == 200
    
    def test_gene_detail_returns_json(self, client, sample_gene_id):
        """Test that gene detail returns valid JSON."""
        if sample_gene_id:
            response = client.get(f'/gene/{sample_gene_id}')
            data = json.loads(response.data)
            assert 'gene_id' in data or 'error' in data
    
    def test_gene_detail_not_found(self, client):
        """Test that non-existent gene returns 404."""
        response = client.get('/gene/999999999')
        assert response.status_code == 404
    
    def test_gene_detail_has_synonyms(self, client, sample_gene_id):
        """Test that gene detail includes synonyms array."""
        if sample_gene_id:
            response = client.get(f'/gene/{sample_gene_id}')
            data = json.loads(response.data)
            assert 'synonyms' in data
    
    def test_gene_detail_includes_traits(self, client, db_path):
        """Test that gene detail includes GWAS trait associations."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT g.gene_id, g.tax_id 
            FROM genes g 
            JOIN gene_traits gt ON g.gene_id = gt.gene_id 
            LIMIT 1
        """)
        row = cursor.fetchone()
        conn.close()
        
        if row:
            gene_id, tax_id = row
            response = client.get(f'/gene/{gene_id}?species={tax_id}')
            data = json.loads(response.data)
            assert 'traits' in data
            assert len(data['traits']) > 0
    
    def test_gene_detail_includes_constraint(self, client, db_path):
        """Test that gene detail includes gnomAD constraint data."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT g.gene_id, g.tax_id 
            FROM genes g 
            JOIN gene_constraints gc ON g.symbol = gc.gene_symbol 
            WHERE g.tax_id = 9606
            LIMIT 1
        """)
        row = cursor.fetchone()
        conn.close()
        
        if row:
            gene_id, tax_id = row
            response = client.get(f'/gene/{gene_id}?species={tax_id}')
            data = json.loads(response.data)
            assert 'constraint' in data
            if data['constraint']:
                assert 'pli' in data['constraint']
                assert 'loeuf' in data['constraint']
    
    def test_gene_detail_includes_clinvar_summary(self, client, db_path):
        """Test that gene detail includes ClinVar gene summary."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT g.gene_id, g.tax_id 
            FROM genes g 
            JOIN clinvar_gene_summary cgs ON g.gene_id = cgs.gene_id 
            LIMIT 1
        """)
        row = cursor.fetchone()
        conn.close()
        
        if row:
            gene_id, tax_id = row
            response = client.get(f'/gene/{gene_id}?species={tax_id}')
            data = json.loads(response.data)
            assert 'clinvar_summary' in data
            if data['clinvar_summary']:
                assert 'pathogenic_alleles' in data['clinvar_summary']
    
    def test_gene_detail_includes_clinvar_variants(self, client, db_path):
        """Test that gene detail includes ClinVar pathogenic variants."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT g.gene_id, g.tax_id 
            FROM genes g 
            JOIN clinvar_variants cv ON g.gene_id = cv.gene_id 
            LIMIT 1
        """)
        row = cursor.fetchone()
        conn.close()
        
        if row:
            gene_id, tax_id = row
            response = client.get(f'/gene/{gene_id}?species={tax_id}')
            data = json.loads(response.data)
            assert 'clinvar_variants' in data
            assert isinstance(data['clinvar_variants'], list)


class TestChromosomesEndpoint:
    """Tests for the /chromosomes endpoint."""
    
    def test_chromosomes_returns_200(self, client):
        """Test that chromosomes endpoint returns successfully."""
        response = client.get('/chromosomes')
        assert response.status_code == 200
    
    def test_chromosomes_returns_json(self, client):
        """Test that chromosomes returns valid JSON."""
        response = client.get('/chromosomes')
        data = json.loads(response.data)
        assert 'chromosomes' in data
    
    def test_chromosomes_has_data(self, client):
        """Test that chromosome list is not empty."""
        response = client.get('/chromosomes?species=9606')
        data = json.loads(response.data)
        assert len(data['chromosomes']) > 0
    
    def test_chromosomes_with_species(self, client):
        """Test chromosomes endpoint with species filter."""
        response = client.get('/chromosomes?species=9606')
        data = json.loads(response.data)
        assert data['tax_id'] == 9606


class TestChromosomeDetailEndpoint:
    """Tests for the /chromosome/<chrom> endpoint."""
    
    def test_chromosome_detail_returns_200(self, client):
        """Test that chromosome detail returns successfully."""
        response = client.get('/chromosome/1?species=9606')
        assert response.status_code == 200
    
    def test_chromosome_detail_returns_genes(self, client):
        """Test that chromosome detail returns gene list."""
        response = client.get('/chromosome/1?species=9606')
        data = json.loads(response.data)
        assert 'genes' in data
        assert 'chromosome' in data
    
    def test_chromosome_x(self, client):
        """Test that chromosome X works."""
        response = client.get('/chromosome/X?species=9606')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['chromosome'] == 'X'


class TestStaticFiles:
    """Tests for static file serving."""
    
    def test_css_loads(self, client):
        """Test that CSS file loads."""
        response = client.get('/static/style.css')
        assert response.status_code == 200
    
    def test_js_loads(self, client):
        """Test that JavaScript file loads."""
        response = client.get('/static/app.js')
        assert response.status_code == 200


class TestFaviconRoute:
    """Tests for favicon handling."""
    
    def test_favicon_no_error(self, client):
        """Test that favicon request doesn't return 404."""
        response = client.get('/favicon.ico')
        assert response.status_code in [200, 204]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
