const express = require("express");
const { Gateway, Wallets } = require("fabric-network");
const path = require("path");
const fs = require("fs");
const cors = require("cors");
const bodyParser = require("body-parser");

const app = express();
const PORT = 4000;

app.use(cors());
app.use(bodyParser.json());

async function getContract() {
  const ccpPath = path.resolve(
    __dirname,
    "..",
    "blockchain",
    "fabric-samples",
    "test-network",
    "organizations",
    "peerOrganizations",
    "org1.example.com",
    "connection-org1.json"
  );

  // Check if connection profile exists
  if (!fs.existsSync(ccpPath)) {
    throw new Error(`Connection profile not found at: ${ccpPath}`);
  }

  const ccp = JSON.parse(fs.readFileSync(ccpPath, "utf8"));

  const walletPath = path.join(process.cwd(), "wallet");
  const wallet = await Wallets.newFileSystemWallet(walletPath);

  // Check if user identity exists
  const userExists = await wallet.get("user4");
  if (!userExists) {
    throw new Error(
      "user4 identity not found in wallet. Please enroll the user first."
    );
  }

  const gateway = new Gateway();

  try {
    await gateway.connect(ccp, {
      wallet,
      identity: "user4",
      discovery: { enabled: true, asLocalhost: true },
    });

    const network = await gateway.getNetwork("mychannel");
    const contract = network.getContract("recordEvent");
    return { contract, gateway };
  } catch (error) {
    gateway.disconnect();
    throw error;
  }
}

app.post("/api/recordEvent", async (req, res) => {
  let gateway;
  try {
    console.log("Received request:", req.body);

    const { contract, gateway: gw } = await getContract();
    gateway = gw;

    // Validate input
    if (!req.body || Object.keys(req.body).length === 0) {
      return res.status(400).json({ error: "Request body cannot be empty" });
    }

    console.log("Submitting transaction...");
    const result = await contract.submitTransaction(
      "recordEvent",
      JSON.stringify(req.body)
    );

    console.log("Raw transaction result:", result.toString());

    // Handle the result
    const resultString = result.toString().trim();
    let responseData;

    if (resultString && resultString.length > 0) {
      try {
        responseData = JSON.parse(resultString);
        console.log("Parsed response:", responseData);
      } catch (parseError) {
        console.log("Result is not valid JSON:", resultString);
        responseData = {
          success: true,
          rawResponse: resultString,
          message: "Event processed but response format unexpected",
        };
      }
    } else {
      console.log("Empty response from chaincode");
      responseData = {
        success: true,
        message: "Event recorded (empty response from chaincode)",
      };
    }

    res.status(200).json({
      message: "Transaction completed",
      data: responseData,
    });
  } catch (err) {
    console.error("Error in recordEvent:", err);
    console.error("Error stack:", err.stack);

    // More specific error handling
    if (err.message.includes("No valid responses from any peers")) {
      res.status(503).json({
        error: "Blockchain network unavailable",
        details:
          "Please check if the Fabric network is running and chaincode is deployed",
        suggestion: "Try: ./network.sh down && ./network.sh up",
      });
    } else if (err.message.includes("identity not found")) {
      res.status(401).json({
        error: "Authentication failed",
        details: "User identity not found in wallet",
        suggestion: "Run: node enrollAdmin.js && node enrollUser.js",
      });
    } else if (err.message.includes("Unexpected end of JSON input")) {
      res.status(500).json({
        error: "Chaincode response error",
        details: "Chaincode returned malformed or empty response",
        suggestion: "Check chaincode logs: docker logs peer0.org1.example.com",
      });
    } else {
      res.status(500).json({
        error: "Internal server error",
        details: err.message,
      });
    }
  } finally {
    if (gateway) {
      gateway.disconnect();
    }
  }
});

// Health check endpoint
app.get("/api/health", async (req, res) => {
  try {
    const { contract, gateway } = await getContract();
    gateway.disconnect();
    res.status(200).json({ status: "Network connection successful" });
  } catch (err) {
    res.status(500).json({
      status: "Network connection failed",
      error: err.message,
    });
  }
});

app.listen(PORT, () => {
  console.log(`🚀 API Server listening at http://localhost:${PORT}`);
});
