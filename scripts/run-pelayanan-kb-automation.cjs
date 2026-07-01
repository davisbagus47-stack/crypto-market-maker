const { runPelayananKbAutomation } = require("../src/browser/pelayanan_kb_automation.cjs");

async function main() {
  const commandText = process.argv.slice(2).join(" ").trim();
  if (!commandText) {
    console.error(
      'Usage: node scripts/run-pelayanan-kb-automation.cjs "input data implant 10 orang dari desa tegalsari rt.2 rw.6"',
    );
    process.exit(2);
  }

  const result = await runPelayananKbAutomation({ commandText });
  console.log(JSON.stringify(result, null, 2));
}

main().catch((error) => {
  console.error(error.stack || error.message || String(error));
  process.exit(1);
});
