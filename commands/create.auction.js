const { default: algosdk } = require("algosdk");
const algodClient = require("../clients/algod.client");
const { POOL_MNEMONIC } = require("../constants/common.constant");
const compile = require("../util/compile_util");
const { waitingForTransaction } = require("../utils/algo.util");
const { scan } = require("../utils/common.util");
const fs = require('fs');

//1. Deploy the stateful. --> application id.
//2.a update the stateless smart contract code.
//2.b Initialize stateless smart contract account and Opt in stateless smart contract to the NFT.
//3. openAuction by passing the stateless smart contract address.

const createAuction = async (startDate, endDate, nftId, nftOwner) => {
    const appId = await deployStateful(startDate, endDate, nftId, nftOwner);
    console.log('Success deploy application, appID: ' + appId);
    updateEscrow(appId, nftId);
    const statelessAddress = await initEscrow(nftId, nftOwner, appId);
    console.log('Success initialize stateless account: ' + statelessAddress);
}

const deployStateful = async (startDate, endDate, nftId, nftOwner) => {
    const params = await algodClient.getTransactionParams().do();

    const poolAccount = algosdk.mnemonicToSecretKey(POOL_MNEMONIC);
    //minimum balance 100000 + 228000 + 150000 = 478000
    let coverFeeTx = algosdk.makePaymentTxnWithSuggestedParams(poolAccount.addr, 
        nftOwner.addr, 479000, undefined, undefined, params);

    //deploy the smart contract
    const onComplete = algosdk.OnApplicationComplete.NoOpOC;
    const approvalProgram = await compile('./contracts/stateful_auction_approval.teal');
    const clearProgram = await compile('./contracts/stateful_auction_clear.teal');
    let deployTx = algosdk.makeApplicationCreateTxn(
        nftOwner.addr, params, onComplete, approvalProgram, clearProgram, 1, 0, 8, 3, 
        [algosdk.encodeUint64(startDate), algosdk.encodeUint64(endDate), algosdk.encodeUint64(nftId)],
        undefined, undefined, undefined, undefined);

    algosdk.assignGroupID([coverFeeTx, deployTx]);
    try {
        await algodClient.sendRawTransaction([
            coverFeeTx.signTxn(poolAccount.sk),
            deployTx.signTxn(nftOwner.sk)
        ]).do();
        const tx = await waitingForTransaction(deployTx.txID());
        return tx.transaction['created-application-index'];
    } catch(e) {
        console.log(e);
    }
}

const initEscrow = async (nftId, nftOwner, appId) => {
    const params = await algodClient.getTransactionParams().do();
    const poolAccount = algosdk.mnemonicToSecretKey(POOL_MNEMONIC);
    
    const statelessCode = await compile('./contracts/stateless_auction.teal');
    const logicSig = algosdk.makeLogicSig(statelessCode);
    
    //minimum balance 100000 + 100000 + 1000 = 2001000
    //Initialize stateless account
    const initAccountTx = algosdk.makePaymentTxnWithSuggestedParams(poolAccount.addr,
        logicSig.address(), 201000, undefined, undefined, params);
    
    //Optin stateless to NFT
    const optInTx = algosdk.makeAssetTransferTxnWithSuggestedParams(logicSig.address(), 
        logicSig.address(), undefined, undefined, 0, undefined, nftId, params);

    //Open auction
    const openAuctionTx = algosdk.makeApplicationNoOpTxn(nftOwner.addr, params, appId,
        [ new Uint8Array(Buffer.from('openAuction')),  new Uint8Array(Buffer.from(logicSig.address()))]);
    
    algosdk.assignGroupID([initAccountTx, optInTx, openAuctionTx]);
    try {
        const logicTx = algosdk.signLogicSigTransaction(optInTx, logicSig);
        await algodClient.sendRawTransaction([
            initAccountTx.signTxn(poolAccount.sk),
            logicTx.blob,
            openAuctionTx.signTxn(nftOwner.sk)
        ]).do();
        const tx = await waitingForTransaction(logicTx.blob);
        return logicSig.address();
    } catch(e) {
        console.log(e);
    }
}

const updateEscrow = (app_id, nft_asset) => {
    const input = fs.readFileSync('./contracts/stateless_auction.teal');
    const array = String(input).split('\n');
    let isPrevLineAppId = false;
    let isPrevLineXferAsset = false;
    let newEscrow = '';
    for(var i = 0; i <= array.length; i++) {
        if (isPrevLineAppId) {
            array[i] = `int ${app_id}\r`
        }

        if (isPrevLineXferAsset) {
            array[i] = `int ${nft_asset}\r`;
        }

        if (array[i] === 'gtxns ApplicationID\r') {
            isPrevLineAppId = true
        } else {
            isPrevLineAppId = false;
        }

        if (array[i] === 'txn XferAsset\r') {
            isPrevLineXferAsset = true
        } else {
            isPrevLineXferAsset = false;
        }

        if (array[i] && !array[i].includes('undefined')) {
            newEscrow = newEscrow + `${array[i]}\n`;
        }
    }
    fs.writeFileSync('./contracts/stateless_auction.teal', newEscrow);
}

const mnemonic = "damage just choice village pyramid crack enter claim donor broom keen wisdom draft clump install anger logic decorate industry initial refuse hill hammer ability hedgehog";
createAuction(1631336899, 1631358899, 24214152, algosdk.mnemonicToSecretKey(mnemonic));
