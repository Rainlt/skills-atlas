const fs = require('node:fs');
const sharp = require('sharp');
(async () => {
  const [input, output] = process.argv.slice(2);
  if (!input || !output) throw new Error('Usage: node render.cjs input.svg new-output.png');
  const buffer = await sharp(input).png().toBuffer();
  fs.writeFileSync(output, buffer, {flag: 'wx'});
})().catch(error => { console.error(error.message); process.exitCode = 1; });
