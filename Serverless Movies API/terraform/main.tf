terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.15.0"
    }
  }

  required_version = ">= 1.1.0"
}

provider "azurerm" {
  subscription_id = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" # Fill your subscription ID
  features {}
}

resource "azurerm_resource_group" "serverless-movies-api-rg" {
  name     = "serverless-movies-api-rg"
  location = "southafricanorth"
}

resource "azurerm_cosmosdb_account" "movie-db" {
  name                       = "movie-dbxx25"
  resource_group_name        = azurerm_resource_group.serverless-movies-api-rg.name
  location                   = azurerm_resource_group.serverless-movies-api-rg.location
  offer_type                 = "Standard"
  kind                       = "GlobalDocumentDB"
  automatic_failover_enabled = false
  free_tier_enabled          = true

  consistency_policy {
    consistency_level = "Session"

  }
  geo_location {
    location          = "eastus"
    failover_priority = 0

  }
  capabilities {
    name = "EnableServerless"

  }
}

resource "azurerm_cosmosdb_sql_database" "movies" {
  name                = "movies"
  resource_group_name = azurerm_resource_group.serverless-movies-api-rg.name
  account_name        = azurerm_cosmosdb_account.movie-db.name
}

resource "azurerm_cosmosdb_sql_container" "movie-info" {
  name                  = "movie-info"
  resource_group_name   = azurerm_resource_group.serverless-movies-api-rg.name
  account_name          = azurerm_cosmosdb_account.movie-db.name
  database_name         = azurerm_cosmosdb_sql_database.movies.name
  partition_key_paths   = ["/id"]
  partition_key_version = 1
}

resource "azurerm_storage_account" "funcappstacct" {
  name                     = "funcappstacctxx25"
  resource_group_name      = azurerm_resource_group.serverless-movies-api-rg.name
  location                 = azurerm_resource_group.serverless-movies-api-rg.location
  account_replication_type = "LRS"
  account_tier             = "Standard"
}

resource "azurerm_service_plan" "serverless-movies-service-plan" {
  name                = "serverless-movies-service-plan"
  resource_group_name = azurerm_resource_group.serverless-movies-api-rg.name
  location            = azurerm_resource_group.serverless-movies-api-rg.location
  os_type             = "Linux"
  sku_name            = "B1"
}

resource "azurerm_application_insights" "func-app-insights" {
  name                = "func-app-insights"
  resource_group_name = azurerm_resource_group.serverless-movies-api-rg.name
  location            = azurerm_resource_group.serverless-movies-api-rg.location
  application_type    = "other"
}

resource "azurerm_linux_function_app" "linux-func-app" {
  name                       = "linux-func-app"
  resource_group_name        = azurerm_resource_group.serverless-movies-api-rg.name
  location                   = azurerm_resource_group.serverless-movies-api-rg.location
  storage_account_name       = azurerm_storage_account.funcappstacct.name
  storage_account_access_key = azurerm_storage_account.funcappstacct.primary_access_key
  service_plan_id            = azurerm_service_plan.serverless-movies-service-plan.id

  site_config {
    application_insights_key               = azurerm_application_insights.func-app-insights.instrumentation_key
    application_insights_connection_string = azurerm_application_insights.func-app-insights.connection_string
    application_stack {
      python_version = "3.9"
    }
  }

  app_settings = {
    "ACCOUNT_URI"                    = "${azurerm_cosmosdb_account.movie-db.endpoint}"
    "ACCOUNT_KEY"                    = "${azurerm_cosmosdb_account.movie-db.primary_readonly_key}"
    "APPINSIGHTS_INSTRUMENTATIONKEY" = "${azurerm_application_insights.func-app-insights.instrumentation_key}"
    "COHERE_API_KEY"                 = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxx" # Fill your Cohere API key
    "AZURE_FUNCTIONS_ENVIRONMENT"    = "Development"
    "WEBSITE_RUN_FROM_PACKAGE"       = 1
  }

  zip_deploy_file = "path/to/func/code.zip" # Fill the path to your function code zip file
}

output "hostname" {
  value = azurerm_linux_function_app.linux-func-app.default_hostname
}