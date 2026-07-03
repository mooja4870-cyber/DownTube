/**
 * DownTube 고정 주소 워커.
 * Mac 서버의 현재 터널 주소(run.sh --tunnel 이 KV에 기록)를 읽어 302로 넘겨준다.
 * 워커 주소는 고정이므로 핸드폰(APK/브라우저)에는 이 주소만 등록하면 된다.
 */
export default {
  async fetch(request, env) {
    const target = await env.TUNNEL.get("url");
    if (!target) {
      return new Response(
        "DownTube 서버가 꺼져 있습니다.\nMac에서 ./run.sh --tunnel 을 실행한 뒤 다시 접속해 주세요.",
        { status: 503, headers: { "content-type": "text/plain; charset=utf-8" } },
      );
    }
    const url = new URL(request.url);
    return Response.redirect(target + url.pathname + url.search, 302);
  },
};
