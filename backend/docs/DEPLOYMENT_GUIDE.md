# Hyperledger Fabric Chaincode Deployment Guide

## Overview

This guide covers packaging and deploying the AgriTrack supply chain chaincode to a Hyperledger Fabric network, specifically the test-network included in the Fabric repository.

## Prerequisites

### System Requirements

- **OS**: Linux, macOS, or Windows with WSL2
- **Go**: v1.17 or later
- **Docker**: v20.10 or later
- **Docker Compose**: v2.0 or later
- **Hyperledger Fabric**: v2.2.x or later
- **Fabric Tools**: peer, orderer, configtxgen

### Fabric Installation

Refer to [FABRIC_INSTALLATION.md](FABRIC_INSTALLATION.md) for complete setup instructions.

### Network Setup

Ensure you have a Hyperledger Fabric network running:

```bash
cd $FABRIC_PATH/fabric-samples/test-network
./network.sh up createChannel -c agritrack-channel
```

## Step 1: Package the Chaincode

### Build the Chaincode Binary

```bash
cd /path/to/agritrack/fabric-chaincode/chaincode
go build -o chaincode-binary .
```

### Create Chaincode Package (v2 format)

```bash
cd /path/to/agritrack/fabric-chaincode

# Create package directory
mkdir -p packages

# Package for Org1
peer lifecycle chaincode package agritrack.tar.gz \
  --path /path/to/agritrack/fabric-chaincode/chaincode \
  --lang golang \
  --label agritrack_1.0

# Result: agritrack.tar.gz
```

## Step 2: Install Chaincode on Peers

### Install on Org1 Peers

```bash
# Set environment variables
export CORE_PEER_TLS_ENABLED=true
export CORE_PEER_LOCALMSPID=Org1MSP
export CORE_PEER_TLS_ROOTCERT_FILE=/path/to/fabric-samples/test-network/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=/path/to/fabric-samples/test-network/organizations/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp
export CORE_PEER_ADDRESS=localhost:7051

# Install
peer lifecycle chaincode install agritrack.tar.gz
```

### Install on Org2 Peers

```bash
# Update peer environment variables for Org2
export CORE_PEER_LOCALMSPID=Org2MSP
export CORE_PEER_TLS_ROOTCERT_FILE=/path/to/fabric-samples/test-network/organizations/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=/path/to/fabric-samples/test-network/organizations/peerOrganizations/org2.example.com/users/Admin@org2.example.com/msp
export CORE_PEER_ADDRESS=localhost:9051

# Install
peer lifecycle chaincode install agritrack.tar.gz
```

### Verify Installation

```bash
# Query installed chaincode
peer lifecycle chaincode queryinstalled
```

Expected output:

```
Installed chaincodes on peer:
Package ID: agritrack_1.0:xxx..., Label: agritrack_1.0
```

## Step 3: Approve Chaincode Definition

### Get Package ID

```bash
# After installation, extract the Package ID from queryinstalled output
export CC_PACKAGE_ID=agritrack_1.0:xxx...
```

### Approve for Org1

```bash
export CORE_PEER_LOCALMSPID=Org1MSP
export CORE_PEER_MSPCONFIGPATH=/path/to/fabric-samples/test-network/organizations/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp
export CORE_PEER_ADDRESS=localhost:7051

peer lifecycle chaincode approveformyorg \
  --channelID agritrack-channel \
  --name agritrack \
  --version 1.0 \
  --package-id $CC_PACKAGE_ID \
  --sequence 1 \
  --tls \
  --cafile /path/to/fabric-samples/test-network/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem
```

### Approve for Org2

```bash
export CORE_PEER_LOCALMSPID=Org2MSP
export CORE_PEER_MSPCONFIGPATH=/path/to/fabric-samples/test-network/organizations/peerOrganizations/org2.example.com/users/Admin@org2.example.com/msp
export CORE_PEER_ADDRESS=localhost:9051

peer lifecycle chaincode approveformyorg \
  --channelID agritrack-channel \
  --name agritrack \
  --version 1.0 \
  --package-id $CC_PACKAGE_ID \
  --sequence 1 \
  --tls \
  --cafile /path/to/fabric-samples/test-network/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem
```

### Verify Approval

```bash
peer lifecycle chaincode checkcommitreadiness \
  --channelID agritrack-channel \
  --name agritrack \
  --version 1.0 \
  --sequence 1 \
  --tls \
  --cafile /path/to/fabric-samples/test-network/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem
```

Expected output:

```
Chaincode definition for chaincode 'agritrack', version '1.0', sequence '1' on channel 'agritrack-channel' approval status by organization:
Org1MSP: true
Org2MSP: true
```

## Step 4: Commit Chaincode Definition

