namespace GenomeSearch.Api.Pleiotropy;

public interface IPleiotropyIndexCalculator
{
    IReadOnlyList<PleiotropyScore> Calculate(IEnumerable<PleiotropyInput> inputs);
}
