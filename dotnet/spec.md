# Genome Search .NET Port: Python Behavior Specification

## Purpose and scope

This document records observable behavior in the current Python/Flask application
for the ASP.NET Core port. It is a behavior reference, not a claim that every
Python implementation detail should be copied into .NET.

**Sources inspected:** `schema.py`, `import_gwas.py`, `app.py`,
`scoring_metric.py`, `semantic_clustering.py`, and the three pytest modules under
`tests/`. The SQLite database and large data files were not read.

## Database schema

### Core tables

| Table | Columns and relationships |
|---|---|
| `species` | `tax_id` (PK, integer), `name` (required), `common_name`, `gene_count` (default 0). |
| `genes` | `gene_id` (PK), `tax_id` (required FK to `species`), `symbol` (required), `name`, `chromosome`, `map_location`, `description`, `gene_type`; `gene_id` is unique. |
| `gene_synonyms` | `id` (autoincrement PK), `gene_id` (required FK), `synonym` (required). |
| `gene_go_terms` | `id` (autoincrement PK), `gene_id` (required FK), `go_id` and `go_term` (required), `category` (`Function`, `Process`, or `Component`). |
| `gene_summaries` | `id` (autoincrement PK), `gene_id` (required and unique FK), `summary` (required), `source`. |

### Search and association tables

| Table | Columns and relationships |
|---|---|
| `gene_fts` | SQLite FTS5 virtual table with `gene_id` (unindexed) and `searchable_text`; Porter/unicode61 tokenization. The application expects symbol, name, description, synonyms, and imported trait text to be represented in the indexed text. |
| `traits` | Created by `import_gwas.py`: `trait_id` (autoincrement PK), `efo_trait`, `reported_trait` (unique), `trait_category`. |
| `gene_traits` | Created by `import_gwas.py`: `id` (autoincrement PK), `gene_id` (required FK), `gene_symbol` (required), optional `trait_id` FK, `reported_trait`, `efo_trait`, `p_value`, `p_value_text`, `risk_allele`, `risk_allele_freq`, `odds_ratio`, `beta_coefficient`, `ci_text`, `chromosome`, `position`, `snp_id`, `study_id`, `pubmed_id`, and `sample_description`. |

### Constraint and clinical tables

| Table | Columns and relationships |
|---|---|
| `gene_constraints` | `id` (autoincrement PK), `gene_id` (required FK), `gene_symbol` (required), `transcript`, `pli`, `loeuf`, `loeuf_lower`, `loeuf_upper`, `oe_lof`, `oe_mis`, `oe_mis_lower`, `oe_mis_upper`, `mis_z`, `oe_syn`, `syn_z`, `gnomad_version`. |
| `clinvar_gene_summary` | `id` (autoincrement PK), `gene_id` (required FK), `gene_symbol` (required), `total_submissions`, `total_alleles`, `pathogenic_alleles`, `uncertain_alleles`, `conflicting_alleles`, `gene_mim_number`. |
| `clinvar_variants` | `id` (autoincrement PK), `allele_id` (required), `variation_id`, `gene_id` (required FK), `gene_symbol`, `variant_name`, `variant_type`, `clinical_significance`, `review_status`, `phenotype_list`, `chromosome`, `start_pos`, `stop_pos`, `reference_allele`, `alternate_allele`, `rs_id`, `last_evaluated`, `origin`, `assembly`. The importer intends this table to contain pathogenic/likely pathogenic variants. |

### Mouse phenotype tables

| Table | Columns and relationships |
|---|---|
| `mouse_phenotype_terms` | `mp_id` (PK), `term_name` (required), `description`. |
| `mouse_phenotypes` | `id` (autoincrement PK), `gene_id` (required FK), `mouse_symbol`, `mp_id` (required FK to `mouse_phenotype_terms`). |

### Indexes and integrity expectations

Indexes cover gene symbol/chromosome/species, foreign-key lookup columns,
constraint metrics, ClinVar lookup fields, and mouse phenotype relationships.
Tests expect every gene to reference an existing species, every gene to have a
non-empty symbol, species `gene_count` to equal the actual count, and the FTS
row count to equal the gene row count. The tests also expect pLI in `[0, 1]`,
non-negative LOEUF, mostly valid GWAS gene links, and ClinVar variant
significances containing “pathogenic”.

