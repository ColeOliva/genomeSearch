"""
Test suite for database integrity and data quality.
"""

import os
import sqlite3
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import DATABASE


@pytest.fixture
def db_connection():
    """Create a database connection for tests."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


class TestDatabaseSchema:
    """Tests for database schema integrity."""
    
    def test_genes_table_exists(self, db_connection):
        """Test that genes table exists."""
        cursor = db_connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='genes'")
        assert cursor.fetchone() is not None
    
    def test_species_table_exists(self, db_connection):
        """Test that species table exists."""
        cursor = db_connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='species'")
        assert cursor.fetchone() is not None
    
    def test_gene_synonyms_table_exists(self, db_connection):
        """Test that gene_synonyms table exists."""
        cursor = db_connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='gene_synonyms'")
        assert cursor.fetchone() is not None
    
    def test_gene_fts_table_exists(self, db_connection):
        """Test that FTS5 virtual table exists."""
        cursor = db_connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='gene_fts'")
        assert cursor.fetchone() is not None
    
    def test_genes_table_columns(self, db_connection):
        """Test that genes table has required columns."""
        cursor = db_connection.cursor()
        cursor.execute("PRAGMA table_info(genes)")
        columns = {row['name'] for row in cursor.fetchall()}
        required = {'gene_id', 'tax_id', 'symbol', 'name', 'chromosome', 'map_location', 'description', 'gene_type'}
        assert required.issubset(columns), f"Missing columns: {required - columns}"


class TestDataIntegrity:
    """Tests for data integrity."""
    
    def test_all_genes_have_species(self, db_connection):
        """Test that all genes have valid species references."""
        cursor = db_connection.cursor()
        cursor.execute('''
            SELECT COUNT(*) as orphans FROM genes g
            LEFT JOIN species s ON g.tax_id = s.tax_id
            WHERE s.tax_id IS NULL
        ''')
        result = cursor.fetchone()
        assert result['orphans'] == 0, f"Found {result['orphans']} genes without valid species"
    
    def test_all_genes_have_symbol(self, db_connection):
        """Test that all genes have a symbol."""
        cursor = db_connection.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM genes WHERE symbol IS NULL OR symbol = ''")
        result = cursor.fetchone()
        assert result['count'] == 0, f"Found {result['count']} genes without symbols"
    
    def test_species_gene_counts_accurate(self, db_connection):
        """Test that species gene_count matches actual gene count."""
        cursor = db_connection.cursor()
        cursor.execute('''
            SELECT s.tax_id, s.gene_count as reported, COUNT(g.gene_id) as actual
            FROM species s
            LEFT JOIN genes g ON s.tax_id = g.tax_id
            GROUP BY s.tax_id
            HAVING reported != actual
        ''')
        mismatches = cursor.fetchall()
        assert len(mismatches) == 0, f"Found {len(mismatches)} species with incorrect gene counts"
    
    def test_fts_index_matches_genes(self, db_connection):
        """Test that FTS index has same number of rows as genes table."""
        cursor = db_connection.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM genes")
        gene_count = cursor.fetchone()['count']
        cursor.execute("SELECT COUNT(*) as count FROM gene_fts")
        fts_count = cursor.fetchone()['count']
        assert gene_count == fts_count, f"Gene count ({gene_count}) != FTS count ({fts_count})"


class TestDataQuality:
    """Tests for data quality."""
    
    def test_human_genes_present(self, db_connection):
        """Test that human genes (tax_id 9606) are present."""
        cursor = db_connection.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM genes WHERE tax_id = 9606")
        result = cursor.fetchone()
        assert result['count'] > 10000, f"Expected >10000 human genes, found {result['count']}"
    
    def test_chromosomes_valid(self, db_connection):
        """Test that chromosome values are reasonable for human."""
        cursor = db_connection.cursor()
        cursor.execute('''
            SELECT DISTINCT chromosome FROM genes 
            WHERE tax_id = 9606 AND chromosome IS NOT NULL
        ''')
        chromosomes = {row['chromosome'] for row in cursor.fetchall()}
        # Should have at least chromosomes 1-22, X, Y
        expected = {'1', '2', '3', '4', '5', '6', '7', '8', '9', '10', 
                   '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', 'X', 'Y'}
        missing = expected - chromosomes
        assert len(missing) < 3, f"Missing chromosomes: {missing}"
    
    def test_known_gene_exists(self, db_connection):
        """Test that a well-known gene (BRCA1) exists."""
        cursor = db_connection.cursor()
        cursor.execute("SELECT * FROM genes WHERE symbol = 'BRCA1' AND tax_id = 9606")
        result = cursor.fetchone()
        assert result is not None, "BRCA1 gene not found in database"
    
    def test_fts_search_works(self, db_connection):
        """Test that FTS search returns results."""
        cursor = db_connection.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM gene_fts WHERE gene_fts MATCH 'cancer'")
        result = cursor.fetchone()
        assert result['count'] > 0, "FTS search for 'cancer' returned no results"


class TestMultiSpeciesData:
    """Tests for multi-species data."""
    
    def test_multiple_species_present(self, db_connection):
        """Test that multiple species are present."""
        cursor = db_connection.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM species WHERE gene_count > 0")
        result = cursor.fetchone()
        assert result['count'] >= 10, f"Expected >=10 species, found {result['count']}"
    
    def test_mouse_genes_present(self, db_connection):
        """Test that mouse genes (tax_id 10090) are present."""
        cursor = db_connection.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM genes WHERE tax_id = 10090")
        result = cursor.fetchone()
        assert result['count'] > 5000, f"Expected >5000 mouse genes, found {result['count']}"
    
    def test_species_have_common_names(self, db_connection):
        """Test that all species have common names."""
        cursor = db_connection.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM species WHERE common_name IS NULL OR common_name = ''")
        result = cursor.fetchone()
        assert result['count'] == 0, f"Found {result['count']} species without common names"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
