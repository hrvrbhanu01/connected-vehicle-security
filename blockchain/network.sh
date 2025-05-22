#!/bin/bash

# Path to the original network script
FABRIC_NETWORK_SCRIPT="./fabric-samples/test-network/network.sh"

# Custom variables for your project
CHANNEL_NAME="mychannel"
CHAINCODE_NAME="recordEvent"
CHAINCODE_PATH="${PWD}/chaincode"  # Relative to fabric-samples/test-network
CHAINCODE_LANG="javascript"

if [ ! -f "${CHAINCODE_PATH}/recordEvent.js" ]; then
  echo "❌ Chaincode file not found at ${CHAINCODE_PATH}/recordEvent.js"
  exit 1
fi

# Wrapper functions
function deploy() {
    # Pre-start checks
    [ ! -f "${CHAINCODE_PATH}/recordEvent.js" ] && echo "❌ Chaincode missing!" && exit 1

    echo "➡️ Starting network with CA..."
    ${FABRIC_NETWORK_SCRIPT} up createChannel -c ${CHANNEL_NAME} -ca
    
    echo "➡️ Deploying ${CHAINCODE_NAME} chaincode..."
    ${FABRIC_NETWORK_SCRIPT} deployCC \
        -ccn ${CHAINCODE_NAME} \
        -ccp ${CHAINCODE_PATH} \
        -ccl ${CHAINCODE_LANG}

    # Post-deploy steps
    echo "✅ Network ready! Access APIs at http://localhost:4000"
}

function clean() {
    ${FABRIC_NETWORK_SCRIPT} down
    docker rm -f $(docker ps -aq)
    docker volume prune -f
}

# Main command switch
case $1 in
    "up") deploy ;;
    "down") clean ;;
    *) echo "Usage: ./network.sh [up|down]" ;;
esac