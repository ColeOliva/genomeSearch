namespace GenomeSearch.Api.Models;

public sealed class MousePhenotypeTerm
{
    public string MpId { get; set; } = null!;
    public string TermName { get; set; } = null!;
    public string? Description { get; set; }

    public ICollection<MousePhenotype> GeneMappings { get; } = new List<MousePhenotype>();
}
