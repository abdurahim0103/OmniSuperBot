export default async (request) => {
  const reqUrl = new URL(request.url);
  const q = reqUrl.searchParams.get("q") || "";
  const sl = reqUrl.searchParams.get("sl") || "auto";
  const tl = reqUrl.searchParams.get("tl") || "uz";

  const corsHeaders = {
    "Content-Type": "application/json; charset=utf-8",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Cache-Control": "public, max-age=1800"
  };

  if (request.method === "OPTIONS") {
    return new Response(null, { status: 204, headers: corsHeaders });
  }

  if (!q.trim()) {
    return new Response(JSON.stringify({ error: "Bo'sh matn kiritildi", translatedText: "", detectedLang: "auto" }), {
      status: 400,
      headers: corsHeaders
    });
  }

  // Tier 1: Google Translate NMT Engine
  try {
    const gUrl = `https://translate.googleapis.com/translate_a/single?client=gtx&sl=${encodeURIComponent(sl)}&tl=${encodeURIComponent(tl)}&dt=t&q=${encodeURIComponent(q)}`;
    const gRes = await fetch(gUrl, {
      headers: {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
      }
    });

    if (gRes.ok) {
      const gData = await gRes.json();
      if (Array.isArray(gData) && Array.isArray(gData[0])) {
        const translatedText = gData[0].map(s => (s && s[0]) ? s[0] : "").join("");
        const detectedLang = gData[2] || (sl !== "auto" ? sl : "unknown");
        return new Response(JSON.stringify({
          success: true,
          translatedText,
          detectedLang,
          engine: "google-nmt"
        }), {
          status: 200,
          headers: corsHeaders
        });
      }
    }
  } catch (err) {
    console.warn("Edge Google NMT error:", err);
  }

  // Tier 2: MyMemory Gateway Fallback
  try {
    const pair = (sl === "auto" ? "en" : sl) + "|" + tl;
    const mUrl = `https://api.mymemory.translated.net/get?q=${encodeURIComponent(q)}&langpair=${encodeURIComponent(pair)}`;
    const mRes = await fetch(mUrl);
    if (mRes.ok) {
      const mData = await mRes.json();
      if (mData && mData.responseData && mData.responseData.translatedText) {
        return new Response(JSON.stringify({
          success: true,
          translatedText: mData.responseData.translatedText,
          detectedLang: sl,
          engine: "mymemory"
        }), {
          status: 200,
          headers: corsHeaders
        });
      }
    }
  } catch (err) {
    console.warn("Edge MyMemory error:", err);
  }

  return new Response(JSON.stringify({
    success: false,
    error: "Tarjima xizmati vaqtincha band",
    translatedText: q,
    detectedLang: sl
  }), {
    status: 502,
    headers: corsHeaders
  });
};
