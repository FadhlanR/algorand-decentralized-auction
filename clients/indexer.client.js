const { default: algosdk } = require("algosdk");
const baseServerUrl = 'https://testnet-algorand.api.purestake.io/idx2';
const token = {
    "x-api-key": "gRuUTaWQ1c29etSbxXBLla7uX8a0hIQl1PZho8X9"
}

const indexerClient = new algosdk.Indexer(token, baseServerUrl, 443);
module.exports = indexerClient;