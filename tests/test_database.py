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
    
    def test_gene_traits_table_exists(self, db_connection):
        """Test that gene_traits table (GWAS associations) exists."""
        cursor = db_connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='gene_traits'")
        assert cursor.fetchone() is not None
    
    def test_gene_constraints_table_exists(self, db_connection):
        """Test that gene_constraints table (gnomAD data) exists."""
        cursor = db_connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='gene_constraints'")
        assert cursor.fetchone() is not None
    
    def test_clinvar_variants_table_exists(self, db_connection):
        """Test that clinvar_variants table exists."""
        cursor = db_connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='clinvar_variants'")
        assert cursor.fetchone() is not None
    
    def test_clinvar_gene_summary_table_exists(self, db_connection):
        """Test that clinvar_gene_summary table exists."""
        cursor = db_connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='clinvar_gene_summary'")
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


class TestGWASData:
    """Tests for GWAS trait association data."""
    
    def test_gene_traits_has_data(self, db_connection):
        """Test that gene_traits table has data."""
        cursor = db_connection.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM gene_traits")
        result = cursor.fetchone()
        assert result['count'] > 100000, f"Expected >100000 trait associations, found {result['count']}"
    
    def test_gene_traits_has_required_columns(self, db_connection):
        """Test that gene_traits has required columns."""
        cursor = db_connection.cursor()
        cursor.execute("PRAGMA table_info(gene_traits)")
        columns = {row['name'] for row in cursor.fetchall()}
        required = {'gene_id', 'reported_trait', 'study_id', 'p_value'}
        assert required.issubset(columns), f"Missing columns: {required - columns}"
    
    def test_traits_linked_to_genes(self, db_connection):
        """Test that most traits are linked to valid genes."""
        cursor = db_connection.cursor()
        # Count orphans vs total - some traits may not have matching gene_ids
        cursor.execute('SELECT COUNT(*) as total FROM gene_traits')
        total = cursor.fetchone()['total']
        cursor.execute('''
            SELECT COUNT(*) as orphans FROM gene_traits gt
            LEFT JOIN genes g ON gt.gene_id = g.gene_id
            WHERE g.gene_id IS NULL
        ''')
        result = cursor.fetchone()
        # Allow some orphans (GWAS catalog may reference genes not in our database)
        orphan_ratio = result['orphans'] / total if total > 0 else 0
        assert orphan_ratio < 0.1, f"Too many orphan traits: {result['orphans']}/{total} ({orphan_ratio:.1%})"


class TestGnomADData:
    """Tests for gnomAD constraint data."""
    
    def test_gene_constraints_has_data(self, db_connection):
        """Test that gene_constraints table has data."""
        cursor = db_connection.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM gene_constraints")
        result = cursor.fetchone()
        assert result['count'] > 10000, f"Expected >10000 constraint records, found {result['count']}"
    
    def test_gene_constraints_has_required_columns(self, db_connection):
        """Test that gene_constraints has required columns."""
        cursor = db_connection.cursor()
        cursor.execute("PRAGMA table_info(gene_constraints)")
        columns = {row['name'] for row in cursor.fetchall()}
        required = {'gene_symbol', 'pli', 'loeuf'}
        assert required.issubset(columns), f"Missing columns: {required - columns}"
    
    def test_pli_values_in_range(self, db_connection):
        """Test that pLI values are between 0 and 1."""
        cursor = db_connection.cursor()
        cursor.execute('''
            SELECT COUNT(*) as count FROM gene_constraints 
            WHERE pli IS NOT NULL AND (pli < 0 OR pli > 1)
        ''')
        result = cursor.fetchone()
        assert result['count'] == 0, f"Found {result['count']} pLI values outside 0-1 range"
    
    def test_loeuf_values_positive(self, db_connection):
        """Test that LOEUF values are positive."""
        cursor = db_connection.cursor()
        cursor.execute('''
            SELECT COUNT(*) as count FROM gene_constraints 
            WHERE loeuf IS NOT NULL AND loeuf < 0
        ''')
        result = cursor.fetchone()
        assert result['count'] == 0, f"Found {result['count']} negative LOEUF values"


class TestClinVarData:
    """Tests for ClinVar pathogenic variant data."""
    
    def test_clinvar_variants_has_data(self, db_connection):
        """Test that clinvar_variants table has data."""
        cursor = db_connection.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM clinvar_variants")
        result = cursor.fetchone()
        assert result['count'] > 100000, f"Expected >100000 variants, found {result['count']}"
    
    def test_clinvar_gene_summary_has_data(self, db_connection):
        """Test that clinvar_gene_summary table has data."""
        cursor = db_connection.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM clinvar_gene_summary")
        result = cursor.fetchone()
        assert result['count'] > 5000, f"Expected >5000 gene summaries, found {result['count']}"
    
    def test_clinvar_variants_has_required_columns(self, db_connection):
        """Test that clinvar_variants has required columns."""
        cursor = db_connection.cursor()
        cursor.execute("PRAGMA table_info(clinvar_variants)")
        columns = {row['name'] for row in cursor.fetchall()}
        required = {'allele_id', 'gene_id', 'variant_name', 'clinical_significance', 'phenotype_list'}
        assert required.issubset(columns), f"Missing columns: {required - columns}"
    
    def test_clinvar_variants_are_pathogenic(self, db_connection):
        """Test that clinvar_variants only contains pathogenic/likely pathogenic variants."""
        cursor = db_connection.cursor()
        cursor.execute('''
            SELECT DISTINCT clinical_significance FROM clinvar_variants
        ''')
        significances = {row['clinical_significance'].lower() for row in cursor.fetchall()}
        for sig in significances:
            assert 'pathogenic' in sig, f"Found non-pathogenic variant: {sig}"
    
    def test_clinvar_brca1_has_variants(self, db_connection):
        """Test that BRCA1 has ClinVar pathogenic variants."""
        cursor = db_connection.cursor()
        cursor.execute('''
            SELECT COUNT(*) as count FROM clinvar_variants cv
            JOIN genes g ON cv.gene_id = g.gene_id
            WHERE g.symbol = 'BRCA1' AND g.tax_id = 9606
        ''')
        result = cursor.fetchone()
        assert result['count'] > 0, "BRCA1 should have pathogenic variants in ClinVar"
    
    def test_clinvar_gene_summary_matches_variants(self, db_connection):
        """Test that gene summaries exist for genes with variants."""
        cursor = db_connection.cursor()
        cursor.execute('''
            SELECT COUNT(DISTINCT cv.gene_id) as variants_genes,
                   COUNT(DISTINCT cgs.gene_id) as summary_genes
            FROM clinvar_variants cv
            LEFT JOIN clinvar_gene_summary cgs ON cv.gene_id = cgs.gene_id
        ''')
        result = cursor.fetchone()
        # Most genes with variants should have summaries
        ratio = result['summary_genes'] / result['variants_genes'] if result['variants_genes'] > 0 else 0
        assert ratio > 0.8, f"Only {ratio:.0%} of genes with variants have summaries"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
