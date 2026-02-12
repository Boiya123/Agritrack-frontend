# AgriTrack Chaincode Environment Variables Reference

This document lists all environment variables needed for deploying and testing the AgriTrack chaincode.

## Fabric Network Configuration

### Core Peer Settings (for peer CLI)

```bash
# Enable TLS for secure communication
export CORE_PEER_TLS_ENABLED=true

# Orderer address for transaction submission
export CORE_ORDERER_ADDRESS=orderer.example.com:7050

# Peer address for queries and invokes
export CORE_PEER_ADDRESS=localhost:7051
```

## Organization-Specific Configuration

### Org1 (FarmOrg - Farmers)

```bash
export CORE_PEER_LOCALMSPID="Org1MSP"
export CORE_PEER_TLS_ROOTCERT_FILE=${PWD}/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=${PWD}/organizations/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp
export CORE_PEER_ADDRESS=localhost:7051
```

### Org2 (RegulatorOrg - Regulators)

```bash
export CORE_PEER_LOCALMSPID="Org2MSP"
export CORE_PEER_TLS_ROOTCERT_FILE=${PWD}/organizations/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=${PWD}/organizations/peerOrganizations/org2.example.com/users/Admin@org2.example.com/msp
export CORE_PEER_ADDRESS=localhost:9051
```

## Fabric Configuration Paths

```bash
# Path to Fabric binaries (peer, configtxgen, etc.)
export PATH=${PWD}/../bin:$PATH

# Fabric configuration directory
export FABRIC_CFG_PATH=${PWD}/../config
```

## TLS Certificates

### Orderer CA Certificate

```bash
export ORDERER_CA=${PWD}/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem
```

### Org1 Peer TLS

```bash
export ORG1_PEER_TLS=${PWD}/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt
```

### Org2 Peer TLS

```bash
export ORG2_PEER_TLS=${PWD}/organizations/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt
```

## Channel Configuration

```bash
# Channel name (default for agritrack)
export CHANNEL_ID=mychannel

# Chaincode name
export CHAINCODE_NAME=agritrack

# Chaincode version
export CHAINCODE_VERSION=1.0

# Chaincode language
export CHAINCODE_LANGUAGE=go

# Package ID (generated after installing)
export PACKAGE_ID=agritrack_1.0:abcdef123456...
```

## Go Build Configuration

### Local Development

```bash
# Go version requirement
export GO_VERSION=1.20

# Module name
export GO_MODULE_NAME=github.com/agritrack/fabric-chaincode

# Build flags (optional)
export GOFLAGS=-mod=readonly
```

### Chaincode Build

```bash
# Chaincode package ID format
export CCPKG_ID=<label>:<hash>

# Example:
# export CCPKG_ID=agritrack_1.0:8a8e1f2d5e7c9b1a3f6d4e9c1f7a2b5d8e9f1c3a
```

## Network Configuration

### Test Network

```bash
# Test network directory (from fabric-samples)
export FABRIC_SAMPLES_DIR=/path/to/fabric-samples

# Chaincode path
export CHAINCODE_PATH=${FABRIC_SAMPLES_DIR}/chaincode/agritrack
```

### Production Network

```bash
# Organization MSP ID
export MSPID=Org1MSP

# User certificate path
export USER_CERT=/path/to/user@org.example.com/msp/signcerts/User@org.example.com-cert.pem

# User private key
export USER_KEY=/path/to/user@org.example.com/msp/keystore/priv_sk
```

## Docker Configuration

```bash
# Docker image for chaincode execution
export DOCKER_IMAGE_NAME=hyperledger/fabric-ccenv:2.5.0

# Container registry (if using custom images)
export CONTAINER_REGISTRY=docker.io
```

## Logging Configuration

```bash
# Peer logging level (DEBUG, INFO, WARN, ERROR)
export CORE_LOGGING_LEVEL=INFO

# Chaincode logging
export FABRIC_LOGGING_SPEC=info

# Enable verbose output for debugging
export CORE_LOGGING_DEBUG=true
```

## Timeout Configuration

