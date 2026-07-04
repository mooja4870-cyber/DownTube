# Oracle Cloud 무료 VM에 DownTube 올리기 (초보자용 단계별)

Oracle Cloud "Always Free" VM은 **평생 무료**다. 여기에 DownTube를 올리면 Mac을 꺼도 24시간 작동한다.
아래 순서를 그대로 따라 하면 된다. (소요: 처음이면 약 30~40분)

> 참고: 이 방식은 cloudflared 터널을 쓰므로 **VM에 들어오는 포트를 열 필요가 없다**(방화벽 설정 불필요).
> 유튜브가 클라우드 IP를 막을 수 있는 점은 감안할 것 → 실패 시 [DEPLOY.md](DEPLOY.md)의 *유튜브 차단 대응* 참고.

---

## 1단계 · Oracle Cloud 계정 만들기

1. https://www.oracle.com/kr/cloud/free/ 접속 → **무료로 시작하기(Start for free)**
2. 이메일 입력 → 인증 메일 확인 → 이름·비밀번호 입력
3. **국가: 대한민국**, 휴대폰 번호 인증(SMS)
4. **홈 리전(Home Region) 선택** — ⚠️ 나중에 못 바꾼다. `South Korea Central (Seoul)` 또는 `Chuncheon` 선택
5. **결제 카드 인증** — Always Free는 요금이 청구되지 않지만 본인 확인용으로 카드가 필요하다(소액 승인 후 취소).
6. 가입 완료 → 잠시 후 콘솔(dashboard) 로그인

## 2단계 · VM(컴퓨트 인스턴스) 만들기

1. 콘솔 왼쪽 위 **≡ 메뉴 → Compute → Instances** → **Create instance**
2. **Name**: `downtube` (아무거나)
3. **Image and shape** 영역:
   - **Image**: Edit → **Canonical Ubuntu** → `22.04` 선택
   - **Shape**: Change shape →
     - 1순위: **Ampere** 탭 → `VM.Standard.A1.Flex` → OCPU **1**, 메모리 **6GB** (Always Free 범위)
     - "Out of capacity" 오류가 뜨면 → **Specialty and previous generation** 또는 **AMD** 탭 → `VM.Standard.E2.1.Micro` (x86, 1GB, 항상 무료) 선택
   - 두 선택지 모두 **"Always Free-eligible"** 라벨이 붙은 것이어야 무료
4. **Add SSH keys**:
   - **Generate a key pair for me** 선택 → **Save private key**(그리고 Save public key)로 키 파일 내려받기 → 잘 보관
   - (이미 SSH 키가 있으면 Paste public key로 붙여넣어도 됨)
5. **Networking**은 기본값 그대로 (별도 포트 개방 불필요)
6. **Create** 클릭 → 1~2분 뒤 상태가 **Running**이 되고 **Public IP address** 가 표시됨 (예: `140.238.x.x`) — 메모

## 3단계 · VM에 접속(SSH)

내려받은 private key로 접속한다. (Mac 터미널 기준)

```bash
chmod 600 ~/Downloads/ssh-key-*.key            # 키 파일 권한
ssh -i ~/Downloads/ssh-key-*.key ubuntu@VM의_공용IP
```

- 처음 접속 시 `yes` 입력. 프롬프트가 `ubuntu@downtube:~$` 로 바뀌면 성공.
- (Ubuntu 기본 사용자 이름은 `ubuntu`)

## 4단계 · Docker 설치

VM 안에서 실행:

```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker ubuntu
exit                                            # 로그아웃
```
다시 SSH 접속(그룹 반영):
```bash
ssh -i ~/Downloads/ssh-key-*.key ubuntu@VM의_공용IP
docker --version                                # 버전 뜨면 OK
```

## 5단계 · Cloudflare API 토큰 발급

고정 주소(KV)를 VM이 갱신하려면 토큰이 필요하다.

1. https://dash.cloudflare.com/profile/api-tokens → **Create Token**
2. **Create Custom Token** → **Get started**
3. **Permissions**: `Account` · `Workers KV Storage` · `Edit` 추가
4. **Continue to summary → Create Token**
5. 나온 토큰 문자열 복사 (이 화면 벗어나면 다시 못 봄)

## 6단계 · DownTube 실행

VM 안에서:

```bash
git clone https://github.com/mooja4870-cyber/DownTube.git
cd DownTube/vm
export CF_API_TOKEN=여기에_복사한_토큰_붙여넣기
docker compose up -d --build
```

- 빌드에 몇 분 걸린다. 완료 후 로그 확인:
  ```bash
  docker compose logs -f
  ```
  `터널 연결됨: https://... → 고정 주소에 반영 완료` 가 보이면 성공. (Ctrl+C로 로그 보기 종료)

## 7단계 · 확인

- 이제 **Mac을 꺼도** 핸드폰 앱(또는 브라우저)에서 고정 주소로 접속하면 작동한다:
  https://downtube.mooja4870.workers.dev
- Mac 쪽 자동 실행은 꺼서 충돌을 막는다(Mac 터미널에서):
  ```bash
  cd ~/project/DownTube && ./cloudflare/uninstall_autostart.sh
  ```

---

## 자주 겪는 문제

- **ARM(A1) "Out of capacity"**: 인기 리전이라 자주 발생. 잠시 후 재시도하거나 5단계에서 `E2.1.Micro`(x86)로 만들면 된다.
- **`docker compose` 명령이 없음**: `sudo apt-get install -y docker-compose-plugin` 후 재시도.
- **다운로드가 "봇 확인" 오류로 실패**: 유튜브의 클라우드 IP 차단. [DEPLOY.md](DEPLOY.md) 하단의 쿠키 우회 참고(요청 시 앱에 쿠키 지원 추가 가능).
- **토큰을 잘못 넣음**: `export CF_API_TOKEN=...` 다시 하고 `docker compose up -d --build --force-recreate`.

## 관리 명령 (VM 안에서, `DownTube/vm` 폴더)

```bash
docker compose logs -f      # 로그 보기
docker compose restart      # 재시작
docker compose down         # 중지
git pull && docker compose up -d --build   # 앱 업데이트 후 재배포
```
