#!/bin/bash

# Azure RAG Accelerator Environment Deployment Script
# Usage: ./scripts/deploy-environment.sh <environment> [resource-group] [environment-name]
# Example: ./scripts/deploy-environment.sh dev rg-ragchat-dev myragchat-dev

set -e

ENVIRONMENT=$1
RESOURCE_GROUP=$2
ENVIRONMENT_NAME=$3

# Function to display usage
usage() {
    echo "Usage: $0 <environment> [resource-group] [environment-name]"
    echo ""
    echo "Environments:"
    echo "  dev        - Development environment (cost-optimized, ~$265-300/month)"
    echo "  staging    - Staging environment (production-like, ~$350-450/month)"
    echo "  prod       - Production environment (full enterprise, ~$600-800/month)"
    echo ""
    echo "Examples:"
    echo "  $0 dev"
    echo "  $0 dev rg-ragchat-dev myragchat-dev"
    echo "  $0 staging rg-ragchat-staging myragchat-staging"
    echo "  $0 prod rg-ragchat-prod myragchat-prod"
    exit 1
}

# Validate environment parameter
if [ -z "$ENVIRONMENT" ]; then
    echo "Error: Environment parameter is required"
    usage
fi

if [ "$ENVIRONMENT" != "dev" ] && [ "$ENVIRONMENT" != "staging" ] && [ "$ENVIRONMENT" != "prod" ]; then
    echo "Error: Invalid environment '$ENVIRONMENT'. Must be 'dev', 'staging', or 'prod'"
    usage
fi

# Set default values if not provided
if [ -z "$RESOURCE_GROUP" ]; then
    RESOURCE_GROUP="rg-ragchat-$ENVIRONMENT"
fi

if [ -z "$ENVIRONMENT_NAME" ]; then
    ENVIRONMENT_NAME="ragchat-$ENVIRONMENT-$(date +%Y%m%d)"
fi

# Determine parameter file
PARAMETER_FILE="infra/$ENVIRONMENT.parameters.json"

# Check if parameter file exists
if [ ! -f "$PARAMETER_FILE" ]; then
    echo "Error: Parameter file '$PARAMETER_FILE' not found"
    exit 1
fi

# Display deployment information
echo "================================================================================"
echo "Azure RAG Accelerator Environment Deployment"
echo "================================================================================"
echo "Environment:      $ENVIRONMENT"
echo "Resource Group:   $RESOURCE_GROUP"
echo "Environment Name: $ENVIRONMENT_NAME"
echo "Parameter File:   $PARAMETER_FILE"
echo "Location:         ${AZURE_LOCATION:-eastus}"
echo ""

# Get cost estimates based on environment
case $ENVIRONMENT in
    "dev")
        echo "Estimated Cost:   ~$265-300/month"
        echo "Services:         Azure AI Search, Storage, OpenAI, App Service (Basic)"
        ;;
    "staging")
        echo "Estimated Cost:   ~$350-450/month"
        echo "Services:         8/11 services, App Service (Standard), Private Endpoints"
        ;;
    "prod")
        echo "Estimated Cost:   ~$600-800/month"
        echo "Services:         All 11 services, App Service (Premium), Multi-region setup"
        ;;
esac

echo "================================================================================"
echo ""

# Confirm deployment
read -p "Do you want to proceed with this deployment? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled"
    exit 0
fi

# Get Azure location (default to eastus if not set)
LOCATION=${AZURE_LOCATION:-eastus}

# Get principal ID for RBAC
echo "Getting current user principal ID for RBAC..."
PRINCIPAL_ID=$(az ad signed-in-user show --query id --output tsv)

if [ -z "$PRINCIPAL_ID" ]; then
    echo "Error: Unable to get current user principal ID. Please ensure you are logged in with 'az login'"
    exit 1
fi

echo "Principal ID: $PRINCIPAL_ID"
echo ""

# Create resource group if it doesn't exist
echo "Creating resource group '$RESOURCE_GROUP' in location '$LOCATION'..."
az group create --name "$RESOURCE_GROUP" --location "$LOCATION" --output table

echo ""

# Deploy the infrastructure
echo "Starting deployment..."
echo "This may take 15-30 minutes depending on the services being deployed..."
echo ""

az deployment group create \
    --resource-group "$RESOURCE_GROUP" \
    --template-file infra/main.bicep \
    --parameters "$PARAMETER_FILE" \
    --parameters environmentName="$ENVIRONMENT_NAME" \
    --parameters location="$LOCATION" \
    --parameters principalId="$PRINCIPAL_ID" \
    --output table

DEPLOYMENT_STATUS=$?

echo ""
echo "================================================================================"

if [ $DEPLOYMENT_STATUS -eq 0 ]; then
    echo "✅ Deployment completed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Wait 5-10 minutes for the application to fully initialize"
    echo "2. Navigate to the deployed application URL"
    echo "3. Upload your documents using the data ingestion scripts"
    echo ""
    echo "Useful commands:"
    echo "  az deployment group show --resource-group $RESOURCE_GROUP --name main --query properties.outputs"
    echo "  ./scripts/prepdocs.sh  # Upload sample documents"
    echo ""
    echo "Documentation:"
    echo "  docs/environment-deployments.md - Environment deployment guide"
    echo "  docs/deployment-parameters.md   - Parameter reference"
else
    echo "❌ Deployment failed!"
    echo ""
    echo "Troubleshooting:"
    echo "1. Check the deployment logs in the Azure portal"
    echo "2. Verify your Azure subscription has sufficient quota"
    echo "3. Ensure the environment name is unique"
    echo "4. Review docs/deploy_troubleshooting.md"
fi

echo "================================================================================" 