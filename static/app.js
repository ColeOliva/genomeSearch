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

// Advanced filter elements
const toggleFiltersBtn = document.getElementById('toggle-filters');
const filterPanel = document.getElementById('filter-panel');
const filterChromosome = document.getElementById('filter-chromosome');
const filterConstraint = document.getElementById('filter-constraint');
const filterClinical = document.getElementById('filter-clinical');
const filterGeneType = document.getElementById('filter-gene-type');
const filterGoCategory = document.getElementById('filter-go-category');
const clearFiltersBtn = document.getElementById('clear-filters');

// Toggle filter panel
toggleFiltersBtn.addEventListener('click', () => {
    filterPanel.classList.toggle('hidden');
    toggleFiltersBtn.classList.toggle('active');
});

// Clear all filters
clearFiltersBtn.addEventListener('click', () => {
    filterChromosome.value = '';
    filterConstraint.value = '';
    filterClinical.value = '';
    filterGeneType.value = '';
    filterGoCategory.value = '';
    updateFilterIndicator();
    if (searchInput.value.trim()) {
        performSearch(searchInput.value);
    }
});

// Update filter indicator
function updateFilterIndicator() {
    const hasFilters = filterChromosome.value || filterConstraint.value || 
                       filterClinical.value || filterGeneType.value || filterGoCategory.value;
    toggleFiltersBtn.classList.toggle('has-filters', hasFilters);
}

