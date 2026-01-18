# Genome Search

A searchable database of genes across multiple species with interactive chromosome visualization. Search genes by keyword, gene name, or biological function, and explore their chromosomal locations.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0-green.svg)
![SQLite](https://img.shields.io/badge/SQLite-FTS5-orange.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## Features

- **Full-Text Search**: Search across 837,000+ genes using keywords, gene symbols, or biological terms
- **Multi-Species Support**: 15 model organisms including Human, Mouse, Zebrafish, Fruit fly, and more
- **Chromosome Viewer**: Interactive karyotype view with zoomable chromosome ideograms
- **Gene Localization**: Visualize gene positions on chromosomes with cytogenetic band locations
- **External Links**: Direct links to NCBI, GeneCards, UniProt, and OMIM databases
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

5. **Build the database** (first time only)
   ```bash
   python build_database.py
   ```
   This processes the NCBI data and creates the SQLite database (~500MB). Takes 10-20 minutes.

6. **Start the application**
   ```bash
   python app.py
   ```

7. **Open in browser**
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
- Synonyms/aliases
- Links to external databases (NCBI, GeneCards, UniProt, OMIM)

## Project Structure

```
genomeSearch/
├── app.py                 # Flask application and API routes
├── schema.py              # Database schema definition
├── build_database.py      # NCBI data parser and database builder
├── download_data.py       # NCBI FTP downloader
├── rebuild_fts.py         # FTS index rebuilder utility
├── requirements.txt       # Python dependencies
├── data/
│   ├── genome.db          # SQLite database (generated)
│   ├── gene_info.txt      # NCBI gene info (downloaded)
│   └── gene2go.txt        # Gene Ontology data (downloaded)
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

Data is processed for 15 model organisms based on NCBI taxonomy IDs.

## Technology Stack

- **Backend**: Python 3, Flask 3.0
- **Database**: SQLite with FTS5 full-text search
- **Frontend**: Vanilla JavaScript, CSS3
- **Data**: NCBI Gene Database

## Performance

- Database size: ~500 MB
- 837,000+ genes indexed
- 1.1M+ gene synonyms
- 2.8M+ GO term associations
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
- [Gene Ontology Consortium](http://geneontology.org/) for functional annotations
- Flask team for the excellent web framework

## Contact

Cole Oliva - [@ColeOliva](https://github.com/ColeOliva)

Project Link: [https://github.com/ColeOliva/genomeSearch](https://github.com/ColeOliva/genomeSearch)
