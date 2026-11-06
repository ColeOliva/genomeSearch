namespace GenomeSearch.Api.Models;

public sealed class Trait
{
    public long TraitId { get; set; }
    public string? EfoTrait { get; set; }
    public string? ReportedTrait { get; set; }
    public string? TraitCategory { get; set; }

    public ICollection<GeneTrait> GeneTraits { get; } = new List<GeneTrait>();
}
