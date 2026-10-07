#!/usr/bin/env bash
# One-off Azure setup for SAGE: resource group, logs, Container Apps environment, GitHub's deploy identity,
# and the storage account that hosts the frontend.
# Run from the repo root after `az login`: bash infra/azure/setup.sh. Safe to run again.
set -euo pipefail # stop at the first error, unset variable or failed pipe

# ---- Settings. Resource names live in names.env, which the deploy workflows read too ----
# shellcheck source=infra/azure/names.env
source "$(dirname "${BASH_SOURCE[0]}")/names.env"
LOCATION="southafricanorth" # Johannesburg. Cape Town's region is disaster-recovery only.
# Who may use the deploy identity: workflows on main in this repo. Repos made after
# 15 July 2026 are identified by name plus permanent ID (owner 164753108, repo 1391659537).
GITHUB_SUBJECT="repo:BumeMxenge@164753108/SAGE@1391659537:ref:refs/heads/main"

say() { printf '\n==> %s\n' "$*"; }

# ---- 0. Checks before anything is created ----
say "Checking your Azure login"
SUBSCRIPTION_ID=$(az account show --query id --output tsv) # fails here if you haven't run az login
TENANT_ID=$(az account show --query tenantId --output tsv)
echo "Subscription:  $(az account show --query name --output tsv)"
echo "Signed in as:  $(az account show --query user.name --output tsv)"
read -rp "Create SAGE's resources in this subscription? [y/N] " reply
[[ $reply == [yY] ]] || exit 1

# Azure for Students allows only a few regions, and they differ per student
ALLOWED=$(az policy assignment list \
  --query "[].parameters.listOfAllowedLocations.value[]" --output tsv)
if [[ -n $ALLOWED ]] && ! grep -qx "$LOCATION" <<<"$ALLOWED"; then
  echo "This subscription can't use $LOCATION. It allows:"
  echo "$ALLOWED"
  exit 1
fi

# ---- 1. Switch on the Azure services SAGE uses (new subscriptions start with them off) ----
say "Registering Azure services (slow the first time only)"
for namespace in Microsoft.App Microsoft.OperationalInsights Microsoft.ManagedIdentity Microsoft.Storage; do
  az provider register --namespace "$namespace" --wait
done

# ---- 2. Resource group ----
say "Resource group $RESOURCE_GROUP"
az group create --name "$RESOURCE_GROUP" --location "$LOCATION" --tags project=sage --output none

# ---- 3. Log Analytics workspace ----
# 30 days of history and a 0.1 GB daily cap keep logs inside Azure's free 5 GB a month
say "Log workspace $LOG_WORKSPACE"
az monitor log-analytics workspace create --resource-group "$RESOURCE_GROUP" \
  --workspace-name "$LOG_WORKSPACE" --location "$LOCATION" \
  --retention-time 30 --quota 0.1 --output none

# ---- 4. Container Apps environment ----
# Free on its own: you pay per app, and an idle app scales to zero. The app itself is
# created by the first deploy, since it needs an image and GitHub hasn't built one yet.
say "Container Apps environment $CONTAINER_ENV (a few minutes the first time)"
if ! az containerapp env show --resource-group "$RESOURCE_GROUP" --name "$CONTAINER_ENV" \
  --output none 2>/dev/null; then
  LOG_ID=$(az monitor log-analytics workspace show --resource-group "$RESOURCE_GROUP" \
    --workspace-name "$LOG_WORKSPACE" --query customerId --output tsv)
  LOG_KEY=$(az monitor log-analytics workspace get-shared-keys --resource-group "$RESOURCE_GROUP" \
    --workspace-name "$LOG_WORKSPACE" --query primarySharedKey --output tsv)
  az containerapp env create --resource-group "$RESOURCE_GROUP" --name "$CONTAINER_ENV" \
    --location "$LOCATION" --logs-workspace-id "$LOG_ID" --logs-workspace-key "$LOG_KEY" --output none
fi

