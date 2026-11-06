namespace GenomeSearch.Api.Models;

public sealed class GeneSynonym
{
    public long Id { get; set; }
    public int GeneId { get; set; }
    public string Synonym { get; set; } = null!;

    public Gene Gene { get; set; } = null!;
}
