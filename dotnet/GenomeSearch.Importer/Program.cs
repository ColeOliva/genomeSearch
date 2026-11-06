using System.Data;
using GenomeSearch.Api.Data;
using Microsoft.Data.SqlClient;
using Microsoft.Data.Sqlite;
using Microsoft.EntityFrameworkCore;

namespace GenomeSearch.Importer;

internal static class Program
{
    private const int DefaultBatchSize = 5_000;

    public static async Task<int> Main(string[] args)
    {
        try
        {
            var options = ImportOptions.Parse(args);
            if (options.ShowHelp)
            {
                ImportOptions.PrintHelp();
                return 0;
            }

            await ImportAsync(options);
            return 0;
        }
        catch (Exception exception)
        {
            Console.Error.WriteLine($"Import failed: {exception.Message}");
            return 1;
        }
    }

    private static async Task ImportAsync(ImportOptions options)
    {
        await using var sqlite = new SqliteConnection($"Data Source={options.SqlitePath};Mode=ReadOnly");
        await sqlite.OpenAsync();

        await using var sqlServer = new SqlConnection(options.SqlServerConnectionString);
        await sqlServer.OpenAsync();

        // The migration creates the relational schema before bulk copy begins.
        var dbOptions = new DbContextOptionsBuilder<GenomeSearchDbContext>()
            .UseSqlServer(sqlServer)
            .Options;
        await using (var context = new GenomeSearchDbContext(dbOptions))
        {
            await context.Database.MigrateAsync();
        }

        var sampleSize = options.SampleSize;
        var selectedGeneIds = sampleSize is null
            ? null
            : await ReadIdsAsync(sqlite, "gene_id", "genes", sampleSize.Value);
        var selectedTaxIds = selectedGeneIds is null
            ? null
            : await ReadIdsAsync(
                sqlite,
                "tax_id",
                "genes",
                sampleSize!.Value,
                $"gene_id IN ({string.Join(',', selectedGeneIds)})");
        selectedTaxIds = selectedTaxIds?.Distinct().ToArray();

        await using var transaction = (SqlTransaction)await sqlServer.BeginTransactionAsync();
        foreach (var table in BuildTables(selectedGeneIds, selectedTaxIds))
        {
            await BulkCopyAsync(sqlite, sqlServer, transaction, table, options.BatchSize);
        }

        await transaction.CommitAsync();
        Console.WriteLine("Import completed.");
    }

    private static IReadOnlyList<TableSpec> BuildTables(
        IReadOnlyList<long>? geneIds,
        IReadOnlyList<long>? taxIds)
    {
        var geneFilter = InFilter("gene_id", geneIds);
        var taxFilter = InFilter("tax_id", taxIds);
        var traitFilter = geneIds is null
            ? ""
            : $" WHERE gene_id IN (SELECT trait_id FROM gene_traits{geneFilter})";
        var phenotypeTermFilter = geneIds is null
            ? ""
            : $" WHERE mp_id IN (SELECT mp_id FROM mouse_phenotypes{geneFilter})";

        return
        [
            new("species", $"SELECT tax_id, name, common_name, gene_count FROM species{taxFilter}"),
            new("genes", $"SELECT gene_id, tax_id, symbol, name, chromosome, map_location, description, gene_type FROM genes{geneFilter}"),
            new("gene_synonyms", $"SELECT id, gene_id, synonym FROM gene_synonyms{geneFilter}"),
            new("gene_go_terms", $"SELECT id, gene_id, go_id, go_term, category FROM gene_go_terms{geneFilter}"),
            new("gene_summaries", $"SELECT id, gene_id, summary, source FROM gene_summaries{geneFilter}"),
            new("traits", $"SELECT trait_id, efo_trait, reported_trait, trait_category FROM traits{traitFilter}"),
            new("gene_traits", $"SELECT id, gene_id, gene_symbol, trait_id, reported_trait, efo_trait, p_value, p_value_text, risk_allele, risk_allele_freq, odds_ratio, beta_coefficient, ci_text, chromosome, position, snp_id, study_id, pubmed_id, sample_description FROM gene_traits{geneFilter}"),
            new("gene_constraints", $"SELECT id, gene_id, gene_symbol, transcript, pli, loeuf, loeuf_lower, loeuf_upper, oe_lof, oe_mis, oe_mis_lower, oe_mis_upper, mis_z, oe_syn, syn_z, gnomad_version FROM gene_constraints{geneFilter}"),
            new("clinvar_gene_summary", $"SELECT id, gene_id, gene_symbol, total_submissions, total_alleles, pathogenic_alleles, uncertain_alleles, conflicting_alleles, gene_mim_number FROM clinvar_gene_summary{geneFilter}"),
            new("clinvar_variants", $"SELECT id, allele_id, variation_id, gene_id, gene_symbol, variant_name, variant_type, clinical_significance, review_status, phenotype_list, chromosome, start_pos, stop_pos, reference_allele, alternate_allele, rs_id, last_evaluated, origin, assembly FROM clinvar_variants{geneFilter}"),
            new("mouse_phenotype_terms", $"SELECT mp_id, term_name, description FROM mouse_phenotype_terms{phenotypeTermFilter}"),
            new("mouse_phenotypes", $"SELECT id, gene_id, mouse_symbol, mp_id FROM mouse_phenotypes{geneFilter}")
        ];
    }