## HTTP endpoints

All JSON responses are produced by Flask's JSON serializer. Database values may
therefore be `null` when the underlying column or related record is absent.

### `GET /`

Returns the rendered HTML search page (`templates/index.html`), not JSON.

### `GET /search`

Searches the FTS index and returns:

```json
{
  "results": [ /* result objects */ ],
  "query": "BRCA",
  "page": 1,
  "per_page": 50,
  "total": 1
}
```

An empty/whitespace `q` returns immediately with `{"results": [], "query": ""}`
and does not include pagination fields.

**Query parameters**

- `q` (string, required for useful results): trimmed search text. The
  implementation quotes the text and appends `*` for prefix matching after
  escaping double quotes.
- `species` (integer text): exact `tax_id` filter.
- `chromosome` (string): exact chromosome filter.
- `constraint`: `essential` means an associated pLI `> 0.9`;
  `constrained` means an associated LOEUF `< 0.35`; `tolerant` means no
  associated pLI `> 0.5`.
- `clinical`: `pathogenic` means ClinVar pathogenic allele count `> 0`;
  `gwas` means at least one `gene_traits` row; `disease` means either condition.
- `gene_type`: `protein-coding` exact match; `pseudo` contains `pseudo`;
  `ncRNA` contains `RNA` or `ncRNA`; `other` is none of those categories.
- `go_category`: `function`, `process`, `component`, or `any`, requiring a
  matching GO category or any GO row.
- `page`: parsed as an integer, minimum 1 (default 1).
- `per_page`: parsed as an integer, default 50; values <= 0 become 50 and the
  maximum is 100.

Each normal result contains:
`gene_id`, `tax_id`, `symbol`, `name`, `chromosome`, `map_location`,
`description`, `gene_type`, `species_name`, `matched_text`, `trait_count`,
`pli`, `loeuf`, `has_summary`, `has_gwas`, and `clinvar_pathogenic`.
Results are ordered by FTS rank. The normal query counts all matches before
pagination. If the FTS query raises `sqlite3.OperationalError`, the current
code falls back to a simple symbol/name/description `LIKE` query limited to
100 rows; its payload still reports the initialized `total` (usually zero).

The .NET port uses SQL Server `CONTAINS` against full-text indexes on gene,
synonym, GO-term, and GWAS trait text columns. Its test provider uses a
case-insensitive substring fallback because SQL Server full-text predicates
cannot be translated by the in-memory EF provider.

### `GET /gene/{gene_id}`

Returns a single gene detail object, or `404 {"error": "Gene not found"}`.
The base gene fields are all `genes` columns plus `species_name` and
`species_scientific`, followed by:

- `synonyms`: array of synonym strings.
- `functional_summary`: `{ "text": "...", "source": "..." }`, or `null`.
- `traits`: up to 20 GWAS rows ordered by ascending `p_value`; each row has
  `reported_trait`, `p_value`, `snp_id`, `risk_allele`, `odds_ratio`, `pubmed_id`.
- `trait_count`: total GWAS row count, not the 20-row response limit.
- `constraint`: one record or `null`, preferring gnomAD `v4.1`, then `v2.1.1`,
  then other versions; fields are `pli`, `loeuf`, `oe_lof`, `oe_mis`, `mis_z`,
  `gnomad_version`.
- `clinvar_summary`: one record or `null` with
  `pathogenic_alleles`, `uncertain_alleles`, `conflicting_alleles`,
  `total_alleles`, `gene_mim_number`.
- `clinvar_variants`: up to 20 records, ordered by review-status priority
  (practice guideline, expert panel, multiple submitters/no conflicts, single
  submitter, then other) and then clinical significance. Fields are
  `allele_id`, `variant_name`, `variant_type`, `clinical_significance`,
  `review_status`, `phenotype_list`, `chromosome`, `start_pos`, `rs_id`.
- `go_terms`: object with exactly `Function`, `Process`, and `Component` keys;
  each value contains `{ "go_id": "...", "go_term": "..." }` objects ordered
  by category and term. Unknown categories are omitted.

The route does not use a `species` query parameter; tests pass one in some
requests, but it is ignored.

### `GET /species`

Returns `{"species": [...]}` for species with `gene_count > 0`, ordered by
descending `gene_count`. Each item has `tax_id`, `name`, `common_name`, and
`gene_count`.

