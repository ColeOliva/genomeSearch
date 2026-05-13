import os
import requests
import sys

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

# MGI (Mouse Genome Informatics) Data URLs
MGI_URLS = {
    # Maps Human Gene -> Mouse Ortholog -> Mammalian Phenotype (MP) IDs
    'HMD_HumanPhenotype.rpt': 'https://www.informatics.jax.org/downloads/reports/HMD_HumanPhenotype.rpt',
    
    # Maps MP IDs -> Readable trait names (e.g. "MP:0000001" -> "abnormal embryonic development")
    'VOC_MammalianPhenotype.rpt': 'https://www.informatics.jax.org/downloads/reports/VOC_MammalianPhenotype.rpt'
}

def download_file(url, filename):
    filepath = os.path.join(DATA_DIR, filename)
    if os.path.exists(filepath):
        print(f"{filename} already exists. Skipping download.")
        return

    print(f"Downloading {filename} from {url}...")
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    total_size = int(response.headers.get('content-length', 0))
    block_size = 1024 * 1024 # 1 MB
    downloaded = 0
    
    with open(filepath, 'wb') as f:
        for data in response.iter_content(block_size):
            f.write(data)
            downloaded += len(data)
            if total_size > 0:
                done = int(50 * downloaded / total_size)
                sys.stdout.write(f"\r[{'=' * done}{' ' * (50-done)}] {downloaded/1024/1024:.1f} MB")
                sys.stdout.flush()
    print(f"\nCompleted: {filename}")

def main():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        
    for filename, url in MGI_URLS.items():
        download_file(url, filename)

if __name__ == '__main__':
    main()
