namespace GenomeSearch.Api.Search;

public interface ISearchResponseCache
{
    bool TryGet(string key, out GeneSearchResponse response);
    void Set(string key, GeneSearchResponse response);
}
