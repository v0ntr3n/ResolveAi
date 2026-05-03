#!/usr/bin/env pwsh
# Seed demo orders for testing ResolveAI customer support system

Write-Host "🌱 Seeding demo orders..." -ForegroundColor Cyan

# Run the seed demo script
python -m app.data.seed_demo

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Demo orders seeded successfully!" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to seed demo orders" -ForegroundColor Red
    exit 1
}
