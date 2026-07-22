export async function onRequestPost(context) {
  try {
    const { request, env } = context;
    const { message } = await request.json();

    // 1. API 키 확인
    const apiKey = env.GEMINI_API_KEY;
    if (!apiKey) {
      return new Response(JSON.stringify({ error: "Cloudflare 대시보드에 GEMINI_API_KEY가 설정되지 않았습니다." }), { status: 500 });
    }

    // 2. Gemini API 호출 (gemini-1.5-flash 적용)
    const geminiUrl = `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${apiKey}`;
    
    const response = await fetch(geminiUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        contents: [{ parts: [{ text: message }] }]
      })
    });

    const data = await response.json();

    // 3. 구글 API 자체에서 에러를 반환한 경우
    if (!response.ok) {
      console.error("Gemini API Error:", data);
      return new Response(JSON.stringify({ 
        error: `Gemini API 오류 (${response.status}): ${data.error?.message || "알 수 없는 오류"}` 
      }), { status: 500 });
    }

    // 4. 정상 응답 추출
    const replyText = data.candidates?.[0]?.content?.parts?.[0]?.text || "답변을 가져오지 못했습니다.";

    return new Response(JSON.stringify({ reply: replyText }), {
      headers: { "Content-Type": "application/json" }
    });

  } catch (error) {
    return new Response(JSON.stringify({ error: "서버 내부 오류: " + error.message }), { status: 500 });
  }
}
