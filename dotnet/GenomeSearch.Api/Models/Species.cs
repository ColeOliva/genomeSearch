namespace GenomeSearch.Api.Models;

public sealed class Species
{
    public int TaxId { get; set; }
    public string Name { get; set; } = null!;
    public string? CommonName { get; set; }
    public int GeneCount { get; set; }

    public ICollection<Gene> Genes { get; } = new List<Gene>();
}