```bash
# Use Org1's environment
export CORE_PEER_LOCALMSPID=Org1MSP
export CORE_PEER_MSPCONFIGPATH=/path/to/fabric-samples/test-network/organizations/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp
export CORE_PEER_ADDRESS=localhost:7051

peer lifecycle chaincode commit \
  --channelID agritrack-channel \
  --name agritrack \
  --version 1.0 \
  --sequence 1 \
  --peerAddresses localhost:7051 \
  --tlsCertFiles /path/to/fabric-samples/test-network/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt \
  --peerAddresses localhost:9051 \
  --tlsCertFiles /path/to/fabric-samples/test-network/organizations/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt \
  --tls \
  --cafile /path/to/fabric-samples/test-network/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem
```

### Verify Commit

```bash
peer lifecycle chaincode querycommitted \
  --channelID agritrack-channel \
  --name agritrack \
  --tls \
  --cafile /path/to/fabric-samples/test-network/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem
```

Expected output:

```
Committed chaincode definitions:
Version: 1.0, Sequence: 1, Endorsement Plugin: escc, Validation Plugin: vscc
```

## Step 5: Test Chaincode Invocation

### Initialize Ledger

```bash
peer chaincode invoke \
  --channelID agritrack-channel \
  --name agritrack \
  -c '{"function":"InitLedger","Args":[]}' \
  --tls \
  --cafile /path/to/fabric-samples/test-network/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem
```

### Create a Product

```bash
peer chaincode invoke \
  --channelID agritrack-channel \
  --name agritrack \
  -c '{"function":"CreateProduct","Args":["POULTRY","Broiler Chicken","Live poultry for processing","Days","FARMER_ORG"]}' \
  --tls \
  --cafile /path/to/fabric-samples/test-network/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem
```

### Query Product

```bash
peer chaincode query \
  --channelID agritrack-channel \
  --name agritrack \
  -c '{"function":"QueryProduct","Args":["PROD_UUID"]}' \
  --tls \
  --cafile /path/to/fabric-samples/test-network/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem
```

## Step 6: Upgrade Chaincode (Future Versions)

### Build New Version

```bash
cd /path/to/agritrack/fabric-chaincode/chaincode
go build -o chaincode-binary .

# Package v1.1
peer lifecycle chaincode package agritrack_v1.1.tar.gz \
  --path /path/to/agritrack/fabric-chaincode/chaincode \
  --lang golang \
  --label agritrack_1.1
```

### Install and Approve (same steps as above, increment sequence)

```bash
# Install on both orgs
peer lifecycle chaincode install agritrack_v1.1.tar.gz

# Approve for both orgs (sequence=2)
peer lifecycle chaincode approveformyorg \
  --channelID agritrack-channel \
  --name agritrack \
  --version 1.1 \
  --package-id $NEW_CC_PACKAGE_ID \
  --sequence 2
```

### Commit New Version

```bash
peer lifecycle chaincode commit \
  --channelID agritrack-channel \
  --name agritrack \
  --version 1.1 \
  --sequence 2 \
  # [repeat peer addresses and cafile from Step 4]
```

## Troubleshooting

### Issue: "chaincode install failed"

**Solution**: Ensure peer is running and accessible:

```bash
docker ps | grep peer
peer channel fetch config  # Test connectivity
```

### Issue: "chaincode definition not approved"

**Solution**: Verify both orgs have approved with same parameters:

```bash
peer lifecycle chaincode checkcommitreadiness --channelID agritrack-channel --name agritrack --version 1.0 --sequence 1
```

### Issue: "invoke failed with: Error invoking chaincode"

**Solution**: Check chaincode logs:

```bash
docker logs $(docker ps --filter "label=chaincode=agritrack" -q)
```

### Issue: "endorsement policy mismatch"

**Solution**: Ensure all peers are on same channel and chaincode is committed:

```bash
peer lifecycle chaincode querycommitted --channelID agritrack-channel --name agritrack
```

## Production Deployment Checklist

- [ ] Chaincode code review completed
- [ ] Security audit performed (esp. authorization checks)
- [ ] Unit tests passing
- [ ] Integration tests with network successful
- [ ] Performance benchmarks acceptable
- [ ] Disaster recovery plan documented
- [ ] Monitoring and alerting configured
- [ ] Multi-org endorsement policy defined
- [ ] Channel access control verified
- [ ] Upgrade path documented for future versions

## Related Documentation

- [FABRIC_INSTALLATION.md](FABRIC_INSTALLATION.md) - Network setup
- [BLOCKCHAIN_QUICK_REFERENCE.md](../BLOCKCHAIN_QUICK_REFERENCE.md) - Quick commands
- [HYPERLEDGER_IMPLEMENTATION_COMPLETE.md](HYPERLEDGER_IMPLEMENTATION_COMPLETE.md) - Implementation details
