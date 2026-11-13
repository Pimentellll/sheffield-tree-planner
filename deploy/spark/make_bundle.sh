#!/usr/bin/env bash
# Build an integrity-checked CANOPY deployment bundle from ONE committed revision.
#
# Runs on a development machine (Linux/WSL/macOS) with git, uv and Node.js 20.19+/22.12+.
# Everything is built from `git archive <rev>` in a fresh temporary directory, never from
# the working tree, so the bundle contains exactly that commit plus:
#   frontend/dist/      static React/Three.js build (Spark needs no Node.js)
#   wheel/              the CANOPY wheel built from that commit
#   requirements.txt    runtime dependencies exported from uv.lock, with hashes
#   wheelhouse/<plat>/  hash-checked binary wheels for each target platform (offline install)
#   BUNDLE.json         commit, tree, tool versions, platforms, per-file SHA-256
#   SHA256SUMS          every file, checked by `canopyctl verify` before install
# No credentials, model weights, workspaces or .env files are included.
#
# usage: deploy/spark/make_bundle.sh [--rev REV] [--out DIR] [--platform aarch64|x86_64]... [--python 3.12]
#   default: --rev HEAD --out ./.artifact-build --platform aarch64 --python 3.12
set -euo pipefail

REV=HEAD
OUT=.artifact-build
PY=3.12
PLATFORMS=()
while [ $# -gt 0 ]; do
  case "$1" in
    --rev) REV="$2"; shift 2 ;;
    --out) OUT="$2"; shift 2 ;;
    --platform) PLATFORMS+=("$2"); shift 2 ;;
    --python) PY="$2"; shift 2 ;;
    -h|--help) sed -n 2,19p "$0"; exit 0 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done
[ ${#PLATFORMS[@]} -eq 0 ] && PLATFORMS=(aarch64)

ROOT="$(git rev-parse --show-toplevel)"
COMMIT="$(git -C "$ROOT" rev-parse --verify "$REV^{commit}")"
TREE="$(git -C "$ROOT" rev-parse "$COMMIT^{tree}")"
SHORT="${COMMIT:0:12}"
if [ "$REV" = HEAD ] && [ -n "$(git -C "$ROOT" status --porcelain --untracked-files=no)" ]; then
  echo "note: working tree has uncommitted changes; they are NOT in the bundle (built from $SHORT)" >&2
fi
for tool in git uv node npm sha256sum tar; do command -v "$tool" >/dev/null || { echo "missing tool: $tool" >&2; exit 1; }; done

mkdir -p "$OUT"
OUT="$(cd "$OUT" && pwd)"
NAME="canopy-spark-$SHORT"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
STAGE="$WORK/$NAME"
mkdir -p "$STAGE"

echo "== source: git archive $COMMIT"
git -C "$ROOT" archive --format=tar "$COMMIT" | tar -x -C "$STAGE"
echo "$COMMIT" > "$STAGE/COMMIT"

echo "== frontend build (from the archived tree)"
(cd "$STAGE/frontend" && npm ci --no-audit --no-fund --loglevel=error && npm run build --silent)
rm -rf "$STAGE/frontend/node_modules"

echo "== wheel"
(cd "$STAGE" && uv build --wheel --out-dir "$STAGE/wheel" --quiet)
rm -rf "$STAGE/.venv"

echo "== requirements (runtime only, hashed, from uv.lock)"
(cd "$STAGE" && uv export --frozen --no-dev --no-emit-project --no-header --format requirements-txt -o requirements.txt --quiet)

PIP_VERSION=25.3
for plat in "${PLATFORMS[@]}"; do
  case "$plat" in
    aarch64) tags=(--platform manylinux_2_28_aarch64 --platform manylinux_2_17_aarch64 --platform manylinux2014_aarch64) ;;
    x86_64)  tags=(--platform manylinux_2_28_x86_64 --platform manylinux_2_17_x86_64 --platform manylinux2014_x86_64) ;;
    *) echo "unsupported platform $plat" >&2; exit 2 ;;
  esac
  echo "== wheelhouse linux-$plat cp${PY/./}"
  dest="$STAGE/wheelhouse/linux-$plat-cp${PY/./}"
  # pip must RUN under the target Python version: requirement markers such as
  # python_full_version >= '3.12' are evaluated against the running interpreter, not
  # --python-version, and the lock pins different numpy/scipy per Python version.
  uvx --quiet --python "$PY" --from "pip==$PIP_VERSION" pip download --disable-pip-version-check --no-deps \
    --only-binary=:all: --implementation cp --python-version "$PY" "${tags[@]}" \
    --require-hashes -r "$STAGE/requirements.txt" -d "$dest" --quiet
  # pip itself, so a Python without ensurepip can bootstrap: python pip.whl/pip install ...
  uvx --quiet --python "$PY" --from "pip==$PIP_VERSION" pip download --disable-pip-version-check --no-deps \
    --only-binary=:all: "pip==$PIP_VERSION" -d "$dest" --quiet
done

echo "== manifest"
(cd "$STAGE" && find . -type f ! -name SHA256SUMS ! -name BUNDLE.json -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS)
python3 - "$STAGE" "$COMMIT" "$TREE" "$PY" "${PLATFORMS[@]}" <<'EOF'
import json, subprocess, sys, datetime, pathlib
stage, commit, tree, py, *plats = sys.argv[1:]
def v(cmd):
    try: return subprocess.check_output(cmd, text=True).strip().splitlines()[0]
    except Exception as exc: return f"unavailable ({type(exc).__name__})"
root = pathlib.Path(stage)
files = [l.split("  ", 1) for l in (root / "SHA256SUMS").read_text().splitlines()]
json.dump({
    "kind": "canopy-spark-bundle/1",
    "commit": commit, "tree": tree,
    "created_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
    "target_python": py, "wheelhouses": [f"linux-{p}-cp{py.replace('.', '')}" for p in plats],
    "builder": {"uv": v(["uv", "--version"]), "node": v(["node", "--version"]), "npm": v(["npm", "--version"]),
                "machine": v(["uname", "-m"])},
    "excluded": ["credentials", ".env files", "model weights", "workspaces/receipts", "node_modules"],
    "spark_verified": False,
    "files": len(files),
}, open(root / "BUNDLE.json", "w"), indent=2)
EOF
(cd "$STAGE" && sha256sum BUNDLE.json >> SHA256SUMS)

TAR="$OUT/$NAME.tar"
tar --sort=name --owner=0 --group=0 --numeric-owner --mtime="@$(git -C "$ROOT" show -s --format=%ct "$COMMIT")" \
  -C "$WORK" -cf "$TAR" "$NAME"
(cd "$OUT" && sha256sum "$NAME.tar" > "$NAME.tar.sha256")
echo "== done"
echo "bundle:  $TAR"
echo "sha256:  $(cut -d' ' -f1 "$TAR.sha256")"
echo "commit:  $COMMIT"
du -h "$TAR" | cut -f1 | sed 's/^/size:    /'
