const { default: algosdk } = require("algosdk");
const algodClient = require("../clients/algod.client");
const { POOL_MNEMONIC } = require("../constants/common.constant");
const { scan } = require("../utils/common.util");
const { waitingForTransaction } = require("../utils/algo.util");


const optInNft = async () => {
    const userMnemonic = await scan("Please input your mnemonic: ")
    const nftID = await scan("ASA ID to opt into: ");

    const userAccount = algosdk.mnemonicToSecretKey(userMnemonic);
    const poolAccount = algosdk.mnemonicToSecretKey(POOL_MNEMONIC);

    const suggestedParams = await algodClient.getTransactionParams().do();


    const feeTransferTx = algosdk.makePaymentTxnWithSuggestedParams(
        poolAccount.addr,
        userAccount.addr,
        101000,
        undefined,
        undefined,
        suggestedParams
    );

    const optInTx = algosdk.makeAssetTransferTxnWithSuggestedParams(
        userAccount.addr,
        userAccount.addr,
        undefined,
        undefined,
        0,
        undefined,
        Number(nftID),
        suggestedParams
    );

    algosdk.assignGroupID([feeTransferTx, optInTx]);

    const signedFeeTransferTx = feeTransferTx.signTxn(poolAccount.sk);
    const signedOptInTx = optInTx.signTxn(userAccount.sk);

    const tx = await algodClient.sendRawTransaction([signedFeeTransferTx, signedOptInTx]).do();

    const minedTx = await waitingForTransaction(optInTx.txID());

    console.log(`Transaction ID: ${tx.txId}`);
}

module.exports = {
    optInNft
}