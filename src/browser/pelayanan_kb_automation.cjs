const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");
const { chromium } = require("playwright-core");

const PROJECT_ROOT = path.resolve(__dirname, "..", "..");
const DEFAULT_TIMEOUT = 30000;

function loadEnv(envPath = path.join(PROJECT_ROOT, ".env")) {
  if (!fs.existsSync(envPath)) return {};

  const env = {};
  const lines = fs.readFileSync(envPath, "utf8").split(/\r?\n/);
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;
    const match = trimmed.match(/^([^=]+)=(.*)$/);
    if (!match) continue;
    const key = match[1].trim();
    const value = match[2].trim().replace(/^['"]|['"]$/g, "");
    env[key] = value;
  }
  return env;
}

function getConfig() {
  const fileEnv = loadEnv();
  const env = { ...fileEnv, ...process.env };
  const python =
    env.PYTHON_EXE ||
    path.join(
      env.USERPROFILE || "",
      ".cache",
      "codex-runtimes",
      "codex-primary-runtime",
      "dependencies",
      "python",
      "python.exe",
    );

  return {
    python,
    chromePath:
      env.CHROME_EXE ||
      "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    username: env.SIGA_USERNAME,
    password: env.SIGA_PASSWORD,
    webBaseUrl: env.SIGA_WEB_BASE_URL || "https://newsiga-siga.bkkbn.go.id",
    headless: String(env.AGENT_HEADLESS || "false").toLowerCase() === "true",
    keepBrowserOpen:
      String(env.AGENT_KEEP_BROWSER_OPEN || "false").toLowerCase() === "true",
    closeDelayMs: Number(env.AGENT_CLOSE_DELAY_MS || "0"),
    dryRun: String(env.AGENT_DRY_RUN || "true").toLowerCase() !== "false",
    requireApproval:
      String(env.AGENT_REQUIRE_APPROVAL || "true").toLowerCase() !== "false",
    userDataDir:
      env.AGENT_BROWSER_PROFILE ||
      path.join(PROJECT_ROOT, ".browser-profile", "siga"),
    outputDir: env.OUTPUT_DIR || path.join(PROJECT_ROOT, "data", "output"),
  };
}

function parseIntent(commandText, config) {
  const result = spawnSync(config.python, ["parse_command.py", commandText], {
    cwd: PROJECT_ROOT,
    encoding: "utf8",
  });

  if (result.status !== 0) {
    throw new Error(
      `Gagal parse instruksi.\nSTDOUT:\n${result.stdout}\nSTDERR:\n${result.stderr}`,
    );
  }

  return JSON.parse(result.stdout);
}

async function runPelayananKbAutomation({ commandText, maxPages = 10 }) {
  const config = getConfig();
  validateConfig(config);

  const parsed = parseIntent(commandText, config);
  const intent = parsed.intent;
  if (intent.needs_confirmation) {
    return writeRunReport(config.outputDir, {
      status: "needs_confirmation",
      reason: "Intent belum cukup jelas.",
      parsed,
    });
  }

  ensureDir(config.userDataDir);
  ensureDir(config.outputDir);

  const browser = await chromium.launchPersistentContext(config.userDataDir, {
    executablePath: config.chromePath,
    headless: config.headless,
    viewport: { width: 1366, height: 900 },
    acceptDownloads: false,
  });

  const page = browser.pages()[0] || (await browser.newPage());
  page.setDefaultTimeout(DEFAULT_TIMEOUT);

  const state = {
    status: "started",
    dryRun: config.dryRun,
    requireApproval: config.requireApproval,
    parsed,
    selectedRows: [],
    warnings: [],
  };

  try {
    await loginIfNeeded(page, config);
    await openPelayananKb(page, config);
    await openSearchModal(page);
    await resolveAndFillLocation(page, intent, state);
    await clickSearchInModal(page);
    state.selectedRows = await collectPusRows(page, intent.quantity, maxPages);

    state.status =
      state.selectedRows.length >= intent.quantity ? "preview_ready" : "partial_preview";
    state.message =
      state.status === "preview_ready"
        ? "Data PUS ditemukan sesuai jumlah permintaan. Submit final belum dijalankan."
        : "Data PUS yang ditemukan belum mencapai jumlah permintaan.";

    if (!config.dryRun) {
      state.warnings.push(
        "AGENT_DRY_RUN=false terdeteksi, tetapi submit final tetap belum diaktifkan di modul awal.",
      );
    }

    return writeRunReport(config.outputDir, state);
  } catch (error) {
    state.status = "failed";
    state.error = error.message || String(error);
    state.currentUrl = page.url();
    state.pageTextSample = await page
      .locator("body")
      .innerText({ timeout: 2000 })
      .then((text) => text.slice(0, 1200))
      .catch(() => "");
    return writeRunReport(config.outputDir, state);
  } finally {
    await finishBrowser(browser, config);
  }
}

function validateConfig(config) {
  if (!fs.existsSync(config.python)) {
    throw new Error(`Python tidak ditemukan: ${config.python}`);
  }
  if (!fs.existsSync(config.chromePath)) {
    throw new Error(`Chrome tidak ditemukan: ${config.chromePath}`);
  }
  if (!config.username || !config.password) {
    throw new Error(
      "SIGA_USERNAME dan SIGA_PASSWORD belum diisi. Copy .env.example menjadi .env lalu isi kredensial.",
    );
  }
}

async function loginIfNeeded(page, config) {
  await page.goto(`${config.webBaseUrl}/#/login`, { waitUntil: "domcontentloaded" });
  await page.waitForLoadState("networkidle").catch(() => {});

  if (await hasValidSigaToken(page)) return;

  const usernameInput = page.locator(
    'input[name="email"], input[id="email"], input[type="text"]',
  ).first();
  const passwordInput = page.locator(
    'input[name="password"], input[id="password"], input[type="password"]',
  ).first();

  await usernameInput.waitFor({ state: "visible" });
  await usernameInput.fill(config.username);
  await passwordInput.fill(config.password);

  await clickByText(page, ["Masuk", "Login", "SIGN IN"], "button");
  await waitForPostLogin(page);

  const bodyText = await page.locator("body").innerText().catch(() => "");
  if (/kesalahan ID|password|belum terdaftar/i.test(bodyText)) {
    throw new Error("Login SIGA gagal. Cek username/password.");
  }
  if (page.url().includes("#/chpass") || /Ubah Kata Sandi|Kata Sandi Baru/i.test(bodyText)) {
    throw new Error(
      "Login berhasil, tetapi SIGA meminta ubah kata sandi. Selesaikan manual dulu, lalu jalankan ulang agent.",
    );
  }
  if (!(await hasValidSigaToken(page))) {
    throw new Error("Login terlihat berhasil, tetapi token SIGA belum tersimpan. Jalankan ulang atau cek popup/login manual.");
  }
}

async function openPelayananKb(page, config) {
  if (!(await hasValidSigaToken(page))) {
    throw new Error("Sesi SIGA belum valid sebelum membuka menu Pelayanan KB.");
  }

  await page.goto(`${config.webBaseUrl}/#/register`, { waitUntil: "domcontentloaded" });
  await page.waitForLoadState("networkidle").catch(() => {});
  await page.waitForTimeout(2000);

  const title = await page.locator("body").innerText().catch(() => "");
  if (page.url().includes("#/login") || /Masukkan ID|Kata Sandi|Login/i.test(title)) {
    throw new Error("SIGA kembali ke halaman login saat membuka /register. Sesi/token belum diterima aplikasi.");
  }
  if (!/Pelayanan KB|Tambah Data Pelayanan KB|Data Peserta/i.test(title)) {
    throw new Error("Halaman Pelayanan KB belum terbuka atau sesi login belum valid.");
  }
}

async function waitForPostLogin(page) {
  const deadline = Date.now() + 20000;
  while (Date.now() < deadline) {
    await page.waitForTimeout(500);
    await page.waitForLoadState("networkidle").catch(() => {});
    const url = page.url();
    if (url.includes("#/dashboard") || url.includes("#/beranda") || url.includes("#/chpass")) {
      return;
    }
    if (await hasValidSigaToken(page)) {
      return;
    }
  }
}

async function hasValidSigaToken(page) {
  return await page
    .evaluate(() => {
      const token = window.localStorage.getItem("token");
      const refreshToken = window.localStorage.getItem("refreshToken");
      return Boolean(token && token !== "null" && token.length > 20 && refreshToken);
    })
    .catch(() => false);
}

async function finishBrowser(browser, config) {
  if (config.keepBrowserOpen) {
    console.log("Browser dibiarkan terbuka. Tekan Ctrl+C di terminal jika ingin menghentikan agent.");
    return;
  }
  if (config.closeDelayMs > 0) {
    await new Promise((resolve) => setTimeout(resolve, config.closeDelayMs));
  }
  await browser.close();
}

async function openSearchModal(page) {
  await clickByText(page, ["Cari"], "button");
  await page.waitForTimeout(1000);
  await page.locator("text=Filter Pencarian Data KK KB").waitFor({ state: "visible" });
}

async function resolveAndFillLocation(page, intent, state) {
  const location = intent.location || {};

  await selectReactOptionByLabel(page, "Desa/Kel", location.desa, state);
  await selectReactOptionByLabel(page, "Dusun/RW", location.rw || location.dusun, state);
  await selectReactOptionByLabel(page, "RT", location.rt, state);
}

async function selectReactOptionByLabel(page, labelText, query, state) {
  if (!query) return;

  const field = await findFieldNearLabel(page, labelText);
  if (!field) {
    state.warnings.push(`Field ${labelText} tidak ditemukan.`);
    return;
  }

  await field.click();
  await page.waitForTimeout(300);

  const options = await readVisibleOptions(page);
  const match = matchOption(query, options);
  if (!match.selected) {
    state.warnings.push(
      `Opsi ${labelText} untuk "${query}" tidak ditemukan. Kandidat: ${options.slice(0, 5).join(", ")}`,
    );
    return;
  }

  await page.getByText(match.selected, { exact: true }).last().click();
  await page.waitForTimeout(300);
  state[`resolved_${normalizeKey(labelText)}`] = match;
}

async function findFieldNearLabel(page, labelText) {
  const label = page.locator(`text=${labelText}`).first();
  const count = await label.count();
  if (!count) return null;

  const handle = await label.elementHandle();
  if (!handle) return null;

  const candidate = await handle.evaluateHandle((node) => {
    const row = node.closest(".row") || node.parentElement;
    if (!row) return null;
    return (
      row.querySelector(".select__control") ||
      row.querySelector("[class*='control']") ||
      row.querySelector("input") ||
      row.querySelector("select")
    );
  });

  const element = candidate.asElement();
  if (!element) return null;
  return element;
}

async function readVisibleOptions(page) {
  const selectors = [
    ".select__menu div",
    "[class*='menu'] [class*='option']",
    "[id*='react-select']",
    ".css-yt9ioa-option",
    ".css-1n7v3ny-option",
  ];
  const values = new Set();
  for (const selector of selectors) {
    const texts = await page
      .locator(selector)
      .allInnerTexts()
      .catch(() => []);
    for (const text of texts) {
      const cleaned = text.trim();
      if (cleaned && cleaned.length < 120) values.add(cleaned);
    }
  }
  return [...values];
}

function matchOption(query, options) {
  const normalizedQuery = normalizeLocation(query);
  const queryNumber = extractNumber(query);
  let best = null;

  for (const option of options) {
    const normalizedOption = normalizeLocation(option);
    const withoutCode = normalizeLocation(option.replace(/^\s*\d+\s*-\s*/, ""));
    const optionNumbers = [...option.matchAll(/\d+/g)].map((m) => m[0].padStart(3, "0"));
    let score = 0;

    if (normalizedOption === normalizedQuery || withoutCode === normalizedQuery) score = 100;
    else if (queryNumber && optionNumbers.includes(queryNumber)) score = 95;
    else if (withoutCode.includes(normalizedQuery)) score = 90;
    else if (normalizedOption.includes(normalizedQuery)) score = 85;

    if (!best || score > best.score) best = { score, selected: option };
  }

  if (!best || best.score === 0) {
    return { query, selected: null, confidence: "none" };
  }
  return {
    query,
    selected: best.selected,
    confidence: best.score >= 95 ? "high" : "medium",
  };
}

async function clickSearchInModal(page) {
  const buttons = page.locator("button", { hasText: "Cari" });
  const count = await buttons.count();
  if (!count) throw new Error("Tombol Cari pada popup tidak ditemukan.");
  await buttons.nth(count - 1).click();
  await page.waitForTimeout(1500);
}

async function collectPusRows(page, quantity, maxPages) {
  const selected = [];
  for (let pageIndex = 1; pageIndex <= maxPages && selected.length < quantity; pageIndex += 1) {
    const rows = await readResultRows(page);
    for (const row of rows) {
      if (selected.length >= quantity) break;
      if (/^ya$/i.test(row.pus || "")) {
        selected.push(row);
      }
    }

    if (selected.length >= quantity) break;
    const moved = await goToNextPage(page);
    if (!moved) break;
    await page.waitForTimeout(1000);
  }
  return selected;
}

async function readResultRows(page) {
  return await page.evaluate(() => {
    const tables = [...document.querySelectorAll("table")];
    const table = tables.find((candidate) =>
      /Kode Keluarga/i.test(candidate.innerText || ""),
    );
    if (!table) return [];

    const headers = [...table.querySelectorAll("thead th, tr:first-child th")].map((cell) =>
      (cell.textContent || "").trim(),
    );
    const bodyRows = [...table.querySelectorAll("tbody tr")];

    return bodyRows
      .map((tr) => {
        const cells = [...tr.querySelectorAll("td")].map((cell) =>
          (cell.textContent || "").trim(),
        );
        if (!cells.length) return null;
        const find = (name) => {
          const index = headers.findIndex((header) =>
            header.toLowerCase().includes(name.toLowerCase()),
          );
          return index >= 0 ? cells[index] : "";
        };
        return {
          no: find("No"),
          kodeKeluarga: find("Kode Keluarga"),
          namaKk: find("Nama KK"),
          pus: find("PUS"),
          raw: cells,
        };
      })
      .filter(Boolean);
  });
}

async function goToNextPage(page) {
  const next = page.getByText(">", { exact: true }).last();
  if ((await next.count()) === 0) return false;
  const before = await page.locator("table").last().innerText().catch(() => "");
  await next.click();
  await page.waitForTimeout(1000);
  const after = await page.locator("table").last().innerText().catch(() => "");
  return before !== after;
}

async function clickByText(page, labels, selector = "*") {
  for (const label of labels) {
    const locator = page.locator(selector, { hasText: label }).first();
    if ((await locator.count()) > 0) {
      await locator.click();
      return;
    }
  }
  throw new Error(`Elemen tidak ditemukan: ${labels.join(" / ")}`);
}

function writeRunReport(outputDir, state) {
  ensureDir(outputDir);
  const jobId = `pelayanan-kb-${new Date().toISOString().replace(/[-:.TZ]/g, "").slice(0, 14)}`;
  const outputPath = path.join(outputDir, `${jobId}.json`);
  fs.writeFileSync(outputPath, JSON.stringify({ jobId, ...state }, null, 2), "utf8");
  return { jobId, outputPath, ...state };
}

function ensureDir(dirPath) {
  fs.mkdirSync(dirPath, { recursive: true });
}

function normalizeLocation(value) {
  return String(value || "")
    .toUpperCase()
    .replace(/[^A-Z0-9]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function extractNumber(value) {
  const match = String(value || "").match(/\d+/);
  return match ? match[0].padStart(3, "0") : null;
}

function normalizeKey(value) {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_|_$/g, "");
}

module.exports = {
  getConfig,
  parseIntent,
  runPelayananKbAutomation,
  matchOption,
};
