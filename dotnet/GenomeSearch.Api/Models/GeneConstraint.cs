namespace GenomeSearch.Api.Models;

public sealed class GeneConstraint
{
    public long Id { get; set; }
    public int GeneId { get; set; }
    public string GeneSymbol { get; set; } = null!;
    public string? Transcript { get; set; }
    public double? Pli { get; set; }
    public double? Loeuf { get; set; }
    public double? LoeufLower { get; set; }
    public double? LoeufUpper { get; set; }
    public double? OeLof { get; set; }
    public double? OeMis { get; set; }
    public double? OeMisLower { get; set; }
    public double? OeMisUpper { get; set; }
    public double? MisZ { get; set; }
    public double? OeSyn { get; set; }
    public double? SynZ { get; set; }
    public string? GnomadVersion { get; set; }

    public Gene Gene { get; set; } = null!;
}
