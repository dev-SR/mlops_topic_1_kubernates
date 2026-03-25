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
