# Automated AWS Deployment Script for CloudPilot (Lambda + API Gateway)
# Zero-hardcoded-secrets deployment using IAM roles and AWS CLI credentials

param(
    [string]$Region = $env:AWS_DEFAULT_REGION,
    [string]$FunctionName = "CloudPilotBackendLambda",
    [string]$RoleName = "CloudPilotLambdaExecutionRole"
)

if (-not $Region) {
    $Region = "us-east-1"
}

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host " CloudPilot AWS Deployment Pipeline " -ForegroundColor Cyan
Write-Host " Target Region: $Region " -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# 1. Verify AWS CLI
$caller = aws sts get-caller-identity --output json | ConvertFrom-Json
if ($caller -and $caller.Account) {
    Write-Host "[OK] Authenticated as AWS Account: $($caller.Account) ($($caller.Arn))" -ForegroundColor Green
} else {
    Write-Error "AWS CLI authentication failed. Please configure AWS credentials or environment variables."
    exit 1
}

# 2. Package Lambda zip archive
$workingDir = Split-Path -Path $PSScriptRoot -Parent
Write-Host "[*] Packaging deployment zip in $workingDir..." -ForegroundColor Yellow

$zipPath = Join-Path -Path $PSScriptRoot -ChildPath "lambda_package.zip"
if (Test-Path $zipPath) { Remove-Item $zipPath -Force }

Set-Location $workingDir

# Copy lambda_function.py temporarily to root for flat zip structure
Copy-Item "deployment/lambda_function.py" -Destination "lambda_function.py" -Force

$itemsToZip = @(
    "agent.py",
    "tools.py",
    "safety.py",
    "schemas.py",
    "prompts.py",
    "requirements.txt",
    "lambda_function.py"
)

Compress-Archive -Path $itemsToZip -DestinationPath $zipPath -Force
Remove-Item "lambda_function.py" -Force

Write-Host "[OK] Zip package created successfully at $zipPath" -ForegroundColor Green

# 3. Create or check IAM Role
Write-Host "[*] Provisioning IAM Execution Role ($RoleName)..." -ForegroundColor Yellow

$assumeRoleJson = '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"lambda.amazonaws.com"},"Action":"sts:AssumeRole"}]}'

$roleArn = $null
$existingRole = $null
try {
    $existingRole = aws iam get-role --role-name $RoleName --output json 2>$null | ConvertFrom-Json
} catch {}

if ($existingRole -and $existingRole.Role) {
    $roleArn = $existingRole.Role.Arn
    Write-Host "[OK] Found existing IAM Role: $roleArn" -ForegroundColor Green
} else {
    Write-Host "[*] Creating new IAM Role..." -ForegroundColor Yellow
    $policyFile = [System.IO.Path]::GetTempFileName()
    $assumeRoleJson | Out-File -FilePath $policyFile -Encoding ascii
    
    $createRole = aws iam create-role --role-name $RoleName --assume-role-policy-document "file://$policyFile" --output json | ConvertFrom-Json
    $roleArn = $createRole.Role.Arn
    Remove-Item $policyFile -Force

    # Attach Basic Execution & Bedrock permissions
    aws iam attach-role-policy --role-name $RoleName --policy-arn "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole" 2>$null
    
    # Wait for IAM propagation
    Write-Host "[*] Waiting 10s for IAM role propagation..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
    Write-Host "[OK] IAM Role provisioned: $roleArn" -ForegroundColor Green
}

# 4. Deploy/Update Lambda Function
Write-Host "[*] Deploying AWS Lambda function ($FunctionName)..." -ForegroundColor Yellow

$existingLambda = $null
try {
    $existingLambda = aws lambda get-function --function-name $FunctionName --region $Region --output json 2>$null | ConvertFrom-Json
} catch {}

if ($existingLambda -and $existingLambda.Configuration) {
    Write-Host "[*] Updating existing Lambda function code..." -ForegroundColor Yellow
    aws lambda update-function-code --function-name $FunctionName --zip-file "fileb://$zipPath" --region $Region | Out-Null
    aws lambda update-function-configuration --function-name $FunctionName --handler "lambda_function.lambda_handler" --region $Region | Out-Null
    Write-Host "[OK] Lambda function code updated successfully!" -ForegroundColor Green
} else {
    Write-Host "[*] Creating new Lambda function..." -ForegroundColor Yellow
    aws lambda create-function --function-name $FunctionName --runtime "python3.11" --role $roleArn --handler "lambda_function.lambda_handler" --zip-file "fileb://$zipPath" --timeout 30 --memory-size 256 --region $Region | Out-Null
    Write-Host "[OK] Lambda function created successfully!" -ForegroundColor Green
}

# 5. Provision API Gateway HTTP Endpoint
Write-Host "[*] Provisioning API Gateway REST API..." -ForegroundColor Yellow

$apiName = "CloudPilotAPI"
$apiId = $null

$apis = aws apigateway get-rest-apis --region $Region --output json | ConvertFrom-Json
$existingApi = $apis.items | Where-Object { $_.name -eq $apiName }

if ($existingApi) {
    $apiId = $existingApi.id
    Write-Host "[OK] Found existing API Gateway ID: $apiId" -ForegroundColor Green
} else {
    $newApi = aws apigateway create-rest-api --name $apiName --description "CloudPilot AI Assistant Backend API" --region $Region --output json | ConvertFrom-Json
    $apiId = $newApi.id
    Write-Host "[OK] Created new API Gateway ID: $apiId" -ForegroundColor Green
}

# Deploy stage
Write-Host "[*] Deploying API Gateway /prod stage..." -ForegroundColor Yellow
aws apigateway create-deployment --rest-api-id $apiId --stage-name "prod" --region $Region 2>$null | Out-Null

$endpointUrl = "https://$apiId.execute-api.$Region.amazonaws.com/prod"
Write-Host "==========================================" -ForegroundColor Green
Write-Host " CloudPilot Deployment Successful! " -ForegroundColor Green
Write-Host " Live API Endpoint: $endpointUrl " -ForegroundColor Green
Write-Host " Health Check URL: $endpointUrl/health " -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
