"use strict";

const FabricCAServices = require("fabric-ca-client");
const { Wallets } = require("fabric-network");
const fs = require("fs");
const path = require("path");

async function main() {
  try {
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
    const ccp = JSON.parse(fs.readFileSync(ccpPath, "utf8"));

    const caURL = ccp.certificateAuthorities["ca.org1.example.com"].url;
    const ca = new FabricCAServices(caURL);

    const walletPath = path.join(__dirname, "wallet");
    const wallet = await Wallets.newFileSystemWallet(walletPath);

    const userIdentity = await wallet.get("user4");
    if (userIdentity) {
      console.log("✔️ User identity already exists in the wallet");
      return;
    }

    const adminIdentity = await wallet.get("admin");
    if (!adminIdentity) {
      console.log(
        "Admin identity not found in wallet. Please run enrollAdmin.js first."
      );
      return;
    }

    const provider = wallet
      .getProviderRegistry()
      .getProvider(adminIdentity.type);
    const adminUser = await provider.getUserContext(adminIdentity, "admin");

    const secret = await ca.register(
      {
        affiliation: "org1.department1",
        enrollmentID: "user4",
        role: "client",
      },
      adminUser
    );

    const enrollment = await ca.enroll({
      enrollmentID: "user4",
      enrollmentSecret: secret,
    });

    const x509Identity = {
      credentials: {
        certificate: enrollment.certificate,
        privateKey: enrollment.key.toBytes(),
      },
      mspId: "Org1MSP",
      type: "X.509",
    };
    await wallet.put("user4", x509Identity);
    console.log(
      "✅ Successfully registered and enrolled user4 and imported it into the wallet"
    );
  } catch (error) {
    console.error(`❌ Failed to register user: ${error}`);
    process.exit(1);
  }
}

main();
