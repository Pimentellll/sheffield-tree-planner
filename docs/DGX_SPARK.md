# DGX Spark: access, inference and application integration

**Status:** event preparation; no Spark access, GPU execution or model inference has occurred. Ben confirmed access is only at the event and approved a private draft PR containing this guide and readiness tools. [BUILD B09/B12](BUILD.md) owns task status. This page is an operational supplement, not a second task board.

## 1. Deployment decision

Target the event's **DGX Spark**, not an x86 DGX server. NVIDIA documents a 20-core Arm CPU, Blackwell GPU and 128 GB unified memory; its newer playbook also lists 64 GB variants. Verify the assigned unit before choosing a profile. Native wheels, CUDA kernels and container architecture must support **Linux ARM64**. Windows or Linux-x86 success does not prove Spark compatibility. [S1–S3]

Recommended order:

1. Inspect any organiser-provided local model service. Reuse it if permitted and it passes the actual structured-tool round trip; record its exact model/runtime. Do not start a duplicate service or stop another team's container.
2. Otherwise, on a confirmed 128 GB Spark, try the pinned **NVIDIA Nemotron 3 Nano 30B A3B BF16 + NVIDIA vLLM** candidate below. Its model card explicitly names a Spark container and tool parser. This is a source-supported candidate, not our tested deployment or a claim that it is the best model. [S4]
3. If measured memory or latency is unsuitable, test a smaller/quantised organiser-supported model against the same tool contract. Changing a model ID is not enough: recheck its chat template, parser, licence and real tool calls. Do not introduce a hosted fallback silently.

No fine-tuning, NIM subscription, paid hosted API or new agent framework is required for this route. OpenAI-compatible describes the **HTTP protocol**, not an OpenAI-hosted service. The product agent is our application loop using local weights; it is not Helios, Codex or a collection of coding assistants.

### Intended final arrangement

```text
Laptop browser
    | SSH tunnel, local port 8080
    v
Spark: application API + built frontend, loopback port 8080  [B01/B05: not built]
    |-- scenario/job store + validated domain dispatcher
    |-- deterministic numerical workers                    [B02/B04/B06: not built]
    `-- local agent loop                                   [B10: not built]
           | OpenAI-compatible HTTP, no cloud credentials
           v
        Spark: vLLM container, host loopback port 8000       [candidate recipe]
           `-- local Nemotron weights on Blackwell GPU
```

For development, the API can stay on the laptop and call the model through local port **8001**. That proves remote model integration, not full-system Spark deployment. The final gate runs the backend, data/jobs and numerical tools on Spark too; the laptop remains the browser. Rendering WebGL in that browser does not demonstrate GPU numerical acceleration on Spark.

## 2. What to obtain at the venue

Ask the organiser or assigned device owner for:

- The exact unit, RAM, DGX OS/driver image, hostname/IP and authorised user account.
- Permission for team SSH access, public-key installation, Docker use, model downloads and a project directory. Docker-group access is root-equivalent; do not grant it to the runtime agent or change membership unilaterally.
- A reachable network path, whether Wi-Fi has client isolation, and permission for a direct Ethernet/private network if necessary.
- The SSH host-key fingerprint from a trusted console/organiser channel; supplied model/container/cache details and whether internet downloads are permitted.
- Event code/AI/asset rules and device cleanup requirements. Repository access does not grant device-administration permission.

Do not paste passwords, private keys or access tokens into chat, GitHub or logs. Each teammate uses their own key, preferably their own account. Never share a single team private key. No router port-forwarding, public inference port, SSH agent forwarding or unapproved VPN installation is needed.

**Can Helios SSH in?** Yes, once this laptop/execution environment can reach the authorised host and use an approved local key/SSH agent. This session already has an OpenSSH client, but no event host or credential is configured. A private venue IP is not reachable automatically from another machine or the internet. Ben can establish/unlock the local credential interactively; subsequent agent commands use noninteractive key authentication, verified host keys and scoped approval. No unrelated VPS is involved.

## 3. SSH setup

These are **event-day instructions**, not claims of an existing connection. NVIDIA Sync is an optional GUI which can import an SSH alias and manage tunnels; manual SSH is sufficient and easier to audit. Do not accept Sync's Docker-group/admin changes without organiser permission. [S2–S3]

