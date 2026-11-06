using GenomeSearch.Api.Data;
using GenomeSearch.Api.Search;
using GenomeSearch.Api.Pleiotropy;
using System.Threading.RateLimiting;
using Microsoft.AspNetCore.RateLimiting;
using Microsoft.EntityFrameworkCore;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();
builder.Services.AddMemoryCache();
builder.Services.AddDbContext<GenomeSearchDbContext>(options =>
    options.UseSqlServer(builder.Configuration.GetConnectionString("GenomeSearch")));
builder.Services.AddScoped<IGeneSearchService, GeneSearchService>();
builder.Services.AddSingleton<ISearchResponseCache, MemorySearchResponseCache>();
builder.Services.AddSingleton<IPleiotropyIndexCalculator, PleiotropyIndexCalculator>();
builder.Services.AddRateLimiter(options =>
{
    options.RejectionStatusCode = StatusCodes.Status429TooManyRequests;
    options.AddPolicy("search", context =>
        RateLimitPartition.GetFixedWindowLimiter(
            context.Connection.RemoteIpAddress?.ToString() ?? "unknown",
            _ => new FixedWindowRateLimiterOptions
            {
                PermitLimit = Math.Max(1, builder.Configuration.GetValue("Search:RateLimitPermitLimit", 60)),
                Window = TimeSpan.FromSeconds(
                    Math.Max(1, builder.Configuration.GetValue("Search:RateLimitWindowSeconds", 60))),
                QueueLimit = 0,
                AutoReplenishment = true
            }));
});

var app = builder.Build();

// Configure the HTTP request pipeline.
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseAuthorization();
app.UseRateLimiter();

app.MapControllers();

app.Run();

public partial class Program;
