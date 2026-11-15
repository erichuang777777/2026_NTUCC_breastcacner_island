// Read the password from stdin; never put it in command arguments or commit output.
import {hashPassword} from '../server/validation.mjs';
let input='';for await(const chunk of process.stdin)input+=chunk;const password=input.replace(/\r?\n$/,'');if(password.length<8||password.length>128)throw Error('密碼須為 8 至 128 字元。');console.log(await hashPassword(password));
