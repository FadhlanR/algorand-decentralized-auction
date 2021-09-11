const fs = require('fs');
const algodClient = require('../clients/algod.client');

const compile = async (path) => {
    const sc = fs.readFileSync(path);
    const results = await algodClient.compile(sc).do();
    let program = new Uint8Array(Buffer.from(results.result , "base64"));
    return program;
};

module.exports = compile