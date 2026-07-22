export async function onRequestPost(context) {
  try {
    const { request, env } = context;
    const { message } = await request.json();

    // Cloudflare 대시보드에 설정한 GEMINI_API_KEY 사용
    const apiKey = env.GEMINI_API_KEY;
    if (!apiKey) {
      return new Response(JSON.stringify({ error: "API 키가 설정되지 않았습니다." }), { status: 500 });
    }

    // Gemini API 호출 (gemini-2.5-flash 모델 사용)
    const response = await fetch(
      `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${apiKey}`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          contents: [{ parts: [{ text: message }] }]
        })
      }
    );

    const data = await response.json();
    
    // Gemini 응답 텍스트 추출
    const replyText = data.candidates?.[0]?.content?.parts?.[0]?.text || "답변을 가져오지 못했습니다.";

    return new Response(JSON.stringify({ reply: replyText }), {
      headers: { "Content-Type": "application/json" }
    });
  } catch (error) {
    return new Response(JSON.stringify({ error: error.message }), { status: 500 });
  }
}
