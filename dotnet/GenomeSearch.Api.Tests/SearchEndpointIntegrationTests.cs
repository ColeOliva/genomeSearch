using System.Net;
using System.Net.Http.Json;
using GenomeSearch.Api.Data;
using GenomeSearch.Api.Models;
using Microsoft.Extensions.DependencyInjection;

namespace GenomeSearch.Api.Tests;

public sealed class SearchEndpointIntegrationTests
{
    private static async Task<SearchApiFactory> CreateFactoryAsync()
    {
        var factory = new SearchApiFactory();
        await factory.SeedAsync();
        return factory;
    }

    [Fact]
    public async Task SearchReturnsPagedResultsThroughHttp()
    {
        await using var factory = await CreateFactoryAsync();
        using var client = factory.CreateClient();

        var response = await client.GetAsync("/search?q=BRCA&page=1&per_page=1");
        var payload = await response.Content.ReadFromJsonAsync<SearchResponseContract>();

        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
        Assert.NotNull(payload);
        Assert.Equal(1, payload.Total);
        Assert.Single(payload.Results);
        Assert.Equal(1, payload.PerPage);
    }

    [Fact]
    public async Task InvalidPageSizeReturnsBadRequest()
    {
        await using var factory = await CreateFactoryAsync();
        using var client = factory.CreateClient();

        var response = await client.GetAsync("/search?q=BRCA&per_page=101");

        Assert.Equal(HttpStatusCode.BadRequest, response.StatusCode);
    }

    [Fact]
    public async Task RepeatedSearchUsesCachedResponse()
    {
        await using var factory = await CreateFactoryAsync();
        using var client = factory.CreateClient();
        var first = await client.GetAsync("/search?q=BRCA");

        await using (var scope = factory.Services.CreateAsyncScope())
        {
            var db = scope.ServiceProvider.GetRequiredService<GenomeSearchDbContext>();
            db.Add(new Gene
            {
                GeneId = 2,
                TaxId = 9606,
                Symbol = "BRCA2",
                Name = "Breast cancer gene 2",
                Description = "A gene",
                GeneType = "protein-coding"
            });
            await db.SaveChangesAsync();
        }

        var second = await client.GetAsync("/search?q=BRCA");
        var payload = await second.Content.ReadFromJsonAsync<SearchResponseContract>();

        Assert.Equal(HttpStatusCode.OK, first.StatusCode);
        Assert.Equal(HttpStatusCode.OK, second.StatusCode);
        Assert.NotNull(payload);
        Assert.Equal(1, payload.Total);
    }

    [Fact]
    public async Task RateLimitReturnsTooManyRequestsAfterConfiguredPermitCount()
    {
        await using var factory = await CreateFactoryAsync();
        using var client = factory.CreateClient();

        var first = await client.GetAsync("/search?q=BRCA&chromosome=1");
        var second = await client.GetAsync("/search?q=BRCA&chromosome=2");
        var third = await client.GetAsync("/search?q=BRCA&chromosome=3");

        Assert.NotEqual(HttpStatusCode.TooManyRequests, first.StatusCode);
        Assert.NotEqual(HttpStatusCode.TooManyRequests, second.StatusCode);
        Assert.Equal(HttpStatusCode.TooManyRequests, third.StatusCode);
    }

    private sealed record SearchResponseContract(
        IReadOnlyList<ResultContract> Results,
        string Query,
        int Page,
        int PerPage,
        int Total);

    private sealed record ResultContract(int GeneId, string Symbol);
}
