const { default: algosdk } = require("algosdk")

const generateKeypair = () => {
    const account = algosdk.generateAccount();
    const mnemonic = algosdk.secretKeyToMnemonic(account.sk);

    console.log(`address: ${account.addr}`);
    console.log(`mnemonic: ${mnemonic}`);
}

generateKeypair();