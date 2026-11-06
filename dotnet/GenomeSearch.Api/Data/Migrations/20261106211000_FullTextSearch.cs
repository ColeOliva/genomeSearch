using Microsoft.EntityFrameworkCore.Migrations;
using Microsoft.EntityFrameworkCore.Infrastructure;

#nullable disable

namespace GenomeSearch.Api.Data.Migrations;

[DbContext(typeof(GenomeSearchDbContext))]
[Migration("20261106211000_FullTextSearch")]
public partial class FullTextSearch : Migration
{
    protected override void Up(MigrationBuilder migrationBuilder)
    {
        migrationBuilder.Sql("""
            IF NOT EXISTS (SELECT 1 FROM sys.fulltext_catalogs WHERE name = N'GenomeSearchFullText')
                CREATE FULLTEXT CATALOG [GenomeSearchFullText] AS DEFAULT;
            """);

        CreateFullTextIndex(migrationBuilder, "genes", "PK_genes",
            "[symbol] LANGUAGE 1033, [name] LANGUAGE 1033, [description] LANGUAGE 1033");
        CreateFullTextIndex(migrationBuilder, "gene_synonyms", "PK_gene_synonyms",
            "[synonym] LANGUAGE 1033");
        CreateFullTextIndex(migrationBuilder, "gene_go_terms", "PK_gene_go_terms",
            "[go_term] LANGUAGE 1033");
        CreateFullTextIndex(migrationBuilder, "gene_traits", "PK_gene_traits",
            "[reported_trait] LANGUAGE 1033, [efo_trait] LANGUAGE 1033");
    }

    protected override void Down(MigrationBuilder migrationBuilder)
    {
        DropFullTextIndex(migrationBuilder, "gene_traits");
        DropFullTextIndex(migrationBuilder, "gene_go_terms");
        DropFullTextIndex(migrationBuilder, "gene_synonyms");
        DropFullTextIndex(migrationBuilder, "genes");
        migrationBuilder.Sql("""
            IF EXISTS (SELECT 1 FROM sys.fulltext_catalogs WHERE name = N'GenomeSearchFullText')
                DROP FULLTEXT CATALOG [GenomeSearchFullText];
            """);
    }

    private static void CreateFullTextIndex(
        MigrationBuilder migrationBuilder,
        string table,
        string keyIndex,
        string columns)
    {
        var escapedTable = $"[dbo].[{table}]";
        migrationBuilder.Sql($"""
            IF NOT EXISTS (
                SELECT 1 FROM sys.fulltext_indexes
                WHERE object_id = OBJECT_ID(N'{escapedTable}')
            )
                CREATE FULLTEXT INDEX ON {escapedTable} ({columns})
                KEY INDEX [{keyIndex}]
                ON [GenomeSearchFullText]
                WITH CHANGE_TRACKING AUTO;
            """);
    }

    private static void DropFullTextIndex(MigrationBuilder migrationBuilder, string table)
    {
        var escapedTable = $"[dbo].[{table}]";
        migrationBuilder.Sql($"""
            IF EXISTS (
                SELECT 1 FROM sys.fulltext_indexes
                WHERE object_id = OBJECT_ID(N'{escapedTable}')
            )
                DROP FULLTEXT INDEX ON {escapedTable};
            """);
    }
}
