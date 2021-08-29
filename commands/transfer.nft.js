const { default: algosdk } = require("algosdk");
const algodClient = require("../clients/algod.client");
const { POOL_MNEMONIC } = require("../constants/common.constant");
const { waitingForTransaction } = require("../utils/algo.util");
const { scan } = require("../utils/common.util");

const transferNFT = async () => {
  const fromUserMnemonic = await scan("Input the user mnemonic: ");
  const toUserAddress = await scan("Input the receiver address: ");
  const nftId = await scan("Input the NFT ID: ");

  const fromAccount = algosdk.mnemonicToSecretKey(fromUserMnemonic);
  const poolAccount = algosdk.mnemonicToSecretKey(POOL_MNEMONIC);

  const suggestedParams = await algodClient.getTransactionParams().do();

  const feeTransferTx = algosdk.makePaymentTxnWithSuggestedParams(
    poolAccount.addr,
    fromAccount.addr,
    1000,
    undefined,
    undefined,
    suggestedParams
  );

  const transferNftTx = algosdk.makeAssetTransferTxnWithSuggestedParams(
    fromAccount.addr,
    toUserAddress,
    undefined,
    undefined,
    1,
    undefined,
    Number(nftId),
    suggestedParams
  );

  algosdk.assignGroupID([feeTransferTx, transferNftTx]);

  const signedFeeTransferTx = feeTransferTx.signTxn(poolAccount.sk);
  const signedTransferNftTx = transferNftTx.signTxn(fromAccount.sk);

  const tx = await algodClient
    .sendRawTransaction([signedFeeTransferTx, signedTransferNftTx])
    .do();

  const minedTx = await waitingForTransaction(transferNftTx.txID());

  console.log(`Transaction ID: ${tx.txId}`);
};

module.exports = { transferNFT };
