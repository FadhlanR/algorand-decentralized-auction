const readline = require('readline');

const pause = (ms) => {
    return new Promise((resolve) => {
        setTimeout(() => {resolve()}, ms);
    });
}

const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
});

const scan = (question) => {
    return new Promise((resolve) => {
        rl.question(question, (answer) => {
            resolve(answer);
        });
    });
}

module.exports = {
    pause,
    scan
}