```bash
# Chaincode startup timeout (seconds)
export CORE_CHAINCODE_STARTUPTIMEOUT=300

# Chaincode execution timeout (seconds)
export CORE_CHAINCODE_EXECUTETIMEOUT=30

# Transaction proposal timeout (seconds)
export CORE_CHAINCODE_DEPLOYTIMEOUT=120
```

## Complete Setup Script

```bash
#!/bin/bash

# Save this as scripts/env-setup.sh and source it before operations

FABRIC_SAMPLES_DIR="/path/to/fabric-samples"
NETWORK_DIR="${FABRIC_SAMPLES_DIR}/test-network"

cd "${NETWORK_DIR}"

# Path setup
export PATH=${PWD}/../bin:$PATH
export FABRIC_CFG_PATH=${PWD}/../config

# Org1 (Farmer)
export CORE_PEER_LOCALMSPID="Org1MSP"
export CORE_PEER_TLS_ENABLED=true
export CORE_PEER_TLS_ROOTCERT_FILE=${PWD}/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=${PWD}/organizations/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp
export CORE_PEER_ADDRESS=localhost:7051
export ORDERER_CA=${PWD}/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem

# Channel & Chaincode
export CHANNEL_ID=mychannel
export CHAINCODE_NAME=agritrack
export CHAINCODE_VERSION=1.0

echo "Environment configured for Org1 (Farmers)"
echo "CORE_PEER_ADDRESS: ${CORE_PEER_ADDRESS}"
echo "CORE_PEER_LOCALMSPID: ${CORE_PEER_LOCALMSPID}"
```

## Quick Reference Commands

### List Current Environment

```bash
# Show all exported variables
env | grep -i "CORE_PEER\|FABRIC\|ORDERER\|CHANNEL\|CHAINCODE"
```

### Switch Organizations

```bash
# Switch to Org2 (Regulator)
source scripts/org2-env.sh

# Switch back to Org1 (Farmer)
source scripts/org1-env.sh
```

### Verify Configuration

```bash
# Test peer connection
peer channel list

# Check peer identity
peer org.hyperledger.fabric.core.chaincode.ShimHandler -peer
```

## Production Considerations

### Key Management

```bash
# Path to HSM for key storage (if using hardware wallet)
export PKCS11_MODULE_PATH=/usr/lib64/softhsm/libsofthsm2.so
export PKCS11_PIN=1234
export PKCS11_LABEL=fabric
```

### Network Policies

```bash
# Enable mutual TLS
export CORE_PEER_TLS_CLIENTAUTHREQUIRED=true

# Certificate rotation
export CERT_ROTATION_INTERVAL=86400  # 24 hours
```

### Audit & Logging

```bash
# Enable audit logging
export FABRIC_LOGGING_SPEC=info:org.hyperledger.fabric=debug

# Log output file
export CORE_CHAINCODE_LOGGING_SHIM=debug

# Syslog configuration
export FABRIC_LOGGING_LEVEL=info
```

## Troubleshooting

### Reset to Clean State

```bash
# Unset all Fabric variables
unset CORE_PEER_TLS_ENABLED
unset CORE_PEER_LOCALMSPID
unset CORE_PEER_TLS_ROOTCERT_FILE
unset CORE_PEER_MSPCONFIGPATH
unset CORE_PEER_ADDRESS
unset ORDERER_CA
unset CHANNEL_ID
unset CHAINCODE_NAME
unset CHAINCODE_VERSION
```

### Common Issues

**Issue**: "endorsement failure during invoke"

- **Check**: `CORE_PEER_ADDRESS` points to correct peer
- **Check**: `CORE_PEER_LOCALMSPID` matches org
- **Check**: Peer is running (docker ps)

**Issue**: "channel not found"

- **Check**: Channel name in `CHANNEL_ID` is correct
- **Check**: Chaincode is committed to channel
- **Command**: `peer lifecycle chaincode querycommitted -C ${CHANNEL_ID}`

**Issue**: "permission denied"

- **Check**: User certificate in `CORE_PEER_MSPCONFIGPATH`
- **Check**: Private key accessible
- **Command**: `ls -la ${CORE_PEER_MSPCONFIGPATH}/msp/`
