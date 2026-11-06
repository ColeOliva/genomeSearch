# Deploying the ASP.NET Core port to Azure

This guide covers the `/dotnet` ASP.NET Core API, Azure App Service on the
Free F1 tier, and Azure SQL Database. It does not deploy the legacy Python
application.

## Architecture

- **App Service:** hosts the ASP.NET Core Web API.
- **Azure SQL Database:** stores the migrated Genome Search relational data.
- **Application cache:** `IMemoryCache` in the App Service process. It is
  intentionally replaceable through `ISearchResponseCache`; use a distributed
  cache before scaling to multiple instances.
- **Full-text search:** SQL Server full-text indexes are created by the
  `FullTextSearch` EF migration. Azure SQL must support the full-text
  features used by the target service tier.

The F1 tier is suitable for a learning and portfolio deployment, but it has
strict quotas, limited CPU/memory, no scale-out, and is not an SLA-backed
production tier. Do not put credentials in the repository or in
`appsettings.json`.

## Prerequisites

Install or have access to:

- Azure CLI
- .NET 8 SDK
- An Azure subscription
- A resource group
- An Azure SQL logical server and database
- The source SQLite database for the one-time import

The repository's GitHub Actions workflow validates the .NET solution but does
not run the data importer or deploy infrastructure.

## Create Azure resources

Choose globally unique names for the server and App Service:

```powershell
$location = "westus2"
$resourceGroup = "genome-search-rg"
$sqlServer = "genomesearch-sql-<unique>"
$sqlDatabase = "genome-search"
$appName = "genome-search-api-<unique>"

az group create `
  --name $resourceGroup `
  --location $location

az sql server create `
  --resource-group $resourceGroup `
  --name $sqlServer `
  --location $location `
  --admin-user "<admin-user>" `
  --admin-password "<strong-password>"

az sql db create `
  --resource-group $resourceGroup `
  --server $sqlServer `
  --name $sqlDatabase `
  --service-objective Basic

az appservice plan create `
  --resource-group $resourceGroup `
  --name "$appName-plan" `
  --is-linux `
  --sku F1

az webapp create `
  --resource-group $resourceGroup `
  --plan "$appName-plan" `
  --name $appName `
  --runtime "DOTNETCORE:8.0"
```

Azure offer availability and SKU names can change. If `Basic` SQL Database or
the F1 App Service plan is unavailable in the selected region, choose the
lowest-cost available equivalent and verify its current pricing separately.

## Configure application settings

App Service settings become environment variables and override
`appsettings.json`. Set the SQL connection string as an App Service connection
string rather than committing it:

```powershell
$sqlConnection = "Server=tcp:$sqlServer.database.windows.net,1433;Initial Catalog=$sqlDatabase;Persist Security Info=False;User ID=<admin-user>;Password=<strong-password>;MultipleActiveResultSets=False;Encrypt=True;TrustServerCertificate=False;Connection Timeout=30;"

az webapp config connection-string set `
  --resource-group $resourceGroup `
  --name $appName `
  --connection-string-type SQLAzure `
  --settings GenomeSearch="$sqlConnection"

az webapp config appsettings set `
  --resource-group $resourceGroup `
  --name $appName `
  --settings `
    ASPNETCORE_ENVIRONMENT=Production `
    Search__CacheDurationSeconds=300 `
    Search__RateLimitPermitLimit=60 `
    Search__RateLimitWindowSeconds=60
```

The application currently reads `ConnectionStrings:GenomeSearch`. If the
deployment platform exposes a connection string under a different environment
variable name, set `ConnectionStrings__GenomeSearch` explicitly:

```powershell
az webapp config appsettings set `
  --resource-group $resourceGroup `
  --name $appName `
  --settings ConnectionStrings__GenomeSearch="$sqlConnection"