### `GET /chromosome/{chrom}`

Optional `species` integer query parameter defaults to human tax ID `9606`.
Returns:

```json
{
  "chromosome": "1",
  "genes": [
    {
      "gene_id": 1,
      "symbol": "GENE",
      "name": "...",
      "map_location": "...",
      "description": "...",
      "gene_type": "..."
    }
  ],
  "tax_id": 9606
}
```

Genes are filtered by exact chromosome and tax ID and ordered by
`map_location`. No result-count or pagination field is returned.

### `GET /chromosomes`

Optional `species` integer query parameter defaults to `9606`. Returns
`{"chromosomes": [{"chromosome": "...", "gene_count": 123}], "tax_id": 9606}`.
Chromosomes with null/empty values are excluded. Ordering is numeric
chromosomes first, then `X`, `Y`, `MT`, then other values.

### `GET /chromosome/{chrom}/region`

Optional `species` integer query parameter defaults to `9606`; optional
`region` string defaults to empty. Returns
`{"chromosome": "...", "region": "...", "genes": [...]}` with the same gene
fields as `/chromosome/{chrom}`. With a region, the query uses
`map_location LIKE "{chrom}{region}%"`; without one, it returns the chromosome.
Results are ordered by `map_location` and capped at 500.

### `GET /favicon.ico`

Returns an empty body with status `204`.

### `POST /_admin/clear_cache`

Clears the configured application cache and returns `{"status": "ok"}`. If
`ADMIN_CLEAR_TOKEN` is set, the caller must provide the same value in
`X-Admin-Token` or form field `token`; otherwise it returns
`401 {"error": "Unauthorized"}`. Cache-clear exceptions are swallowed.

## Normalized Pleiotropy Index (NPI)

The NPI is a batch-generated CSV, not an HTTP endpoint in the current app.
`scoring_metric.py` reads `results/semantic_pleiotropy_hubs.csv` and left-joins
it to `gene_constraints` by gene symbol. Missing pLI values are replaced with
the median pLI of the merged data.

For each row:

1. `log_traits = ln(1 + total_raw_traits)`.
2. `domain_score = (unique_domain_count / 8) * 50`.
3. `trait_score = (log_traits / max(log_traits)) * 25`.
4. `constraint_score = pli * 25`.
5. `Pleiotropy_Index = domain_score + trait_score + constraint_score`.

The semantic input is produced by `semantic_clustering.py`: traits are
categorized using keyword lists, `Other` and `Uncategorized` are removed,
unique retained domains are counted per gene, and distinct `reported_trait`
values provide `total_raw_traits`. The final CSV is sorted descending by the
index. `Is_Novel` is false for `APOE`, `ABO`, and symbols beginning with
`HLA-`; otherwise it is true. The script prints the top 10 overall and novel
genes and writes `results/normalized_pleiotropy_index.csv`.

The current API does not expose NPI values, and no pytest module directly tests
the scoring formula or its generated CSV.

The .NET port exposes the calculation as an internal application service rather
than an HTTP endpoint at this stage. APOE and ABO remain the Python benchmark
mega-hubs and are marked non-novel; HLA-prefixed symbols are also non-novel.

## Caching behavior

The default cache is an in-process, thread-safe dictionary with a 300-second
expiration. A Redis adapter can be selected with `CACHE_BACKEND=redis` and
`REDIS_URL`; if Redis cannot be constructed, the code falls back to the
in-process cache. Search cache keys include database mtime, query, every filter,
page, and page size. Touching the database therefore changes the key and avoids
using the old search response.

Cache serialization in the Redis adapter is JSON. Cache read/write/clear
failures are generally converted to cache misses or ignored, so search remains
available when caching fails. This is behavior to evaluate rather than a
recommended .NET error-handling policy.

The .NET port currently uses `IMemoryCache` behind `ISearchResponseCache`.
Search keys include the normalized query, every filter, page, and page size.
Entries use an absolute expiration configured by
`Search:CacheDurationSeconds` (300 seconds by default). A future Redis adapter
can implement the same interface without changing the search service.

Search query parameters are validated at the HTTP boundary: `q` is limited to
200 characters, `species` must be positive when supplied, `page` must be at
least 1, and `per_page` must be between 1 and 100. Invalid values return 400.
This is an intentional .NET API improvement over Python's direct integer
conversion and `per_page` normalization.

