# Production Deployment Guide: Hyperledger Fabric on Kubernetes

## Overview

This guide covers deploying AgriTrack's Hyperledger Fabric blockchain to production on Kubernetes, ensuring high availability, scalability, and operational resilience.

## Architecture

### Production Topology

```
┌─────────────────────────────────────────────────────────────────┐
│                     Kubernetes Cluster                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Hyperledger Fabric Network                 │   │
│  │                                                          │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │   │
│  │  │   Orderer 1  │  │   Orderer 2  │  │   Orderer 3  │  │   │
│  │  │   (Raft)     │  │   (Raft)     │  │   (Raft)     │  │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  │   │
│  │         │                │                │             │   │
│  │  ┌──────────────┬──────────────┬──────────────┐        │   │
│  │  │              │              │              │        │   │
│  │  ▼              ▼              ▼              ▼        │   │
│  │ ┌─────────────────────────────────────────────────┐   │   │
│  │ │      Peers (Org1, Org2, Org3)                  │   │   │
│  │ │  - peer0.org1.example.com (endorser)          │   │   │
│  │ │  - peer0.org2.example.com (endorser)          │   │   │
│  │ │  - peer0.org3.example.com (endorser)          │   │   │
│  │ │  - CouchDB instances for state database        │   │   │
│  │ └─────────────────────────────────────────────────┘   │   │
│  │         │                │                │            │   │
│  │         └────────────────┬────────────────┘            │   │
│  │                          │                             │   │
│  │  ┌──────────────────────────────────────────────┐    │   │
│  │  │     Chaincode Containers (agritrack)        │    │   │
│  │  │  - Supply chain operations                  │    │   │
│  │  │  - Event recording                          │    │   │
│  │  └──────────────────────────────────────────────┘    │   │
│  │                                                      │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │          Monitoring & Observability                 │   │
│  │  ┌──────────────┐  ┌──────────────┐                │   │
│  │  │ Prometheus   │  │  Grafana     │                │   │
│  │  └──────────────┘  └──────────────┘                │   │
│  │  ┌──────────────┐  ┌──────────────┐                │   │
│  │  │  ELK Stack   │  │  Jaeger      │                │   │
│  │  └──────────────┘  └──────────────┘                │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         Storage (Persistent Volumes)                 │   │
│  │  ┌──────────────┐  ┌──────────────┐                │   │
│  │  │  Ledger PV   │  │  CouchDB PV  │                │   │
│  │  └──────────────┘  └──────────────┘                │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

## Prerequisites

### Infrastructure

- **Kubernetes Cluster**: v1.24+ with 10+ nodes
- **Storage**: Persistent Volume provider (NFS, EBS, GCP persistent disks)
- **Container Registry**: Docker Hub, ECR, GCR, or private registry
- **Load Balancer**: Kubernetes ingress or external load balancer

### Tools

```bash
# Install required tools
brew install kubectl helm docker

# Verify versions
kubectl version --client
helm version
docker version
```

### Access & Credentials

- Kubeconfig for production cluster
- Container registry credentials
- TLS certificates for orderers/peers
- Fabric CA credentials

## Phase 1: Network Setup

### 1.1 Create Fabric Namespace

```yaml
# fabric-namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: fabric-production
  labels:
    name: fabric-production
```

Apply:

```bash
kubectl apply -f fabric-namespace.yaml
```

### 1.2 Generate Crypto Materials

Use `cryptogen` and `configtxgen`:

```bash
# Generate org certificates and keys
cryptogen generate --config=cryptogen.yaml --output=crypto-config

# Generate genesis block and channel configurations
configtxgen -profile OrdererGenesis -channelID orderer-system-channel \
  -outputBlock genesis.block

configtxgen -profile TwoOrgsChannel -outputCreateChannelTx agritrack-channel.tx \
  -channelID agritrack-channel
