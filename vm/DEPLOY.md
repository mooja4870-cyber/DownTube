# 클라우드 VM 배포 — Mac 없이 24시간 작동

Mac을 꺼도 되도록, 다운로드 서버를 클라우드 VM에서 24시간 돌린다.
핸드폰 앱/브라우저는 지금과 똑같이 고정 주소(https://downtube.mooja4870.workers.dev)로 접속한다.

> ⚠️ **중요**: 유튜브는 클라우드/데이터센터 IP를 봇으로 감지해 다운로드를 막는 경우가 많다.
> VM에서 "Sign in to confirm you're not a bot" 류 오류로 다운로드가 실패하면 맨 아래 *유튜브 차단 대응*을 참고.

---

## 1. VM 준비

- Ubuntu 22.04+ VM 하나 (RAM 1GB 이상 권장).
  - 무료: **Oracle Cloud Always Free** → 계정 생성부터 배포까지 초보자용 단계별: [ORACLE_SETUP.md](ORACLE_SETUP.md)
  - 유료: Hetzner·Vultr·DigitalOcean 등 월 수천 원대 VPS
- 이 저장소를 VM에 복제:
  ```bash
  git clone https://github.com/mooja4870-cyber/DownTube.git
  cd DownTube
  ```

## 2. Docker 설치 (Ubuntu)

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER   # 로그아웃 후 재로그인
```

## 3. Cloudflare API 토큰 만들기

고정 주소(KV)를 VM이 갱신하려면 토큰이 필요하다.

1. https://dash.cloudflare.com/profile/api-tokens → **Create Token**
2. **Create Custom Token** → 권한에 **Account · Workers KV Storage · Edit** 추가
3. 생성된 토큰 문자열을 복사

## 4. 실행

```bash
export CF_API_TOKEN=붙여넣은_토큰
cd vm
docker compose up -d --build
```

- 1~2분 뒤 로그에서 `터널 연결됨 ... → 고정 주소에 반영 완료` 확인:
  ```bash
  docker compose logs -f
  ```
- 이제 핸드폰에서 고정 주소로 접속하면 **Mac이 꺼져 있어도** 작동한다.

## 관리

```bash
docker compose logs -f      # 로그
docker compose restart      # 재시작
docker compose down         # 중지 (고정 주소는 "서버 꺼짐" 안내 표시)
docker compose up -d --build --pull always   # 코드 업데이트 후 재배포
```

VM은 재부팅되어도 `restart: unless-stopped` 정책으로 컨테이너가 자동 재시작된다.

## Mac 자동 실행과 함께 쓰지 말 것

VM과 Mac(`install_autostart.sh`) 둘 다 켜 두면 고정 주소(KV)를 서로 자기 터널로 덮어써 충돌한다.
VM으로 옮겼다면 Mac에서는 `./cloudflare/uninstall_autostart.sh` 로 자동 실행을 끈다.

## 유튜브 차단 대응 (다운로드가 실패할 때)

VM(클라우드 IP)에서 봇 감지로 막히면:
1. 브라우저에서 로그인한 유튜브 쿠키를 내보내(`cookies.txt`) VM에 두고 yt-dlp에 전달하는 방식으로 상당 부분 우회 가능.
2. 또는 가정용 IP를 쓰는 방법(집 저전력 기기 배포)이 가장 확실하다.

필요하면 쿠키 지원을 앱에 추가할 수 있으니 요청 바람.
