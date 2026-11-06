using GenomeSearch.Api.Data;
using GenomeSearch.Api.Models;
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Mvc.Testing;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Infrastructure;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.DependencyInjection.Extensions;

namespace GenomeSearch.Api.Tests;

public sealed class SearchApiFactory : WebApplicationFactory<Program>
{
    private readonly string _databaseName = $"GenomeSearchTests-{Guid.NewGuid():N}";

    protected override void ConfigureWebHost(IWebHostBuilder builder)
    {
        builder.UseEnvironment("Testing");
        builder.ConfigureAppConfiguration((_, configuration) =>
        {
            configuration.AddInMemoryCollection(new Dictionary<string, string?>
            {
                ["Search:RateLimitPermitLimit"] = "2",
                ["Search:RateLimitWindowSeconds"] = "60",
                ["Search:CacheDurationSeconds"] = "300"
            });
        });
        builder.ConfigureServices(services =>
        {
            services.RemoveAll<GenomeSearchDbContext>();
            services.RemoveAll<DbContextOptions<GenomeSearchDbContext>>();
            services.RemoveAll<IDbContextOptionsConfiguration<GenomeSearchDbContext>>();
            services.AddDbContext<GenomeSearchDbContext>(options =>
                options.UseInMemoryDatabase(_databaseName));
        });
    }

    public async Task SeedAsync()
    {
        await using var scope = Services.CreateAsyncScope();
        var db = scope.ServiceProvider.GetRequiredService<GenomeSearchDbContext>();
        await db.Database.EnsureCreatedAsync();

        if (await db.Genes.AnyAsync())
        {
            return;
        }

        var species = new Species
        {
            TaxId = 9606,
            Name = "Homo sapiens",
            CommonName = "Human",
            GeneCount = 1
        };
        db.Add(new Gene
        {
            GeneId = 1,
            TaxId = species.TaxId,
            Symbol = "BRCA1",
            Name = "Breast cancer gene",
            Description = "A gene involved in DNA repair",
            GeneType = "protein-coding",
            Species = species
        });
        await db.SaveChangesAsync();
    }
}
