namespace GenomeSearch.Api.Models;

public sealed class GeneGoTerm
{
    public long Id { get; set; }
    public int GeneId { get; set; }
    public string GoId { get; set; } = null!;
    public string GoTerm { get; set; } = null!;
    public string? Category { get; set; }

    public Gene Gene { get; set; } = null!;
}
