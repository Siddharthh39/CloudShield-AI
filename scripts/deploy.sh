#!/usr/bin/env bash
set -euo pipefail

STACK_NAME="${STACK_NAME:-cloudshield-ai}"
REGION="${AWS_REGION:-ap-south-1}"
: "${VpcId:?Set VpcId to an existing VPC ID}"
: "${PrivateSubnetIds:?Set PrivateSubnetIds to comma-separated private subnet IDs}"

sam build --template-file template.yaml --use-container --use-container
sam deploy \
  --template-file .aws-sam/build/template.yaml \
  --stack-name "$STACK_NAME" \
  --region "$REGION" \
  --capabilities CAPABILITY_IAM \
  --resolve-s3 \
  --parameter-overrides "VpcId=${VpcId}" "PrivateSubnetIds=${PrivateSubnetIds}" "FrontendAllowedOrigin=*" \
  --no-confirm-changeset \
  --no-fail-on-empty-changeset

API_URL="$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$REGION" --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" --output text)"
BUCKET="$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$REGION" --query "Stacks[0].Outputs[?OutputKey=='FrontendBucketName'].OutputValue" --output text)"
COGNITO_DOMAIN="$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$REGION" --query "Stacks[0].Outputs[?OutputKey=='CognitoDomain'].OutputValue" --output text)"
COGNITO_CLIENT_ID="$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$REGION" --query "Stacks[0].Outputs[?OutputKey=='CognitoClientId'].OutputValue" --output text)"
FRONTEND_URL="$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$REGION" --query "Stacks[0].Outputs[?OutputKey=='FrontendUrl'].OutputValue" --output text)"

cat > Frontend/config.js <<EOF
window.CLOUDSHIELD_CONFIG = {
  apiBaseUrl: "${API_URL}",
  cognitoDomain: "${COGNITO_DOMAIN}",
  cognitoClientId: "${COGNITO_CLIENT_ID}",
  cognitoRegion: "${REGION}",
  redirectUri: "${FRONTEND_URL}"
};
EOF
aws s3 sync Frontend "s3://${BUCKET}" --delete
echo "CloudShield AI deployed: $(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$REGION" --query "Stacks[0].Outputs[?OutputKey=='FrontendUrl'].OutputValue" --output text)"
