#!/bin/sh

set -eu

usage() {
  echo "Usage: $0 APP_SELECTOR [WORKFLOW_ID]" >&2
}

if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
  usage
  exit 64
fi

if ! command -v asc >/dev/null 2>&1; then
  echo "Error: asc is required." >&2
  exit 69
fi

if ! command -v jq >/dev/null 2>&1; then
  echo "Error: jq is required." >&2
  exit 69
fi

app_selector=$1
workflow_id=${2:-}
audit_dir=$(mktemp -d)

cleanup() {
  rm -f \
    "$audit_dir/products.json" \
    "$audit_dir/workflows.json" \
    "$audit_dir/workflow.json" \
    "$audit_dir/repository.json" \
    "$audit_dir/runs.json" \
    "$audit_dir/builds.json"
  rmdir "$audit_dir" 2>/dev/null || true
}

trap cleanup EXIT HUP INT TERM

printf '{"data":null}\n' > "$audit_dir/workflow.json"
printf '{"data":[]}\n' > "$audit_dir/repository.json"
printf '{"data":[]}\n' > "$audit_dir/runs.json"
printf '{"data":[]}\n' > "$audit_dir/builds.json"

asc xcode-cloud products list \
  --app "$app_selector" \
  --paginate \
  --output json > "$audit_dir/products.json"

asc xcode-cloud workflows list \
  --app "$app_selector" \
  --paginate \
  --output json > "$audit_dir/workflows.json"

if [ -z "$workflow_id" ]; then
  workflow_count=$(jq '.data | length' "$audit_dir/workflows.json")
  if [ "$workflow_count" -eq 1 ]; then
    workflow_id=$(jq -r '.data[0].id' "$audit_dir/workflows.json")
  fi
fi

if [ -n "$workflow_id" ]; then
  asc xcode-cloud workflows view \
    --id "$workflow_id" \
    --output json > "$audit_dir/workflow.json"

  asc xcode-cloud workflows repository \
    --id "$workflow_id" \
    --output json > "$audit_dir/repository.json"

  asc xcode-cloud build-runs list \
    --workflow-id "$workflow_id" \
    --sort=-number \
    --limit 1 \
    --output json > "$audit_dir/runs.json"

  latest_run_id=$(jq -r '.data[0].id // empty' "$audit_dir/runs.json")
  if [ -n "$latest_run_id" ]; then
    asc xcode-cloud build-runs builds \
      --run-id "$latest_run_id" \
      --output json > "$audit_dir/builds.json"
  fi
fi

jq -n \
  --arg queriedApp "$app_selector" \
  --arg selectedWorkflowId "$workflow_id" \
  --slurpfile products "$audit_dir/products.json" \
  --slurpfile workflows "$audit_dir/workflows.json" \
  --slurpfile workflow "$audit_dir/workflow.json" \
  --slurpfile repository "$audit_dir/repository.json" \
  --slurpfile runs "$audit_dir/runs.json" \
  --slurpfile builds "$audit_dir/builds.json" \
  '{
    queriedApp: $queriedApp,
    products: [
      $products[0].data[]? |
      {
        id,
        name: .attributes.name,
        productType: .attributes.productType,
        createdDate: .attributes.createdDate
      }
    ],
    workflows: [
      $workflows[0].data[]? |
      {
        id,
        name: .attributes.name,
        description: .attributes.description,
        enabled: .attributes.isEnabled,
        clean: .attributes.clean,
        containerFilePath: .attributes.containerFilePath,
        branchStartCondition: .attributes.branchStartCondition,
        actions: .attributes.actions,
        lastModifiedDate: .attributes.lastModifiedDate
      }
    ],
    selectedWorkflowId: ($selectedWorkflowId | select(length > 0) // null),
    selectedWorkflow: (
      $workflow[0].data? |
      if . == null then null else {
        id,
        name: .attributes.name,
        enabled: .attributes.isEnabled,
        clean: .attributes.clean,
        containerFilePath: .attributes.containerFilePath,
        branchStartCondition: .attributes.branchStartCondition,
        actions: .attributes.actions
      } end
    ),
    repository: (
      $repository[0].data[0]? |
      if . == null then null else {
        id,
        owner: .attributes.ownerName,
        name: .attributes.repositoryName,
        httpCloneUrl: .attributes.httpCloneUrl
      } end
    ),
    latestRun: (
      $runs[0].data[0]? |
      if . == null then null else {
        id,
        number: .attributes.number,
        executionProgress: .attributes.executionProgress,
        completionStatus: .attributes.completionStatus,
        startReason: .attributes.startReason,
        createdDate: .attributes.createdDate,
        finishedDate: .attributes.finishedDate,
        sourceCommit: .attributes.sourceCommit
      } end
    ),
    builds: [
      $builds[0].data[]? |
      {
        id,
        version: .attributes.version,
        processingState: .attributes.processingState,
        buildAudienceType: .attributes.buildAudienceType,
        uploadedDate: .attributes.uploadedDate,
        expirationDate: .attributes.expirationDate
      }
    ]
  }'
