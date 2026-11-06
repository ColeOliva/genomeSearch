namespace GenomeSearch.Api.Models;

public sealed class GeneSummary
{
    public long Id { get; set; }
    public int GeneId { get; set; }
    public string Summary { get; set; } = null!;
    public string? Source { get; set; }

    public Gene Gene { get; set; } = null!;
}
