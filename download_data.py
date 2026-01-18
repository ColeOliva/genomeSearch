"""
Download NCBI Gene data files for human genome.

Files downloaded:
1. gene_info - Gene names, descriptions, chromosome locations (~50MB compressed)
2. gene2go - Gene Ontology annotations for keyword searching (~15MB compressed)

These are official NCBI FTP files updated regularly.
"""

import gzip
import os
import shutil
import urllib.request

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

# NCBI FTP URLs
FILES = {
    'gene_info': {
        'url': 'https://ftp.ncbi.nlm.nih.gov/gene/DATA/gene_info.gz',
        'description': 'Gene information (names, descriptions, locations)'
    },
    'gene2go': {
        'url': 'https://ftp.ncbi.nlm.nih.gov/gene/DATA/gene2go.gz',
        'description': 'Gene Ontology annotations (biological keywords)'
    }
}

# Human taxonomy ID (we only want human genes)
HUMAN_TAX_ID = '9606'


def download_file(name, url, dest_dir):
    """Download a file with progress indication."""
    gz_path = os.path.join(dest_dir, f'{name}.gz')
    txt_path = os.path.join(dest_dir, f'{name}.txt')
    
    print(f"Downloading {name}...")
    print(f"  URL: {url}")
    
    # Download with progress
    def report_progress(block_num, block_size, total_size):
        downloaded = block_num * block_size
        if total_size > 0:
            percent = min(100, downloaded * 100 / total_size)
            mb_downloaded = downloaded / (1024 * 1024)
            mb_total = total_size / (1024 * 1024)
            print(f"\r  Progress: {percent:.1f}% ({mb_downloaded:.1f}/{mb_total:.1f} MB)", end='', flush=True)
    
    urllib.request.urlretrieve(url, gz_path, reporthook=report_progress)
    print()  # New line after progress
    
    # Decompress
    print(f"  Decompressing...")
    with gzip.open(gz_path, 'rb') as f_in:
        with open(txt_path, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    
    # Remove .gz file to save space
    os.remove(gz_path)
    
    file_size = os.path.getsize(txt_path) / (1024 * 1024)
    print(f"  Done! File size: {file_size:.1f} MB")
    
    return txt_path


def filter_human_genes(input_path, output_path):
    """Filter gene_info to only include human genes (tax_id 9606)."""
    print(f"Filtering for human genes only (tax_id={HUMAN_TAX_ID})...")
    
    human_count = 0
    with open(input_path, 'r', encoding='utf-8') as f_in:
        with open(output_path, 'w', encoding='utf-8') as f_out:
            for line in f_in:
                # Keep header line
                if line.startswith('#'):
                    f_out.write(line)
                    continue
                
                # Check if this is a human gene
                parts = line.split('\t')
                if parts[0] == HUMAN_TAX_ID:
                    f_out.write(line)
                    human_count += 1
    
    print(f"  Found {human_count:,} human genes")
    return human_count


def main():
    """Download and prepare all data files."""
    os.makedirs(DATA_DIR, exist_ok=True)
    
    print("=" * 60)
    print("NCBI Gene Data Downloader")
    print("=" * 60)
    print()
    
    for name, info in FILES.items():
        print(f"[{name}] {info['description']}")
        txt_path = download_file(name, info['url'], DATA_DIR)
        
        # Filter to human-only for gene_info
        if name == 'gene_info':
            human_path = os.path.join(DATA_DIR, 'human_gene_info.txt')
            filter_human_genes(txt_path, human_path)
            # Keep full file for reference, but we'll use the filtered one
            print(f"  Human genes saved to: human_gene_info.txt")
        
        if name == 'gene2go':
            human_path = os.path.join(DATA_DIR, 'human_gene2go.txt')
            filter_human_genes(txt_path, human_path)
            print(f"  Human GO terms saved to: human_gene2go.txt")
        
        print()
    
    print("=" * 60)
    print("Download complete!")
    print()
    print("Next step: Run 'python build_database.py' to create the searchable database.")
    print("=" * 60)


if __name__ == '__main__':
    main()
