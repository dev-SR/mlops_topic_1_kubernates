# MLOP proj1

## Commands

1. Uv env setup and run

```bash
uv init
uv add -r requirements.txt  
uv run uvicorn main:app --proxy-headers --host 0.0.0.0 --port 8083 
```

## Docker Build

```bash
docker build . -t hello-joker:v1
docker images
docker run -it -p 8081:8083 hello-joker:v1 
# open http://localhost:8081 in browser
docker login
docker tag hello-joker:v1 <dockerhub-user-name>/hello-joker:v1 
docker push <docker_username>/hello-joker:v1
```

## Kubernetes

```bash
# kubectl create -f pod.yaml   
kubectl apply -f pod.yaml 
kubectl get pod  
kubectl describe pod joker      
kubectl logs joker 
kubectl delete pod joker
kubectl port-forward joker 8080:8083  


kubectl apply -f deployment.yaml   
kubectl get deployments
kubectl describe deployment joker-deployment    
kubectl logs joker-deployment-xxxxxxx-xxxxxx
kubectl delete deployment joker-deployment  
kubectl delete -f deployment.yaml

#Networking And Services
kubectl apply -f node-port-service.yaml 
kubectl get services
# In Docker Desktop, NodePorts are exposed via localhost, so just open:
http://localhost:30000

kubectl apply -f cluster-ip-service.yaml
kubectl get services
# tesing communication from other pod
kubectl run curl-test --rm -it --image=curlimages/curl:latest -- sh 
curl http://joker-nodeport-service:80
curl http://<CLUSTER-IP>:80

kubectl apply -f loadbalancer-service.yaml     
# We can see that the load balancer service has an external IP (localhost for dd) associated with it.
http://localhost:30000
```

Ohter objects:

```bash
kubectl create namespace funny
```

## helm chart

Let us now create a similar chart for our joker-application. We do that by running

```bash
helm create hello-joker
```

We can see multiple configurations in the **values.yaml** file. We *must* modify only those configurations for *deployments* and *services*.
This involves the replicaCount, image-related information, and specifying the service type and port.

```yaml
replicaCount: 3
image:
	repository: varunmallya/hello-joker
	pullPolicy: IfNotPresent
	tag: v1
..
service:
	type: NodePort
	port: 8080
```

Once the values are modified we can try installing this chart *in namespace funny* by using the Helm install command

```bash
helm install hello-joker --generate-name -n funny
helm upgrade hello-joker ./k8s -n funny
```

Your chart is located at `k8s/hello-joker`. Here’s the step-by-step workflow for Helm with a **custom chart**.

---

1. Install the chart in a namespace

Let’s say the namespace is `funny` and release name is `hello-joker`.

```bash
helm install hello-joker k8s/hello-joker -n funny --create-namespace
```

Explanation:

* `hello-joker` → release name (your deployment instance)
* `k8s/hello-joker` → path to your chart
* `-n funny` → namespace
* `--create-namespace` → creates `funny` if it doesn’t exist

---

```bash
kubectl get all -n funny
```

This shows all resources created by the Helm release in the `funny` namespace.


2. Update the chart after changing `values.yaml`

```yml
# This sets the container image more information can be found here: https://kubernetes.io/docs/concepts/containers/images/
image:
  repository: devhellosr/hello-joker
#   ....
service:
  # This sets the ports more information can be found here: https://kubernetes.io/docs/concepts/services-networking/service/#field-spec-ports
  port: 8083
```

If you changed anything in `k8s/hello-joker/values.yaml`:

```bash
helm upgrade hello-joker k8s/hello-joker -n funny
```

Explanation:

* `upgrade` → applies updates without uninstalling
<!-- * `-f values.yaml` → uses your modified values -->

Optional: check the status after upgrade:

```bash
helm status hello-joker -n funny
```

---

3. Delete the chart (uninstall release)

```bash
helm uninstall hello-joker -n funny
```

This removes all resources created by this Helm release in the `funny` namespace.


## ArgoCD


### Part 1 — Install ArgoCD into your local cluster

```bash
kubectl create namespace argocd

kubectl apply -n argocd -f \
  https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```