### On each laptop

Windows PowerShell example, with OpenSSH installed:

```powershell
ssh -V
ssh-keygen -t ed25519 -f "$HOME/.ssh/sheffield_ed25519" -C "sheffield-event"
```

Create the `.ssh` directory first if it is absent. If that key filename already exists, stop and reuse only if intentionally approved, or choose a new filename; never overwrite it. Enter a passphrase in the local prompt, not chat. Arrange for the organiser to install **only the `.pub` file** into the assigned account's `authorized_keys` using their approved process. Alternatively complete their initial password login yourself in a secure local terminal. This guide does not alter SSH server settings or generate a key automatically.

Copy [ssh_config.example](../deploy/spark/ssh_config.example) to a private `~/.ssh/sheffield_config`, **without overwriting an existing configuration**. Replace its `HostName` and `User` with the assigned values; adjust `IdentityFile` if necessary. The placeholder `.invalid` hostname is deliberately unusable. Keep the configured copy outside the repository.

```powershell
ssh -F "$HOME/.ssh/sheffield_config" sheffield-spark
```

Before accepting the first key, compare its fingerprint with the trusted value. At the Spark console the owner can inspect the public host key using `ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub`. Do not treat `ssh-keyscan` alone as identity verification and never use `StrictHostKeyChecking=no` to fix a mismatch. After trust is established, automated read-only inspection uses:

```powershell
ssh -F "$HOME/.ssh/sheffield_config" -o BatchMode=yes -o StrictHostKeyChecking=yes sheffield-spark "uname -m"
```

A locked/unavailable key should fail, not prompt through an agent or cause password guessing. If using an SSH agent, load/unlock it locally with the same SSH client/agent environment used for subsequent commands. Git Bash OpenSSH and Windows OpenSSH may not share an agent automatically.

### Keep one foreground tunnel open

```powershell
ssh -F "$HOME/.ssh/sheffield_config" -o BatchMode=yes -o StrictHostKeyChecking=yes -N -T -L 127.0.0.1:8001:127.0.0.1:8000 -L 127.0.0.1:8080:127.0.0.1:8080 sheffield-spark
```

- Laptop `http://127.0.0.1:8001/v1` reaches Spark inference.
- Laptop `http://127.0.0.1:8080` reaches the future application, only once it exists and runs.
- Ctrl+C closes this tunnel, not the remote services. The template exits on forwarding failure rather than hiding a local port collision.
- The `0.0.0.0` model bind **inside** its container is paired with `127.0.0.1:8000:8000` host publishing. Never change the latter to `8000:8000`, host networking or a public host bind just to bypass venue networking.

If mDNS fails, use the assigned IP. If TCP/22 is unreachable, have the organiser resolve network isolation/reachability. Do not weaken authentication or expose the server publicly.

## 4. Spark preflight and source transfer

Once authorised, run these read-only checks **on Spark**, not on the laptop:

```bash
uname -m
cat /etc/os-release
free -h
df -h .
nvidia-smi
python3 --version
docker version
docker compose version
docker ps
ss -ltn
```

Expected architecture is `aarch64`/ARM64; confirm device identity using organiser allocation and hardware/OS information, not just a GPU name. Check actual available RAM/disk, existing workloads and occupied ports. Unified-memory accounting is not equivalent to a discrete GPU's dedicated VRAM: capture system memory too. Driver requirements must match the selected CUDA image. Do not upgrade the driver, DGX OS, Docker or Container Toolkit without organiser approval. If a command is unavailable or denied, record that and ask the owner rather than guessing successful output.

Transfer the reviewed code revision without copying personal GitHub tokens/private keys onto a borrowed machine. Either use an organiser-approved GitHub login/clone, or make a tracked-source archive on the laptop:

```powershell
$Commit = git rev-parse HEAD
# Use an existing private scratch directory; never include .env, models or raw assets.
git archive --format=tar --output=".artifact-build/sheffield-$Commit.tar" HEAD
Get-FileHash ".artifact-build/sheffield-$Commit.tar" -Algorithm SHA256
scp -F "$HOME/.ssh/sheffield_config" ".artifact-build/sheffield-$Commit.tar" "sheffield-spark:~/sheffield-$Commit.tar"
```