// Re-search when filters change
[filterChromosome, filterConstraint, filterClinical, filterGeneType, filterGoCategory].forEach(el => {
    el.addEventListener('change', () => {
        updateFilterIndicator();
        if (searchInput.value.trim()) {
            performSearch(searchInput.value);
        }
    });
});

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
    const chromosome = filterChromosome.value;
    const constraint = filterConstraint.value;
    const clinical = filterClinical.value;
    const geneType = filterGeneType.value;
    const goCategory = filterGoCategory.value;
    
    resultsSection.classList.remove('hidden');
    resultsList.innerHTML = '<div class="loading">Searching</div>';
    queryDisplay.textContent = query;
    
    try {
        let url = `/search?q=${encodeURIComponent(query)}`;
        if (species) url += `&species=${species}`;
        if (chromosome) url += `&chromosome=${chromosome}`;
        if (constraint) url += `&constraint=${constraint}`;
        if (clinical) url += `&clinical=${clinical}`;
        if (geneType) url += `&gene_type=${geneType}`;
        if (goCategory) url += `&go_category=${goCategory}`;
        
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
    
    resultsList.innerHTML = results.map(gene => {
        // Determine constraint status
        let constraintBadge = '';
        if (gene.pli !== null && gene.pli > 0.9) {
            constraintBadge = '<span class="constraint-badge essential" title="High pLI (>0.9): Gene is likely essential">🔒 Essential</span>';
        } else if (gene.loeuf !== null && gene.loeuf < 0.35) {
            constraintBadge = '<span class="constraint-badge constrained" title="Low LOEUF (<0.35): Gene is constrained">⚠️ Constrained</span>';
        }
        
        // ClinVar pathogenic badge
        let clinvarBadge = '';
        if (gene.clinvar_pathogenic && gene.clinvar_pathogenic > 0) {
            clinvarBadge = `<span class="clinvar-badge" title="${gene.clinvar_pathogenic} pathogenic variants in ClinVar">⚕️ ${gene.clinvar_pathogenic} pathogenic</span>`;
        }
        // Functional summary badge (available)
        let summaryBadge = '';
        if (gene.has_summary) {
            summaryBadge = `<span class="summary-badge" title="Functional summary available">📖</span>`;
        }
        // gnomAD badge (presence of constraint metrics)
        let gnomadBadge = '';
        if (gene.pli !== null || gene.loeuf !== null) {
            const pliText = (gene.pli !== null && !Number.isNaN(Number(gene.pli))) ? Number(gene.pli).toFixed(2) : 'NA';
            const loeufText = (gene.loeuf !== null && !Number.isNaN(Number(gene.loeuf))) ? Number(gene.loeuf).toFixed(2) : 'NA';
            gnomadBadge = `<span class="gnomad-badge" title="gnomAD pLI: ${pliText}, LOEUF: ${loeufText}">GNOMAD</span>`;
        }
        // GWAS presence badge
        let gwasBadge = '';
        if (gene.has_gwas) {
            gwasBadge = `<span class="gwas-badge" title="This gene has GWAS associations">GWAS</span>`;
        }
        
        return `
        <div class="gene-card" data-gene-id="${gene.gene_id}">
            <div class="gene-header">
                <span class="gene-symbol">${escapeHtml(gene.symbol)}</span>
                <span class="gene-name">${escapeHtml(gene.name || '')}</span>
                ${constraintBadge}
                ${clinvarBadge}
                ${gnomadBadge}
                ${summaryBadge}
                ${gwasBadge}
                ${gene.trait_count > 0 ? `<span class="trait-badge" title="${gene.trait_count} GWAS associations">🧬 ${gene.trait_count}</span>` : ''}
            </div>
            <div class="gene-meta">
                ${gene.species_name ? `<span class="species-badge">${escapeHtml(gene.species_name)}</span>` : ''}
                ${gene.chromosome ? `<span class="chromosome-badge">Chr ${escapeHtml(gene.chromosome)}</span>` : ''}
                ${gene.map_location ? `<span>📍 ${escapeHtml(gene.map_location)}</span>` : ''}
                ${gene.gene_type && gene.gene_type !== 'unknown' ? `<span class="gene-type-badge">🏷️ ${escapeHtml(gene.gene_type)}</span>` : ''}
            </div>
            ${gene.description ? `<p class="gene-description">${escapeHtml(truncate(gene.description, 200))}</p>` : ''}
            ${gene.matched_text ? `<p class="gene-description"><small>Match: ${gene.matched_text}</small></p>` : ''}
        </div>
        `;
    }).join('');
    
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
        
        // Build constraint section HTML (gnomAD)
        let constraintHtml = '';
        if (gene.constraint) {
            const c = gene.constraint;
            const pliClass = c.pli > 0.9 ? 'constraint-high' : (c.pli > 0.5 ? 'constraint-medium' : 'constraint-low');
            const loeufClass = c.loeuf < 0.35 ? 'constraint-high' : (c.loeuf < 1.0 ? 'constraint-medium' : 'constraint-low');
            
            constraintHtml = `
            <div class="detail-section constraint-section">
                <h3>🧬 Mutation Tolerance (gnomAD)</h3>
                <p class="constraint-intro">How tolerant is this gene to loss-of-function mutations?</p>
                <div class="constraint-grid">
                    ${c.pli !== null ? `
                    <div class="constraint-metric ${pliClass}">
                        <div class="constraint-label">pLI Score</div>
                        <div class="constraint-value">${c.pli.toFixed(2)}</div>
                        <div class="constraint-desc">${c.pli > 0.9 ? 'Likely essential gene' : (c.pli > 0.5 ? 'Moderately constrained' : 'Tolerant to LoF')}</div>
                    </div>
                    ` : ''}
                    ${c.loeuf !== null ? `
                    <div class="constraint-metric ${loeufClass}">
                        <div class="constraint-label">LOEUF</div>
                        <div class="constraint-value">${c.loeuf.toFixed(2)}</div>
                        <div class="constraint-desc">${c.loeuf < 0.35 ? 'Strongly constrained' : (c.loeuf < 1.0 ? 'Moderately constrained' : 'Less constrained')}</div>
                    </div>
                    ` : ''}
                    ${c.oe_lof !== null ? `
                    <div class="constraint-metric">
                        <div class="constraint-label">O/E (LoF)</div>
                        <div class="constraint-value">${c.oe_lof.toFixed(3)}</div>
                        <div class="constraint-desc">Observed / Expected LoF variants</div>
                    </div>
                    ` : ''}
                    ${c.oe_mis !== null ? `
                    <div class="constraint-metric">
                        <div class="constraint-label">O/E (Missense)</div>
                        <div class="constraint-value">${c.oe_mis.toFixed(3)}</div>
                        <div class="constraint-desc">Observed / Expected missense</div>
                    </div>
                    ` : ''}
                </div>
                <p class="constraint-help">
                    <strong>pLI &gt; 0.9</strong>: Gene is likely essential (mutations cause disease)<br>
                    <strong>LOEUF &lt; 0.35</strong>: Gene is strongly constrained against loss-of-function variants<br>
                    <small>Source: gnomAD ${c.gnomad_version}</small>
                </p>
            </div>
            `;
        }
        
        // Build ClinVar section HTML
        let clinvarHtml = '';
        if (gene.clinvar_summary && gene.clinvar_summary.pathogenic_alleles > 0) {
            const cv = gene.clinvar_summary;
            clinvarHtml = `
            <div class="detail-section clinvar-section">
                <h3>⚕️ ClinVar Pathogenic Variants</h3>
                <p class="clinvar-intro">Known disease-causing mutations reported in this gene</p>
                <div class="clinvar-summary">
                    <div class="clinvar-stat pathogenic">
                        <div class="clinvar-stat-value">${cv.pathogenic_alleles.toLocaleString()}</div>
                        <div class="clinvar-stat-label">Pathogenic</div>
                    </div>
                    ${cv.uncertain_alleles > 0 ? `
                    <div class="clinvar-stat uncertain">
                        <div class="clinvar-stat-value">${cv.uncertain_alleles.toLocaleString()}</div>
                        <div class="clinvar-stat-label">Uncertain</div>
                    </div>
                    ` : ''}
                    ${cv.conflicting_alleles > 0 ? `
                    <div class="clinvar-stat conflicting">
                        <div class="clinvar-stat-value">${cv.conflicting_alleles.toLocaleString()}</div>
                        <div class="clinvar-stat-label">Conflicting</div>
                    </div>
                    ` : ''}
                    <div class="clinvar-stat total">
                        <div class="clinvar-stat-value">${cv.total_alleles.toLocaleString()}</div>
                        <div class="clinvar-stat-label">Total Alleles</div>
                    </div>
                </div>
                ${gene.clinvar_variants && gene.clinvar_variants.length > 0 ? `
                <div class="clinvar-variants">
                    <h4>Top Pathogenic Variants</h4>
                    <table class="clinvar-table">
                        <thead>
                            <tr>
                                <th>Variant</th>
                                <th>Type</th>
                                <th>Significance</th>
                                <th>Condition</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${gene.clinvar_variants.slice(0, 10).map(v => `
                                <tr>
                                    <td>
                                        <a href="https://www.ncbi.nlm.nih.gov/clinvar/variation/${v.allele_id}/" target="_blank" title="${escapeHtml(v.variant_name || '')}">
                                            ${escapeHtml(truncateVariant(v.variant_name))}
                                        </a>
                                        ${v.rs_id ? `<span class="rs-tag">rs${v.rs_id}</span>` : ''}
                                    </td>
                                    <td><span class="variant-type">${escapeHtml(v.variant_type || '')}</span></td>
                                    <td><span class="clinvar-sig ${v.clinical_significance?.toLowerCase().includes('pathogenic') ? 'sig-pathogenic' : ''}">${escapeHtml(truncate(v.clinical_significance, 30))}</span></td>
                                    <td><span class="condition-text" title="${escapeHtml(v.phenotype_list || '')}">${escapeHtml(truncate(v.phenotype_list, 50)) || '-'}</span></td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                    ${gene.clinvar_variants.length > 10 ? `<p class="clinvar-more">Showing top 10 of ${gene.clinvar_variants.length} variants</p>` : ''}
                </div>
                ` : ''}
                ${cv.gene_mim_number ? `<p class="clinvar-mim">OMIM Gene: <a href="https://www.omim.org/entry/${cv.gene_mim_number}" target="_blank">${cv.gene_mim_number}</a></p>` : ''}
            </div>
            `;
        }
        
        // Build Gene Ontology section HTML
        let goHtml = '';
        if (gene.go_terms) {
            const hasFunction = gene.go_terms.Function && gene.go_terms.Function.length > 0;
            const hasProcess = gene.go_terms.Process && gene.go_terms.Process.length > 0;
            const hasComponent = gene.go_terms.Component && gene.go_terms.Component.length > 0;
            
            if (hasFunction || hasProcess || hasComponent) {
                goHtml = `
                <div class="detail-section go-section">
                    <h3>🔬 Gene Ontology</h3>
                    ${hasFunction ? `
                    <div class="go-category">
                        <h4>Molecular Function</h4>
                        <div class="go-terms">
                            ${gene.go_terms.Function.slice(0, 8).map(t => 
                                `<a href="https://amigo.geneontology.org/amigo/term/${t.go_id}" target="_blank" class="go-tag go-function" title="${escapeHtml(t.go_id)}">${escapeHtml(t.go_term)}</a>`
                            ).join('')}
                            ${gene.go_terms.Function.length > 8 ? `<span class="go-more">+${gene.go_terms.Function.length - 8} more</span>` : ''}
                        </div>
                    </div>
                    ` : ''}
                    ${hasProcess ? `
                    <div class="go-category">
                        <h4>Biological Process</h4>
                        <div class="go-terms">
                            ${gene.go_terms.Process.slice(0, 8).map(t => 
                                `<a href="https://amigo.geneontology.org/amigo/term/${t.go_id}" target="_blank" class="go-tag go-process" title="${escapeHtml(t.go_id)}">${escapeHtml(t.go_term)}</a>`
                            ).join('')}
                            ${gene.go_terms.Process.length > 8 ? `<span class="go-more">+${gene.go_terms.Process.length - 8} more</span>` : ''}
                        </div>
                    </div>
                    ` : ''}
                    ${hasComponent ? `
                    <div class="go-category">
                        <h4>Cellular Component</h4>
                        <div class="go-terms">
                            ${gene.go_terms.Component.slice(0, 8).map(t => 
                                `<a href="https://amigo.geneontology.org/amigo/term/${t.go_id}" target="_blank" class="go-tag go-component" title="${escapeHtml(t.go_id)}">${escapeHtml(t.go_term)}</a>`
                            ).join('')}
                            ${gene.go_terms.Component.length > 8 ? `<span class="go-more">+${gene.go_terms.Component.length - 8} more</span>` : ''}
                        </div>
                    </div>
                    ` : ''}
                </div>
                `;
            }
        }
        
        detailContent.innerHTML = `
            <div class="detail-symbol">${escapeHtml(gene.symbol)}</div>
            <div class="detail-name">${escapeHtml(gene.name || 'Unknown')}</div>
            
            ${gene.functional_summary ? `
            <div class="detail-section functional-summary">
                <h3>📖 Function</h3>
                <p class="summary-text">${escapeHtml(gene.functional_summary.text)}</p>
                <span class="summary-source">Source: ${escapeHtml(gene.functional_summary.source)}</span>
            </div>
            ` : ''}
            
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
            
            ${constraintHtml}
            
            ${clinvarHtml}
            
            ${goHtml}
            
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
                <a href="https://gnomad.broadinstitute.org/gene/${encodeURIComponent(gene.symbol)}?dataset=gnomad_r4" target="_blank">
                    🧬 gnomAD
                </a>
                <a href="https://www.ncbi.nlm.nih.gov/clinvar/?term=${encodeURIComponent(gene.symbol)}%5Bgene%5D" target="_blank">
                    ⚕️ ClinVar
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

function truncateVariant(name) {
    // Truncate variant names intelligently
    if (!name) return '';
    if (name.length <= 40) return name;
    // Try to find a good break point (at parenthesis or colon)
    const colonIdx = name.indexOf(':');
    if (colonIdx > 10 && colonIdx < 35) {
        return name.substring(0, colonIdx + 15) + '...';
    }
    return name.substring(0, 37) + '...';
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
