namespace GenomeSearch.Api.Pleiotropy;

public sealed record PleiotropyInput(
    string Symbol,
    int UniqueDomainCount,
    int TotalRawTraits,
    double? Pli);

public sealed record PleiotropyScore(
    string Symbol,
    double Index,
    double DomainScore,
    double TraitScore,
    double ConstraintScore,
    bool IsNovel);
