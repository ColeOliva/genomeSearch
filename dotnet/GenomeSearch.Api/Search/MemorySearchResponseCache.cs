using Microsoft.Extensions.Caching.Memory;

namespace GenomeSearch.Api.Search;

public sealed class MemorySearchResponseCache(
    IMemoryCache memoryCache,
    IConfiguration configuration) : ISearchResponseCache
{
    private readonly MemoryCacheEntryOptions _entryOptions = new()
    {
        AbsoluteExpirationRelativeToNow = TimeSpan.FromSeconds(
            Math.Max(1, configuration.GetValue("Search:CacheDurationSeconds", 300)))
    };

    public bool TryGet(string key, out GeneSearchResponse response)
    {
        if (memoryCache.TryGetValue(key, out GeneSearchResponse? cached) && cached is not null)
        {
            response = cached;
            return true;
        }

        response = null!;
        return false;
    }

    public void Set(string key, GeneSearchResponse response)
        => memoryCache.Set(key, response, _entryOptions);
}
