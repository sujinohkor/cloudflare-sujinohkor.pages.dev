export async function onRequestPost(context) {
  try {
    const { request, env } = context;
    const { message } = await request.json();

    const apiKey = env.GEMINI_API_KEY;
    if (!apiKey) {
      return new Response(JSON.stringify({ error: "Cloudflare 대시보드에 GEMINI_API_KEY가 설정되지 않았습니다." }), { status: 500 });
    }

    // 최신 @google/genai SDK 표준 모델: gemini-2.5-flash / gemini-2.0-flash
    // v1beta 엔드포인트 + models/ 경로 규격 적용
    const geminiUrl = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${apiKey}`;

    const response = await fetch(geminiUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        contents: [
          {
            role: "user",
            parts: [{ text: message }]
          }
        ]
      })
    });

    const data = await response.json();

    if (!response.ok) {
      return new Response(JSON.stringify({ 
        error: `Gemini API 오류 (${response.status}): ${data.error?.message || "알 수 없는 오류"}` 
      }), { status: response.status });
    }

    // 최신 응답 구조에서 텍스트 추출
    const replyText = data.candidates?.[0]?.content?.parts?.[0]?.text || "답변을 가져오지 못했습니다.";

    return new Response(JSON.stringify({ reply: replyText }), {
      headers: { "Content-Type": "application/json" }
    });

  } catch (error) {
    return new Response(JSON.stringify({ error: "서버 내부 오류: " + error.message }), { status: 500 });
  }
}
