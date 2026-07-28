#!/bin/bash
set -euo pipefail

if [[ $EUID -ne 0 ]]; then
  echo "Run this deploy helper as root." >&2
  exit 1
fi

# Serialize deployments so concurrent automation cannot race source.new/source.previous.
lock_file=/run/lock/courserekt-deploy.lock
exec 9>"$lock_file"
if ! flock -n 9; then
  echo "Another CourseRekt deployment is already in progress." >&2
  exit 1
fi

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
repo_root=$(git -C "$script_dir/.." rev-parse --show-toplevel)
if [[ ! "$repo_root/scripts/deploy.sh" -ef "${BASH_SOURCE[0]}" ]]; then
  echo "Refusing to deploy from an unexpected repository." >&2
  exit 1
fi
origin_url=$(git -C "$repo_root" remote get-url origin)
case "$origin_url" in
  git@github.com:hermes-jro/courserekt.git|https://github.com/hermes-jro/courserekt.git) ;;
  *) echo "Unexpected origin remote: $origin_url" >&2; exit 1 ;;
esac
cd "$repo_root"
if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "Refusing to deploy an uncommitted tree." >&2
  exit 1
fi

commit=$(git rev-parse --verify HEAD)
new_image="courserekt:$commit"
release_root=/srv/courserekt
new_source=$release_root/source.new
current_source=$release_root/source
previous_source=$release_root/source.previous

install -d -o root -g dockeruser -m 0750 "$release_root"
install -d -o dockeruser -g dockeruser -m 0770 "$release_root/run"
setfacl -m u:www-data:--x "$release_root"
setfacl -m u:www-data:rwx "$release_root/run"
setfacl -d -m u:www-data:rwX "$release_root/run"

rm -rf "$new_source"
install -d -o root -g dockeruser -m 0750 "$new_source"
git archive --format=tar HEAD | tar -xf - -C "$new_source"
printf '%s\n' "$commit" > "$new_source/.release-commit"
chown -R root:dockeruser "$new_source"
chmod -R u=rwX,g=rX,o= "$new_source"

export COURSEREKT_IMAGE="$new_image"
if ! docker buildx build --load --tag "$new_image" "$new_source"; then
  rm -rf "$new_source"
  exit 1
fi

rollback() {
  if [[ -f "$current_source/.release-commit" ]]; then
    export COURSEREKT_IMAGE="courserekt:$(<"$current_source/.release-commit")"
    cd "$current_source"
    docker compose up -d --no-build --remove-orphans --wait --wait-timeout 90
  else
    docker compose -f "$new_source/compose.yaml" rm -sf app || true
  fi
}

if ! (
  cd "$new_source"
  docker compose up -d --no-build --remove-orphans --wait --wait-timeout 90
  curl --fail --silent --show-error --unix-socket "$release_root/run/http.sock" \
    http://localhost/healthz >/dev/null
); then
  rollback
  rm -rf "$new_source"
  exit 1
fi

rm -rf "$previous_source"
if [[ -d "$current_source" ]]; then
  mv "$current_source" "$previous_source"
fi
mv "$new_source" "$current_source"
cd "$current_source"
docker compose ps
