const I18N = {
  en: {
    "app.title": "Compression Trade-Offs",
    "app.tag": "CPU vs Disk I/O balance on a single machine",
    "nav.slides": "Presentation",
    "nav.docs": "API docs",
    "lang.toggle": "ខ្មែរ",

    "panel.configure": "Configure ingestion",
    "field.format": "Format",
    "field.codec": "Codec",
    "field.level": "Zstd level",
    "field.threads": "Threads",
    "field.maxRows": "Max rows",

    "btn.download": "Download dataset",
    "btn.ingest": "Run ingest",
    "btn.matrix": "Codec matrix",
    "btn.sweep": "Zstd sweep",
    "btn.full": "Full benchmark",
    "check.zstdFull": "Full Zstd levels 1–22 (slower)",

    "msg.ready": "Ready — download a dataset, then ingest or benchmark.",
    "panel.recommend": "Recommendation",
    "recommend.empty":
      "Run a benchmark to get a clear recommendation (e.g. zstd level X is best because…).",

    "panel.live": "Live metrics",
    "chart.cpu": "CPU %",
    "chart.disk": "Disk wait %",
    "chart.thr": "Throughput MB/s",
    "panel.balance": "Balance point (CPU% vs disk-wait%)",
    "panel.results": "Results",

    "th.name": "Name",
    "th.codec": "Codec",
    "th.level": "Level",
    "th.format": "Format",
    "th.ratio": "Ratio",
    "th.readproc": "Read+Proc (s)",
    "th.total": "Total (s)",
    "th.mbs": "MB/s",
    "th.cpu": "CPU%",
    "th.diskwait": "Disk wait%",
    "th.rss": "Peak RSS MB",

    "panel.path": "Data path",
    "path.1": "Compressed disk",
    "path.1d": "Parquet / Feather / Blosc2 / Zarr",
    "path.2": "CPU decompress",
    "path.2d": "Snappy, LZ4, Zstd, Gzip, Brotli",
    "path.3": "In-memory columns",
    "path.3d": "Apache Arrow / Pandas",
    "path.4": "Process",
    "path.4d": "filter / aggregate (column subset)",

    "footer.note": "Case Study 2 · Bcolz → Parquet / Arrow / Blosc2 / Zarr",

    "status.idle": "idle",
    "status.running": "running",
    "status.error": "error",
  },
  km: {
    "app.title": "តុល្យភាពនៃការបង្ហាប់ទិន្នន័យ",
    "app.tag": "តុល្យភាព CPU ធៀបនឹង Disk I/O លើម៉ាស៊ីនតែមួយ",
    "nav.slides": "បទបង្ហាញ",
    "nav.docs": "ឯកសារ API",
    "lang.toggle": "English",

    "panel.configure": "កំណត់ការបញ្ចូលទិន្នន័យ",
    "field.format": "ទម្រង់ (Format)",
    "field.codec": "ក្បួនបង្ហាប់ (Codec)",
    "field.level": "កម្រិត Zstd",
    "field.threads": "ចំនួន Threads",
    "field.maxRows": "ចំនួនជួរអតិបរមា",

    "btn.download": "ទាញយក Dataset",
    "btn.ingest": "ដំណើរការបញ្ចូល",
    "btn.matrix": "ប្រៀបធៀបក្បួន",
    "btn.sweep": "សាកល្បង Zstd គ្រប់កម្រិត",
    "btn.full": "តេស្តពេញលេញ",
    "check.zstdFull": "Zstd កម្រិត ១–២២ ទាំងអស់ (យឺតជាង)",

    "msg.ready": "រួចរាល់ — ទាញយក Dataset រួចធ្វើការបញ្ចូល ឬតេស្ត។",
    "panel.recommend": "អនុសាសន៍",
    "recommend.empty":
      "សូមដំណើរការតេស្ត ដើម្បីទទួលបានអនុសាសន៍ច្បាស់លាស់ (ឧ. zstd កម្រិត X ល្អបំផុត ព្រោះ…)។",

    "panel.live": "ការវាស់វែងផ្ទាល់",
    "chart.cpu": "CPU %",
    "chart.disk": "រង់ចាំថាស %",
    "chart.thr": "ល្បឿន MB/s",
    "panel.balance": "ចំណុចលំនឹង (CPU% ធៀប រង់ចាំថាស%)",
    "panel.results": "លទ្ធផល",

    "th.name": "ឈ្មោះ",
    "th.codec": "ក្បួន",
    "th.level": "កម្រិត",
    "th.format": "ទម្រង់",
    "th.ratio": "អត្រាបង្ហាប់",
    "th.readproc": "អាន+ដំណើរការ (វិ)",
    "th.total": "សរុប (វិ)",
    "th.mbs": "MB/s",
    "th.cpu": "CPU%",
    "th.diskwait": "រង់ចាំថាស%",
    "th.rss": "RAM អតិបរមា MB",

    "panel.path": "ផ្លូវទិន្នន័យ",
    "path.1": "ថាសដែលបង្ហាប់",
    "path.1d": "Parquet / Feather / Blosc2 / Zarr",
    "path.2": "CPU រំសាយបង្ហាប់",
    "path.2d": "Snappy, LZ4, Zstd, Gzip, Brotli",
    "path.3": "ជួរឈរក្នុង RAM",
    "path.3d": "Apache Arrow / Pandas",
    "path.4": "ដំណើរការ",
    "path.4d": "ត្រង / សរុប (ជ្រើសតែជួរឈរដែលត្រូវការ)",

    "footer.note": "ករណីសិក្សាទី ២ · Bcolz → Parquet / Arrow / Blosc2 / Zarr",

    "status.idle": "ទំនេរ",
    "status.running": "កំពុងដំណើរការ",
    "status.error": "កំហុស",
  },
};

const LANG_KEY = "ct_lang";

function getLang() {
  return localStorage.getItem(LANG_KEY) || "en";
}

function t(key, lang) {
  const l = lang || getLang();
  return (I18N[l] && I18N[l][key]) || I18N.en[key] || key;
}

function applyLang(lang) {
  const l = lang || getLang();
  localStorage.setItem(LANG_KEY, l);
  document.documentElement.lang = l === "km" ? "km" : "en";
  document.body.classList.toggle("lang-km", l === "km");

  document.querySelectorAll("[data-i18n]").forEach((el) => {
    el.textContent = t(el.dataset.i18n, l);
  });
  document.querySelectorAll("[data-i18n-html]").forEach((el) => {
    el.innerHTML = t(el.dataset.i18nHtml, l);
  });

  const btn = document.getElementById("langToggle");
  if (btn) btn.textContent = t("lang.toggle", l);

  document.dispatchEvent(new CustomEvent("langchange", { detail: { lang: l } }));
}

function initLangToggle() {
  const btn = document.getElementById("langToggle");
  if (btn) {
    btn.addEventListener("click", () => {
      applyLang(getLang() === "km" ? "en" : "km");
    });
  }
  applyLang(getLang());
}

document.addEventListener("DOMContentLoaded", initLangToggle);
