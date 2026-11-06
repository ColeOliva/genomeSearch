namespace GenomeSearch.Api.Models;

public sealed class ClinVarVariant
{
    public long Id { get; set; }
    public long AlleleId { get; set; }
    public long? VariationId { get; set; }
    public int GeneId { get; set; }
    public string? GeneSymbol { get; set; }
    public string? VariantName { get; set; }
    public string? VariantType { get; set; }
    public string? ClinicalSignificance { get; set; }
    public string? ReviewStatus { get; set; }
    public string? PhenotypeList { get; set; }
    public string? Chromosome { get; set; }
    public long? StartPos { get; set; }
    public long? StopPos { get; set; }
    public string? ReferenceAllele { get; set; }
    public string? AlternateAllele { get; set; }
    public long? RsId { get; set; }
    public string? LastEvaluated { get; set; }
    public string? Origin { get; set; }
    public string? Assembly { get; set; }

    public Gene Gene { get; set; } = null!;
}