```

### 1.3 Create Secrets from Crypto Materials

```bash
# Create secret for orderer TLS certs
kubectl create secret tls orderer-tls \
  --cert=crypto-config/ordererOrganizations/orderer/orderers/orderer0/tls/server.crt \
  --key=crypto-config/ordererOrganizations/orderer/orderers/orderer0/tls/server.key \
  -n fabric-production

# Create secrets for each peer
kubectl create secret tls org1-peer-tls \
  --cert=crypto-config/peerOrganizations/org1.example.com/peers/peer0/tls/server.crt \
  --key=crypto-config/peerOrganizations/org1.example.com/peers/peer0/tls/server.key \
  -n fabric-production

# Store channel configuration
kubectl create configmap channel-config \
  --from-file=agritrack-channel.tx=agritrack-channel.tx \
  -n fabric-production
```

## Phase 2: Orderer Deployment (RAFT)

### 2.1 Orderer StatefulSet

```yaml
# orderer-statefulset.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: orderer
  namespace: fabric-production
spec:
  serviceName: orderer
  replicas: 3
  selector:
    matchLabels:
      app: orderer
  template:
    metadata:
      labels:
        app: orderer
    spec:
      containers:
        - name: orderer
          image: hyperledger/fabric-orderer:2.2.0
          ports:
            - containerPort: 7050
              name: orderer
          env:
            - name: FABRIC_LOGGING_SPEC
              value: "orderer=debug"
            - name: ORDERER_GENERAL_LISTENADDRESS
              value: "0.0.0.0"
            - name: ORDERER_GENERAL_LISTENPORT
              value: "7050"
            - name: ORDERER_GENERAL_GENESISMETHOD
              value: "file"
            - name: ORDERER_GENERAL_GENESISFILE
              value: /var/hyperledger/orderer/genesis.block
            - name: ORDERER_GENERAL_BOOTSTRAPMETHOD
              value: "none"
            - name: ORDERER_CHANNELPARTICIPATION_ENABLED
              value: "true"
          volumeMounts:
            - name: genesis-volume
              mountPath: /var/hyperledger/orderer
            - name: orderer-data
              mountPath: /var/hyperledger/production
            - name: orderer-tls
              mountPath: /var/hyperledger/orderer/tls
      volumes:
        - name: genesis-volume
          configMap:
            name: orderer-genesis
        - name: orderer-tls
          secret:
            secretName: orderer-tls
  volumeClaimTemplates:
    - metadata:
        name: orderer-data
      spec:
        accessModes: ["ReadWriteOnce"]
        resources:
          requests:
            storage: 20Gi
---
apiVersion: v1
kind: Service
metadata:
  name: orderer
  namespace: fabric-production
spec:
  clusterIP: None
  selector:
    app: orderer
  ports:
    - port: 7050
      name: orderer
```

### 2.2 Deploy Orderers

```bash
kubectl apply -f orderer-statefulset.yaml
kubectl rollout status statefulset/orderer -n fabric-production
```

## Phase 3: Peer Deployment

### 3.1 Peer StatefulSet with CouchDB

```yaml
# peer-statefulset.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: peer0-org1
  namespace: fabric-production
