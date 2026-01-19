/**
 * Genome Search - Frontend JavaScript (Multi-Species)
 */

const searchInput = document.getElementById('search-input');
const searchBtn = document.getElementById('search-btn');
const speciesFilter = document.getElementById('species-filter');
const resultsSection = document.getElementById('results-section');
const resultsList = document.getElementById('results-list');
const queryDisplay = document.getElementById('query-display');
const resultCount = document.getElementById('result-count');
const geneDetail = document.getElementById('gene-detail');
const detailContent = document.getElementById('detail-content');
const closeDetail = document.getElementById('close-detail');

// Load species list on page load
async function loadSpecies() {
    try {
        const response = await fetch('/species');
        const data = await response.json();
        
        data.species.forEach(sp => {
            const option = document.createElement('option');
            option.value = sp.tax_id;
            option.textContent = `${sp.common_name} (${sp.gene_count.toLocaleString()} genes)`;
            speciesFilter.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading species:', error);
    }
}

// Search functionality
async function performSearch(query) {
    if (!query.trim()) return;
    
    const species = speciesFilter.value;
    
    resultsSection.classList.remove('hidden');
    resultsList.innerHTML = '<div class="loading">Searching</div>';
    queryDisplay.textContent = query;
    
    try {
        let url = `/search?q=${encodeURIComponent(query)}`;
        if (species) {
            url += `&species=${species}`;
        }
        const response = await fetch(url);
        const data = await response.json();
        
        displayResults(data.results);
    } catch (error) {
        resultsList.innerHTML = '<p class="error">Error searching. Please try again.</p>';
        console.error('Search error:', error);
    }
}

function displayResults(results) {
    if (results.length === 0) {
        resultsList.innerHTML = '<p class="no-results">No genes found. Try different keywords or a different species.</p>';
        resultCount.textContent = '0 results';
        return;
    }
    
    resultCount.textContent = `${results.length} result${results.length !== 1 ? 's' : ''}`;
    
    resultsList.innerHTML = results.map(gene => `
        <div class="gene-card" data-gene-id="${gene.gene_id}">
            <div class="gene-header">
                <span class="gene-symbol">${escapeHtml(gene.symbol)}</span>
                <span class="gene-name">${escapeHtml(gene.name || '')}</span>
                ${gene.trait_count > 0 ? `<span class="trait-badge" title="${gene.trait_count} GWAS associations">🧬 ${gene.trait_count}</span>` : ''}
            </div>
            <div class="gene-meta">
                ${gene.species_name ? `<span class="species-badge">${escapeHtml(gene.species_name)}</span>` : ''}
                ${gene.chromosome ? `<span class="chromosome-badge">Chr ${escapeHtml(gene.chromosome)}</span>` : ''}
                ${gene.map_location ? `<span>📍 ${escapeHtml(gene.map_location)}</span>` : ''}
                ${gene.gene_type && gene.gene_type !== 'unknown' ? `<span>🏷️ ${escapeHtml(gene.gene_type)}</span>` : ''}
            </div>
            ${gene.description ? `<p class="gene-description">${escapeHtml(truncate(gene.description, 200))}</p>` : ''}
            ${gene.matched_text ? `<p class="gene-description"><small>Match: ${gene.matched_text}</small></p>` : ''}
        </div>
    `).join('');
    
    // Add click handlers
    document.querySelectorAll('.gene-card').forEach(card => {
        card.addEventListener('click', () => {
            showGeneDetail(card.dataset.geneId);
        });
    });
}

async function showGeneDetail(geneId) {
    geneDetail.classList.remove('hidden');
    geneDetail.classList.add('visible');
    detailContent.innerHTML = '<div class="loading">Loading</div>';
    
    try {
        const response = await fetch(`/gene/${geneId}`);
        const gene = await response.json();
        
        if (gene.error) {
            detailContent.innerHTML = '<p>Gene not found.</p>';
            return;
        }
        
        // Build traits section HTML
        let traitsHtml = '';
        if (gene.traits && gene.traits.length > 0) {
            traitsHtml = `
            <div class="detail-section traits-section">
                <h3>🧬 Associated Traits/Diseases</h3>
                <p class="traits-intro">${gene.trait_count} association${gene.trait_count > 1 ? 's' : ''} from GWAS studies</p>
                <div class="traits-list">
                    ${gene.traits.map(t => `
                        <div class="trait-item">
                            <div class="trait-name">${escapeHtml(t.reported_trait)}</div>
                            <div class="trait-details">
                                ${t.snp_id ? `<span class="trait-snp">${escapeHtml(t.snp_id)}</span>` : ''}
                                ${t.p_value ? `<span class="trait-pvalue">p=${formatPValue(t.p_value)}</span>` : ''}
                                ${t.odds_ratio ? `<span class="trait-or">OR: ${t.odds_ratio.toFixed(2)}</span>` : ''}
                                ${t.pubmed_id ? `<a href="https://pubmed.ncbi.nlm.nih.gov/${t.pubmed_id}" target="_blank" class="trait-pubmed">📄 PubMed</a>` : ''}
                            </div>
                        </div>
                    `).join('')}
                </div>
                ${gene.trait_count > 20 ? `<p class="traits-more">Showing top 20 of ${gene.trait_count} associations (sorted by p-value)</p>` : ''}
            </div>
            `;
        }
        
        detailContent.innerHTML = `
            <div class="detail-symbol">${escapeHtml(gene.symbol)}</div>
            <div class="detail-name">${escapeHtml(gene.name || 'Unknown')}</div>
            
            <div class="detail-section">
                <h3>Species</h3>
                <p>${escapeHtml(gene.species_name || 'Unknown')} <em>(${escapeHtml(gene.species_scientific || '')})</em></p>
            </div>
            
            <div class="detail-section">
                <h3>Chromosome Location</h3>
                <div class="chromosome-visual">
                    <span class="chromosome-label">${gene.chromosome || '?'}</span>
                </div>
                ${gene.map_location ? `<p>Position: ${escapeHtml(gene.map_location)}</p>` : ''}
            </div>
            
            ${gene.description ? `
            <div class="detail-section">
                <h3>Description</h3>
                <p>${escapeHtml(gene.description)}</p>
            </div>
            ` : ''}
            
            ${traitsHtml}
            
            ${gene.gene_type && gene.gene_type !== 'unknown' ? `
            <div class="detail-section">
                <h3>Gene Type</h3>
                <p>${escapeHtml(gene.gene_type)}</p>
            </div>
            ` : ''}
            
            ${gene.synonyms && gene.synonyms.length > 0 ? `
            <div class="detail-section">
                <h3>Also Known As</h3>
                <div class="synonyms-list">
                    ${gene.synonyms.slice(0, 10).map(s => `<span class="synonym-tag">${escapeHtml(s)}</span>`).join('')}
                    ${gene.synonyms.length > 10 ? `<span class="synonym-tag">+${gene.synonyms.length - 10} more</span>` : ''}
                </div>
            </div>
            ` : ''}
            
            <div class="external-links">
                <h3>Learn More</h3>
                <a href="https://www.ncbi.nlm.nih.gov/gene/${gene.gene_id}" target="_blank">
                    📚 NCBI Gene Database
                </a>
                <a href="https://www.genecards.org/cgi-bin/carddisp.pl?gene=${encodeURIComponent(gene.symbol)}" target="_blank">
                    🃏 GeneCards
                </a>
                <a href="https://www.uniprot.org/uniprotkb?query=${encodeURIComponent(gene.symbol)}+AND+organism_id:${gene.tax_id}" target="_blank">
                    🧪 UniProt
                </a>
                ${gene.tax_id === 9606 ? `
                <a href="https://www.omim.org/search?search=${encodeURIComponent(gene.symbol)}" target="_blank">
                    🏥 OMIM (Disease Associations)
                </a>
                <a href="https://www.ebi.ac.uk/gwas/genes/${encodeURIComponent(gene.symbol)}" target="_blank">
                    📊 GWAS Catalog
                </a>
                ` : ''}
            </div>
        `;
    } catch (error) {
        detailContent.innerHTML = '<p>Error loading gene details.</p>';
        console.error('Detail error:', error);
    }
}

function closeGeneDetail() {
    geneDetail.classList.remove('visible');
    setTimeout(() => {
        geneDetail.classList.add('hidden');
    }, 300);
}

// Utility functions
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function truncate(text, maxLength) {
    if (!text || text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

function formatPValue(pval) {
    if (!pval) return '';
    if (pval < 0.0001) {
        return pval.toExponential(1);
    }
    return pval.toFixed(4);
}

// Event listeners
searchBtn.addEventListener('click', () => performSearch(searchInput.value));

searchInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        performSearch(searchInput.value);
    }
});

closeDetail.addEventListener('click', closeGeneDetail);

// Close detail panel when clicking outside
document.addEventListener('click', (e) => {
    if (geneDetail.classList.contains('visible') && 
        !geneDetail.contains(e.target) && 
        !e.target.closest('.gene-card') &&
        !e.target.closest('.gene-marker') &&
        !e.target.closest('.chr-gene-item') &&
        !e.target.closest('.highlight-tag')) {
        closeGeneDetail();
    }
});

// Handle hint clicks
document.querySelectorAll('.hint').forEach(hint => {
    hint.addEventListener('click', (e) => {
        e.preventDefault();
        searchInput.value = hint.textContent;
        performSearch(hint.textContent);
    });
});

// Load species on page load
loadSpecies();

// Focus search input on load
searchInput.focus();

/* ================================
   Chromosome Viewer
   ================================ */

const chromosomeViewer = document.getElementById('chromosome-viewer');
const closeChromosomeBtn = document.getElementById('close-chromosome');
const karyotypeView = document.getElementById('karyotype-view');
const karyotypeGrid = document.getElementById('karyotype-grid');
const chromosomeDetail = document.getElementById('chromosome-detail');
const chromosomeTitle = document.getElementById('chromosome-title');
const chromosomeIdeogram = document.getElementById('chromosome-ideogram');
const chromosomeGeneList = document.getElementById('chromosome-gene-list');
const chromosomeSpecies = document.getElementById('chromosome-species');
const viewChromosomesBtn = document.getElementById('view-chromosomes-btn');
const backToKaryotype = document.getElementById('back-to-karyotype');
const zoomInBtn = document.getElementById('zoom-in');
const zoomOutBtn = document.getElementById('zoom-out');
const zoomResetBtn = document.getElementById('zoom-reset');
const zoomLevelDisplay = document.getElementById('zoom-level');
const regionSelect = document.getElementById('region-select');
const regionSearch = document.getElementById('region-search');
const highlightedGenesPanel = document.getElementById('highlighted-genes');
const highlightedList = document.getElementById('highlighted-list');

let currentSearchResults = [];
let currentZoom = 100;
let currentChromosome = null;
let chromosomeData = {};

// Store search results for highlighting
function storeSearchResults(results) {
    currentSearchResults = results;
}

// Open chromosome viewer
viewChromosomesBtn.addEventListener('click', () => {
    openChromosomeViewer();
});

async function openChromosomeViewer() {
    chromosomeViewer.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
    
    // Load species for chromosome viewer
    await loadChromosomeSpecies();
    
    // Show karyotype view
    showKaryotypeView();
}

function closeChromosomeViewer() {
    chromosomeViewer.classList.add('hidden');
    document.body.style.overflow = '';
}

closeChromosomeBtn.addEventListener('click', closeChromosomeViewer);

// ESC key to close
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && !chromosomeViewer.classList.contains('hidden')) {
        if (!chromosomeDetail.classList.contains('hidden')) {
            showKaryotypeView();
        } else {
            closeChromosomeViewer();
        }
    }
});

