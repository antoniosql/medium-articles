terraform {
  required_version = ">= 1.5.0"

  required_providers {
    databricks = {
      source  = "databricks/databricks"
      version = ">= 1.42.0"
    }
  }
}

# This file is intentionally minimal.
# Extend it to provision catalogs, schemas, jobs, permissions, secret scopes,
# and any workspace-level assets needed by your platform team.

provider "databricks" {
  host  = var.databricks_host
  token = var.databricks_token
}
