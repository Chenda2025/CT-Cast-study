const SLIDES_I18N = {
  en: {
    "nav.dashboard": "Dashboard",
    "sl.kicker": "Case Study 2",
    "sl.hint": "Use ← → arrow keys or the buttons below",
    "sl.step1": "Step 1",
    "sl.step2": "Step 2",
    "sl.step3": "Step 3",
    "sl.step4": "Step 4",
    "sl.step5": "Step 5",

    "sl1.title": "Balancing Compression Trade-Offs",
    "sl1.sub": "For high-speed data processing on a single machine",

    "sl2.title": "Core idea",
    "sl2.lead": "Compression saves space but costs CPU time.",
    "sl2.help": "Compression helps",
    "sl2.helpd": "Smaller files mean less disk I/O and a smaller memory footprint.",
    "sl2.cost": "Compression costs",
    "sl2.costd": "The CPU must decompress every block before the data can be used.",
    "sl2.goal": "Goal: find the balance point where I/O savings beat decode cost.",

    "sl3.title": "Two competing bottlenecks",
    "sl3.cpu": "CPU bottleneck",
    "sl3.cpud": "Too much decoding work — the processor cannot keep up.",
    "sl3.disk": "Disk I/O bottleneck",
    "sl3.diskd": "Reading large uncompressed files is slow.",
    "sl3.point": "Balance point",

    "sl4.title": "Codec comparison",
    "sl4.h1": "Codec",
    "sl4.h2": "Ratio",
    "sl4.h3": "Decode speed",
    "sl4.h4": "Best for",
    "sl4.low": "Low",
    "sl4.med": "Medium–high",
    "sl4.high": "High",
    "sl4.vhigh": "Highest",
    "sl4.vfast": "Very fast",
    "sl4.tune": "Fast, tunable",
    "sl4.slow": "Slow",
    "sl4.vslow": "Slowest",
    "sl4.none": "none (CSV)",
    "sl4.r1": "CPU-bound work",
    "sl4.r2": "Best balance — the star",
    "sl4.r3": "Disk-bound work",
    "sl4.r4": "Long-term storage",
    "sl4.r5": "Uncompressed baseline",

    "sl5.title": "The data path",

    "sl6.title": "Download the dataset",
    "sl6.lead": "Fetch a compressed dataset from a public online repository.",
    "sl6.note": "If the network fails, a synthetic dataset is generated so the demo still runs.",

    "sl7.title": "Choose format and codec",
    "sl7.lead": "The user picks the columnar format, the codec, and the Zstd level 1–22.",

    "sl8.title": "Write compressed to disk",
    "sl8.note": "Compression ratio = original size ÷ compressed size.",

    "sl9.title": "CPU decompresses on read",
    "sl9.lead": "Columnar formats let us read only the columns we need.",
    "sl9.note": "This is where the CPU cost of compression appears.",

    "sl10.title": "Process in memory",
    "sl10.note": "The same analytics run for every codec, so the comparison is fair.",

    "sl11.title": "Metrics we capture",
    "sl11.m1": "Throughput",
    "sl11.m1d": "MB/s processed",
    "sl11.m2": "CPU usage",
    "sl11.m2d": "percent while decoding",
    "sl11.m3": "Disk wait",
    "sl11.m3d": "I/O stall percent",
    "sl11.m4": "Peak memory",
    "sl11.m4d": "maximum RAM used",
    "sl11.m5": "Ratio",
    "sl11.m5d": "original ÷ compressed",

    "sl12.title": "Finding the balance point",
    "sl12.lead":
      "Plot CPU% against disk-wait% across Zstd levels. Where the two lines meet is the sweet spot.",

    "sl13.title": "Measured results",
    "sl13.speed": "Speedup",
    "sl13.note":
      "Measured on this laptop with an SSD. On slower disks the winner shifts toward higher Zstd levels.",

    "sl14.title": "Recommendation",
    "sl14.quote":
      "On this machine, LZ4 on Parquet gave the best wall-clock time (about 8× faster than uncompressed CSV), because decoding is cheap and the files are already small enough that heavier compression does not pay off.",
    "sl14.note": "When storage is slow or data is much larger, Zstd levels 3–9 usually win instead.",

    "sl15.title": "Bcolz is old — use the modern stack",
    "sl15.old": "Legacy",
    "sl15.oldd": "no longer actively maintained",
    "sl15.new": "Modern replacements",
    "sl15.p": "columnar analytics standard",
    "sl15.a": "very fast in memory",
    "sl15.b": "multi-threaded decompression",
    "sl15.z": "chunked N-dimensional arrays",

    "sl16.title": "Why theory says this happens",
    "sl16.a":
      "Once disk time shrinks, the remaining decode work dominates total time — so more compression stops helping.",
    "sl16.r":
      "Performance is capped by bandwidth or by compute. The best codec sits on the ridge between the two.",
    "sl16.t":
      "Multi-threaded decompression (Blosc2, Zstd) pushes the CPU limit higher by using more cores.",

    "slApi1.title": "What is the API?",
    "slApi1.lead":
      "The dashboard talks to the server through small HTTP commands. Swagger at /docs lets you try them by hand.",
    "slApi1.ui": "Web UI",
    "slApi1.uid": "Buttons on the dashboard call these APIs. Charts read /api/state every 0.5s.",
    "slApi1.docs": "Swagger /docs",
    "slApi1.docsd": "Open /docs to see every route, send a test request, and read the JSON reply.",
    "slApi1.note": "Pages: GET / (dashboard) · GET /slides (presentation) · GET /docs (API explorer)",

    "slApi2.title": "API endpoints explained",
    "slApi2.h1": "Method",
    "slApi2.h2": "Path",
    "slApi2.h3": "What it does",
    "slApi2.state": "Live status, message, CPU/disk samples, latest results",
    "slApi2.results": "Saved benchmark JSON (matrix, sweep, recommendation)",
    "slApi2.codecs": "Short guide for each codec (ratio, decode speed, use case)",
    "slApi2.download": "Download a public dataset (or create synthetic data)",
    "slApi2.ingest": "Write + read + process with your format / codec / level",
    "slApi2.bench": "Run matrix, Zstd sweep, or full suite — then recommend the best",

    "sl17.title": "How to run the app",
    "sl17.s1": "Open http://127.0.0.1:8000",
    "sl17.s2": "Click Download dataset",
    "sl17.s3": "Pick a format, a codec, and drag the Zstd slider",
    "sl17.s4": "Click Full benchmark and watch the live charts",
    "sl17.s5": "Read the recommendation banner",

    "sl18.kicker": "Summary",
    "sl18.title": "Balance, not maximum compression",
    "sl18.a": "Compression trades disk I/O for CPU work.",
    "sl18.b": "Columnar formats read only the needed columns.",
    "sl18.c": "Measure CPU, disk wait, memory, and ratio together.",
    "sl18.d": "The best codec depends on your disk and your data.",
    "sl18.thanks": "Thank you — questions welcome.",
  },
  km: {
    "nav.dashboard": "ផ្ទាំងគ្រប់គ្រង",
    "sl.kicker": "ករណីសិក្សាទី ២",
    "sl.hint": "ប្រើគ្រាប់ចុច ← → ឬប៊ូតុងខាងក្រោម",
    "sl.step1": "ជំហានទី ១",
    "sl.step2": "ជំហានទី ២",
    "sl.step3": "ជំហានទី ៣",
    "sl.step4": "ជំហានទី ៤",
    "sl.step5": "ជំហានទី ៥",

    "sl1.title": "ការធ្វើឲ្យមានតុល្យភាពនៃការបង្ហាប់ទិន្នន័យ",
    "sl1.sub": "សម្រាប់ការដំណើរការទិន្នន័យល្បឿនលឿន លើម៉ាស៊ីនតែមួយ",

    "sl2.title": "គំនិតសំខាន់",
    "sl2.lead": "ការបង្ហាប់សន្សំទំហំ ប៉ុន្តែចំណាយពេល CPU។",
    "sl2.help": "ការបង្ហាប់ជួយ",
    "sl2.helpd": "ឯកសារតូចជាង មានន័យថាការអានពីថាស (disk I/O) តិចជាង និងប្រើ memory តិចជាង។",
    "sl2.cost": "ការបង្ហាប់មានតម្លៃ",
    "sl2.costd": "CPU ត្រូវរំសាយបង្ហាប់រាល់ប្លុក មុននឹងអាចប្រើទិន្នន័យបាន។",
    "sl2.goal": "គោលដៅ៖ ស្វែងរកចំណុចលំនឹង ដែលការសន្សំ I/O ឈ្នះលើតម្លៃនៃការ decode។",

    "sl3.title": "ឧបសគ្គពីរដែលប្រកួតគ្នា",
    "sl3.cpu": "ឧបសគ្គ CPU",
    "sl3.cpud": "ការ decode ច្រើនពេក — processor តាមមិនទាន់។",
    "sl3.disk": "ឧបសគ្គ Disk I/O",
    "sl3.diskd": "ការអានឯកសារធំដែលមិនបង្ហាប់ គឺយឺត។",
    "sl3.point": "ចំណុចលំនឹង",

    "sl4.title": "ការប្រៀបធៀបក្បួនបង្ហាប់",
    "sl4.h1": "ក្បួន",
    "sl4.h2": "អត្រាបង្ហាប់",
    "sl4.h3": "ល្បឿន Decode",
    "sl4.h4": "សម្រាប់",
    "sl4.low": "ទាប",
    "sl4.med": "មធ្យម–ខ្ពស់",
    "sl4.high": "ខ្ពស់",
    "sl4.vhigh": "ខ្ពស់បំផុត",
    "sl4.vfast": "លឿនខ្លាំង",
    "sl4.tune": "លឿន និងលៃតម្រូវបាន",
    "sl4.slow": "យឺត",
    "sl4.vslow": "យឺតបំផុត",
    "sl4.none": "គ្មាន (CSV)",
    "sl4.r1": "ការងារដែលជាប់ CPU",
    "sl4.r2": "តុល្យភាពល្អបំផុត — តារា",
    "sl4.r3": "ការងារដែលជាប់ថាស",
    "sl4.r4": "ការផ្ទុករយៈពេលវែង",
    "sl4.r5": "មូលដ្ឋានមិនបង្ហាប់",

    "sl5.title": "ផ្លូវទិន្នន័យ",

    "sl6.title": "ទាញយក Dataset",
    "sl6.lead": "ទាញយកទិន្នន័យបង្ហាប់ពីឃ្លាំងអនឡាញសាធារណៈ។",
    "sl6.note": "បើអ៊ីនធឺណិតដាច់ ប្រព័ន្ធបង្កើតទិន្នន័យសំយោគ ដើម្បីឲ្យការសាកល្បងនៅដំណើរការបាន។",

    "sl7.title": "ជ្រើសរើសទម្រង់ និងក្បួនបង្ហាប់",
    "sl7.lead": "អ្នកប្រើជ្រើសរើសទម្រង់ columnar ក្បួនបង្ហាប់ និងកម្រិត Zstd ១–២២។",

    "sl8.title": "សរសេរទិន្នន័យបង្ហាប់ទៅថាស",
    "sl8.note": "អត្រាបង្ហាប់ = ទំហំដើម ÷ ទំហំបង្ហាប់។",

    "sl9.title": "CPU រំសាយបង្ហាប់ពេលអាន",
    "sl9.lead": "ទម្រង់ columnar អនុញ្ញាតឲ្យអានតែជួរឈរណាដែលត្រូវការ។",
    "sl9.note": "នេះជាកន្លែងដែលតម្លៃ CPU នៃការបង្ហាប់លេចឡើង។",

    "sl10.title": "ដំណើរការក្នុង Memory",
    "sl10.note": "ការគណនាដូចគ្នាដំណើរការសម្រាប់គ្រប់ក្បួន ដូច្នេះការប្រៀបធៀបមានយុត្តិធម៌។",

    "sl11.title": "ទិន្នន័យវាស់វែងដែលយើងចាប់យក",
    "sl11.m1": "ល្បឿនដំណើរការ",
    "sl11.m1d": "MB/s ដែលដំណើរការបាន",
    "sl11.m2": "ការប្រើ CPU",
    "sl11.m2d": "ភាគរយពេល decode",
    "sl11.m3": "ការរង់ចាំថាស",
    "sl11.m3d": "ភាគរយនៃការឈប់រង់ចាំ I/O",
    "sl11.m4": "Memory អតិបរមា",
    "sl11.m4d": "RAM ដែលប្រើច្រើនបំផុត",
    "sl11.m5": "អត្រាបង្ហាប់",
    "sl11.m5d": "ដើម ÷ បង្ហាប់",

    "sl12.title": "ការស្វែងរកចំណុចលំនឹង",
    "sl12.lead":
      "គូរក្រាហ្វ CPU% ធៀបនឹង រង់ចាំថាស% តាមកម្រិត Zstd។ កន្លែងដែលបន្ទាត់ពីរជួបគ្នា គឺជាចំណុចល្អបំផុត។",

    "sl13.title": "លទ្ធផលដែលបានវាស់",
    "sl13.speed": "ល្បឿនកើនឡើង",
    "sl13.note":
      "វាស់លើកុំព្យូទ័រយួរដៃនេះដែលប្រើ SSD។ លើថាសយឺតជាង អ្នកឈ្នះនឹងប្តូរទៅកម្រិត Zstd ខ្ពស់ជាង។",

    "sl14.title": "អនុសាសន៍",
    "sl14.quote":
      "លើម៉ាស៊ីននេះ LZ4 លើ Parquet ផ្តល់ពេលវេលាល្អបំផុត (លឿនប្រហែល ៨ ដង ធៀបនឹង CSV មិនបង្ហាប់) ព្រោះការ decode មានតម្លៃថោក ហើយឯកសារតូចគ្រប់គ្រាន់ហើយ ដូច្នេះការបង្ហាប់ធ្ងន់ជាងនេះមិនមានប្រយោជន៍ទេ។",
    "sl14.note": "ពេលថាសយឺត ឬទិន្នន័យធំជាងច្រើន Zstd កម្រិត ៣–៩ តែងតែឈ្នះជំនួសវិញ។",

    "sl15.title": "Bcolz ចាស់ហើយ — ប្រើឧបករណ៍ទំនើប",
    "sl15.old": "ចាស់ (Legacy)",
    "sl15.oldd": "លែងមានការអភិវឌ្ឍសកម្មទៀតហើយ",
    "sl15.new": "ជម្រើសទំនើប",
    "sl15.p": "ស្តង់ដារ columnar សម្រាប់ analytics",
    "sl15.a": "លឿនខ្លាំងក្នុង memory",
    "sl15.b": "រំសាយបង្ហាប់បែប multi-thread",
    "sl15.z": "អារេ N-dimensional ជាកំណាត់",

    "sl16.title": "ហេតុអ្វីទ្រឹស្ដីពន្យល់បែបនេះ",
    "sl16.a":
      "ពេលពេលវេលាថាសថយចុះ ការងារ decode ដែលនៅសល់គ្រប់គ្រងពេលវេលាសរុប — ដូច្នេះការបង្ហាប់បន្ថែមលែងជួយ។",
    "sl16.r":
      "សមត្ថភាពត្រូវបានកំណត់ដោយ bandwidth ឬដោយការគណនា។ ក្បួនល្អបំផុតស្ថិតនៅចំណុចកណ្តាលរវាងទាំងពីរ។",
    "sl16.t":
      "ការរំសាយបង្ហាប់បែប multi-thread (Blosc2, Zstd) បង្កើនដែនកំណត់ CPU ដោយប្រើ core ច្រើន។",

    "slApi1.title": "API គឺជាអ្វី?",
    "slApi1.lead":
      "ផ្ទាំងគ្រប់គ្រងនិយាយជាមួយ server តាមពាក្យបញ្ជា HTTP តូចៗ។ Swagger នៅ /docs ឲ្យអ្នកសាកល្បងដោយដៃ។",
    "slApi1.ui": "ផ្ទាំងគេហទំព័រ",
    "slApi1.uid": "ប៊ូតុងលើ dashboard ហៅ API ទាំងនេះ។ ក្រាហ្វអាន /api/state រៀងរាល់ ០.៥ វិនាទី។",
    "slApi1.docs": "Swagger /docs",
    "slApi1.docsd": "បើក /docs ដើម្បីមើល route ទាំងអស់ ផ្ញើសំណើសាកល្បង និងអានចម្លើយ JSON។",
    "slApi1.note": "ទំព័រ៖ GET / (ផ្ទាំងគ្រប់គ្រង) · GET /slides (បទបង្ហាញ) · GET /docs (រុករក API)",

    "slApi2.title": "ពន្យល់ API endpoints",
    "slApi2.h1": "វិធី",
    "slApi2.h2": "ផ្លូវ",
    "slApi2.h3": "ធ្វើអ្វី",
    "slApi2.state": "ស្ថានភាពផ្ទាល់ សារ គំរូ CPU/ថាស និងលទ្ធផលថ្មីៗ",
    "slApi2.results": "JSON តេស្តដែលរក្សាទុក (matrix, sweep, អនុសាសន៍)",
    "slApi2.codecs": "ការណែនាំខ្លីសម្រាប់ក្បួននីមួយៗ (អត្រា ល្បឿន decode ករណីប្រើ)",
    "slApi2.download": "ទាញយក dataset សាធារណៈ (ឬបង្កើតទិន្នន័យសំយោគ)",
    "slApi2.ingest": "សរសេរ + អាន + ដំណើរការ តាមទម្រង់ / ក្បួន / កម្រិតរបស់អ្នក",
    "slApi2.bench": "ដំណើរការ matrix, Zstd sweep ឬតេស្តពេញ — រួចណែនាំមួយល្អបំផុត",

    "sl17.title": "របៀបដំណើរការកម្មវិធី",
    "sl17.s1": "បើក http://127.0.0.1:8000",
    "sl17.s2": "ចុច ទាញយក Dataset",
    "sl17.s3": "ជ្រើសទម្រង់ ក្បួនបង្ហាប់ ហើយអូស slider Zstd",
    "sl17.s4": "ចុច តេស្តពេញលេញ ហើយមើលក្រាហ្វផ្ទាល់",
    "sl17.s5": "អានផ្ទាំងអនុសាសន៍",

    "sl18.kicker": "សេចក្តីសង្ខេប",
    "sl18.title": "តុល្យភាព មិនមែនការបង្ហាប់អតិបរមា",
    "sl18.a": "ការបង្ហាប់ដូរ disk I/O យកការងារ CPU។",
    "sl18.b": "ទម្រង់ columnar អានតែជួរឈរដែលត្រូវការ។",
    "sl18.c": "វាស់ CPU ការរង់ចាំថាស memory និងអត្រាបង្ហាប់ ជាមួយគ្នា។",
    "sl18.d": "ក្បួនល្អបំផុតអាស្រ័យលើថាស និងទិន្នន័យរបស់អ្នក។",
    "sl18.thanks": "សូមអរគុណ — សូមស្វាគមន៍សំណួរ។",
  },
};

Object.assign(I18N.en, SLIDES_I18N.en);
Object.assign(I18N.km, SLIDES_I18N.km);
