const { default: algosdk } = require("algosdk");
const algodClient = require("../clients/algod.client");
const { POOL_MNEMONIC } = require("../constants/common.constant");
const { waitingForTransaction } = require("../utils/algo.util");

const createToken = async () => {
    const account = algosdk.mnemonicToSecretKey(POOL_MNEMONIC);
    const params = await algodClient.getTransactionParams().do();
    const createAlgoTrainTokenTx = algosdk.makeAssetCreateTxnWithSuggestedParams(
        account.addr,
        undefined,
        10000000000000,
        5,
        false,
        account.addr,
        account.addr,
        account.addr,
        account.addr,
        'ALT',
        'ALT',
        undefined,
        undefined,
        params
    );
    const txSigned = createAlgoTrainTokenTx.signTxn(account.sk);
    const tx = await algodClient.sendRawTransaction(txSigned).do();
    const minedTx = await waitingForTransaction(tx);
    console.log(minedTx.transaction['created-asset-index']);
}

createToken();