async function loadChromosomeSpecies() {
    try {
        const response = await fetch('/species');
        const data = await response.json();
        
        chromosomeSpecies.innerHTML = '';
        data.species.forEach(sp => {
            const option = document.createElement('option');
            option.value = sp.tax_id;
            option.textContent = sp.common_name;
            chromosomeSpecies.appendChild(option);
        });
        
        // Default to human or the species from search filter
        if (speciesFilter.value) {
            chromosomeSpecies.value = speciesFilter.value;
        }
    } catch (error) {
        console.error('Error loading species:', error);
    }
}

chromosomeSpecies.addEventListener('change', () => {
    if (chromosomeDetail.classList.contains('hidden')) {
        showKaryotypeView();
    } else {
        loadChromosomeDetail(currentChromosome);
    }
});

async function showKaryotypeView() {
    karyotypeView.classList.remove('hidden');
    chromosomeDetail.classList.add('hidden');
    
    const taxId = chromosomeSpecies.value || 9606;
    
    karyotypeGrid.innerHTML = '<div class="loading">Loading chromosomes</div>';
    
    try {
        const response = await fetch(`/chromosomes?species=${taxId}`);
        const data = await response.json();
        
        // Group search results by chromosome
        const highlightsByChrom = {};
        currentSearchResults.forEach(gene => {
            if (gene.chromosome && gene.tax_id == taxId) {
                if (!highlightsByChrom[gene.chromosome]) {
                    highlightsByChrom[gene.chromosome] = [];
                }
                highlightsByChrom[gene.chromosome].push(gene);
            }
        });
        
        karyotypeGrid.innerHTML = data.chromosomes.map(chr => {
            const highlights = highlightsByChrom[chr.chromosome] || [];
            const isHighlighted = highlights.length > 0;
            
            let shapeClass = 'chr-shape';
            if (chr.chromosome === 'X') shapeClass += ' chr-x';
            else if (chr.chromosome === 'Y') shapeClass += ' chr-y';
            else if (chr.chromosome === 'MT' || chr.chromosome === 'M') shapeClass += ' chr-mt';
            
            return `
                <div class="chromosome-card ${isHighlighted ? 'highlighted' : ''}" 
                     data-chromosome="${chr.chromosome}">
                    <div class="chr-ideogram">
                        <div class="${shapeClass}"></div>
                    </div>
                    <div class="chr-name">${chr.chromosome}</div>
                    <div class="chr-genes">${chr.gene_count.toLocaleString()} genes</div>
                    ${isHighlighted ? `<div class="chr-highlights">${highlights.length} match${highlights.length > 1 ? 'es' : ''}</div>` : ''}
                </div>
            `;
        }).join('');
        
        // Add click handlers
        document.querySelectorAll('.chromosome-card').forEach(card => {
            card.addEventListener('click', () => {
                loadChromosomeDetail(card.dataset.chromosome);
            });
        });
        
        // Show highlighted genes panel if we have search results
        updateHighlightedGenesPanel();
        
    } catch (error) {
        karyotypeGrid.innerHTML = '<p class="error">Error loading chromosomes.</p>';
        console.error('Error:', error);
    }
}

