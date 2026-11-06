namespace GenomeSearch.Api.Models;

public sealed class MousePhenotype
{
    public long Id { get; set; }
    public int GeneId { get; set; }
    public string? MouseSymbol { get; set; }
    public string MpId { get; set; } = null!;

    public Gene Gene { get; set; } = null!;
    public MousePhenotypeTerm Term { get; set; } = null!;
}