Wait for all pods to reach `Running` (~90 seconds):

```bash
kubectl get pods -n argocd --watch
```

You should see these pods all `Running`:
- `argocd-server-*`
- `argocd-repo-server-*`
- `argocd-application-controller-*`
- `argocd-dex-server-*`
- `argocd-redis-*`

---

### Part 2 — Install the ArgoCD CLI

```bash
# macOS
brew install argocd

# Windows
winget install argoproj.argocd

# Linux
curl -sSL -o argocd \
  https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
chmod +x argocd && sudo mv argocd /usr/local/bin/
```

---

### Part 3 — Expose the ArgoCD UI and log in

Port-forward the ArgoCD server — keep this terminal open:

```bash
kubectl port-forward svc/argocd-server -n argocd 8443:443
```

Get the auto-generated admin password:

```bash
kubectl get secret argocd-initial-admin-secret \
  -n argocd \
  -o jsonpath="{.data.password}" | base64 -d
```

#### CLI login

```bash
argocd login localhost:8443 \
  --username admin \
  --password <password-from-above> \
  --insecure
```

`--insecure` is required locally because ArgoCD uses a self-signed certificate.

#### UI login

Open https://localhost:8443 in your browser (accept the certificate warning), then log in with:
- Username: `admin`
- Password: the value from the secret above

---

### Part 4 — Connect your GitHub repo

#### CLI (recommended)

```bash
argocd repo add https://github.com/<your-org>/<your-repo>.git \
  --username <github-username> \
  --password <GH_TOKEN>
```

`GH_TOKEN` is a fine-grained Personal Access Token with **Contents: Read** permission on the repo.
This is the same token you set as `GH_PGH_TOKENAT` in GitHub Actions secrets.

Verify the connection succeeded:

```bash
argocd repo list
# CONNECTION STATE should show: Successful
```

#### UI

1. Go to **Settings → Repositories → Connect Repo**
2. Choose HTTPS
3. Fill in repo URL, username, and PAT
4. Click **Connect**

Or navigate directly: https://localhost:8443/settings/repos

---

### Part 5 — Create the ArgoCD Application

This is the core step — it tells ArgoCD which repo to watch and where to deploy.

> **Critical:** Never use `--helm-set image.tag=<value>` here.
> That bakes a hardcoded tag into the ArgoCD spec which permanently overrides
> `values.yaml` — meaning CI can update the file all it wants and ArgoCD
> will ignore it. Let `values.yaml` be the only source of truth for the tag.

#### CLI

```bash
argocd app create hello-joker \
  --repo https://github.com/<your-org>/<your-repo>.git \
  --path k8s/hello-joker \
  --dest-server https://kubernetes.default.svc \
  --dest-namespace funny \
  --sync-policy automated \
  --auto-prune \
  --self-heal
```

If you already have an app with wrong settings (e.g. an old `--helm-set`), recreate it with `--upsert`:

```bash
argocd app create hello-joker \
  --repo https://github.com/<your-org>/<your-repo>.git \
  --path k8s/hello-joker \
  --dest-server https://kubernetes.default.svc \
  --dest-namespace funny \
  --sync-policy automated \
  --auto-prune \
  --self-heal \
  --upsert       # updates in place if the app already exists
```

Verify ArgoCD is reading the image tag from `values.yaml` (not a hardcoded override):

```bash
argocd app manifests hello-joker | grep image:
# Must show the sha from values.yaml, e.g.: devhellosr/hello-joker:8e09c454
# If it shows :v1, the --helm-set override is still active — re-create with --upsert
```

#### UI

1. Click **New App**
2. Fill in:

| Field          | Value                            |
| -------------- | -------------------------------- |
| App name       | `hello-joker`                    |
| Project        | `default`                        |
| Sync policy    | `Automatic`                      |
| Prune          | ✓                                |
| Self-heal      | ✓                                |
| Repository URL | your GitHub repo URL             |
| Revision       | `main`                           |
| Path           | `k8s/hello-joker`                |
| Cluster        | `https://kubernetes.default.svc` |
| Namespace      | `funny`                          |