async function loadChromosomeDetail(chromosome) {
    currentChromosome = chromosome;
    karyotypeView.classList.add('hidden');
    chromosomeDetail.classList.remove('hidden');
    
    chromosomeTitle.textContent = `Chromosome ${chromosome}`;
    currentZoom = 100;
    updateZoomDisplay();
    
    const taxId = chromosomeSpecies.value || 9606;
    const region = regionSearch.value || '';
    
    chromosomeGeneList.innerHTML = '<div class="loading">Loading genes</div>';
    
    try {
        const response = await fetch(`/chromosome/${chromosome}?species=${taxId}`);
        const data = await response.json();
        
        chromosomeData = data;
        renderIdeogram(data.genes);
        renderGeneList(data.genes);
        
    } catch (error) {
        chromosomeGeneList.innerHTML = '<p class="error">Error loading chromosome data.</p>';
        console.error('Error:', error);
    }
}

function renderIdeogram(genes) {
    const taxId = chromosomeSpecies.value || 9606;
    
    // Get highlighted gene IDs
    const highlightedIds = new Set(
        currentSearchResults
            .filter(g => g.chromosome === currentChromosome && g.tax_id == taxId)
            .map(g => g.gene_id)
    );
    
    // Group genes by cytogenetic band
    const bandGroups = {};
    genes.forEach(gene => {
        const band = gene.map_location || 'unknown';
        if (!bandGroups[band]) {
            bandGroups[band] = [];
        }
        bandGroups[band].push(gene);
    });
    
    // Sort bands
    const sortedBands = Object.keys(bandGroups).sort((a, b) => {
        // p arm comes before q arm
        const aArm = a.includes('p') ? 0 : 1;
        const bArm = b.includes('p') ? 0 : 1;
        if (aArm !== bArm) return aArm - bArm;
        return a.localeCompare(b, undefined, {numeric: true});
    });
    
    // Calculate position for each gene based on band
    const totalBands = sortedBands.length;
    let genePositions = [];
    
    sortedBands.forEach((band, bandIndex) => {
        const basePosition = (bandIndex / totalBands) * 100;
        const bandGenes = bandGroups[band];
        
        bandGenes.forEach((gene, geneIndex) => {
            const offset = (geneIndex / Math.max(bandGenes.length, 1)) * (100 / totalBands) * 0.8;
            genePositions.push({
                ...gene,
                position: Math.min(basePosition + offset, 99),
                isHighlighted: highlightedIds.has(gene.gene_id)
            });
        });
    });
    
    // Limit visible markers for performance
    const maxMarkers = 200;
    let visibleGenes = genePositions;
    
    // Prioritize highlighted genes
    if (genePositions.length > maxMarkers) {
        const highlighted = genePositions.filter(g => g.isHighlighted);
        const others = genePositions.filter(g => !g.isHighlighted);
        const sampledOthers = others.filter((_, i) => i % Math.ceil(others.length / (maxMarkers - highlighted.length)) === 0);
        visibleGenes = [...highlighted, ...sampledOthers].slice(0, maxMarkers);
    }
    
    chromosomeIdeogram.innerHTML = `
        <div class="ideogram-container" style="width: ${currentZoom}%">
            <div class="ideogram-bar">
                <span class="arm-label p-arm">p (short arm)</span>
                <div class="centromere"></div>
                <span class="arm-label q-arm">q (long arm)</span>
                ${visibleGenes.map(gene => `
                    <div class="gene-marker ${gene.isHighlighted ? 'highlighted' : ''}" 
                         style="left: ${gene.position}%"
                         data-gene-id="${gene.gene_id}">
                        <span class="marker-tooltip">
                            <span class="tooltip-symbol">${escapeHtml(gene.symbol)}</span>
                            ${gene.name ? `<span class="tooltip-name">${escapeHtml(truncate(gene.name, 50))}</span>` : ''}
                            <span class="tooltip-location">📍 ${escapeHtml(gene.map_location || 'Unknown')}</span>
                            <span class="tooltip-hint">Click for details</span>
                        </span>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
    
    // Add click handlers to markers
    document.querySelectorAll('.gene-marker').forEach(marker => {
        marker.addEventListener('click', (e) => {
            e.stopPropagation();
            const geneId = marker.dataset.geneId;
            console.log('Marker clicked, gene ID:', geneId);
            showGeneDetail(geneId);
        });
    });
}

