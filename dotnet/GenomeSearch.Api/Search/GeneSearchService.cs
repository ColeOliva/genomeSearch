using GenomeSearch.Api.Data;
using GenomeSearch.Api.Models;
using Microsoft.EntityFrameworkCore;

namespace GenomeSearch.Api.Search;

public sealed class GeneSearchService(
    GenomeSearchDbContext db,
    ISearchResponseCache cache) : IGeneSearchService
{
    private const int DefaultPageSize = 50;
    private const int MaxPageSize = 100;

    public async Task<GeneSearchResponse> SearchAsync(
        GeneSearchRequest request,
        CancellationToken cancellationToken = default)
    {
        var queryText = request.Query?.Trim() ?? string.Empty;
        if (queryText.Length == 0)
        {
            return new GeneSearchResponse([], queryText, 1, DefaultPageSize, 0);
        }

        var page = Math.Max(request.Page, 1);
        var perPage = request.PerPage <= 0
            ? DefaultPageSize
            : Math.Min(request.PerPage, MaxPageSize);
        var cacheKey = BuildCacheKey(request with { Query = queryText, Page = page, PerPage = perPage });
        if (cache.TryGet(cacheKey, out var cached))
        {
            return cached;
        }

        var query = db.Genes.AsNoTracking();
        query = ApplySearch(query, queryText);

        if (request.Species is not null)
        {
            query = query.Where(g => g.TaxId == request.Species.Value);
        }

        if (!string.IsNullOrWhiteSpace(request.Chromosome))
        {
            query = query.Where(g => g.Chromosome == request.Chromosome);
        }

        query = ApplyConstraintFilter(query, request.Constraint);
        query = ApplyClinicalFilter(query, request.Clinical);
        query = ApplyGeneTypeFilter(query, request.GeneType);
        query = ApplyGoCategoryFilter(query, request.GoCategory);

        var total = await query.CountAsync(cancellationToken);
        var results = await query
            .OrderBy(g => g.Symbol)
            .ThenBy(g => g.GeneId)
            .Skip((page - 1) * perPage)
            .Take(perPage)
            .Select(g => new GeneSearchResult(
                g.GeneId,
                g.TaxId,
                g.Symbol,
                g.Name,
                g.Chromosome,
                g.MapLocation,
                g.Description,
                g.GeneType,
                g.Species.CommonName,
                g.Traits.Count,
                g.Constraints.Max(c => (double?)c.Pli),
                g.Constraints.Min(c => (double?)c.Loeuf),
                g.Summary != null,
                g.Traits.Any(),
                g.ClinVarSummary.Max(c => (int?)c.PathogenicAlleles)))
            .ToListAsync(cancellationToken);

        var response = new GeneSearchResponse(results, queryText, page, perPage, total);
        cache.Set(cacheKey, response);
        return response;
    }

    private static string BuildCacheKey(GeneSearchRequest request)
        => string.Join(
            "|",
            "search",
            request.Query?.Trim().ToUpperInvariant(),
            request.Species,
            request.Chromosome?.Trim().ToUpperInvariant(),
            request.Constraint?.Trim().ToLowerInvariant(),
            request.Clinical?.Trim().ToLowerInvariant(),
            request.GeneType?.Trim().ToLowerInvariant(),
            request.GoCategory?.Trim().ToLowerInvariant(),
            request.Page,
            request.PerPage);

    private IQueryable<Gene> ApplySearch(IQueryable<Gene> query, string queryText)
    {
        var provider = db.Database.ProviderName;
        if (provider == "Microsoft.EntityFrameworkCore.SqlServer")
        {
            // SQL Server CONTAINS requires full-text indexes on these columns.
            // The migration that provisions those indexes is intentionally separate.
            var containsTerm = $"\"{EscapeFullTextTerm(queryText)}*\"";
            return query.Where(g =>
                EF.Functions.Contains(g.Symbol, containsTerm) ||
                EF.Functions.Contains(g.Name!, containsTerm) ||
                EF.Functions.Contains(g.Description!, containsTerm) ||
                g.Synonyms.Any(s => EF.Functions.Contains(s.Synonym, containsTerm)) ||
                g.GoTerms.Any(t => EF.Functions.Contains(t.GoTerm, containsTerm)) ||
                g.Traits.Any(t => EF.Functions.Contains(t.ReportedTrait!, containsTerm)));
        }

        // This branch keeps unit tests provider-independent; production uses SQL Server CONTAINS.
        var pattern = queryText.ToUpperInvariant();
        return query.Where(g =>
            (g.Symbol != null && g.Symbol.ToUpper().Contains(pattern)) ||
            (g.Name != null && g.Name.ToUpper().Contains(pattern)) ||
            (g.Description != null && g.Description.ToUpper().Contains(pattern)) ||
            g.Synonyms.Any(s => s.Synonym.ToUpper().Contains(pattern)) ||
            g.GoTerms.Any(t => t.GoTerm.ToUpper().Contains(pattern)) ||
            g.Traits.Any(t => t.ReportedTrait != null && t.ReportedTrait.ToUpper().Contains(pattern)));
    }

    private static IQueryable<Gene> ApplyConstraintFilter(IQueryable<Gene> query, string? value)
        => value?.ToLowerInvariant() switch
        {
            "essential" => query.Where(g => g.Constraints.Any(c => c.Pli > 0.9)),
            "constrained" => query.Where(g => g.Constraints.Any(c => c.Loeuf < 0.35)),
            "tolerant" => query.Where(g => !g.Constraints.Any(c => c.Pli > 0.5)),
            _ => query
        };

    private static IQueryable<Gene> ApplyClinicalFilter(IQueryable<Gene> query, string? value)
        => value?.ToLowerInvariant() switch
        {
            "pathogenic" => query.Where(g => g.ClinVarSummary.Any(c => c.PathogenicAlleles > 0)),
            "gwas" => query.Where(g => g.Traits.Any()),
            "disease" => query.Where(g =>
                g.ClinVarSummary.Any(c => c.PathogenicAlleles > 0) || g.Traits.Any()),
            _ => query
        };

    private static IQueryable<Gene> ApplyGeneTypeFilter(IQueryable<Gene> query, string? value)
        => value?.ToLowerInvariant() switch
        {
            "protein-coding" => query.Where(g => g.GeneType == "protein-coding"),
            "pseudo" => query.Where(g => g.GeneType != null && g.GeneType.Contains("pseudo")),
            "ncrna" => query.Where(g => g.GeneType != null &&
                (g.GeneType.Contains("RNA") || g.GeneType.Contains("ncRNA"))),
            "other" => query.Where(g => g.GeneType != "protein-coding" &&
                (g.GeneType == null || !g.GeneType.Contains("pseudo")) &&
                (g.GeneType == null || !g.GeneType.Contains("RNA"))),
            _ => query
        };

    private static IQueryable<Gene> ApplyGoCategoryFilter(IQueryable<Gene> query, string? value)
        => value?.ToLowerInvariant() switch
        {
            "function" => query.Where(g => g.GoTerms.Any(t => t.Category == "Function")),
            "process" => query.Where(g => g.GoTerms.Any(t => t.Category == "Process")),
            "component" => query.Where(g => g.GoTerms.Any(t => t.Category == "Component")),
            "any" => query.Where(g => g.GoTerms.Any()),
            _ => query
        };

    private static string EscapeFullTextTerm(string value)
        => value.Replace("\"", "\"\"", StringComparison.Ordinal);
}