spec:
  serviceName: peer0-org1
  replicas: 1
  selector:
    matchLabels:
      app: peer0-org1
  template:
    metadata:
      labels:
        app: peer0-org1
    spec:
      containers:
        # CouchDB container
        - name: couchdb
          image: couchdb:3.1.1
          ports:
            - containerPort: 5984
          env:
            - name: COUCHDB_USER
              valueFrom:
                secretKeyRef:
                  name: couchdb-credentials
                  key: username
            - name: COUCHDB_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: couchdb-credentials
                  key: password
          volumeMounts:
            - name: couchdb-data
              mountPath: /opt/couchdb/data

        # Peer container
        - name: peer
          image: hyperledger/fabric-peer:2.2.0
          ports:
            - containerPort: 7051
              name: peer
            - containerPort: 7052
              name: chaincode
          env:
            - name: FABRIC_LOGGING_SPEC
              value: "peer=debug"
            - name: CORE_PEER_ID
              value: peer0.org1.example.com
            - name: CORE_PEER_ADDRESS
              value: peer0-org1:7051
            - name: CORE_PEER_LISTENADDRESS
              value: 0.0.0.0:7051
            - name: CORE_PEER_CHAINCODEADDRESS
              value: 0.0.0.0:7052
            - name: CORE_PEER_CHAINCODELISTENADDRESS
              value: 0.0.0.0:7052
            - name: CORE_PEER_GOSSIP_EXTERNALENDPOINT
              value: peer0-org1:7051
            - name: CORE_PEER_GOSSIP_BOOTSTRAP
              value: peer0-org1:7051
            - name: CORE_PEER_LOCALMSPID
              value: Org1MSP
            - name: CORE_VM_ENDPOINT
              value: unix:///host/var/run/docker.sock
            - name: CORE_CHAINCODE_EXECUTETIMEOUT
              value: "300s"
            - name: CORE_LEDGER_STATE_STATEDATABASE
              value: "CouchDB"
            - name: CORE_LEDGER_STATE_COUCHDBCONFIG_COUCHDBADDRESS
              value: "localhost:5984"
            - name: CORE_LEDGER_STATE_COUCHDBCONFIG_USERNAME
              valueFrom:
                secretKeyRef:
                  name: couchdb-credentials
                  key: username
            - name: CORE_LEDGER_STATE_COUCHDBCONFIG_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: couchdb-credentials
                  key: password
          volumeMounts:
            - name: peer-msp
              mountPath: /etc/hyperledger/fabric/msp
            - name: peer-tls
              mountPath: /etc/hyperledger/fabric/tls
            - name: peer-data
              mountPath: /var/hyperledger/production
            - name: docker-sock
              mountPath: /host/var/run/docker.sock

      volumes:
        - name: peer-msp
          secret:
            secretName: org1-peer-msp
        - name: peer-tls
          secret:
            secretName: org1-peer-tls
        - name: docker-sock
          hostPath:
            path: /var/run/docker.sock

  volumeClaimTemplates:
    - metadata:
        name: peer-data
      spec:
        accessModes: ["ReadWriteOnce"]
        resources:
          requests:
            storage: 50Gi
    - metadata:
        name: couchdb-data
      spec:
        accessModes: ["ReadWriteOnce"]
        resources:
          requests:
            storage: 50Gi
---
apiVersion: v1
kind: Service
metadata:
  name: peer0-org1
  namespace: fabric-production
spec:
  clusterIP: None
  selector:
    app: peer0-org1
  ports:
    - port: 7051
      name: peer
    - port: 7052
      name: chaincode
```

### 3.2 Deploy Peers

```bash
kubectl apply -f peer-statefulset.yaml
kubectl rollout status statefulset/peer0-org1 -n fabric-production
```

## Phase 4: Chaincode Deployment

### 4.1 Build and Push Chaincode Image

```bash
# Build chaincode package
cd fabric-chaincode/chaincode
go build -o agritrack-cc .

# Create Docker image
docker build -t agritrack-chaincode:1.0 .
docker tag agritrack-chaincode:1.0 registry.example.com/agritrack-chaincode:1.0
docker push registry.example.com/agritrack-chaincode:1.0
```

### 4.2 Install and Commit Chaincode

```bash
# Use kubectl exec to run peer commands inside cluster
kubectl exec -it peer0-org1-0 -n fabric-production -- \
  peer lifecycle chaincode install agritrack.tar.gz

# Approve chaincode definition
kubectl exec -it peer0-org1-0 -n fabric-production -- \
  peer lifecycle chaincode approveformyorg \
    --channelID agritrack-channel \
    --name agritrack \
    --version 1.0 \
    --package-id agritrack_1.0:xxx
