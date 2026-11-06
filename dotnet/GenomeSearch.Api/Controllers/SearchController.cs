using GenomeSearch.Api.Search;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.RateLimiting;

namespace GenomeSearch.Api.Controllers;

[ApiController]
[Route("search")]
[EnableRateLimiting("search")]
public sealed class SearchController(IGeneSearchService searchService) : ControllerBase
{
    [HttpGet]
    public Task<GeneSearchResponse> Search(
        [FromQuery] SearchQueryParameters parameters,
        CancellationToken cancellationToken = default)
        => searchService.SearchAsync(parameters.ToRequest(), cancellationToken);
}