The `/search` endpoint uses ASP.NET Core's fixed-window partitioned rate limiter.
Requests are partitioned by client IP, permit 60 requests per 60 seconds by
default, queue no requests, and receive 429 after the limit. Both values are
configuration-driven (`Search:RateLimitPermitLimit` and
`Search:RateLimitWindowSeconds`). Integration tests override these settings to
two requests per window.

## Test coverage observed

### Flask/API tests (`tests/test_app.py`)

- Database file/connection/data and FTS availability.
- HTML index status, content type/content marker, and search form marker.
- Species status, JSON shape, required fields, non-empty data, and human tax ID.
- Search success, JSON shape, empty query, positive results, required result
  fields, species/chromosome/constraint/clinical/gene-type filters, combined
  filters, constraint/ClinVar result fields, quote handling, and maximum 100
  returned rows.
- Gene detail success/not-found behavior and presence of synonyms, GWAS traits,
  constraint, ClinVar summary, and ClinVar variants. Full-detail tests skip
  against the minimal sample database.
- Chromosome list/detail status and response shape, including chromosome X.
- Static CSS/JavaScript delivery and non-404 favicon behavior.

### Database tests (`tests/test_database.py`)

- Required tables and required `genes` columns.
- Gene-to-species integrity, non-empty symbols, accurate species counts, and
  equal `genes`/FTS row counts.
- Human/mouse/multiple-species presence, reasonable human chromosomes, BRCA1
  presence, common names, and working FTS search.
- GWAS volume, required columns, and orphan-link ratio.
- gnomAD volume/columns, pLI range, and non-negative LOEUF.
- ClinVar volume/columns, pathogenic-only significance, BRCA1 variants, and
  coverage of gene summaries for genes with variants.

### Cache tests (`tests/test_cache_behavior.py`)

- Search cache population and database-mtime key invalidation.
- Cache clearing without a configured token.
- Unauthorized clear when a token is configured.
- Authorized clear with `X-Admin-Token`.

## Open questions and migration decisions

1. **Schema ownership:** `gene_traits` and `traits` are absent from
   `schema.py` but are created by `import_gwas.py`. Should the .NET migrations
   treat the importer schema as authoritative and include both tables?
2. **NPI exposure:** NPI is currently an offline CSV workflow. Should the port
   expose it as a new endpoint, import the generated values, or leave it as a
   separate batch job?
3. **NPI edge cases:** The formula does not define behavior when the merged data
   is empty, `max(log_traits)` is zero, pLI median is unavailable, or domain
   counts exceed the assumed cap of 8.
4. **Search input errors:** `species`, `page`, and `per_page` are converted
   directly to integers. Invalid values can produce a server error rather than
   a documented 4xx response. The .NET API should define validation behavior.
5. **FTS fallback:** The fallback `LIKE` query does not preserve filters,
   highlighting, total count, or all normal result fields. Should SQL Server
   full-text failure be an explicit error instead of a degraded result?
6. **Endpoint wiring defect:** In `app.py`, the admin route declaration appears
   nested inside `chromosome_region` before the region query code. This may mean
   `/_admin/clear_cache` is registered only after the region endpoint is
   called. Confirm intended route registration before porting.
7. **Cache failure policy:** Python silently ignores cache failures. Should the
   .NET interface log cache errors with `ILogger` and continue, or fail requests
   when a configured distributed cache is unavailable?
8. **Constraint record selection:** Search aggregates multiple constraint rows
   with `MAX(pli)`/`MIN(loeuf)`, while gene detail selects a preferred gnomAD
   version. Confirm whether the port should preserve this intentionally
   different behavior.
9. **ClinVar variant semantics:** The schema comment says pathogenic/likely
   pathogenic only, but the API does not add a significance filter. Is the
   importer invariant sufficient for Azure SQL, or should the API enforce it?
10. **Region matching:** Region matching prefixes the requested region with the
    chromosome again (`{chrom}{region}%`). Confirm whether callers pass `p22`
    or `1p22`; the latter would search for `11p22%`.
11. **Security of cache administration:** With no `ADMIN_CLEAR_TOKEN`, any
    caller can clear the cache. Decide whether the port should require a
    configured secret or omit this administrative endpoint.
