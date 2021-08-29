const issueNFT = require("./commands/issue.nft");
const userRegistration = require("./commands/user.registration");
const { scan } = require("./utils/common.util");

var isExit = false;

const commandFactory = async (input) => {
    const commands = input.split(' ');
    switch(commands[0]) {
        case "register":
            await userRegistration();
            break;
        case "issue":
            await issueNFT();
            break;
        case "exit":
            isExit = true;
            break;
        default:
            console.log('Unknown command');
    }
}

const main = async () => {
    do {
        const input = await scan('Please input the command:\n');
        await commandFactory(input);
    } while(!isExit);
    console.log('Thanks for using this app');
}

main();