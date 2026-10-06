#!/bin/bash

set -euo pipefail

if [[ $(uname -s) != Darwin ]]; then
    echo "FAIL: Finder Sync inspection requires macOS." >&2
    exit 1
fi

if (( $# < 2 || $# > 3 )); then
    echo "Usage: $0 <app-path> <extension-relative-path> [extension-bundle-id]" >&2
    exit 64
fi

app_path=$1
extension_relative_path=$2
extension_bundle_id=${3:-}
case "$extension_relative_path" in
    /*|..|../*|*/../*|*/..)
        echo "FAIL: extension path must stay relative to the app bundle." >&2
        exit 64
        ;;
esac
extension_path="$app_path/$extension_relative_path"

if [[ ! -d "$app_path" ]]; then
    echo "FAIL: app bundle does not exist: $app_path" >&2
    exit 1
fi

if [[ ! -d "$extension_path" ]]; then
    echo "FAIL: Finder extension does not exist: $extension_path" >&2
    exit 1
fi

app_info="$app_path/Contents/Info.plist"
extension_info="$extension_path/Contents/Info.plist"

if [[ ! -f "$app_info" || ! -f "$extension_info" ]]; then
    echo "FAIL: one or both bundles lack Contents/Info.plist." >&2
    exit 1
fi

extension_point=$(/usr/libexec/PlistBuddy -c 'Print :NSExtension:NSExtensionPointIdentifier' "$extension_info" 2>/dev/null || true)
principal_class=$(/usr/libexec/PlistBuddy -c 'Print :NSExtension:NSExtensionPrincipalClass' "$extension_info" 2>/dev/null || true)

echo "Extension point: ${extension_point:-<missing>}"
echo "Principal class: ${principal_class:-<missing>}"

if [[ "$extension_point" != "com.apple.FinderSync" ]]; then
    echo "FAIL: embedded extension is not a Finder Sync extension." >&2
    exit 1
fi

if [[ -z "$principal_class" ]]; then
    echo "FAIL: Finder extension lacks its principal class." >&2
    exit 1
fi

codesign --verify --strict --verbose=2 "$app_path"
codesign --verify --strict --verbose=2 "$extension_path"

inspection_tmp=$(mktemp -d "${TMPDIR:-/tmp}/finder-inspection.XXXXXX")
trap 'rm -rf "$inspection_tmp"' EXIT

inspect_entitlements() {
    local label=$1
    local target_path=$2
    local entitlement_file=$3

    if codesign -d --entitlements - --xml "$target_path" 2>/dev/null > "$entitlement_file"; then
        echo "$label entitlements:"
        plutil -p "$entitlement_file"
    else
        echo "FAIL: could not read $label entitlements." >&2
        return 1
    fi
}

app_team=$(codesign -dvv "$app_path" 2>&1 | sed -n 's/^TeamIdentifier=//p' | head -n 1)
extension_team=$(codesign -dvv "$extension_path" 2>&1 | sed -n 's/^TeamIdentifier=//p' | head -n 1)
echo "Main app team: ${app_team:-<adhoc or unavailable>}"
echo "Finder extension team: ${extension_team:-<adhoc or unavailable>}"

inspect_entitlements "Main app" "$app_path" "$inspection_tmp/app-entitlements.plist"
inspect_entitlements "Finder extension" "$extension_path" "$inspection_tmp/extension-entitlements.plist"

if [[ -n "$app_team" && -n "$extension_team" && "$app_team" != "$extension_team" ]]; then
    echo "FAIL: containing app and Finder extension use different signing teams." >&2
    exit 1
fi

if [[ -z "$app_team" || -z "$extension_team" ]]; then
    echo "WARN: a signing team is unavailable; team compatibility is not established."
fi

echo "File and media entitlements found:"
file_entitlements=$(
    for entitlement_file in \
        "$inspection_tmp/app-entitlements.plist" \
        "$inspection_tmp/extension-entitlements.plist"
    do
        plutil -p "$entitlement_file" 2>/dev/null || true
    done | grep 'com.apple.security.files.\|com.apple.security.assets.' | sort -u || true
)
if [[ -n "$file_entitlements" ]]; then
    echo "$file_entitlements"
else
    echo "<none>"
fi

if [[ -n "$extension_bundle_id" ]]; then
    echo "Finder extension registration:"
    registration_output=$(pluginkit -m -v -i "$extension_bundle_id" 2>/dev/null || true)
    echo "${registration_output:-<not registered>}"

    registration_count=$(grep -F -c "$extension_bundle_id" <<< "$registration_output" || true)
    if [[ "$registration_count" -ne 1 ]]; then
        echo "FAIL: expected exactly one registration for $extension_bundle_id, found $registration_count." >&2
        exit 1
    fi
fi

echo "PASS: Finder Sync structure, signatures, entitlements, and requested registration were inspected."
echo "Real Finder interaction and file authorization remain separate checks."