3. Leave **Helm parameters** empty — do not override `image.tag` here
4. Click **Create**

---

### Part 6 — Test the full CI/CD cycle end-to-end

### The code change

`main.py` returns which pod served the request using the Kubernetes Downward API:

```python
import os
from fastapi import FastAPI
import pyjokes

app = FastAPI()

# POD_NAME is injected by Kubernetes via the Downward API (see values.yaml).
# This lets you see which pod handled each request when running multiple replicas.
POD_NAME = os.getenv("POD_NAME", "unknown-pod")

@app.get("/")
async def root():
    random_joke = pyjokes.get_joke("en", "neutral")
    return {
        "pod": POD_NAME,
        "random_joke": random_joke
    }
```

`k8s/hello-joker/values.yaml` — add the `env` block (above `nodeSelector`):

```yaml
env:
  - name: POD_NAME
    valueFrom:
      fieldRef:
        fieldPath: metadata.name   # Kubernetes fills this with the pod's own name at runtime
```

`k8s/hello-joker/templates/deployment.yaml` — add the `env` block between `imagePullPolicy` and `ports`:

```yaml
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          {{- with .Values.env }}
          env:
            {{- toYaml . | nindent 12 }}
          {{- end }}
          ports:
```

Verify the template renders correctly before pushing:

```bash
helm template hello-joker k8s/hello-joker | grep -A5 "env:"
# Expected:
#   env:
#     - name: POD_NAME
#       valueFrom:
#         fieldRef:
#           fieldPath: metadata.name
```

#### Trigger the pipeline

```bash
git add .
git commit -m "feat: return pod name with joke response"
git push origin main
```

### Watch it flow

**Step 1 — GitHub Actions**

Go to your repo → **Actions** tab. Three jobs run in sequence:
- `test` → runs pytest
- `build` → builds and pushes `devhellosr/hello-joker:<sha>` to Docker Hub
- `update` → opens a PR like `helm/<sha>` that bumps the tag in `values.yaml`

**Step 2 — Merge the Helm PR**

GitHub will open a PR titled `ci: update image tag to <sha>`.
Merge it. This is the only manual step in the entire flow.

Note: merging this PR does **not** re-trigger GitHub Actions — only `k8s/` files changed,
which is excluded by `paths-ignore` in the workflow.

**Step 3 — ArgoCD syncs**

ArgoCD polls every 3 minutes. To trigger immediately:

```bash
argocd app sync hello-joker
```

Watch the rollout:

```bash
kubectl rollout status deployment/hello-joker -n funny
```

**Step 4 — Verify**

Confirm the pods are running the new image:

```bash
kubectl get pods -n funny \
  -o jsonpath="{range .items[*]}{.metadata.name}{'\t'}{.spec.containers[0].image}{'\n'}{end}"
# Should show devhellosr/hello-joker:<new-sha> on all three pods
```

Confirm `POD_NAME` is injected:

```bash
kubectl exec -n funny \
  $(kubectl get pod -n funny -l app.kubernetes.io/name=hello-joker \
    -o jsonpath='{.items[0].metadata.name}') \
  -- env | grep POD_NAME
# POD_NAME=hello-joker-xxxxxxxxx-xxxxx
```

---

## Part 7 — Hit the app and see load balancing

> Do not use `kubectl port-forward pod/<name>` — that tunnels directly to one pod
> and bypasses the load balancer entirely. You will always see the same pod.

### Option A — NodePort (simplest, no extra command needed)

Docker Desktop automatically exposes NodePorts on `localhost`.

```bash
# Find your NodePort
kubectl get svc -n funny
# Look for: 8083:3XXXX/TCP — the 3XXXX is the NodePort

# Hit it 9 times
for i in {1..9}; do curl -s http://localhost:<nodeport> | python3 -m json.tool; done
```

### Option B — Port-forward to the Service (not a pod)

```bash
kubectl port-forward svc/hello-joker -n funny 8081:8083
# Then open http://localhost:8081
```

Either option distributes across your 3 replicas:

```json
{ "pod": "hello-joker-7bdf9f6ff-f22wg", "random_joke": "Why do Java programmers wear glasses? Because they don't C#." }
{ "pod": "hello-joker-7bdf9f6ff-lmjtv", "random_joke": "A SQL query walks into a bar..." }
{ "pod": "hello-joker-7bdf9f6ff-v9jq6", "random_joke": "Don't compute and drive; the life you save may be your own." }
{ "pod": "hello-joker-7bdf9f6ff-f22wg", "random_joke": "..." }
```

| Method                      | Hits                  |
| --------------------------- | --------------------- |
| `port-forward pod/<name>`   | always the same pod ❌ |
| `port-forward svc/<name>`   | load balanced ✓       |
| `curl localhost:<nodeport>` | load balanced ✓       |

---

## Part 8 — Useful commands for day-to-day

```bash
# Check app health and sync status
argocd app get hello-joker

# List all apps
argocd app list

# Force an immediate sync (skips the 3-minute poll)
argocd app sync hello-joker

# Hard refresh — re-reads Git, bypasses ArgoCD's internal cache
argocd app sync hello-joker --force

# View what manifests ArgoCD would apply
argocd app manifests hello-joker

# Rollback to a previous version
argocd app history hello-joker          # list revision numbers
argocd app rollback hello-joker 2       # roll back to revision 2

# Watch sync complete in terminal
argocd app wait hello-joker --sync

# Delete app but keep the running pods
argocd app delete hello-joker

# Delete app AND all deployed Kubernetes resources
argocd app delete hello-joker --cascade
```

---

## Prometheus + Grafana Setup
> Observability for hello-joker on Docker Desktop Kubernetes

---

### How it works

```
hello-joker pods
  └── GET /metrics          ← exposed by prometheus-fastapi-instrumentator

ServiceMonitor (CRD)
  └── selects hello-joker Service by label
  └── tells Prometheus Operator: "scrape these pods every 15s"

Prometheus
  └── reads ServiceMonitor → scrapes /metrics → stores time-series data

Grafana
  └── queries Prometheus via PromQL → renders dashboards
```

The key piece is the **ServiceMonitor** — it's a Kubernetes custom resource installed
by `kube-prometheus-stack`. Instead of editing Prometheus config files manually,
you declare a ServiceMonitor and the Prometheus Operator picks it up automatically.

---

### Part 1 — Update the app

#### 1a. Add the instrumentator to requirements.txt

```
prometheus-fastapi-instrumentator
```

#### 1b. Update main.py

```python
import os
from fastapi import FastAPI
import pyjokes
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()

POD_NAME = os.getenv("POD_NAME", "unknown-pod")

# Exposes /metrics with standard HTTP metrics automatically.
# Metrics: http_requests_total, http_request_duration_seconds,
#          http_request_size_bytes, http_response_size_bytes
Instrumentator().instrument(app).expose(app)


@app.get("/")
async def root():
    random_joke = pyjokes.get_joke("en", "neutral")
    return {
        "pod": POD_NAME,
        "random_joke": random_joke,
    }
```

Test it locally before pushing:

```bash
uv run uvicorn main:app --host 0.0.0.0 --port 8083
curl http://localhost:8083/metrics
# You should see lines like:
# http_requests_total{handler="/",method="GET",status="2xx"} 1.0
```

---

### Part 2 — Add the ServiceMonitor Helm template

Create `k8s/hello-joker/templates/servicemonitor.yaml`:

```yaml
{{- if .Values.serviceMonitor.enabled }}
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: {{ include "hello-joker.fullname" . }}
  namespace: {{ .Values.serviceMonitor.namespace | default .Release.Namespace }}
  labels:
    {{- include "hello-joker.labels" . | nindent 4 }}
    # Must match kube-prometheus-stack's serviceMonitorSelector.
    # The default selector is: matchLabels: {release: prometheus}
    release: {{ .Values.serviceMonitor.prometheusRelease | default "prometheus" }}
spec:
  namespaceSelector:
    matchNames:
      - {{ .Release.Namespace }}
  selector:
    matchLabels:
      {{- include "hello-joker.selectorLabels" . | nindent 6 }}
  endpoints:
    - port: http
      path: /metrics
      interval: {{ .Values.serviceMonitor.interval | default "15s" }}
      scrapeTimeout: {{ .Values.serviceMonitor.scrapeTimeout | default "10s" }}
{{- end }}
```

