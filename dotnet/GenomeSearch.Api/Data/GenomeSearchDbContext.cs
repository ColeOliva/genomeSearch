using GenomeSearch.Api.Models;
using Microsoft.EntityFrameworkCore;

namespace GenomeSearch.Api.Data;

public sealed class GenomeSearchDbContext(DbContextOptions<GenomeSearchDbContext> options)
    : DbContext(options)
{
    public DbSet<Species> Species => Set<Species>();
    public DbSet<Gene> Genes => Set<Gene>();
    public DbSet<GeneSynonym> GeneSynonyms => Set<GeneSynonym>();
    public DbSet<GeneGoTerm> GeneGoTerms => Set<GeneGoTerm>();
    public DbSet<GeneSummary> GeneSummaries => Set<GeneSummary>();
    public DbSet<Trait> Traits => Set<Trait>();
    public DbSet<GeneTrait> GeneTraits => Set<GeneTrait>();
    public DbSet<GeneConstraint> GeneConstraints => Set<GeneConstraint>();
    public DbSet<ClinVarGeneSummary> ClinVarGeneSummaries => Set<ClinVarGeneSummary>();
    public DbSet<ClinVarVariant> ClinVarVariants => Set<ClinVarVariant>();
    public DbSet<MousePhenotypeTerm> MousePhenotypeTerms => Set<MousePhenotypeTerm>();
    public DbSet<MousePhenotype> MousePhenotypes => Set<MousePhenotype>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.Entity<Species>(entity =>
        {
            entity.ToTable("species");
            entity.HasKey(x => x.TaxId);
            entity.Property(x => x.TaxId).HasColumnName("tax_id");
            entity.Property(x => x.Name).HasColumnName("name").HasMaxLength(255).IsRequired();
            entity.Property(x => x.CommonName).HasColumnName("common_name").HasMaxLength(255);
            entity.Property(x => x.GeneCount).HasColumnName("gene_count").HasDefaultValue(0);
        });

        modelBuilder.Entity<Gene>(entity =>
        {
            entity.ToTable("genes");
            entity.HasKey(x => x.GeneId);
            entity.HasIndex(x => x.Symbol).HasDatabaseName("idx_genes_symbol");
            entity.HasIndex(x => x.Chromosome).HasDatabaseName("idx_genes_chromosome");
            entity.HasIndex(x => x.TaxId).HasDatabaseName("idx_genes_tax_id");
            entity.Property(x => x.GeneId).HasColumnName("gene_id");
            entity.Property(x => x.TaxId).HasColumnName("tax_id");
            entity.Property(x => x.Symbol).HasColumnName("symbol").HasMaxLength(255).IsRequired();
            entity.Property(x => x.Name).HasColumnName("name").HasMaxLength(1000);
            entity.Property(x => x.Chromosome).HasColumnName("chromosome").HasMaxLength(50);
            entity.Property(x => x.MapLocation).HasColumnName("map_location").HasMaxLength(100);
            entity.Property(x => x.Description).HasColumnName("description").HasColumnType("nvarchar(max)");
            entity.Property(x => x.GeneType).HasColumnName("gene_type").HasMaxLength(100);
            entity.HasOne(x => x.Species).WithMany(x => x.Genes).HasForeignKey(x => x.TaxId);
        });

        modelBuilder.Entity<GeneSynonym>(entity =>
        {
            entity.ToTable("gene_synonyms");
            entity.HasKey(x => x.Id);
            entity.HasIndex(x => x.GeneId).HasDatabaseName("idx_synonyms_gene");
            entity.Property(x => x.Id).HasColumnName("id");
            entity.Property(x => x.GeneId).HasColumnName("gene_id");
            entity.Property(x => x.Synonym).HasColumnName("synonym").HasMaxLength(255).IsRequired();
            entity.HasOne(x => x.Gene).WithMany(x => x.Synonyms).HasForeignKey(x => x.GeneId);
        });

        modelBuilder.Entity<GeneGoTerm>(entity =>
        {
            entity.ToTable("gene_go_terms");
            entity.HasKey(x => x.Id);
            entity.HasIndex(x => x.GeneId).HasDatabaseName("idx_go_gene");
            entity.Property(x => x.Id).HasColumnName("id");
            entity.Property(x => x.GeneId).HasColumnName("gene_id");
            entity.Property(x => x.GoId).HasColumnName("go_id").HasMaxLength(50).IsRequired();
            entity.Property(x => x.GoTerm).HasColumnName("go_term").HasMaxLength(1000).IsRequired();
            entity.Property(x => x.Category).HasColumnName("category").HasMaxLength(50);
            entity.HasOne(x => x.Gene).WithMany(x => x.GoTerms).HasForeignKey(x => x.GeneId);
        });

        modelBuilder.Entity<GeneSummary>(entity =>
        {
            entity.ToTable("gene_summaries");
            entity.HasKey(x => x.Id);
            entity.HasIndex(x => x.GeneId).HasDatabaseName("idx_summaries_gene").IsUnique();
            entity.Property(x => x.Id).HasColumnName("id");
            entity.Property(x => x.GeneId).HasColumnName("gene_id");
            entity.Property(x => x.Summary).HasColumnName("summary").HasColumnType("nvarchar(max)").IsRequired();
            entity.Property(x => x.Source).HasColumnName("source").HasMaxLength(255);
            entity.HasOne(x => x.Gene).WithOne(x => x.Summary).HasForeignKey<GeneSummary>(x => x.GeneId);
        });

        modelBuilder.Entity<Trait>(entity =>
        {
            entity.ToTable("traits");
            entity.HasKey(x => x.TraitId);
            entity.HasIndex(x => x.ReportedTrait).IsUnique();
            entity.Property(x => x.TraitId).HasColumnName("trait_id");
            entity.Property(x => x.EfoTrait).HasColumnName("efo_trait").HasMaxLength(1000);
            entity.Property(x => x.ReportedTrait).HasColumnName("reported_trait").HasMaxLength(1000);
            entity.Property(x => x.TraitCategory).HasColumnName("trait_category").HasMaxLength(255);
        });

        modelBuilder.Entity<GeneTrait>(entity =>
        {
            entity.ToTable("gene_traits");
            entity.HasKey(x => x.Id);
            entity.HasIndex(x => x.GeneId).HasDatabaseName("idx_gene_traits_gene_id");
            entity.HasIndex(x => x.GeneSymbol).HasDatabaseName("idx_gene_traits_symbol");
            entity.HasIndex(x => x.ReportedTrait).HasDatabaseName("idx_gene_traits_trait");
            entity.Property(x => x.Id).HasColumnName("id");
            entity.Property(x => x.GeneId).HasColumnName("gene_id");
            entity.Property(x => x.GeneSymbol).HasColumnName("gene_symbol").HasMaxLength(255).IsRequired();
            entity.Property(x => x.TraitId).HasColumnName("trait_id");
            entity.Property(x => x.ReportedTrait).HasColumnName("reported_trait").HasMaxLength(1000);
            entity.Property(x => x.EfoTrait).HasColumnName("efo_trait").HasMaxLength(1000);
            entity.Property(x => x.PValue).HasColumnName("p_value").HasColumnType("float");
            entity.Property(x => x.PValueText).HasColumnName("p_value_text").HasMaxLength(100);
            entity.Property(x => x.RiskAllele).HasColumnName("risk_allele").HasMaxLength(100);
            entity.Property(x => x.RiskAlleleFreq).HasColumnName("risk_allele_freq").HasColumnType("float");
            entity.Property(x => x.OddsRatio).HasColumnName("odds_ratio").HasColumnType("float");
            entity.Property(x => x.BetaCoefficient).HasColumnName("beta_coefficient").HasColumnType("float");
            entity.Property(x => x.CiText).HasColumnName("ci_text").HasMaxLength(255);
            entity.Property(x => x.Chromosome).HasColumnName("chromosome").HasMaxLength(50);
            entity.Property(x => x.Position).HasColumnName("position");
            entity.Property(x => x.SnpId).HasColumnName("snp_id").HasMaxLength(100);
            entity.Property(x => x.StudyId).HasColumnName("study_id").HasMaxLength(100);
            entity.Property(x => x.PubMedId).HasColumnName("pubmed_id").HasMaxLength(100);
            entity.Property(x => x.SampleDescription).HasColumnName("sample_description").HasColumnType("nvarchar(max)");
            entity.HasOne(x => x.Gene).WithMany(x => x.Traits).HasForeignKey(x => x.GeneId);
            entity.HasOne(x => x.Trait).WithMany(x => x.GeneTraits).HasForeignKey(x => x.TraitId);
        });

        ConfigureConstraint(modelBuilder);
        ConfigureClinVar(modelBuilder);
        ConfigureMousePhenotypes(modelBuilder);
    }

    private static void ConfigureConstraint(ModelBuilder modelBuilder)
    {
        modelBuilder.Entity<GeneConstraint>(entity =>
        {
            entity.ToTable("gene_constraints");
            entity.HasKey(x => x.Id);
            entity.HasIndex(x => x.GeneId).HasDatabaseName("idx_constraints_gene");
            entity.HasIndex(x => x.GeneSymbol).HasDatabaseName("idx_constraints_symbol");
            entity.HasIndex(x => x.Pli).HasDatabaseName("idx_constraints_pli");
            entity.HasIndex(x => x.Loeuf).HasDatabaseName("idx_constraints_loeuf");
            entity.Property(x => x.Id).HasColumnName("id");
            entity.Property(x => x.GeneId).HasColumnName("gene_id");
            entity.Property(x => x.GeneSymbol).HasColumnName("gene_symbol").HasMaxLength(255).IsRequired();
            entity.Property(x => x.Transcript).HasColumnName("transcript").HasMaxLength(255);
            entity.Property(x => x.Pli).HasColumnName("pli").HasColumnType("float");
            entity.Property(x => x.Loeuf).HasColumnName("loeuf").HasColumnType("float");
            entity.Property(x => x.LoeufLower).HasColumnName("loeuf_lower").HasColumnType("float");
            entity.Property(x => x.LoeufUpper).HasColumnName("loeuf_upper").HasColumnType("float");
            entity.Property(x => x.OeLof).HasColumnName("oe_lof").HasColumnType("float");
            entity.Property(x => x.OeMis).HasColumnName("oe_mis").HasColumnType("float");
            entity.Property(x => x.OeMisLower).HasColumnName("oe_mis_lower").HasColumnType("float");
            entity.Property(x => x.OeMisUpper).HasColumnName("oe_mis_upper").HasColumnType("float");
            entity.Property(x => x.MisZ).HasColumnName("mis_z").HasColumnType("float");
            entity.Property(x => x.OeSyn).HasColumnName("oe_syn").HasColumnType("float");
            entity.Property(x => x.SynZ).HasColumnName("syn_z").HasColumnType("float");
            entity.Property(x => x.GnomadVersion).HasColumnName("gnomad_version").HasMaxLength(50);
            entity.HasOne(x => x.Gene).WithMany(x => x.Constraints).HasForeignKey(x => x.GeneId);
        });
    }

    private static void ConfigureClinVar(ModelBuilder modelBuilder)
    {
        modelBuilder.Entity<ClinVarGeneSummary>(entity =>
        {
            entity.ToTable("clinvar_gene_summary");
            entity.HasKey(x => x.Id);
            entity.HasIndex(x => x.GeneId).HasDatabaseName("idx_clinvar_summary_gene");
            entity.HasIndex(x => x.GeneSymbol).HasDatabaseName("idx_clinvar_summary_symbol");
            entity.HasIndex(x => x.PathogenicAlleles).HasDatabaseName("idx_clinvar_summary_pathogenic");
            entity.Property(x => x.Id).HasColumnName("id");
            entity.Property(x => x.GeneId).HasColumnName("gene_id");
            entity.Property(x => x.GeneSymbol).HasColumnName("gene_symbol").HasMaxLength(255).IsRequired();
            entity.Property(x => x.TotalSubmissions).HasColumnName("total_submissions").HasDefaultValue(0);
            entity.Property(x => x.TotalAlleles).HasColumnName("total_alleles").HasDefaultValue(0);
            entity.Property(x => x.PathogenicAlleles).HasColumnName("pathogenic_alleles").HasDefaultValue(0);
            entity.Property(x => x.UncertainAlleles).HasColumnName("uncertain_alleles").HasDefaultValue(0);
            entity.Property(x => x.ConflictingAlleles).HasColumnName("conflicting_alleles").HasDefaultValue(0);
            entity.Property(x => x.GeneMimNumber).HasColumnName("gene_mim_number").HasMaxLength(50);
            entity.HasOne(x => x.Gene).WithMany(x => x.ClinVarSummary).HasForeignKey(x => x.GeneId);
        });

        modelBuilder.Entity<ClinVarVariant>(entity =>
        {
            entity.ToTable("clinvar_variants");
            entity.HasKey(x => x.Id);
            entity.HasIndex(x => x.GeneId).HasDatabaseName("idx_clinvar_variants_gene");
            entity.HasIndex(x => x.GeneSymbol).HasDatabaseName("idx_clinvar_variants_symbol");
            entity.HasIndex(x => x.AlleleId).HasDatabaseName("idx_clinvar_variants_allele");
            entity.HasIndex(x => x.Chromosome).HasDatabaseName("idx_clinvar_variants_chr");
            entity.HasIndex(x => x.ClinicalSignificance).HasDatabaseName("idx_clinvar_variants_significance");
            entity.Property(x => x.Id).HasColumnName("id");
            entity.Property(x => x.AlleleId).HasColumnName("allele_id");
            entity.Property(x => x.VariationId).HasColumnName("variation_id");
            entity.Property(x => x.GeneId).HasColumnName("gene_id");
            entity.Property(x => x.GeneSymbol).HasColumnName("gene_symbol").HasMaxLength(255);
            entity.Property(x => x.VariantName).HasColumnName("variant_name").HasMaxLength(1000);
            entity.Property(x => x.VariantType).HasColumnName("variant_type").HasMaxLength(100);
            entity.Property(x => x.ClinicalSignificance).HasColumnName("clinical_significance").HasMaxLength(255);
            entity.Property(x => x.ReviewStatus).HasColumnName("review_status").HasMaxLength(255);
            entity.Property(x => x.PhenotypeList).HasColumnName("phenotype_list").HasColumnType("nvarchar(max)");
            entity.Property(x => x.Chromosome).HasColumnName("chromosome").HasMaxLength(50);
            entity.Property(x => x.StartPos).HasColumnName("start_pos");
            entity.Property(x => x.StopPos).HasColumnName("stop_pos");
            entity.Property(x => x.ReferenceAllele).HasColumnName("reference_allele").HasMaxLength(1000);
            entity.Property(x => x.AlternateAllele).HasColumnName("alternate_allele").HasMaxLength(1000);
            entity.Property(x => x.RsId).HasColumnName("rs_id");
            entity.Property(x => x.LastEvaluated).HasColumnName("last_evaluated").HasMaxLength(100);
            entity.Property(x => x.Origin).HasColumnName("origin").HasMaxLength(100);
            entity.Property(x => x.Assembly).HasColumnName("assembly").HasMaxLength(50);
            entity.HasOne(x => x.Gene).WithMany(x => x.ClinVarVariants).HasForeignKey(x => x.GeneId);
        });
    }

    private static void ConfigureMousePhenotypes(ModelBuilder modelBuilder)
    {
        modelBuilder.Entity<MousePhenotypeTerm>(entity =>
        {
            entity.ToTable("mouse_phenotype_terms");
            entity.HasKey(x => x.MpId);
            entity.Property(x => x.MpId).HasColumnName("mp_id").HasMaxLength(50);
            entity.Property(x => x.TermName).HasColumnName("term_name").HasMaxLength(1000).IsRequired();
            entity.Property(x => x.Description).HasColumnName("description").HasColumnType("nvarchar(max)");
        });

        modelBuilder.Entity<MousePhenotype>(entity =>
        {
            entity.ToTable("mouse_phenotypes");
            entity.HasKey(x => x.Id);
            entity.HasIndex(x => x.GeneId).HasDatabaseName("idx_mouse_phenotypes_gene");
            entity.HasIndex(x => x.MpId).HasDatabaseName("idx_mouse_phenotypes_mp");
            entity.Property(x => x.Id).HasColumnName("id");
            entity.Property(x => x.GeneId).HasColumnName("gene_id");
            entity.Property(x => x.MouseSymbol).HasColumnName("mouse_symbol").HasMaxLength(255);
            entity.Property(x => x.MpId).HasColumnName("mp_id").HasMaxLength(50).IsRequired();
            entity.HasOne(x => x.Gene).WithMany(x => x.MousePhenotypes).HasForeignKey(x => x.GeneId);
            entity.HasOne(x => x.Term).WithMany(x => x.GeneMappings).HasForeignKey(x => x.MpId);
        });
    }
}
