# Genome Search

A searchable database of genes across multiple species with interactive chromosome visualization. Search genes by keyword, gene name, or biological function, and explore their chromosomal locations.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0-green.svg)
![SQLite](https://img.shields.io/badge/SQLite-FTS5-orange.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## Features

- **Full-Text Search**: Search across 837,000+ genes using keywords, gene symbols, or biological terms
- **GWAS Trait Associations**: Search by disease/trait names (e.g., "diabetes", "heart disease") with 1M+ gene-trait associations from the NHGRI-EBI GWAS Catalog
- **ClinVar Pathogenic Variants**: Known disease-causing mutations with 700K+ pathogenic variants linked to conditions
- **gnomAD Constraint Scores**: Population genetics data showing which genes are essential (pLI, LOEUF scores from 230K+ transcripts)
- **Multi-Species Support**: 15 model organisms including Human, Mouse, Zebrafish, Fruit fly, and more
- **Chromosome Viewer**: Interactive karyotype view with zoomable chromosome ideograms
- **Gene Localization**: Visualize gene positions on chromosomes with cytogenetic band locations
- **External Links**: Direct links to NCBI, GeneCards, UniProt, OMIM, GWAS Catalog, gnomAD, and ClinVar
- **Fast Performance**: SQLite with FTS5 full-text search for instant results

## Screenshots

### Search Interface
Search for genes by keyword with species filtering and instant results.

### Chromosome Viewer
Interactive karyotype showing all chromosomes with gene markers. Click any chromosome to zoom in and explore individual genes.

## Supported Species

| Species | Common Name | Genes |
|---------|-------------|-------|
| *Homo sapiens* | Human | 193,773 |
| *Mus musculus* | Mouse | 112,256 |
| *Bos taurus* | Cattle | 57,271 |
| *Danio rerio* | Zebrafish | 54,581 |
| *Canis lupus familiaris* | Dog | 50,756 |
| *Rattus norvegicus* | Rat | 47,812 |
| *Caenorhabditis elegans* | Roundworm | 46,927 |
| *Sus scrofa* | Pig | 45,360 |
| *Macaca mulatta* | Rhesus macaque | 44,894 |
| *Pan troglodytes* | Chimpanzee | 41,953 |
| *Felis catus* | Cat | 39,395 |
| *Arabidopsis thaliana* | Thale cress | 38,313 |
| *Gallus gallus* | Chicken | 32,180 |
| *Drosophila melanogaster* | Fruit fly | 25,079 |
| *Saccharomyces cerevisiae* | Yeast | 6,478 |

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/ColeOliva/genomeSearch.git
   cd genomeSearch
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Download gene data from NCBI** (first time only)
   ```bash
   python download_data.py
   ```
   This downloads ~3GB of gene annotation data from NCBI FTP.

5. **Download GWAS Catalog** (optional, for trait associations)
   ```bash
   python download_gwas.py
   ```
   This downloads ~60MB of gene-trait association data from EBI.

6. **Download gnomAD Constraint Data** (optional, for mutation tolerance)
   ```bash
   python download_gnomad.py
   ```
   This downloads ~100MB of gene constraint metrics from gnomAD.

7. **Download ClinVar Data** (optional, for pathogenic variants)
   ```bash
   python download_clinvar.py
   ```
   This downloads ~400MB of clinical variant data from NCBI ClinVar.

8. **Build the database** (first time only)
   ```bash
   python build_database.py
   ```
   This processes the NCBI data and creates the SQLite database (~500MB). Takes 10-20 minutes.

9. **Import GWAS data** (optional, if downloaded)
   ```bash
   python import_gwas.py
   ```
   This adds 1M+ gene-trait associations to the database.

10. **Import gnomAD data** (optional, if downloaded)
    ```bash
    python import_gnomad.py
    ```
    This adds 230K+ gene constraint records with pLI and LOEUF scores.

11. **Import ClinVar data** (optional, if downloaded)
    ```bash
    python import_clinvar.py
    ```
    This adds 700K+ pathogenic variant records with clinical significance.

12. **Start the application**
    ```bash
    python app.py
    ```

13. **Open in browser**
    Navigate to http://localhost:5000

## Usage

### Searching Genes

1. Enter keywords in the search box (e.g., "cancer", "BRCA", "insulin", "eye color")
2. Optionally filter by species using the dropdown
3. Click a result to see detailed gene information

### Chromosome Viewer

1. Search for genes first
2. Click "🧬 View on Chromosomes" button
3. See the karyotype with highlighted chromosomes containing your search results
4. Click any chromosome to zoom in
5. Hover over gene markers to see tooltips
6. Click markers or gene list items for full details

### Gene Details

Each gene shows:
- Symbol and full name
- Species information
- Chromosome location and cytogenetic band
- Description and gene type
- **gnomAD constraint metrics** (pLI, LOEUF) showing mutation tolerance (human genes)
- **ClinVar pathogenic variants** with clinical significance, conditions, and review status (human genes)
- **GWAS trait/disease associations** with p-values, SNPs, and PubMed links (human genes)
- Synonyms/aliases
- Links to external databases (NCBI, GeneCards, UniProt, OMIM, GWAS Catalog, gnomAD, ClinVar)

## Project Structure

```
genomeSearch/
├── app.py                 # Flask application and API routes
├── schema.py              # Database schema definition
├── build_database.py      # NCBI data parser and database builder
├── download_data.py       # NCBI FTP downloader
├── download_gwas.py       # GWAS Catalog downloader
├── import_gwas.py         # GWAS data importer
├── download_gnomad.py     # gnomAD constraint data downloader
├── import_gnomad.py       # gnomAD data importer
├── download_clinvar.py    # ClinVar variant data downloader
├── import_clinvar.py      # ClinVar data importer
├── rebuild_fts.py         # FTS index rebuilder utility
├── requirements.txt       # Python dependencies
├── data/
│   ├── genome.db          # SQLite database (generated)
│   ├── gene_info.txt      # NCBI gene info (downloaded)
│   ├── gene2go.txt        # Gene Ontology data (downloaded)
│   └── gwas_catalog.tsv   # GWAS Catalog data (downloaded)
├── static/
│   ├── style.css          # Application styles
│   └── app.js             # Frontend JavaScript
├── templates/
│   └── index.html         # Main HTML template
└── tests/
    ├── test_app.py        # API endpoint tests
    └── test_database.py   # Database integrity tests
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main search page |
| `/search?q=<query>&species=<tax_id>` | GET | Search genes |
| `/species` | GET | List all species |
| `/gene/<gene_id>` | GET | Get gene details |
| `/chromosomes?species=<tax_id>` | GET | List chromosomes for a species |
| `/chromosome/<chrom>?species=<tax_id>` | GET | Get genes on a chromosome |

## Running Tests

```bash
# Install pytest if needed
pip install pytest

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_app.py -v

# Run with coverage
pip install pytest-cov
pytest tests/ --cov=. --cov-report=html
```

## Data Source

Gene data is sourced from the [NCBI Gene Database](https://www.ncbi.nlm.nih.gov/gene):
- `gene_info.gz`: Gene symbols, names, descriptions, chromosomes, and types
- `gene2go.gz`: Gene Ontology term associations

Trait associations are from the [NHGRI-EBI GWAS Catalog](https://www.ebi.ac.uk/gwas/):
- `gwas_catalog.tsv`: 1M+ SNP-trait associations from genome-wide association studies

Gene constraint data is from [gnomAD](https://gnomad.broadinstitute.org/) (Genome Aggregation Database):
- `gnomad_v4_constraint.tsv`: Gene-level constraint metrics (pLI, LOEUF) from v4.1
- `gnomad_v2_lof_metrics.txt`: Loss-of-function metrics from v2.1.1

Clinical variant data is from [ClinVar](https://www.ncbi.nlm.nih.gov/clinvar/) (NCBI):
- `variant_summary.txt`: Pathogenic/likely pathogenic variants with clinical significance
- `gene_specific_summary.txt`: Gene-level summary of variant counts

Data is processed for 15 model organisms based on NCBI taxonomy IDs.

## Technology Stack

- **Backend**: Python 3, Flask 3.0
- **Database**: SQLite with FTS5 full-text search
- **Frontend**: Vanilla JavaScript, CSS3
- **Data**: NCBI Gene Database

## Performance

- Database size: ~1.2 GB
- 837,000+ genes indexed
- 1.1M+ gene synonyms
- 2.8M+ GO term associations
- 1.08M+ GWAS trait associations (40,689 unique traits)
- 231K+ gnomAD constraint records
- 700K+ ClinVar pathogenic variants
- 92K+ genes with ClinVar annotations
- 3,063 genes identified as essential (pLI > 0.9)
- 30,840 human genes linked to diseases/traits
- Search response: <100ms typical

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [NCBI Gene Database](https://www.ncbi.nlm.nih.gov/gene) for comprehensive gene annotation data
- [NHGRI-EBI GWAS Catalog](https://www.ebi.ac.uk/gwas/) for gene-trait association data
- [gnomAD](https://gnomad.broadinstitute.org/) (Genome Aggregation Database) for population genetics and constraint data
- [ClinVar](https://www.ncbi.nlm.nih.gov/clinvar/) for clinical variant interpretations and pathogenicity data
- [Gene Ontology Consortium](http://geneontology.org/) for functional annotations
- Flask team for the excellent web framework

## Contact

Cole Oliva - [@ColeOliva](https://github.com/ColeOliva)

Project Link: [https://github.com/ColeOliva/genomeSearch](https://github.com/ColeOliva/genomeSearch)