```

## Phase 5: Monitoring & Observability

### 5.1 Prometheus Scrape Config

```yaml
# prometheus-config.yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: "fabric-orderer"
    static_configs:
      - targets: ["orderer-0.orderer.fabric-production.svc.cluster.local:7050"]

  - job_name: "fabric-peer"
    static_configs:
      - targets:
          ["peer0-org1-0.peer0-org1.fabric-production.svc.cluster.local:7051"]

  - job_name: "couchdb"
    static_configs:
      - targets:
          ["peer0-org1-0.peer0-org1.fabric-production.svc.cluster.local:5984"]
```

### 5.2 Deploy Monitoring Stack

```bash
# Add Prometheus Helm repo
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Install Prometheus
helm install prometheus prometheus-community/prometheus \
  -n monitoring --create-namespace \
  -f prometheus-config.yaml

# Install Grafana
helm install grafana grafana/grafana \
  -n monitoring --create-namespace \
  --set adminPassword=admin
```

### 5.3 Alerting Rules

```yaml
# alerting-rules.yaml
groups:
  - name: fabric.rules
    interval: 30s
    rules:
      - alert: OrdererDown
        expr: up{job="fabric-orderer"} == 0
        for: 2m
        annotations:
          summary: "Orderer is down"

      - alert: PeerDown
        expr: up{job="fabric-peer"} == 0
        for: 2m
        annotations:
          summary: "Peer is down"

      - alert: HighPeerCPU
        expr: rate(container_cpu_usage_seconds_total{pod=~"peer.*"}[5m]) > 0.8
        for: 5m
        annotations:
          summary: "High peer CPU usage"

      - alert: CouchDBDown
        expr: up{job="couchdb"} == 0
        for: 2m
        annotations:
          summary: "CouchDB is down"
```

## Phase 6: High Availability & Disaster Recovery

### 6.1 Backup Strategy

```bash
#!/bin/bash
# backup-fabric.sh - Backup ledger and CouchDB data

BACKUP_DIR="/backups/fabric-$(date +%Y%m%d-%H%M%S)"
mkdir -p $BACKUP_DIR

# Backup ledger data
for pod in $(kubectl get pods -l app=peer -o name -n fabric-production); do
  kubectl exec $pod -n fabric-production -- \
    tar czf /tmp/ledger-backup.tar.gz /var/hyperledger/production
  kubectl cp fabric-production/$pod:/tmp/ledger-backup.tar.gz \
    $BACKUP_DIR/$(echo $pod | cut -d'/' -f2)-ledger.tar.gz
done

# Backup CouchDB
for pod in $(kubectl get pods -l app=peer -o name -n fabric-production); do
  kubectl exec $pod -c couchdb -n fabric-production -- \
    curl -X GET http://admin:password@localhost:5984/_all_dbs \
    > $BACKUP_DIR/$(echo $pod | cut -d'/' -f2)-couchdb-dbs.json
done

echo "Backup completed to $BACKUP_DIR"
```

### 6.2 Disaster Recovery

```bash
#!/bin/bash
# restore-fabric.sh - Restore from backup

BACKUP_DIR=$1

# Scale down peers
kubectl scale statefulset peer0-org1 --replicas=0 -n fabric-production

