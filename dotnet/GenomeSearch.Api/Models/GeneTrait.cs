namespace GenomeSearch.Api.Models;

public sealed class GeneTrait
{
    public long Id { get; set; }
    public int GeneId { get; set; }
    public string GeneSymbol { get; set; } = null!;
    public long? TraitId { get; set; }
    public string? ReportedTrait { get; set; }
    public string? EfoTrait { get; set; }
    public double? PValue { get; set; }
    public string? PValueText { get; set; }
    public string? RiskAllele { get; set; }
    public double? RiskAlleleFreq { get; set; }
    public double? OddsRatio { get; set; }
    public double? BetaCoefficient { get; set; }
    public string? CiText { get; set; }
    public string? Chromosome { get; set; }
    public long? Position { get; set; }
    public string? SnpId { get; set; }
    public string? StudyId { get; set; }
    public string? PubMedId { get; set; }
    public string? SampleDescription { get; set; }

    public Gene Gene { get; set; } = null!;
    public Trait? Trait { get; set; }
}
