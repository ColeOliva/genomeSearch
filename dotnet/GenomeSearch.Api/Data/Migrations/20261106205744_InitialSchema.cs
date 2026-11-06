using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace GenomeSearch.Api.Data.Migrations
{
    /// <inheritdoc />
    public partial class InitialSchema : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.CreateTable(
                name: "mouse_phenotype_terms",
                columns: table => new
                {
                    mp_id = table.Column<string>(type: "nvarchar(50)", maxLength: 50, nullable: false),
                    term_name = table.Column<string>(type: "nvarchar(1000)", maxLength: 1000, nullable: false),
                    description = table.Column<string>(type: "nvarchar(max)", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_mouse_phenotype_terms", x => x.mp_id);
                });

            migrationBuilder.CreateTable(
                name: "species",
                columns: table => new
                {
                    tax_id = table.Column<int>(type: "int", nullable: false)
                        .Annotation("SqlServer:Identity", "1, 1"),
                    name = table.Column<string>(type: "nvarchar(255)", maxLength: 255, nullable: false),
                    common_name = table.Column<string>(type: "nvarchar(255)", maxLength: 255, nullable: true),
                    gene_count = table.Column<int>(type: "int", nullable: false, defaultValue: 0)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_species", x => x.tax_id);
                });

            migrationBuilder.CreateTable(
                name: "traits",
                columns: table => new
                {
                    trait_id = table.Column<long>(type: "bigint", nullable: false)
                        .Annotation("SqlServer:Identity", "1, 1"),
                    efo_trait = table.Column<string>(type: "nvarchar(1000)", maxLength: 1000, nullable: true),
                    reported_trait = table.Column<string>(type: "nvarchar(1000)", maxLength: 1000, nullable: true),
                    trait_category = table.Column<string>(type: "nvarchar(255)", maxLength: 255, nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_traits", x => x.trait_id);
                });

            migrationBuilder.CreateTable(
                name: "genes",
                columns: table => new
                {
                    gene_id = table.Column<int>(type: "int", nullable: false)
                        .Annotation("SqlServer:Identity", "1, 1"),
                    tax_id = table.Column<int>(type: "int", nullable: false),
                    symbol = table.Column<string>(type: "nvarchar(255)", maxLength: 255, nullable: false),
                    name = table.Column<string>(type: "nvarchar(1000)", maxLength: 1000, nullable: true),
                    chromosome = table.Column<string>(type: "nvarchar(50)", maxLength: 50, nullable: true),
                    map_location = table.Column<string>(type: "nvarchar(100)", maxLength: 100, nullable: true),
                    description = table.Column<string>(type: "nvarchar(max)", nullable: true),
                    gene_type = table.Column<string>(type: "nvarchar(100)", maxLength: 100, nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_genes", x => x.gene_id);
                    table.ForeignKey(
                        name: "FK_genes_species_tax_id",
                        column: x => x.tax_id,
                        principalTable: "species",
                        principalColumn: "tax_id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "clinvar_gene_summary",
                columns: table => new
                {
                    id = table.Column<long>(type: "bigint", nullable: false)
                        .Annotation("SqlServer:Identity", "1, 1"),
                    gene_id = table.Column<int>(type: "int", nullable: false),
                    gene_symbol = table.Column<string>(type: "nvarchar(255)", maxLength: 255, nullable: false),
                    total_submissions = table.Column<int>(type: "int", nullable: false, defaultValue: 0),
                    total_alleles = table.Column<int>(type: "int", nullable: false, defaultValue: 0),
                    pathogenic_alleles = table.Column<int>(type: "int", nullable: false, defaultValue: 0),
                    uncertain_alleles = table.Column<int>(type: "int", nullable: false, defaultValue: 0),
                    conflicting_alleles = table.Column<int>(type: "int", nullable: false, defaultValue: 0),
                    gene_mim_number = table.Column<string>(type: "nvarchar(50)", maxLength: 50, nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_clinvar_gene_summary", x => x.id);
                    table.ForeignKey(
                        name: "FK_clinvar_gene_summary_genes_gene_id",
                        column: x => x.gene_id,
                        principalTable: "genes",
                        principalColumn: "gene_id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "clinvar_variants",
                columns: table => new
                {
                    id = table.Column<long>(type: "bigint", nullable: false)
                        .Annotation("SqlServer:Identity", "1, 1"),
                    allele_id = table.Column<long>(type: "bigint", nullable: false),
                    variation_id = table.Column<long>(type: "bigint", nullable: true),
                    gene_id = table.Column<int>(type: "int", nullable: false),
                    gene_symbol = table.Column<string>(type: "nvarchar(255)", maxLength: 255, nullable: true),
                    variant_name = table.Column<string>(type: "nvarchar(1000)", maxLength: 1000, nullable: true),
                    variant_type = table.Column<string>(type: "nvarchar(100)", maxLength: 100, nullable: true),
                    clinical_significance = table.Column<string>(type: "nvarchar(255)", maxLength: 255, nullable: true),
                    review_status = table.Column<string>(type: "nvarchar(255)", maxLength: 255, nullable: true),
                    phenotype_list = table.Column<string>(type: "nvarchar(max)", nullable: true),
                    chromosome = table.Column<string>(type: "nvarchar(50)", maxLength: 50, nullable: true),
                    start_pos = table.Column<long>(type: "bigint", nullable: true),
                    stop_pos = table.Column<long>(type: "bigint", nullable: true),
                    reference_allele = table.Column<string>(type: "nvarchar(1000)", maxLength: 1000, nullable: true),
                    alternate_allele = table.Column<string>(type: "nvarchar(1000)", maxLength: 1000, nullable: true),
                    rs_id = table.Column<long>(type: "bigint", nullable: true),
                    last_evaluated = table.Column<string>(type: "nvarchar(100)", maxLength: 100, nullable: true),
                    origin = table.Column<string>(type: "nvarchar(100)", maxLength: 100, nullable: true),
                    assembly = table.Column<string>(type: "nvarchar(50)", maxLength: 50, nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_clinvar_variants", x => x.id);
                    table.ForeignKey(
                        name: "FK_clinvar_variants_genes_gene_id",
                        column: x => x.gene_id,
                        principalTable: "genes",
                        principalColumn: "gene_id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "gene_constraints",
                columns: table => new
                {
                    id = table.Column<long>(type: "bigint", nullable: false)
                        .Annotation("SqlServer:Identity", "1, 1"),
                    gene_id = table.Column<int>(type: "int", nullable: false),
                    gene_symbol = table.Column<string>(type: "nvarchar(255)", maxLength: 255, nullable: false),
                    transcript = table.Column<string>(type: "nvarchar(255)", maxLength: 255, nullable: true),
                    pli = table.Column<double>(type: "float", nullable: true),
                    loeuf = table.Column<double>(type: "float", nullable: true),
                    loeuf_lower = table.Column<double>(type: "float", nullable: true),
                    loeuf_upper = table.Column<double>(type: "float", nullable: true),
                    oe_lof = table.Column<double>(type: "float", nullable: true),
                    oe_mis = table.Column<double>(type: "float", nullable: true),
                    oe_mis_lower = table.Column<double>(type: "float", nullable: true),
                    oe_mis_upper = table.Column<double>(type: "float", nullable: true),
                    mis_z = table.Column<double>(type: "float", nullable: true),
                    oe_syn = table.Column<double>(type: "float", nullable: true),
                    syn_z = table.Column<double>(type: "float", nullable: true),
                    gnomad_version = table.Column<string>(type: "nvarchar(50)", maxLength: 50, nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_gene_constraints", x => x.id);
                    table.ForeignKey(
                        name: "FK_gene_constraints_genes_gene_id",
                        column: x => x.gene_id,
                        principalTable: "genes",
                        principalColumn: "gene_id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "gene_go_terms",
                columns: table => new
                {
                    id = table.Column<long>(type: "bigint", nullable: false)
                        .Annotation("SqlServer:Identity", "1, 1"),
                    gene_id = table.Column<int>(type: "int", nullable: false),
                    go_id = table.Column<string>(type: "nvarchar(50)", maxLength: 50, nullable: false),
                    go_term = table.Column<string>(type: "nvarchar(1000)", maxLength: 1000, nullable: false),
                    category = table.Column<string>(type: "nvarchar(50)", maxLength: 50, nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_gene_go_terms", x => x.id);
                    table.ForeignKey(
                        name: "FK_gene_go_terms_genes_gene_id",
                        column: x => x.gene_id,
                        principalTable: "genes",
                        principalColumn: "gene_id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "gene_summaries",
                columns: table => new
                {
                    id = table.Column<long>(type: "bigint", nullable: false)
                        .Annotation("SqlServer:Identity", "1, 1"),
                    gene_id = table.Column<int>(type: "int", nullable: false),
                    summary = table.Column<string>(type: "nvarchar(max)", nullable: false),
                    source = table.Column<string>(type: "nvarchar(255)", maxLength: 255, nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_gene_summaries", x => x.id);
                    table.ForeignKey(
                        name: "FK_gene_summaries_genes_gene_id",
                        column: x => x.gene_id,
                        principalTable: "genes",
                        principalColumn: "gene_id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "gene_synonyms",
                columns: table => new
                {
                    id = table.Column<long>(type: "bigint", nullable: false)
                        .Annotation("SqlServer:Identity", "1, 1"),
                    gene_id = table.Column<int>(type: "int", nullable: false),
                    synonym = table.Column<string>(type: "nvarchar(255)", maxLength: 255, nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_gene_synonyms", x => x.id);
                    table.ForeignKey(
                        name: "FK_gene_synonyms_genes_gene_id",
                        column: x => x.gene_id,
                        principalTable: "genes",
                        principalColumn: "gene_id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "gene_traits",
                columns: table => new
                {
                    id = table.Column<long>(type: "bigint", nullable: false)
                        .Annotation("SqlServer:Identity", "1, 1"),
                    gene_id = table.Column<int>(type: "int", nullable: false),
                    gene_symbol = table.Column<string>(type: "nvarchar(255)", maxLength: 255, nullable: false),
                    trait_id = table.Column<long>(type: "bigint", nullable: true),
                    reported_trait = table.Column<string>(type: "nvarchar(1000)", maxLength: 1000, nullable: true),
                    efo_trait = table.Column<string>(type: "nvarchar(1000)", maxLength: 1000, nullable: true),
                    p_value = table.Column<double>(type: "float", nullable: true),
                    p_value_text = table.Column<string>(type: "nvarchar(100)", maxLength: 100, nullable: true),
                    risk_allele = table.Column<string>(type: "nvarchar(100)", maxLength: 100, nullable: true),
                    risk_allele_freq = table.Column<double>(type: "float", nullable: true),
                    odds_ratio = table.Column<double>(type: "float", nullable: true),
                    beta_coefficient = table.Column<double>(type: "float", nullable: true),
                    ci_text = table.Column<string>(type: "nvarchar(255)", maxLength: 255, nullable: true),
                    chromosome = table.Column<string>(type: "nvarchar(50)", maxLength: 50, nullable: true),
                    position = table.Column<long>(type: "bigint", nullable: true),
                    snp_id = table.Column<string>(type: "nvarchar(100)", maxLength: 100, nullable: true),
                    study_id = table.Column<string>(type: "nvarchar(100)", maxLength: 100, nullable: true),
                    pubmed_id = table.Column<string>(type: "nvarchar(100)", maxLength: 100, nullable: true),
                    sample_description = table.Column<string>(type: "nvarchar(max)", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_gene_traits", x => x.id);
                    table.ForeignKey(
                        name: "FK_gene_traits_genes_gene_id",
                        column: x => x.gene_id,
                        principalTable: "genes",
                        principalColumn: "gene_id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_gene_traits_traits_trait_id",
                        column: x => x.trait_id,
                        principalTable: "traits",
                        principalColumn: "trait_id");
                });

            migrationBuilder.CreateTable(
                name: "mouse_phenotypes",
                columns: table => new
                {
                    id = table.Column<long>(type: "bigint", nullable: false)
                        .Annotation("SqlServer:Identity", "1, 1"),
                    gene_id = table.Column<int>(type: "int", nullable: false),
                    mouse_symbol = table.Column<string>(type: "nvarchar(255)", maxLength: 255, nullable: true),
                    mp_id = table.Column<string>(type: "nvarchar(50)", maxLength: 50, nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_mouse_phenotypes", x => x.id);
                    table.ForeignKey(
                        name: "FK_mouse_phenotypes_genes_gene_id",
                        column: x => x.gene_id,
                        principalTable: "genes",
                        principalColumn: "gene_id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_mouse_phenotypes_mouse_phenotype_terms_mp_id",
                        column: x => x.mp_id,
                        principalTable: "mouse_phenotype_terms",
                        principalColumn: "mp_id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateIndex(
                name: "idx_clinvar_summary_gene",
                table: "clinvar_gene_summary",
                column: "gene_id");

            migrationBuilder.CreateIndex(
                name: "idx_clinvar_summary_pathogenic",
                table: "clinvar_gene_summary",
                column: "pathogenic_alleles");

            migrationBuilder.CreateIndex(
                name: "idx_clinvar_summary_symbol",
                table: "clinvar_gene_summary",
                column: "gene_symbol");

            migrationBuilder.CreateIndex(
                name: "idx_clinvar_variants_allele",
                table: "clinvar_variants",
                column: "allele_id");

            migrationBuilder.CreateIndex(
                name: "idx_clinvar_variants_chr",
                table: "clinvar_variants",
                column: "chromosome");

            migrationBuilder.CreateIndex(
                name: "idx_clinvar_variants_gene",
                table: "clinvar_variants",
                column: "gene_id");

            migrationBuilder.CreateIndex(
                name: "idx_clinvar_variants_significance",
                table: "clinvar_variants",
                column: "clinical_significance");

            migrationBuilder.CreateIndex(
                name: "idx_clinvar_variants_symbol",
                table: "clinvar_variants",
                column: "gene_symbol");

            migrationBuilder.CreateIndex(
                name: "idx_constraints_gene",
                table: "gene_constraints",
                column: "gene_id");

            migrationBuilder.CreateIndex(
                name: "idx_constraints_loeuf",
                table: "gene_constraints",
                column: "loeuf");

            migrationBuilder.CreateIndex(
                name: "idx_constraints_pli",
                table: "gene_constraints",
                column: "pli");

            migrationBuilder.CreateIndex(
                name: "idx_constraints_symbol",
                table: "gene_constraints",
                column: "gene_symbol");

            migrationBuilder.CreateIndex(
                name: "idx_go_gene",
                table: "gene_go_terms",
                column: "gene_id");

            migrationBuilder.CreateIndex(
                name: "idx_summaries_gene",
                table: "gene_summaries",
                column: "gene_id",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "idx_synonyms_gene",
                table: "gene_synonyms",
                column: "gene_id");

            migrationBuilder.CreateIndex(
                name: "idx_gene_traits_gene_id",
                table: "gene_traits",
                column: "gene_id");

            migrationBuilder.CreateIndex(
                name: "idx_gene_traits_symbol",
                table: "gene_traits",
                column: "gene_symbol");

            migrationBuilder.CreateIndex(
                name: "idx_gene_traits_trait",
                table: "gene_traits",
                column: "reported_trait");

            migrationBuilder.CreateIndex(
                name: "IX_gene_traits_trait_id",
                table: "gene_traits",
                column: "trait_id");

            migrationBuilder.CreateIndex(
                name: "idx_genes_chromosome",
                table: "genes",
                column: "chromosome");

            migrationBuilder.CreateIndex(
                name: "idx_genes_symbol",
                table: "genes",
                column: "symbol");

            migrationBuilder.CreateIndex(
                name: "idx_genes_tax_id",
                table: "genes",
                column: "tax_id");

            migrationBuilder.CreateIndex(
                name: "idx_mouse_phenotypes_gene",
                table: "mouse_phenotypes",
                column: "gene_id");

            migrationBuilder.CreateIndex(
                name: "idx_mouse_phenotypes_mp",
                table: "mouse_phenotypes",
                column: "mp_id");

            migrationBuilder.CreateIndex(
                name: "IX_traits_reported_trait",
                table: "traits",
                column: "reported_trait",
                unique: true,
                filter: "[reported_trait] IS NOT NULL");
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropTable(
                name: "clinvar_gene_summary");

            migrationBuilder.DropTable(
                name: "clinvar_variants");

            migrationBuilder.DropTable(
                name: "gene_constraints");

            migrationBuilder.DropTable(
                name: "gene_go_terms");

            migrationBuilder.DropTable(
                name: "gene_summaries");

            migrationBuilder.DropTable(
                name: "gene_synonyms");

            migrationBuilder.DropTable(
                name: "gene_traits");

            migrationBuilder.DropTable(
                name: "mouse_phenotypes");

            migrationBuilder.DropTable(
                name: "traits");

            migrationBuilder.DropTable(
                name: "genes");

            migrationBuilder.DropTable(
                name: "mouse_phenotype_terms");

            migrationBuilder.DropTable(
                name: "species");
        }
    }
}
