exports.handler = async (event) => {
  const params = event.queryStringParameters || {};
  const q = params.q || "";
  const sl = params.sl || "auto";
  const tl = params.tl || "uz";

  const corsHeaders = {
    "Content-Type": "application/json; charset=utf-8",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type"
  };

  if (event.httpMethod === "OPTIONS") {
    return { statusCode: 204, headers: corsHeaders, body: "" };
  }

  if (!q.trim()) {
    return {
      statusCode: 400,
      headers: corsHeaders,
      body: JSON.stringify({ error: "Bo'sh matn kiritildi", translatedText: "" })
    };
  }

  // Tier 1: Google NMT
  try {
    const gUrl = `https://translate.googleapis.com/translate_a/single?client=gtx&sl=${encodeURIComponent(sl)}&tl=${encodeURIComponent(tl)}&dt=t&q=${encodeURIComponent(q)}`;
    const res = await fetch(gUrl, {
      headers: {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
      }
    });
    if (res.ok) {
      const gData = await res.json();
      if (Array.isArray(gData) && Array.isArray(gData[0])) {
        const translatedText = gData[0].map(s => (s && s[0]) ? s[0] : "").join("");
        const detectedLang = gData[2] || (sl !== "auto" ? sl : "unknown");
        return {
          statusCode: 200,
          headers: corsHeaders,
          body: JSON.stringify({
            success: true,
            translatedText,
            detectedLang,
            engine: "google-nmt"
          })
        };
      }
    }
  } catch(e) {
    console.warn("Serverless Google NMT failed:", e);
  }

  // Tier 2: MyMemory fallback
  try {
    const pair = (sl === "auto" ? "en" : sl) + "|" + tl;
    const mUrl = `https://api.mymemory.translated.net/get?q=${encodeURIComponent(q)}&langpair=${encodeURIComponent(pair)}`;
    const mRes = await fetch(mUrl);
    if (mRes.ok) {
      const mData = await mRes.json();
      if (mData && mData.responseData && mData.responseData.translatedText) {
        return {
          statusCode: 200,
          headers: corsHeaders,
          body: JSON.stringify({
            success: true,
            translatedText: mData.responseData.translatedText,
            detectedLang: sl,
            engine: "mymemory"
          })
        };
      }
    }
  } catch(e) {}

  return {
    statusCode: 200,
    headers: corsHeaders,
    body: JSON.stringify({
      success: false,
      translatedText: q,
      detectedLang: sl,
      error: "Barcha tarjima dvigatellari band"
    })
  };
};
