namespace GenomeSearch.Api.Search;

public sealed record GeneSearchRequest(
    string? Query,
    int? Species = null,
    string? Chromosome = null,
    string? Constraint = null,
    string? Clinical = null,
    string? GeneType = null,
    string? GoCategory = null,
    int Page = 1,
    int PerPage = 50);

public sealed record GeneSearchResult(
    int GeneId,
    int TaxId,
    string Symbol,
    string? Name,
    string? Chromosome,
    string? MapLocation,
    string? Description,
    string? GeneType,
    string? SpeciesName,
    int TraitCount,
    double? Pli,
    double? Loeuf,
    bool HasSummary,
    bool HasGwas,
    int? ClinvarPathogenic);

public sealed record GeneSearchResponse(
    IReadOnlyList<GeneSearchResult> Results,
    string Query,
    int Page,
    int PerPage,
    int Total);
