# MLOP proj1

## Commands

1. Uv env setup and run

```bash
uv init
uv add -r requirements.txt  
uv run uvicorn main:app --proxy-headers --host 0.0.0.0 --port 8083 
```

2. Docker Build

```bash
docker build . -t hello-joker:v1
docker images
docker run -it -p 8081:8083 hello-joker:v1 
# open http://localhost:8081 in browser
docker login
docker tag hello-joker:v1 <dockerhub-user-name>/hello-joker:v1 
docker push <docker_username>/hello-joker:v1
```

3.  Kubernetes

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