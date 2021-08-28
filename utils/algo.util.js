const indexerClient = require("../clients/indexer.client");
const { pause } = require("./common.util");

const waitingForTransaction = async (tx) => {
    const maxRetry = 5;
    let retryCount = 1;
    let minedTx = null;
    do {
        await pause(10000);
        try {
            minedTx = await indexerClient.lookupTransactionByID(tx.txId).do();
        } catch(e) {
        }
        retryCount++;
    } while(!minedTx && retryCount <= maxRetry);
    return minedTx;
}

module.exports = {
    waitingForTransaction
}