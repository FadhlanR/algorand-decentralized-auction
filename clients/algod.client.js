const { default: algosdk } = require("algosdk");
const baseServerUrl = 'https://testnet-algorand.api.purestake.io/ps2';
const token = {
    "x-api-key": "gRuUTaWQ1c29etSbxXBLla7uX8a0hIQl1PZho8X9"
}

const algodClient = new algosdk.Algodv2(token, baseServerUrl, 443);
module.exports = algodClient;