function renderGeneList(genes) {
    const taxId = chromosomeSpecies.value || 9606;
    const regionFilter = regionSelect.value;
    const regionSearchVal = regionSearch.value.toLowerCase();
    
    // Get highlighted gene IDs
    const highlightedIds = new Set(
        currentSearchResults
            .filter(g => g.chromosome === currentChromosome && g.tax_id == taxId)
            .map(g => g.gene_id)
    );
    
    // Filter genes
    let filteredGenes = genes;
    
    if (regionFilter) {
        filteredGenes = filteredGenes.filter(g => 
            g.map_location && g.map_location.includes(regionFilter)
        );
    }
    
    if (regionSearchVal) {
        filteredGenes = filteredGenes.filter(g => 
            (g.map_location && g.map_location.toLowerCase().includes(regionSearchVal)) ||
            (g.symbol && g.symbol.toLowerCase().includes(regionSearchVal))
        );
    }
    
    // Sort: highlighted first, then by location
    filteredGenes.sort((a, b) => {
        const aHigh = highlightedIds.has(a.gene_id) ? 0 : 1;
        const bHigh = highlightedIds.has(b.gene_id) ? 0 : 1;
        if (aHigh !== bHigh) return aHigh - bHigh;
        return (a.map_location || '').localeCompare(b.map_location || '', undefined, {numeric: true});
    });
    
    // Limit display
    const displayLimit = 500;
    const displayGenes = filteredGenes.slice(0, displayLimit);
    
    chromosomeGeneList.innerHTML = displayGenes.map(gene => `
        <div class="chr-gene-item ${highlightedIds.has(gene.gene_id) ? 'highlighted' : ''}" 
             data-gene-id="${gene.gene_id}">
            <span class="gene-symbol">${escapeHtml(gene.symbol)}</span>
            <span class="gene-location">${escapeHtml(gene.map_location || '?')}</span>
            <span class="gene-name">${escapeHtml(truncate(gene.name || '', 40))}</span>
        </div>
    `).join('');
    
    if (filteredGenes.length > displayLimit) {
        chromosomeGeneList.innerHTML += `<div class="chr-gene-item" style="justify-content: center; color: var(--text-muted);">
            +${(filteredGenes.length - displayLimit).toLocaleString()} more genes. Use filters to narrow down.
        </div>`;
    }
    
    // Add click handlers
    document.querySelectorAll('.chr-gene-item').forEach(item => {
        if (item.dataset.geneId) {
            item.addEventListener('click', (e) => {
                e.stopPropagation();
                const geneId = item.dataset.geneId;
                console.log('Gene item clicked, gene ID:', geneId);
                showGeneDetail(geneId);
            });
        }
    });
}