Compare `sha256sum` on Spark to the laptop hash before extraction into a **new, empty project directory**. Preserve the commit ID alongside the extracted source because `git archive` does not contain `.git`. Transfer approved datasets separately with their licence/provenance manifest. Do not overwrite an existing checkout or claim the draft PR is merged.

## 5. Model and inference setup

### Pinned candidate and its limits

The machine-readable profile is [model-profile.json](../deploy/spark/model-profile.json). It fixes:

- Model: `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16`, revision `bf77c3174f68ad409e1c2aa60daeb46e32d1c606`; NVIDIA Nemotron Open Model License, publicly ungated when checked. Ungated does not remove licence obligations. [S4–S5]
- Runtime: `nvcr.io/nvidia/vllm:25.12.post1-py3`, pinned to its **ARM64 manifest digest** in [inference.compose.yml](../deploy/spark/inference.compose.yml), not a mutable `latest` tag.
- Registry metadata was retrieved and digest-checked: Linux ARM64, `VLLM_VERSION=0.12.0+35a9f223`, `CUDA_VERSION=13.1.0.036`. This resolves the difference from generic 25.12 release notes listing vLLM 0.11.1: we selected **post1**, not the base tag. Metadata is not evidence of successful GPU execution. [S6]
- `qwen3_coder` tool-call parser plus the pinned model repository's `nano_v3` reasoning plugin. The plugin and model custom Python are executable dependencies. Review/trust the exact pinned code before starting `--trust-remote-code`; no arbitrary repository URLs or main-branch parser download.
- Initial **proposed**, not benchmarked, settings: 8,192-token context, one active sequence, GPU-memory-utilisation 0.65. Reserve room for OS, application and numerical work; this fraction is not a hard whole-system memory limit or a guarantee that the model fits. Disable thinking for the initial diagnostic, using the model card's supported request option.

The model registry lists **63,156,694,272 weight bytes** (about 63.16 GB / 58.82 GiB); compressed container layers are about 6.12 GB, and extraction/caches need additional space. No weights or image layers were downloaded in preparation. Do not discover this download requirement on crowded event Wi-Fi. Prefer an approved preloaded model or arrange a lawful pre-download/transfer after checking disk capacity. Do not run this BF16 recipe on a 64 GB unit and expect the application to coexist.

### Prepare assets — only after access/download approval

On Spark, from the source root, use an available reviewed Hugging Face CLI (`hf download --help` must work). If it is absent, install it in an isolated tool environment following its official documentation rather than altering system Python. [S7]

```bash
HF_HUB_DISABLE_IMPLICIT_TOKEN=1 hf download nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16 --revision bf77c3174f68ad409e1c2aa60daeb46e32d1c606 --local-dir models/nemotron-nano
sha256sum -c deploy/spark/model.sha256
mkdir -p state/vllm-cache
```

`model.sha256` covers all 13 weight shards plus five configuration/code files, including the custom parser; it is not a claim of a whole-repository checksum. A transferred snapshot must contain the tokenizer and weight-index JSON as well. Keep the complete pinned snapshot. Retain model licence/attribution files. The model is public; do not add an NGC/Hugging Face secret unless a real authorised operation actually requires one.

The Compose file mounts this model directory read-only and a project-specific writable cache; it does not mount personal credential directories or the Docker socket. Offline Hugging Face/Transformers settings prevent normal download fallback but are **not a network firewall**. The server still needs the selected GPU driver's compatibility and all runtime libraries. The official runtime image includes NVIDIA's entrypoint; the service command starts its installed vLLM API module.

```bash
docker compose -f deploy/spark/inference.compose.yml config --quiet
docker compose -f deploy/spark/inference.compose.yml pull
docker compose -f deploy/spark/inference.compose.yml up -d
docker compose -f deploy/spark/inference.compose.yml ps
docker compose -f deploy/spark/inference.compose.yml logs --follow inference
```

This starts **only inference**, not the planning application. Stop at the first driver, memory, parser or model-loading error. Do not mark it ready just because a container is running. After startup:

