using System.ComponentModel.DataAnnotations;
using Microsoft.AspNetCore.Mvc;

namespace GenomeSearch.Api.Search;

public sealed class SearchQueryParameters
{
    [StringLength(200)]
    public string? Q { get; set; }

    [Range(1, int.MaxValue)]
    public int? Species { get; set; }

    public string? Chromosome { get; set; }
    public string? Constraint { get; set; }
    public string? Clinical { get; set; }

    [FromQuery(Name = "gene_type")]
    public string? GeneType { get; set; }

    [FromQuery(Name = "go_category")]
    public string? GoCategory { get; set; }

    [Range(1, int.MaxValue)]
    public int Page { get; set; } = 1;

    [Range(1, 100)]
    [FromQuery(Name = "per_page")]
    public int PerPage { get; set; } = 50;

    public GeneSearchRequest ToRequest()
        => new(Q, Species, Chromosome, Constraint, Clinical, GeneType, GoCategory, Page, PerPage);
}
