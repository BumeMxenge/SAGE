#!/usr/bin/env bash
# One-off Azure setup for SAGE: resource group, logs, Container Apps environment, GitHub's deploy identity.
# Run from the repo root after `az login`: bash infra/azure/setup.sh. Safe to run again.
set -euo pipefail # stop at the first error, unset variable or failed pipe

# ---- Settings. Names follow Microsoft's naming guide: a type prefix, then the project ----
LOCATION="southafricanorth"      # Johannesburg. Cape Town's region is disaster-recovery only.
RESOURCE_GROUP="rg-sage"         # the folder that holds everything below
LOG_WORKSPACE="log-sage"         # where the backend's logs go
ENVIRONMENT="cae-sage"           # Container Apps environment: the space the backend runs in
DEPLOY_IDENTITY="id-sage-github" # the robot account GitHub Actions deploys as
# Who may use that robot account: workflows on main in this repo. Repos made after
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
for namespace in Microsoft.App Microsoft.OperationalInsights Microsoft.ManagedIdentity; do
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
say "Container Apps environment $ENVIRONMENT (a few minutes the first time)"
if ! az containerapp env show --resource-group "$RESOURCE_GROUP" --name "$ENVIRONMENT" \
  --output none 2>/dev/null; then
  LOG_ID=$(az monitor log-analytics workspace show --resource-group "$RESOURCE_GROUP" \
    --workspace-name "$LOG_WORKSPACE" --query customerId --output tsv)
  LOG_KEY=$(az monitor log-analytics workspace get-shared-keys --resource-group "$RESOURCE_GROUP" \
    --workspace-name "$LOG_WORKSPACE" --query primarySharedKey --output tsv)
  az containerapp env create --resource-group "$RESOURCE_GROUP" --name "$ENVIRONMENT" \
    --location "$LOCATION" --logs-workspace-id "$LOG_ID" --logs-workspace-key "$LOG_KEY" --output none
fi

# ---- 5. GitHub's deploy identity (deploy-backend.yml uses it next) ----
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

CLIENT_ID=$(az identity show --resource-group "$RESOURCE_GROUP" --name "$DEPLOY_IDENTITY" \
  --query clientId --output tsv)
cat <<DONE

Done. On GitHub, add these three as repository secrets
(Settings > Secrets and variables > Actions > New repository secret):

  AZURE_CLIENT_ID        $CLIENT_ID
  AZURE_TENANT_ID        $TENANT_ID
  AZURE_SUBSCRIPTION_ID  $SUBSCRIPTION_ID
DONE