```

For production, prefer a managed identity and Azure SQL Microsoft Entra
authentication when that support is added to the application. The current
configuration uses a SQL username/password connection string, which must be
stored only in App Service configuration or a secret manager.

## Apply migrations and import data

Run migrations against the target database before importing data. From the
repository root:

```powershell
dotnet ef database update `
  --project dotnet/GenomeSearch.Api/GenomeSearch.Api.csproj `
  --startup-project dotnet/GenomeSearch.Api/GenomeSearch.Api.csproj `
  --connection "$sqlConnection"
```

The migration creates the relational schema and SQL Server full-text indexes.
Run it only against an empty or intentionally managed database; review pending
migrations before applying them to an existing database.

Build and run the importer locally. The importer streams the SQLite source and
uses batched `SqlBulkCopy` writes:

```powershell
dotnet run `
  --project dotnet/GenomeSearch.Importer/GenomeSearch.Importer.csproj `
  -- `
  --sqlite "data/genome.db" `
  --sqlserver "$sqlConnection" `
  --batch-size 5000
```

For a small verification import:

```powershell
dotnet run `
  --project dotnet/GenomeSearch.Importer/GenomeSearch.Importer.csproj `
  -- `
  --sqlite "data/genome.db" `
  --sqlserver "$sqlConnection" `
  --sample 100
```

`--sample` selects the first N genes and related rows. It is intended for
validation, not as a production data-loading strategy. The importer does not
delete existing rows; use a fresh database for a clean import.

## Deploy the API

Publish the API and deploy the generated package:

```powershell
dotnet publish dotnet/GenomeSearch.Api/GenomeSearch.Api.csproj `
  --configuration Release `
  --output ./dotnet/publish

Compress-Archive `
  -Path ./dotnet/publish/* `
  -DestinationPath ./dotnet/genome-search-api.zip `
  -Force

az webapp deploy `
  --resource-group $resourceGroup `
  --name $appName `
  --src-path ./dotnet/genome-search-api.zip `
  --type zip
```

Then open:

```text
https://<appName>.azurewebsites.net/swagger
```

Swagger is enabled only in the Development environment by the current
`Program.cs`. For a deployed API, use an authenticated or otherwise controlled
diagnostic environment if Swagger is enabled later; do not expose development
diagnostics unintentionally.

## GitHub Actions deployment option

The checked-in [.NET CI workflow](../.github/workflows/dotnet-ci.yml) only
restores, builds, and tests. A deployment workflow should be added only after
the Azure resources and secret strategy are agreed.

If deployment is automated later:

1. Create a GitHub Actions federated credential or a narrowly scoped publish
   profile.
2. Store the Azure client ID, tenant ID, subscription ID, and SQL connection
   configuration in GitHub or Azure secret storage.
3. Keep deployment behind a protected environment such as `production`.
4. Run migrations/import as an explicit controlled step, not on every App
   Service startup.
5. Grant the deployment identity only the resource-group permissions it needs.

Do not put a SQL password, Azure publish profile, or service-principal secret
in workflow YAML.

## Verification checklist

1. `dotnet test dotnet/GenomeSearch.Api.Tests/GenomeSearch.Api.Tests.csproj`
   passes locally.
2. `dotnet ef migrations list` shows the expected migrations.
3. The Azure SQL firewall permits the deployment/import client and App Service
   connectivity path.
4. The importer reports the expected row counts.
5. The App Service starts without connection-string errors.
6. `GET /search?q=BRCA1` returns a JSON response.
7. A full-text query succeeds after the full-text migration completes.
8. Invalid `per_page` values return 400 and rate-limit responses return 429
   after the configured threshold.

## Operational limitations

- F1 is not appropriate for sustained production traffic.
- `IMemoryCache` is local to one process and is lost on restart. It is not a
  shared cache across instances.
- The current rate limiter is process-local; distributed rate limiting needs a
  shared store before scale-out.
- The importer is a one-time/batch utility and is not an App Service startup
  task.
- Azure SQL firewall, full-text availability, quotas, and pricing should be
  verified against the current Azure service documentation before deployment.
