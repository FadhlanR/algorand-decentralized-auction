const { default: algosdk } = require("algosdk");
const algodClient = require("../clients/algod.client");
const { POOL_MNEMONIC } = require("../constants/common.constant");
const { waitingForTransaction } = require("../utils/algo.util");
const { scan } = require("../utils/common.util");

//issue_nft
//mnemonic
const issueNFT = async () => {
    const userMnemonic = await scan("Please input your mnemonic: ");
    const nftName = await scan("NFT name: ");
    const nftUnitName = await scan("NFT unit name: ");
    const nftUrl = await scan("NFT url: ");
    const nftHash = await scan("digital asset hash: ");
    
    const poolAccount = algosdk.mnemonicToSecretKey(POOL_MNEMONIC);
    const userAccount = algosdk.mnemonicToSecretKey(userMnemonic);
    const params = await algodClient.getTransactionParams().do();
    
    const firstTX = algosdk.makePaymentTxnWithSuggestedParams(
        poolAccount.addr,
        userAccount.addr,
        101000,
        undefined,
        undefined,
        params
    );

    const secondTx = algosdk.makeAssetCreateTxnWithSuggestedParams(
        userAccount.addr,
        undefined,
        1,
        0,
        false,
        userAccount.addr,
        userAccount.addr,
        userAccount.addr,
        undefined,
        nftUnitName,
        nftName,
        nftUrl,
        undefined,
        params
    );

    algosdk.assignGroupID([firstTX, secondTx]);
    const tx = await algodClient.sendRawTransaction(
        [firstTX.signTxn(poolAccount.sk), secondTx.signTxn(userAccount.sk)]).do();
    console.log(secondTx.txID());
    const minedTx = await waitingForTransaction(secondTx.txID());
    console.log(`asset id: ${minedTx.transaction['created-asset-index']}`);
}

module.exports = issueNFT;