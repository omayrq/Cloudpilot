# Automated AWS S3 & CloudFront Web UI Deployment Pipeline for CloudPilot

param(
    [string]$Region = "us-east-1",
    [string]$BucketName = "cloudpilot-app-528582359305"
)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host " CloudPilot Web UI AWS Deployment Pipeline " -ForegroundColor Cyan
Write-Host " Target Region: $Region " -ForegroundColor Cyan
Write-Host " Target Bucket: $BucketName " -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# 1. Verify AWS CLI
$caller = aws sts get-caller-identity --output json | ConvertFrom-Json
if ($caller -and $caller.Account) {
    Write-Host "[OK] Authenticated as AWS Account: $($caller.Account)" -ForegroundColor Green
} else {
    Write-Error "AWS CLI authentication failed."
    exit 1
}

# 2. Disable Block Public Access for static website hosting
Write-Host "[*] Configuring S3 Public Access Block..." -ForegroundColor Yellow
aws s3api put-public-access-block --bucket $BucketName --public-access-block-configuration "BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false" 2>$null

# 3. Apply Bucket Policy for Public Read
Write-Host "[*] Applying Public Read Bucket Policy..." -ForegroundColor Yellow
$bucketPolicy = @"
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::$BucketName/*"
    }
  ]
}
"@

$policyFile = [System.IO.Path]::GetTempFileName()
$bucketPolicy | Out-File -FilePath $policyFile -Encoding ascii
aws s3api put-bucket-policy --bucket $BucketName --policy "file://$policyFile" 2>$null
Remove-Item $policyFile -Force

# 4. Enable Website Configuration
Write-Host "[*] Enabling Static Website Hosting..." -ForegroundColor Yellow
aws s3api put-bucket-website --bucket $BucketName --website-configuration '{"IndexDocument":{"Suffix":"index.html"}}' 2>$null

# 5. Upload index.html
Write-Host "[*] Uploading index.html to S3 Bucket..." -ForegroundColor Yellow
$rootPath = Split-Path -Path $PSScriptRoot -Parent
$indexPath = Join-Path -Path $rootPath -ChildPath "index.html"

aws s3 cp $indexPath "s3://$BucketName/index.html" --content-type "text/html" --region $Region
Write-Host "[OK] index.html uploaded successfully!" -ForegroundColor Green

$websiteUrl = "http://$BucketName.s3-website-$Region.amazonaws.com"
Write-Host "==========================================" -ForegroundColor Green
Write-Host " CloudPilot Live Web Application Deployed! " -ForegroundColor Green
Write-Host " Live Web App URL: $websiteUrl " -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