```bash
curl --fail http://127.0.0.1:8000/health
curl --fail http://127.0.0.1:8000/v1/models
```

The served model alias should be exactly `tree-planner-local`. Also verify host bindings using `ss -ltn` and Docker's published-port information. Loopback prevents general LAN exposure; it is not isolation from other users on the same host. Shared-host access needs an organiser-approved account/authentication policy. This initial diagnostic deliberately does not manage API secrets.

### Prove an actual tool round trip

Install this repository's readiness wheel using [the root README](../README.md), or use `python -m pip install .` in an isolated environment for a source checkout. Then on Spark:

```bash
sheffield-readiness environment
sheffield-readiness inference --base-url http://127.0.0.1:8000/v1 --model tree-planner-local --disable-thinking
```

Through the laptop tunnel, use port **8001** instead. The diagnostic gets `/models`, asks the actual model to call the allowlisted `inspect_runtime` function, executes that harmless Python handler, sends its fresh nonce back, and requires the model to consume it correctly. It never invents a model answer, runs arbitrary tools or falls back to cloud inference. In laptop mode the inspected Python runtime is the **laptop**; do not mistake it for remote GPU identity.

A pass proves this endpoint's basic structured-tool/observation round trip. It does **not** prove tree-planning competence, domain-dispatcher safety, performance or full Spark deployment; receipts label those boundaries. The unit tests use an explicitly synthetic HTTP protocol fixture, not a local LLM. Failure should stay failure: inspect model/parser settings, context/token limit and service logs rather than replacing the model with scripted successful responses.

## 6. Integrate the local model into the product

This is the B01/B09/B10 implementation contract, **not existing application code**. [application.env.example](../deploy/spark/application.env.example) proposes configuration keys; no backend currently loads them.

- Host backend on Spark: `LLM_BASE_URL=http://127.0.0.1:8000/v1`, model alias `tree-planner-local`.
- Laptop backend: `LLM_BASE_URL=http://127.0.0.1:8001/v1` through SSH.
- If the backend later becomes a container, its `127.0.0.1` is **itself**. Put both services on an approved private Compose network and use the inference service DNS name, rather than copying the host URL blindly.
- The browser calls our API, not vLLM. The product backend owns accepted constraints, revisions, job records, permissions and tool execution. Inference credentials, if introduced later, stay server-side.

The agent turn:

1. Read the accepted task and immutable scenario reference. Present only useful validated summaries and tool schemas, not full meshes or raw restricted files.
2. Call the local chat-completions endpoint with schemas generated from the **same backend models** as our API. Start with implemented `inspect_site`/`evaluate_layout`; expose later tools only when real handlers exist.
3. Parse structured calls. Validate function name, exact arguments, identity, permissions and scenario eligibility outside the model. Reject unsupported operations and model-manufactured approvals.
4. Dispatch through the domain service. A long simulation returns a job handle; a non-model scheduler waits/polls/cancels and resumes with its actual terminal result. Do not hold inference generation open throughout computation or let model polling create duplicate jobs.
5. Feed back the observation with matching tool-call ID. Include result/delivery identity, units, currentness, constraints and assumptions. The model chooses the next investigation from observed evidence.
6. End on a supported answer, required clarification, cancellation, unavailable dependency, task deadline or repeated no-progress condition. Never convert a partial/failed tool into a successful recommendation.
7. Validate numerical claims against current results before presentation. Retain compact model/config/tool/run IDs and timings; do not log credentials, unrestricted source text or raw private prompts by default.

[CONTRACTS](CONTRACTS.md) remains authoritative for hypothetical versus accepted scenarios, immutable identity, stale results, errors and the operation allowlist. Do not treat the readiness package's `inspect_runtime` demonstration as a product tool. The product agent has no SSH, shell, Docker, arbitrary HTTP or filesystem access. Helios's development access is separate.

A useful first real agent trace is: inspect the site → notice the missing/available target information → request clarification or evaluate an accepted one-tree layout → explain the actual measured shade difference with its run ID. Later traces add relocation versus redesign and sensitivity; more agents are not required.

## 7. Deployment acceptance and recovery