    private static async Task BulkCopyAsync(
        SqliteConnection sqlite,
        SqlConnection sqlServer,
        SqlTransaction transaction,
        TableSpec table,
        int batchSize)
    {
        await using var command = sqlite.CreateCommand();
        command.CommandText = table.Query;
        await using var reader = await command.ExecuteReaderAsync(CommandBehavior.SequentialAccess);

        var rowsImported = 0;
        var batch = CreateBatch(reader);
        while (await reader.ReadAsync())
        {
            var values = new object[reader.FieldCount];
            reader.GetValues(values);
            for (var index = 0; index < values.Length; index++)
            {
                if (values[index] is DBNull)
                {
                    values[index] = DBNull.Value;
                }
            }

            batch.Rows.Add(values);
            if (batch.Rows.Count < batchSize)
            {
                continue;
            }

            await WriteBatchAsync(sqlServer, transaction, table.Name, batch, batchSize);
            rowsImported += batch.Rows.Count;
            batch.Clear();
        }

        if (batch.Rows.Count > 0)
        {
            await WriteBatchAsync(sqlServer, transaction, table.Name, batch, batchSize);
            rowsImported += batch.Rows.Count;
        }

        Console.WriteLine($"  {table.Name}: {rowsImported:N0} rows");
    }

    private static DataTable CreateBatch(SqliteDataReader reader)
    {
        var table = new DataTable();
        for (var index = 0; index < reader.FieldCount; index++)
        {
            // SQLite may expose a nullable column as object; SqlBulkCopy accepts
            // DBNull values and converts compatible numeric values on the server.
            table.Columns.Add(reader.GetName(index), reader.GetFieldType(index));
        }

        return table;
    }

    private static async Task WriteBatchAsync(
        SqlConnection connection,
        SqlTransaction transaction,
        string destination,
        DataTable batch,
        int batchSize)
    {
        using var bulkCopy = new SqlBulkCopy(
            connection,
            SqlBulkCopyOptions.KeepIdentity | SqlBulkCopyOptions.CheckConstraints,
            transaction)
        {
            DestinationTableName = $"dbo.{destination}",
            BatchSize = batchSize,
            BulkCopyTimeout = 0
        };

        foreach (DataColumn column in batch.Columns)
        {
            bulkCopy.ColumnMappings.Add(column.ColumnName, column.ColumnName);
        }

        await bulkCopy.WriteToServerAsync(batch);
    }

    private static async Task<IReadOnlyList<long>> ReadIdsAsync(
        SqliteConnection connection,
        string column,
        string table,
        int limit,
        string? predicate = null)
    {
        await using var command = connection.CreateCommand();
        command.CommandText = $"SELECT {column} FROM {table}{(string.IsNullOrWhiteSpace(predicate) ? "" : $" WHERE {predicate}")} ORDER BY {column} LIMIT $limit";
        command.Parameters.AddWithValue("$limit", limit);

        var ids = new List<long>();
        await using var reader = await command.ExecuteReaderAsync();
        while (await reader.ReadAsync())
        {
            ids.Add(reader.GetInt64(0));
        }

        return ids;
    }

    private static string InFilter(string column, IReadOnlyList<long>? ids)
        => ids is null ? "" : $" WHERE {column} IN ({string.Join(',', ids)})";

    private sealed record TableSpec(string Name, string Query);
}

internal sealed record ImportOptions(
    string SqlitePath,
    string SqlServerConnectionString,
    int BatchSize,
    int? SampleSize,
    bool ShowHelp)
{
    public static ImportOptions Parse(string[] args)
    {
        var sqlitePath = "data/genome.db";
        var sqlServer = Environment.GetEnvironmentVariable("GENOME_SEARCH_SQLSERVER");
        var batchSize = 5_000;
        int? sampleSize = null;
        var showHelp = args.Contains("--help") || args.Contains("-h");

        for (var index = 0; index < args.Length; index++)
        {
            switch (args[index])
            {
                case "--sqlite":
                    sqlitePath = RequiredValue(args, ref index, "--sqlite");
                    break;
                case "--sqlserver":
                    sqlServer = RequiredValue(args, ref index, "--sqlserver");
                    break;
                case "--batch-size":
                    batchSize = ParsePositiveInt(RequiredValue(args, ref index, "--batch-size"), "--batch-size");
                    break;
                case "--sample":
                    sampleSize = ParsePositiveInt(RequiredValue(args, ref index, "--sample"), "--sample");
                    break;
                case "--help":
                case "-h":
                    break;
                default:
                    throw new ArgumentException($"Unknown argument '{args[index]}'. Use --help for usage.");
            }
        }

        if (!showHelp && string.IsNullOrWhiteSpace(sqlServer))
        {
            throw new ArgumentException("Provide --sqlserver or set GENOME_SEARCH_SQLSERVER.");
        }

        return new ImportOptions(
            sqlitePath,
            sqlServer ?? string.Empty,
            batchSize,
            sampleSize,
            showHelp);
    }

    public static void PrintHelp()
    {
        Console.WriteLine("""
            Genome Search SQLite-to-SQL Server importer

            Usage:
              dotnet run --project GenomeSearch.Importer -- --sqlite <path> --sqlserver <connection> [options]

            Options:
              --sqlite <path>          SQLite database path (default: data/genome.db)
              --sqlserver <string>     SQL Server connection string
              --sample <count>         Import the first count genes and related rows
              --batch-size <count>     Rows per SqlBulkCopy batch (default: 5000)
              --help                   Show this help

            The SQL Server database is migrated before import. Existing rows are not deleted;
            use a fresh database for the first import.
            """);
    }

    private static string RequiredValue(string[] args, ref int index, string option)
    {
        if (++index >= args.Length || args[index].StartsWith("--", StringComparison.Ordinal))
        {
            throw new ArgumentException($"Option {option} requires a value.");
        }

        return args[index];
    }

    private static int ParsePositiveInt(string value, string option)
        => int.TryParse(value, out var result) && result > 0
            ? result
            : throw new ArgumentException($"{option} must be a positive integer.");
}