# ---- 5. GitHub's deploy identity (both deploy workflows sign in as it) ----
# There's no password. For each run, GitHub signs a short-lived token saying which repo,
# branch and workflow it came from. Azure accepts it only if it matches GITHUB_SUBJECT.
say "Deploy identity $DEPLOY_IDENTITY"
az identity create --resource-group "$RESOURCE_GROUP" --name "$DEPLOY_IDENTITY" \
  --location "$LOCATION" --output none
az identity federated-credential create --resource-group "$RESOURCE_GROUP" \
  --identity-name "$DEPLOY_IDENTITY" --name github-main \
  --issuer https://token.actions.githubusercontent.com --subject "$GITHUB_SUBJECT" \
  --audiences api://AzureADTokenExchange --output none

# Contributor on this resource group only: enough to deploy SAGE, nothing else you own
PRINCIPAL_ID=$(az identity show --resource-group "$RESOURCE_GROUP" --name "$DEPLOY_IDENTITY" \
  --query principalId --output tsv)
az role assignment create --assignee-object-id "$PRINCIPAL_ID" \
  --assignee-principal-type ServicePrincipal --role Contributor \
  --scope "$(az group show --name "$RESOURCE_GROUP" --query id --output tsv)" --output none

# ---- 6. Frontend website: a storage account that serves the built files ----
say "Frontend storage account $STORAGE_ACCOUNT"
if ! az storage account show --resource-group "$RESOURCE_GROUP" --name "$STORAGE_ACCOUNT" \
  --output none 2>/dev/null; then
  AVAILABLE=$(az storage account check-name --name "$STORAGE_ACCOUNT" --query nameAvailable --output tsv)
  if [[ $AVAILABLE != true ]]; then
    echo "Another Azure customer already has the name $STORAGE_ACCOUNT."
    echo "Choose another (3 to 24 lowercase letters and digits) and change STORAGE_ACCOUNT in infra/azure/names.env."
    exit 1
  fi
  # Blob public access only affects the account's other containers. The website stays public either way.
  az storage account create --resource-group "$RESOURCE_GROUP" --name "$STORAGE_ACCOUNT" \
    --location "$LOCATION" --sku Standard_LRS --kind StorageV2 \
    --allow-blob-public-access false --tags project=sage --output none
fi

# Serve the $web container as a website. Every unknown path gets index.html too, so a refresh
# on a page like /history still loads the app (with a 404 status that visitors never see).
# --auth-mode key: you own the subscription, so az fetches the account key for you.
az storage blob service-properties update --account-name "$STORAGE_ACCOUNT" --auth-mode key \
  --static-website true --index-document index.html --404-document index.html \
  --only-show-errors --output none

# Lets the deploy identity upload files, on this account only. Contributor alone could only upload
# by fetching the account key; this role lets it upload with its own sign-in, so no key is handled.
az role assignment create --assignee-object-id "$PRINCIPAL_ID" \
  --assignee-principal-type ServicePrincipal --role "Storage Blob Data Contributor" \
  --scope "$(az storage account show --resource-group "$RESOURCE_GROUP" --name "$STORAGE_ACCOUNT" \
    --query id --output tsv)" --output none
WEBSITE=$(az storage account show --resource-group "$RESOURCE_GROUP" --name "$STORAGE_ACCOUNT" \
  --query primaryEndpoints.web --output tsv)

CLIENT_ID=$(az identity show --resource-group "$RESOURCE_GROUP" --name "$DEPLOY_IDENTITY" \
  --query clientId --output tsv)
cat <<DONE

Done. On GitHub, add these three as repository secrets
(Settings > Secrets and variables > Actions > New repository secret):

  AZURE_CLIENT_ID        $CLIENT_ID
  AZURE_TENANT_ID        $TENANT_ID
  AZURE_SUBSCRIPTION_ID  $SUBSCRIPTION_ID

The frontend will be served at ${WEBSITE%/}
Add ${WEBSITE%/}/** to Supabase: Authentication > URL Configuration > Redirect URLs.
Then add the Supabase variables on GitHub (docs/setup.md, section 11).
DONE
