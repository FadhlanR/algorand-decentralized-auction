const { default: algosdk } = require("algosdk");
const algodClient = require("../clients/algod.client");
const { POOL_MNEMONIC, ALGOTRAIN_TOKEN_ID } = require("../constants/common.constant");
const { waitingForTransaction } = require("../utils/algo.util");

const userRegistration = async () => {
    const poolAccount = algosdk.mnemonicToSecretKey(POOL_MNEMONIC);
    const newAccount = algosdk.generateAccount();
    const suggestedParams = await algodClient.getTransactionParams().do();
    const initAccountTx = algosdk.makePaymentTxnWithSuggestedParams(
        poolAccount.addr,
        newAccount.addr,
        201000, //100000 (account min balance) + 100000 (min balance to opt in) + 1000 (transaction's fee)
        undefined,
        undefined,
        suggestedParams
    );
    const optInTx = algosdk.makeAssetTransferTxnWithSuggestedParams(
        newAccount.addr,
        newAccount.addr,
        undefined,
        undefined,
        0,
        undefined,
        ALGOTRAIN_TOKEN_ID,
        suggestedParams
    );
    algosdk.assignGroupID([initAccountTx, optInTx]);
    const tx = await algodClient.sendRawTransaction(
        [initAccountTx.signTxn(poolAccount.sk), optInTx.signTxn(newAccount.sk)]).do();
    await waitingForTransaction(tx.txId);
    console.log("Please store this data safely");
    console.log(`address: ${newAccount.addr}`);
    console.log(`mnemonic: ${algosdk.secretKeyToMnemonic(newAccount.sk)}`);
}

module.exports = userRegistration;