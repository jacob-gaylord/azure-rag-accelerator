#!/usr/bin/env pwsh

<#
.SYNOPSIS
    Azure RAG Accelerator Environment Deployment Script
.DESCRIPTION
    Deploys the Azure RAG Accelerator using environment-specific parameter files
.PARAMETER Environment
    The environment to deploy (dev, staging, prod)
.PARAMETER ResourceGroup
    The Azure resource group name (optional, defaults to rg-ragchat-{environment})
.PARAMETER EnvironmentName
    The environment name for resource naming (optional, defaults to ragchat-{environment}-{date})
.EXAMPLE
    .\scripts\deploy-environment.ps1 -Environment dev
.EXAMPLE
    .\scripts\deploy-environment.ps1 -Environment dev -ResourceGroup "rg-ragchat-dev" -EnvironmentName "myragchat-dev"
#>

param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("dev", "staging", "prod")]
    [string]$Environment,
    
    [Parameter(Mandatory = $false)]
    [string]$ResourceGroup,
    
    [Parameter(Mandatory = $false)]
    [string]$EnvironmentName
)

# Set default values
if (-not $ResourceGroup) {
    $ResourceGroup = "rg-ragchat-$Environment"
}

if (-not $EnvironmentName) {
    $date = Get-Date -Format "yyyyMMdd"
    $EnvironmentName = "ragchat-$Environment-$date"
}

# Determine parameter file
$ParameterFile = "infra/$Environment.parameters.json"

# Check if parameter file exists
if (-not (Test-Path $ParameterFile)) {
    Write-Error "Parameter file '$ParameterFile' not found"
    exit 1
}

# Display deployment information
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "Azure RAG Accelerator Environment Deployment" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "Environment:      $Environment" -ForegroundColor White
Write-Host "Resource Group:   $ResourceGroup" -ForegroundColor White
Write-Host "Environment Name: $EnvironmentName" -ForegroundColor White
Write-Host "Parameter File:   $ParameterFile" -ForegroundColor White
Write-Host "Location:         $($env:AZURE_LOCATION ?? 'eastus')" -ForegroundColor White
Write-Host ""

# Get cost estimates based on environment
switch ($Environment) {
    "dev" {
        Write-Host "Estimated Cost:   ~`$265-300/month" -ForegroundColor Green
        Write-Host "Services:         Azure AI Search, Storage, OpenAI, App Service (Basic)" -ForegroundColor White
    }
    "staging" {
        Write-Host "Estimated Cost:   ~`$350-450/month" -ForegroundColor Yellow
        Write-Host "Services:         8/11 services, App Service (Standard), Private Endpoints" -ForegroundColor White
    }
    "prod" {
        Write-Host "Estimated Cost:   ~`$600-800/month" -ForegroundColor Red
        Write-Host "Services:         All 11 services, App Service (Premium), Multi-region setup" -ForegroundColor White
    }
}

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

# Confirm deployment
$confirmation = Read-Host "Do you want to proceed with this deployment? (y/N)"
if ($confirmation -ne 'y' -and $confirmation -ne 'Y') {
    Write-Host "Deployment cancelled" -ForegroundColor Yellow
    exit 0
}

# Get Azure location (default to eastus if not set)
$Location = $env:AZURE_LOCATION ?? "eastus"

# Get principal ID for RBAC
Write-Host "Getting current user principal ID for RBAC..." -ForegroundColor Blue
try {
    $PrincipalId = az ad signed-in-user show --query id --output tsv
    if (-not $PrincipalId) {
        throw "Unable to get principal ID"
    }
}
catch {
    Write-Error "Unable to get current user principal ID. Please ensure you are logged in with 'az login'"
    exit 1
}

Write-Host "Principal ID: $PrincipalId" -ForegroundColor White
Write-Host ""

# Create resource group if it doesn't exist
Write-Host "Creating resource group '$ResourceGroup' in location '$Location'..." -ForegroundColor Blue
az group create --name $ResourceGroup --location $Location --output table

Write-Host ""

# Deploy the infrastructure
Write-Host "Starting deployment..." -ForegroundColor Blue
Write-Host "This may take 15-30 minutes depending on the services being deployed..." -ForegroundColor Yellow
Write-Host ""

$deploymentResult = az deployment group create `
    --resource-group $ResourceGroup `
    --template-file infra/main.bicep `
    --parameters $ParameterFile `
    --parameters environmentName=$EnvironmentName `
    --parameters location=$Location `
    --parameters principalId=$PrincipalId `
    --output table

$deploymentSuccess = $LASTEXITCODE -eq 0

Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan

if ($deploymentSuccess) {
    Write-Host "✅ Deployment completed successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor White
    Write-Host "1. Wait 5-10 minutes for the application to fully initialize" -ForegroundColor White
    Write-Host "2. Navigate to the deployed application URL" -ForegroundColor White
    Write-Host "3. Upload your documents using the data ingestion scripts" -ForegroundColor White
    Write-Host ""
    Write-Host "Useful commands:" -ForegroundColor White
    Write-Host "  az deployment group show --resource-group $ResourceGroup --name main --query properties.outputs" -ForegroundColor Gray
    Write-Host "  .\scripts\prepdocs.ps1  # Upload sample documents" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Documentation:" -ForegroundColor White
    Write-Host "  docs/environment-deployments.md - Environment deployment guide" -ForegroundColor Gray
    Write-Host "  docs/deployment-parameters.md   - Parameter reference" -ForegroundColor Gray
}
else {
    Write-Host "❌ Deployment failed!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Troubleshooting:" -ForegroundColor White
    Write-Host "1. Check the deployment logs in the Azure portal" -ForegroundColor White
    Write-Host "2. Verify your Azure subscription has sufficient quota" -ForegroundColor White
    Write-Host "3. Ensure the environment name is unique" -ForegroundColor White
    Write-Host "4. Review docs/deploy_troubleshooting.md" -ForegroundColor White
}

Write-Host "================================================================================" -ForegroundColor Cyan 