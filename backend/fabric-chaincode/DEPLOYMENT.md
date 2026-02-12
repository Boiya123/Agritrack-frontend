# AgriTrack Hyperledger Fabric Chaincode Deployment Guide

## Prerequisites

- Docker and Docker Compose
- Go 1.20+
- Fabric CLI tools (`peer`, `configtxgen`, `orderer`)
- Hyperledger Fabric v2.5+ test-network
- Basic understanding of Fabric concepts

## Installation Steps

### 1. Set Up Hyperledger Fabric test-network

```bash
# Clone fabric-samples
git clone https://github.com/hyperledger/fabric-samples.git
cd fabric-samples/test-network

# Start the test network with CouchDB
./network.sh up createChannel -c mychannel -ca -s couchdb

# Verify network is running
docker ps | grep fabric
```

### 2. Copy Chaincode to fabric-samples

```bash
# From agritrack project root
cp -r fabric-chaincode/chaincode \
  /path/to/fabric-samples/chaincode/agritrack

# Ensure go.mod is present
cd /path/to/fabric-samples/chaincode/agritrack
ls -la go.mod  # Should exist
```

### 3. Package Chaincode

```bash
cd /path/to/fabric-samples/test-network

# Set environment variables
export PATH=${PWD}/../bin:$PATH
export FABRIC_CFG_PATH=${PWD}/../config
export CORE_PEER_TLS_ENABLED=true
export CORE_PEER_LOCALMSPID="Org1MSP"
export CORE_PEER_TLS_ROOTCERT_FILE=${PWD}/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=${PWD}/organizations/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp
export CORE_PEER_ADDRESS=localhost:7051

# Package the chaincode
peer lifecycle chaincode package agritrack.tar.gz \
  --path ../chaincode/agritrack \
  --lang go \
  --label agritrack_1.0
```

### 4. Install Chaincode on Peers

```bash
# Install on Org1
peer lifecycle chaincode install agritrack.tar.gz

# Install on Org2
export CORE_PEER_LOCALMSPID="Org2MSP"
export CORE_PEER_TLS_ROOTCERT_FILE=${PWD}/organizations/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=${PWD}/organizations/peerOrganizations/org2.example.com/users/Admin@org2.example.com/msp
export CORE_PEER_ADDRESS=localhost:9051

peer lifecycle chaincode install agritrack.tar.gz
```

### 5. Query Installed Chaincodes

```bash
# Get the package ID
peer lifecycle chaincode queryinstalled

# Set PACKAGE_ID (from output above)
export PACKAGE_ID=<copy_from_queryinstalled>
```

### 6. Approve Chaincode for Organizations

```bash
# Org2 approves
peer lifecycle chaincode approveformyorg \
  --channelID mychannel \
  --name agritrack \
  --version 1.0 \
  --package-id $PACKAGE_ID \
  --sequence 1 \
  --tls \
  --cafile ${PWD}/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem

# Switch to Org1 and approve
export CORE_PEER_LOCALMSPID="Org1MSP"
export CORE_PEER_TLS_ROOTCERT_FILE=${PWD}/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=${PWD}/organizations/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp
export CORE_PEER_ADDRESS=localhost:7051

peer lifecycle chaincode approveformyorg \
  --channelID mychannel \
  --name agritrack \
  --version 1.0 \
  --package-id $PACKAGE_ID \
  --sequence 1 \
  --tls \
  --cafile ${PWD}/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem
```

### 7. Check Approval Status

```bash
peer lifecycle chaincode checkcommitreadiness \
  --channelID mychannel \
  --name agritrack \
  --version 1.0 \
  --sequence 1 \
  --tls \
  --cafile ${PWD}/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem
```

### 8. Commit Chaincode to Channel

```bash
peer lifecycle chaincode commit \
  --channelID mychannel \
  --name agritrack \
  --version 1.0 \
  --sequence 1 \
  --tls \
  --cafile ${PWD}/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem \
  --peerAddresses localhost:7051 \
  --tlsRootCertFiles ${PWD}/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt \
  --peerAddresses localhost:9051 \
  --tlsRootCertFiles ${PWD}/organizations/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt
```

### 9. Verify Chaincode Deployment

```bash
peer lifecycle chaincode querycommitted \
  --channelID mychannel \
  --name agritrack \
  --tls \
  --cafile ${PWD}/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem
```

## Testing Chaincode

### Run Unit Tests Locally

```bash
cd /path/to/agritrack/fabric-chaincode

# Run all tests
go test ./... -v

# Run specific test
go test -run TestCreateBatch -v

# Run with coverage
go test ./... -cover
```

### Invoke Chaincode via CLI

See **CLI_COMMANDS.md** in the same directory for comprehensive invoke and query examples.

## Updating Chaincode

To update the chaincode after making changes:

```bash
# 1. Increment version and sequence
# 2. Package new version
peer lifecycle chaincode package agritrack.tar.gz \
  --path ../chaincode/agritrack \
  --lang go \
  --label agritrack_2.0

# 3. Install on all peers
peer lifecycle chaincode install agritrack.tar.gz

# 4. Approve with new sequence
peer lifecycle chaincode approveformyorg \
  --channelID mychannel \
  --name agritrack \
  --version 2.0 \
  --package-id <NEW_PACKAGE_ID> \
  --sequence 2 \
  --tls \
  --cafile ${PWD}/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem

# 5. Commit new version
peer lifecycle chaincode commit \
  --channelID mychannel \
  --name agritrack \
  --version 2.0 \
  --sequence 2 \
  --tls \
  --cafile ${PWD}/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem \
  --peerAddresses localhost:7051 \
  --tlsRootCertFiles ${PWD}/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt \
  --peerAddresses localhost:9051 \
  --tlsRootCertFiles ${PWD}/organizations/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt
```

## Troubleshooting

### Chaincode Installation Fails

```bash
# Check peer logs
docker logs peer0.org1.example.com

# Verify go.mod exists and dependencies
cd fabric-samples/chaincode/agritrack
go mod tidy
go build ./...
```

### Invoke Returns "Unknown Command"

- Ensure chaincode is committed to channel
- Check function name capitalization (must be public: `CreateProduct` not `createProduct`)
- Verify arguments are properly formatted JSON strings

### Transaction Timeout

- Increase CORE_CHAINCODE_STARTUPTIMEOUT in peer environment
- Check Docker resource limits

## Best Practices

1. **Use Structured Logging**: Leverage stub logging instead of fmt.Println
2. **Avoid External Calls**: No HTTP, no time.Now(), no randomness
3. **Validate All Inputs**: Check empty strings, negative numbers, missing references
4. **Use Events Sparingly**: Emit only critical state changes
5. **Version Your Chaincode**: Use semantic versioning (1.0, 2.0, etc.)
6. **Test Before Deploy**: Always run unit tests locally first
7. **Backup Ledger Data**: Export state before major upgrades
8. **Monitor Fabric Network**: Watch orderer and peer logs for anomalies

## Production Considerations

- Use production-grade Fabric network (not test-network)
- Configure HSM for key management
- Implement audit logging
- Set up monitoring/alerting
- Plan disaster recovery procedures
- Test upgrade/downgrade procedures
- Use external CA for certificate management
- Implement access control policies