function updateHighlightedGenesPanel() {
    const taxId = chromosomeSpecies.value || 9606;
    const matchingResults = currentSearchResults.filter(g => g.tax_id == taxId);
    
    if (matchingResults.length === 0) {
        highlightedGenesPanel.classList.add('hidden');
        return;
    }
    
    highlightedGenesPanel.classList.remove('hidden');
    highlightedList.innerHTML = matchingResults.slice(0, 20).map(gene => `
        <span class="highlight-tag" data-chromosome="${gene.chromosome}" data-gene-id="${gene.gene_id}">
            ${escapeHtml(gene.symbol)} (${gene.chromosome || '?'})
        </span>
    `).join('');
    
    if (matchingResults.length > 20) {
        highlightedList.innerHTML += `<span class="highlight-tag">+${matchingResults.length - 20} more</span>`;
    }
    
    // Add click handlers
    document.querySelectorAll('.highlight-tag[data-chromosome]').forEach(tag => {
        tag.addEventListener('click', () => {
            if (tag.dataset.chromosome) {
                loadChromosomeDetail(tag.dataset.chromosome);
            }
        });
    });
}

// Navigation
backToKaryotype.addEventListener('click', showKaryotypeView);

// Zoom controls
zoomInBtn.addEventListener('click', () => {
    currentZoom = Math.min(currentZoom + 50, 500);
    updateZoomDisplay();
    if (chromosomeData.genes) {
        renderIdeogram(chromosomeData.genes);
    }
});

zoomOutBtn.addEventListener('click', () => {
    currentZoom = Math.max(currentZoom - 50, 50);
    updateZoomDisplay();
    if (chromosomeData.genes) {
        renderIdeogram(chromosomeData.genes);
    }
});

zoomResetBtn.addEventListener('click', () => {
    currentZoom = 100;
    updateZoomDisplay();
    showKaryotypeView();
});

function updateZoomDisplay() {
    zoomLevelDisplay.textContent = `${currentZoom}%`;
}

// Region filters
regionSelect.addEventListener('change', () => {
    if (chromosomeData.genes) {
        renderGeneList(chromosomeData.genes);
    }
});

regionSearch.addEventListener('input', debounce(() => {
    if (chromosomeData.genes) {
        renderGeneList(chromosomeData.genes);
    }
}, 300));

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Update the displayResults function to store results
const originalDisplayResults = displayResults;
displayResults = function(results) {
    storeSearchResults(results);
    originalDisplayResults(results);
};
