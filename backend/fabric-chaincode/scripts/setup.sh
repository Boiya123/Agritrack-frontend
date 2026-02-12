#!/bin/bash

# AgriTrack Hyperledger Fabric Chaincode - Setup Script
# This script automates the initial setup for deploying the chaincode

set -e

echo "=========================================="
echo "AgriTrack Chaincode Setup"
echo "=========================================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if ! command -v go &> /dev/null; then
    echo -e "${RED}✗ Go is not installed${NC}"
    echo "Install from: https://golang.org/dl/"
    exit 1
else
    echo -e "${GREEN}✓ Go installed: $(go version)${NC}"
fi

if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker is not installed${NC}"
    exit 1
else
    echo -e "${GREEN}✓ Docker installed${NC}"
fi

if ! command -v peer &> /dev/null; then
    echo -e "${YELLOW}⚠ Fabric CLI tools not found in PATH${NC}"
    echo "Download fabric-samples: https://github.com/hyperledger/fabric-samples"
fi

# Verify project structure
echo ""
echo -e "${YELLOW}Verifying project structure...${NC}"

if [ ! -f "go.mod" ]; then
    echo -e "${RED}✗ go.mod not found in $(pwd)${NC}"
    exit 1
else
    echo -e "${GREEN}✓ go.mod found${NC}"
fi

if [ ! -f "chaincode/supplychain.go" ]; then
    echo -e "${RED}✗ chaincode/supplychain.go not found${NC}"
    exit 1
else
    echo -e "${GREEN}✓ Chaincode source found${NC}"
fi

# Download Go dependencies
echo ""
echo -e "${YELLOW}Downloading Go dependencies...${NC}"
go mod download
echo -e "${GREEN}✓ Dependencies downloaded${NC}"

# Run unit tests
echo ""
echo -e "${YELLOW}Running unit tests...${NC}"
if go test ./test/... -v; then
    echo -e "${GREEN}✓ All tests passed${NC}"
else
    echo -e "${RED}✗ Tests failed${NC}"
    exit 1
fi

# Build chaincode
echo ""
echo -e "${YELLOW}Building chaincode...${NC}"
go build -v ./chaincode/
echo -e "${GREEN}✓ Build successful${NC}"

# Summary
echo ""
echo "=========================================="
echo -e "${GREEN}✓ Setup complete!${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Start Fabric test-network:"
echo "   cd /path/to/fabric-samples/test-network"
echo "   ./network.sh up createChannel -c mychannel -ca -s couchdb"
echo ""
echo "2. Deploy chaincode (see DEPLOYMENT.md):"
echo "   Follow the step-by-step guide in DEPLOYMENT.md"
echo ""
echo "3. Test with CLI commands:"
echo "   See CLI_COMMANDS.md for examples"
echo ""
echo "4. Read documentation:"
echo "   - README.md (quick start)"
echo "   - ARCHITECTURE.md (design patterns)"
echo "   - CLI_COMMANDS.md (invoke/query examples)"
echo ""
