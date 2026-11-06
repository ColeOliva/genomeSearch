namespace GenomeSearch.Api.Models;

public sealed class Gene
{
    public int GeneId { get; set; }
    public int TaxId { get; set; }
    public string Symbol { get; set; } = null!;
    public string? Name { get; set; }
    public string? Chromosome { get; set; }
    public string? MapLocation { get; set; }
    public string? Description { get; set; }
    public string? GeneType { get; set; }

    public Species Species { get; set; } = null!;
    public ICollection<GeneSynonym> Synonyms { get; } = new List<GeneSynonym>();
    public ICollection<GeneGoTerm> GoTerms { get; } = new List<GeneGoTerm>();
    public GeneSummary? Summary { get; set; }
    public ICollection<GeneTrait> Traits { get; } = new List<GeneTrait>();
    public ICollection<GeneConstraint> Constraints { get; } = new List<GeneConstraint>();
    public ICollection<ClinVarGeneSummary> ClinVarSummary { get; } = new List<ClinVarGeneSummary>();
    public ICollection<ClinVarVariant> ClinVarVariants { get; } = new List<ClinVarVariant>();
    public ICollection<MousePhenotype> MousePhenotypes { get; } = new List<MousePhenotype>();
}
