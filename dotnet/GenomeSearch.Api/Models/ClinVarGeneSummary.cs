namespace GenomeSearch.Api.Models;

public sealed class ClinVarGeneSummary
{
    public long Id { get; set; }
    public int GeneId { get; set; }
    public string GeneSymbol { get; set; } = null!;
    public int TotalSubmissions { get; set; }
    public int TotalAlleles { get; set; }
    public int PathogenicAlleles { get; set; }
    public int UncertainAlleles { get; set; }
    public int ConflictingAlleles { get; set; }
    public string? GeneMimNumber { get; set; }

    public Gene Gene { get; set; } = null!;
}
