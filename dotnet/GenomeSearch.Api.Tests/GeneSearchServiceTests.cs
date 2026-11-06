using GenomeSearch.Api.Data;
using GenomeSearch.Api.Models;
using GenomeSearch.Api.Search;
using Microsoft.EntityFrameworkCore;

namespace GenomeSearch.Api.Tests;

public sealed class GeneSearchServiceTests
{
    [Fact]
    public async Task EmptyQueryReturnsEmptyPayloadWithoutPagingFieldsBeingRelevant()
    {
        await using var db = CreateContext();
        var service = new GeneSearchService(db, new TestSearchCache());

        var response = await service.SearchAsync(new GeneSearchRequest("  "));

        Assert.Empty(response.Results);
        Assert.Equal(string.Empty, response.Query);
        Assert.Equal(0, response.Total);
        Assert.Equal(1, response.Page);
        Assert.Equal(50, response.PerPage);
    }

    [Fact]
    public async Task SearchMatchesGeneTextAndRelatedText()
    {
        await using var db = CreateContext();
        Seed(db);
        var service = new GeneSearchService(db, new TestSearchCache());

        var response = await service.SearchAsync(new GeneSearchRequest("metabolism"));

        Assert.Equal(1, response.Total);
        Assert.Equal("BRCA1", Assert.Single(response.Results).Symbol);
    }

    [Fact]
    public async Task FiltersAreCombined()
    {
        await using var db = CreateContext();
        Seed(db);
        var service = new GeneSearchService(db, new TestSearchCache());

        var response = await service.SearchAsync(new GeneSearchRequest(
            "gene",
            Species: 9606,
            Chromosome: "17",
            Constraint: "essential",
            Clinical: "pathogenic",
            GeneType: "protein-coding",
            GoCategory: "function"));

        var result = Assert.Single(response.Results);
        Assert.Equal("BRCA1", result.Symbol);
        Assert.Equal(0.95, result.Pli);
        Assert.Equal(5, result.ClinvarPathogenic);
    }

    [Fact]
    public async Task PagingCapsPageSizeAndReportsTotalBeforePaging()
    {
        await using var db = CreateContext();
        SeedMany(db, 105);
        var service = new GeneSearchService(db, new TestSearchCache());

        var response = await service.SearchAsync(new GeneSearchRequest(
            "gene",
            Page: 2,
            PerPage: 500));

        Assert.Equal(100, response.PerPage);
        Assert.Equal(105, response.Total);
        Assert.Equal(5, response.Results.Count);
    }

    [Fact]
    public async Task ConstraintAndClinicalFiltersExcludeNonmatchingGenes()
    {
        await using var db = CreateContext();
        Seed(db);
        var service = new GeneSearchService(db, new TestSearchCache());

        var tolerant = await service.SearchAsync(new GeneSearchRequest("gene", Constraint: "tolerant"));
        var gwas = await service.SearchAsync(new GeneSearchRequest("gene", Clinical: "gwas"));

        Assert.Equal("GNAI2", Assert.Single(tolerant.Results).Symbol);
        Assert.Equal("BRCA1", Assert.Single(gwas.Results).Symbol);
    }

    private static GenomeSearchDbContext CreateContext()
    {
        var options = new DbContextOptionsBuilder<GenomeSearchDbContext>()
            .UseInMemoryDatabase(Guid.NewGuid().ToString())
            .Options;
        return new GenomeSearchDbContext(options);
    }

    private sealed class TestSearchCache : ISearchResponseCache
    {
        public bool TryGet(string key, out GeneSearchResponse response)
        {
            response = null!;
            return false;
        }

        public void Set(string key, GeneSearchResponse response)
        {
        }
    }

    private static void Seed(GenomeSearchDbContext db)
    {
        var human = new Species { TaxId = 9606, Name = "Homo sapiens", CommonName = "Human", GeneCount = 2 };
        var mouse = new Species { TaxId = 10090, Name = "Mus musculus", CommonName = "Mouse", GeneCount = 1 };
        var brca1 = new Gene
        {
            GeneId = 1,
            TaxId = human.TaxId,
            Symbol = "BRCA1",
            Name = "Breast cancer gene",
            Chromosome = "17",
            MapLocation = "17q21",
            Description = "A gene involved in metabolism",
            GeneType = "protein-coding",
            Species = human
        };
        brca1.GoTerms.Add(new GeneGoTerm { Id = 1, GeneId = 1, GoId = "GO:1", GoTerm = "Metabolism", Category = "Function" });
        brca1.Traits.Add(new GeneTrait { Id = 1, GeneId = 1, GeneSymbol = "BRCA1", ReportedTrait = "breast cancer" });
        brca1.Constraints.Add(new GeneConstraint { Id = 1, GeneId = 1, GeneSymbol = "BRCA1", Pli = 0.95, Loeuf = 0.2 });
        brca1.ClinVarSummary.Add(new ClinVarGeneSummary { Id = 1, GeneId = 1, GeneSymbol = "BRCA1", PathogenicAlleles = 5 });

        var gnai2 = new Gene
        {
            GeneId = 2,
            TaxId = mouse.TaxId,
            Symbol = "GNAI2",
            Name = "Signaling gene",
            Chromosome = "3",
            MapLocation = "3q",
            Description = "A gene",
            GeneType = "protein-coding",
            Species = mouse
        };
        gnai2.Constraints.Add(new GeneConstraint { Id = 2, GeneId = 2, GeneSymbol = "GNAI2", Pli = 0.1, Loeuf = 0.8 });

        db.AddRange(human, mouse, brca1, gnai2);
        db.SaveChanges();
    }

    private static void SeedMany(GenomeSearchDbContext db, int count)
    {
        var species = new Species { TaxId = 9606, Name = "Homo sapiens", CommonName = "Human", GeneCount = count };
        db.Species.Add(species);
        for (var index = 1; index <= count; index++)
        {
            db.Genes.Add(new Gene
            {
                GeneId = index,
                TaxId = species.TaxId,
                Symbol = $"GENE{index:D3}",
                Name = "Gene",
                Description = "Gene",
                Species = species
            });
        }

        db.SaveChanges();
    }
}
