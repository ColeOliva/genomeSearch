using GenomeSearch.Api.Pleiotropy;

namespace GenomeSearch.Api.Tests;

public sealed class PleiotropyIndexCalculatorTests
{
    [Fact]
    public void ApoeAndAboAreRecognizedAsPythonBenchmarkMegaHubs()
    {
        var scores = CalculateBenchmarks();

        Assert.False(scores.Single(score => score.Symbol == "APOE").IsNovel);
        Assert.False(scores.Single(score => score.Symbol == "ABO").IsNovel);
    }

    [Fact]
    public void BenchmarkScoresUseDomainTraitAndConstraintWeights()
    {
        var scores = CalculateBenchmarks();

        var apoe = scores.Single(score => score.Symbol == "APOE");
        Assert.Equal(50.0, apoe.DomainScore, precision: 10);
        Assert.Equal(25.0, apoe.TraitScore, precision: 10);
        Assert.Equal(25.0, apoe.ConstraintScore, precision: 10);
        Assert.Equal(100.0, apoe.Index, precision: 10);

        var abo = scores.Single(score => score.Symbol == "ABO");
        Assert.Equal(25.0, abo.DomainScore, precision: 10);
        Assert.Equal(Math.Log(11) / Math.Log(101) * 25, abo.TraitScore, precision: 10);
        Assert.Equal(12.5, abo.ConstraintScore, precision: 10);
        Assert.Equal(25 + Math.Log(11) / Math.Log(101) * 25 + 12.5, abo.Index, precision: 10);
    }

    [Fact]
    public void MissingPliUsesMedianOfObservedConstraints()
    {
        var calculator = new PleiotropyIndexCalculator();

        var scores = calculator.Calculate(
        [
            new PleiotropyInput("APOE", 8, 100, 1.0),
            new PleiotropyInput("ABO", 4, 25, null),
            new PleiotropyInput("TP53", 2, 1, 0.2)
        ]);

        var abo = scores.Single(score => score.Symbol == "ABO");
        Assert.Equal(0.6 * 25, abo.ConstraintScore, precision: 10);
    }

    [Fact]
    public void ResultsAreSortedByIndexDescendingWithSymbolTieBreaker()
    {
        var calculator = new PleiotropyIndexCalculator();

        var scores = calculator.Calculate(
        [
            new PleiotropyInput("ZETA", 4, 10, 0.5),
            new PleiotropyInput("ALPHA", 4, 10, 0.5)
        ]);

        Assert.Equal(["ALPHA", "ZETA"], scores.Select(score => score.Symbol));
    }

    private static IReadOnlyList<PleiotropyScore> CalculateBenchmarks()
    {
        var calculator = new PleiotropyIndexCalculator();
        return calculator.Calculate(
        [
            new PleiotropyInput("APOE", 8, 100, 1.0),
            new PleiotropyInput("ABO", 4, 10, 0.5)
        ]);
    }
}
