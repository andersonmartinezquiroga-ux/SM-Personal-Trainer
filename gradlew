#!/usr/bin/env sh
set -e

GRADLE_VERSION=8.9
DIST_URL="https://services.gradle.org/distributions/gradle-${GRADLE_VERSION}-bin.zip"
CACHE_DIR="${HOME}/.gradle/sm-wrapper"
GRADLE_DIR="${CACHE_DIR}/gradle-${GRADLE_VERSION}"

if [ ! -x "${GRADLE_DIR}/bin/gradle" ]; then
  mkdir -p "${CACHE_DIR}"
  ZIP_PATH="${CACHE_DIR}/gradle-${GRADLE_VERSION}-bin.zip"
  if [ ! -f "${ZIP_PATH}" ]; then
    curl -L "${DIST_URL}" -o "${ZIP_PATH}"
  fi
  unzip -q -o "${ZIP_PATH}" -d "${CACHE_DIR}"
fi

exec "${GRADLE_DIR}/bin/gradle" "$@"
