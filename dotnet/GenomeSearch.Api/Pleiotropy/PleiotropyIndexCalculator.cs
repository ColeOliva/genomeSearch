namespace GenomeSearch.Api.Pleiotropy;

public sealed class PleiotropyIndexCalculator : IPleiotropyIndexCalculator
{
    private const double MaxDomains = 8.0;
    private const double DomainWeight = 50.0;
    private const double TraitWeight = 25.0;
    private const double ConstraintWeight = 25.0;

    public IReadOnlyList<PleiotropyScore> Calculate(IEnumerable<PleiotropyInput> inputs)
    {
        ArgumentNullException.ThrowIfNull(inputs);

        var rows = inputs.ToArray();
        if (rows.Length == 0)
        {
            return [];
        }

        var observedPli = rows
            .Where(row => row.Pli is not null)
            .Select(row => row.Pli!.Value)
            .Order()
            .ToArray();
        var medianPli = Median(observedPli);

        var logTraits = rows
            // .NET 10 has no Log1p API; integer trait counts make Log(1 + n)
            // equivalent for this port.
            .Select(row => Math.Log(1 + row.TotalRawTraits))
            .ToArray();
        var maxLogTraits = logTraits.Max();

        return rows
            .Select((row, index) =>
            {
                var domainScore = row.UniqueDomainCount / MaxDomains * DomainWeight;
                var traitScore = maxLogTraits == 0
                    ? 0
                    : logTraits[index] / maxLogTraits * TraitWeight;
                var constraintScore = (row.Pli ?? medianPli) * ConstraintWeight;
                var score = domainScore + traitScore + constraintScore;

                return new PleiotropyScore(
                    row.Symbol,
                    score,
                    domainScore,
                    traitScore,
                    constraintScore,
                    IsNovel(row.Symbol));
            })
            .OrderByDescending(score => score.Index)
            .ThenBy(score => score.Symbol, StringComparer.Ordinal)
            .ToArray();
    }

    private static double Median(IReadOnlyList<double> values)
    {
        if (values.Count == 0)
        {
            return 0;
        }

        var middle = values.Count / 2;
        return values.Count % 2 == 0
            ? (values[middle - 1] + values[middle]) / 2
            : values[middle];
    }

    private static bool IsNovel(string symbol)
        => !string.Equals(symbol, "APOE", StringComparison.Ordinal) &&
           !string.Equals(symbol, "ABO", StringComparison.Ordinal) &&
           !symbol.StartsWith("HLA-", StringComparison.Ordinal);
}