# Restore ledger data
for backup_file in $BACKUP_DIR/*-ledger.tar.gz; do
  pod_name=$(basename $backup_file | cut -d'-' -f1)
  kubectl exec peer0-org1-0 -n fabric-production -- \
    tar xzf /tmp/ledger-backup.tar.gz -C /var/hyperledger/production
done

# Scale up peers
kubectl scale statefulset peer0-org1 --replicas=1 -n fabric-production

echo "Recovery completed"
```

## Phase 7: Security Hardening

### 7.1 RBAC Configuration

```yaml
# fabric-rbac.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: fabric-operator
  namespace: fabric-production
rules:
  - apiGroups: [""]
    resources: ["pods", "services", "configmaps", "secrets"]
    verbs: ["get", "list", "watch"]
  - apiGroups: ["apps"]
    resources: ["statefulsets"]
    verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: fabric-operator-binding
  namespace: fabric-production
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: fabric-operator
subjects:
  - kind: ServiceAccount
    name: fabric-operator
    namespace: fabric-production
```

### 7.2 Network Policies

```yaml
# network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: fabric-network-policy
  namespace: fabric-production
spec:
  podSelector:
    matchLabels:
      app: peer
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              name: fabric-production
      ports:
        - protocol: TCP
          port: 7051
        - protocol: TCP
          port: 7052
  egress:
    - to:
        - namespaceSelector:
            matchLabels:
              name: fabric-production
      ports:
        - protocol: TCP
          port: 7050 # Orderer
```

## Phase 8: Deployment Automation (GitOps)

### 8.1 ArgoCD Setup

```bash
# Install ArgoCD
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```

### 8.2 ArgoCD Application

```yaml
# fabric-argocd-app.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: fabric-agritrack
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/agritrack/fabric-k8s
    targetRevision: main
    path: k8s/
  destination:
    server: https://kubernetes.default.svc
    namespace: fabric-production
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
```

## Production Checklist

### Pre-Deployment

- [ ] Kubernetes cluster configured with proper resource limits
- [ ] Persistent volumes provisioned and tested
- [ ] TLS certificates generated and validated
- [ ] Container registry credentials configured
- [ ] Load balancer/ingress configured
- [ ] Network policies defined
- [ ] RBAC roles and bindings configured

### Deployment

- [ ] Crypto materials generated and stored securely
- [ ] Orderers deployed and healthy (3+ replicas)
- [ ] Peers deployed and healthy (2+ per org)
- [ ] Channel created and peer joined
- [ ] Chaincode installed and committed
- [ ] Monitoring deployed and alerts configured

### Post-Deployment

- [ ] All components passing health checks
- [ ] Monitoring dashboards created
- [ ] Backup/restore procedures tested
- [ ] Disaster recovery plan documented
- [ ] Load testing completed successfully
- [ ] Security audit completed
- [ ] Documentation updated
- [ ] Team trained on operations

## Performance Optimization

### Tuning Parameters

```yaml
# Performance tuning
CORE_CHAINCODE_EXECUTETIMEOUT: "300s"
CORE_LEDGER_BLOCKSTORE_RBFTLEDGER_INDICES_CONFIG: "BLOCK_NUM,BLOCK_HASH"
CORE_LEDGER_HISTORY_ENABLEHISTORY: "true"
CORE_VM_DOCKER_HOSTCONFIG_MEMORY: "1073741824" # 1GB per chaincode
CORE_METRICS_ENABLED: "true"
```

### Resource Limits

```yaml
resources:
  requests:
    memory: "2Gi"
    cpu: "1000m"
  limits:
    memory: "4Gi"
    cpu: "2000m"
```

## Troubleshooting

### Pod Stuck in Pending

```bash
kubectl describe pod peer0-org1-0 -n fabric-production
# Check PVC status and available storage
kubectl get pvc -n fabric-production
```

### Orderer Consensus Issues

```bash
# Check orderer logs
kubectl logs orderer-0 -n fabric-production | grep raft
# Verify all orderers are running
kubectl get statefulset orderer -n fabric-production
```

## Related Documentation

- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- [BLOCKCHAIN_FASTAPI_INTEGRATION.md](BLOCKCHAIN_FASTAPI_INTEGRATION.md)
- [HYPERLEDGER_INTEGRATION.md](HYPERLEDGER_INTEGRATION.md)
- Kubernetes documentation: https://kubernetes.io/docs/
- Hyperledger Fabric documentation: https://hyperledger-fabric.readthedocs.io/