**Prepared locally:** transport diagnostic/tests, installable diagnostic artifact, parsed SSH configuration and Compose configuration, source/architecture/model pins. See BUILD for actual executed evidence; do not infer a check passed because it is listed here.

**Still required on the assigned device:**

- Trusted key-authenticated SSH from an authorised laptop and working loopback tunnels.
- Driver/container/model load; real structured-tool call and consumed observation, cold-start and warm timings.
- Full application clean installation on Linux ARM64, frontend build/static serving, actual deterministic baseline → one-tree → UI path, persistent state and stale-job behaviour.
- Real model → **domain** dispatcher → numerical result → grounded answer, not only `inspect_runtime`.
- Co-resident inference/physics memory and latency, model-down and worker-failure behaviour; final B09/V08 and B12/V12 evidence.

Record exact code SHA, image digest, model revision, parser, quantisation, driver, environment and data hashes. Separate model device from physics device. A GPU inference run does not prove RT-core ray tracing. Local protocol tests, x86 CI and matching image manifests are not ARM64 execution evidence.

Recovery is deliberately small:

- Model failure: preserve the real manual simulator/UI path, label agent unavailable, fix or choose another validated local model. The mandatory local-agent gate remains incomplete; do not relabel manual output as agent output.
- Memory pressure: stop **this project's** inference service, inspect actual usage, reduce context/concurrency or select a smaller validated profile. Do not flush system caches, kill unrelated containers or monopolise all memory.
- Shutdown: `docker compose -f deploy/spark/inference.compose.yml down` stops/removes this project's container/network; bind-mounted models/cache remain. Never add `--volumes`, delete weights or alter shared assets without owner approval.
- Preserve the known-good source/model/profile and receipts. On borrowed-device handback, ask the owner how to remove project credentials/data. Remove only authorised project-owned material.

## Sources

All sources below were read on 11 November 2026. Live vendor pages may move; the selected model revision and registry digests are frozen in the profile.

- **S1:** [NVIDIA DGX Spark hardware](https://docs.nvidia.com/dgx/dgx-spark/hardware.html) — Arm, GPU, unified memory; not project compatibility proof.
- **S2:** [NVIDIA manual SSH connection guide](https://build.nvidia.com/spark/connect-to-your-spark/manual-ssh.md) — host/IP, client and tunnelling route.
- **S3:** [NVIDIA vLLM/Sync setup](https://build.nvidia.com/spark/vllm/intermediate.md) — supported device/memory choices and SSH-managed model endpoints; its current recipes differ from this pinned model-card route.
- **S4:** [Pinned NVIDIA Nemotron model card](https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16/blob/bf77c3174f68ad409e1c2aa60daeb46e32d1c606/README.md) — Spark container, parser, local API and thinking option.
- **S5:** [NVIDIA Nemotron Open Model License](https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-nemotron-open-model-license/) and [public model metadata](https://huggingface.co/api/models/nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16) — access/licence and revision; review terms before use/redistribution.
- **S6:** [NVIDIA vLLM container](https://catalog.ngc.nvidia.com/orgs/nvidia/containers/vllm?version=25.12.post1-py3), [base release notes](https://docs.nvidia.com/deeplearning/frameworks/vllm-release-notes/rel-25-12.html), and registry manifest/config metadata retained in the profile — distinguish base from post1.
- **S7:** [Hugging Face download CLI](https://huggingface.co/docs/huggingface_hub/guides/cli#hf-download) — pinned download and local directory.
- **S8:** [vLLM tool calling](https://docs.vllm.ai/en/latest/features/tool_calling/) — API/parser concepts, not assurance that every model/server combination works.

## Architecture relationship

The [integrated architecture design](ARCHITECTURE_DESIGN.md) explains how local model inference, the portable deterministic CPU reference, optional target-verified GPU kernels, site/revision/job authority and the four-screen UI fit together. The [adversarial architecture audit](ARCHITECTURE_AUDIT.md) records unresolved model/worker contention and hardware claims. **This DGX guide remains the operational authority for the pinned readiness recipe**; design synthesis has not changed image digests, parser, model revision, ports, permissions or acceptance. The reference 128 GB unified-memory configuration and proposed BF16 setup are not device-access, model-loading or co-residency proof.