---

### Part 3 — Add serviceMonitor to values.yaml

Add this block to the bottom of `k8s/hello-joker/values.yaml`:

```yaml
serviceMonitor:
  enabled: true
  prometheusRelease: prometheus   # must match your helm release name for kube-prometheus-stack
  namespace: ""                   # defaults to app namespace (funny)
  interval: 15s
  scrapeTimeout: 10s
```

Verify the template renders correctly:

```bash
helm template hello-joker k8s/hello-joker | grep -A20 "ServiceMonitor"
```

---

### Part 4 — Install kube-prometheus-stack

This single Helm chart installs Prometheus, Grafana, AlertManager, node exporters,
and the Prometheus Operator (which reads ServiceMonitor CRDs) all at once.

```bash
# Add the community charts repo
helm repo add prometheus-community \
  https://prometheus-community.github.io/helm-charts
helm repo update

# Install into the monitoring namespace
# Release name MUST be "prometheus" to match serviceMonitor.prometheusRelease in values.yaml
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --set grafana.adminPassword=admin123
```

Wait for all pods to be Running (~2-3 minutes):

```bash
kubectl get pods -n monitoring --watch
```

You'll see pods for: prometheus, grafana, alertmanager, kube-state-metrics, node-exporter, operator.

---

### Part 5 — Push and let ArgoCD sync

```bash
git add main.py \
  requirements.txt \
  k8s/hello-joker/templates/servicemonitor.yaml \
  k8s/hello-joker/values.yaml

git commit -m "feat: add prometheus metrics and servicemonitor"
git push origin main
```

GitHub Actions will:
1. Run tests
2. Build and push new image with the instrumentator installed
3. Open a Helm PR with the new image SHA

Merge the PR, then sync ArgoCD:

```bash
argocd app sync hello-joker
```

Verify the ServiceMonitor was created:

```bash
kubectl get servicemonitor -n funny
# NAME           AGE
# hello-joker    30s
```

Verify Prometheus discovered the targets:

```bash
# Port-forward to the Prometheus UI
kubectl port-forward svc/prometheus-kube-prometheus-prometheus -n monitoring 9090:9090
```

Open http://localhost:9090 → **Status → Targets**

You should see `serviceMonitor/funny/hello-joker` with state `UP` for each pod.
If it shows as `Unknown` or `Down`, check Part 7 Troubleshooting.

---

### Part 6 — Access Grafana and build a dashboard

#### Access

```bash
kubectl port-forward svc/prometheus-grafana -n monitoring 3000:80
```

Open http://localhost:3000
- Username: `admin`
- Password: `admin123` (or whatever you set in `--set grafana.adminPassword`)

#### Import the FastAPI dashboard

The fastest way to get a useful dashboard is to import a pre-built one:

1. In Grafana: click **Dashboards → Import**
2. Enter dashboard ID: **17175** (FastAPI Observability)
3. Click **Load**
4. Select your Prometheus data source
5. Click **Import**

You'll immediately see request rate, latency percentiles, and error rate per endpoint.

#### Key metrics to query manually (Explore → select Prometheus)

```promql
# Total requests per second across all pods
rate(http_requests_total{job="hello-joker"}[1m])

# Request rate broken down by pod (shows load balancing)
rate(http_requests_total{job="hello-joker"}[1m]) by (pod)

# 95th percentile latency
histogram_quantile(0.95,
  rate(http_request_duration_seconds_bucket{handler="/"}[5m])
)

# Error rate (non-2xx responses)
rate(http_requests_total{job="hello-joker", status!~"2.."}[1m])

# Requests per pod — confirms load is spread across your 3 replicas
sum by (pod) (
  increase(http_requests_total{job="hello-joker"}[5m])
)
```

#### Generate some traffic to see the graphs fill in

```bash
# Hit the NodePort 200 times quickly
for i in {1..200}; do curl -s http://localhost:<nodeport> > /dev/null; done
```

---
