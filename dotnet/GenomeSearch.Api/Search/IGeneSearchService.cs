namespace GenomeSearch.Api.Search;

public interface IGeneSearchService
{
    Task<GeneSearchResponse> SearchAsync(
        GeneSearchRequest request,
        CancellationToken cancellationToken = default);
}
