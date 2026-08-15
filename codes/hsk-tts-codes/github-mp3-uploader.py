import os
import sys
import time
import base64
import getpass
import requests
from pathlib import Path

# ============================================================
# GitHub MP3 Bulk Uploader
#
# - 로컬 Git 사용 안 함
# - git init / clone / add / commit / push 전혀 사용 안 함
# - GitHub GraphQL API 사용
# - MP3 바이너리 안전 업로드
# - 이미 GitHub에 있는 파일 자동 skip
# - 150개씩 묶어서 commit
# - 중간에 중단해도 다시 실행하면 이어서 진행
# ============================================================

# ------------------------------------------------------------
# 기본 설정
# ------------------------------------------------------------

OWNER = "sujinohkor"
REPO = "cloudflare-sujinohkor.pages.dev"

BRANCH = "main"

# GitHub 내부 경로
TARGET_DIR = "codes/hsk-tts"

# 한 번의 GitHub commit에 넣을 파일 수
BATCH_SIZE = 150

# API 오류 재시도
MAX_RETRIES = 6

# 정상 요청 사이 잠깐 대기
REQUEST_DELAY = 0.5

GRAPHQL_URL = "https://api.github.com/graphql"
REST_URL = "https://api.github.com"


# ------------------------------------------------------------
# 출력
# ------------------------------------------------------------

def info(message):
    print(f"[INFO] {message}")


def success(message):
    print(f"[OK]   {message}")


def warning(message):
    print(f"[WARN] {message}")


def error(message):
    print(f"[ERROR] {message}")


# ------------------------------------------------------------
# GitHub API 요청
# ------------------------------------------------------------

def graphql_request(token, query, variables):

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Python-GitHub-MP3-Uploader",
    }

    payload = {
        "query": query,
        "variables": variables,
    }

    for attempt in range(1, MAX_RETRIES + 1):

        try:

            response = requests.post(
                GRAPHQL_URL,
                headers=headers,
                json=payload,
                timeout=180,
            )

            # Rate limit / temporary server error
            if response.status_code in (429, 500, 502, 503, 504):

                if attempt == MAX_RETRIES:
                    response.raise_for_status()

                wait = min(60, 2 ** attempt)

                warning(
                    f"GitHub API {response.status_code} "
                    f"오류. {wait}초 후 재시도..."
                )

                time.sleep(wait)
                continue

            response.raise_for_status()

            data = response.json()

            if "errors" in data:

                messages = []

                for e in data["errors"]:
                    messages.append(
                        e.get("message", str(e))
                    )

                raise RuntimeError(
                    "GraphQL 오류:\n" +
                    "\n".join(messages)
                )

            return data["data"]

        except requests.RequestException as e:

            if attempt == MAX_RETRIES:
                raise

            wait = min(60, 2 ** attempt)

            warning(
                f"네트워크 오류: {e}"
            )

            warning(
                f"{wait}초 후 재시도 "
                f"{attempt}/{MAX_RETRIES}"
            )

            time.sleep(wait)

    raise RuntimeError("GitHub API 요청 실패")


# ------------------------------------------------------------
# GitHub Repository 상태 확인
# ------------------------------------------------------------

def get_repository_state(token):

    query = """
    query($owner: String!, $repo: String!, $branch: String!) {
      repository(owner: $owner, name: $repo) {
        name
        nameWithOwner

        ref(qualifiedName: $branch) {
          name
          target {
            oid
          }
        }
      }
    }
    """

    variables = {
        "owner": OWNER,
        "repo": REPO,
        "branch": f"refs/heads/{BRANCH}",
    }

    data = graphql_request(
        token,
        query,
        variables,
    )

    repository = data["repository"]

    if repository is None:
        raise RuntimeError(
            "Repository를 찾을 수 없습니다."
        )

    ref = repository["ref"]

    if ref is None:
        raise RuntimeError(
            f"Branch를 찾을 수 없습니다: {BRANCH}"
        )

    return {
        "name": repository["name"],
        "nameWithOwner": repository["nameWithOwner"],
        "head_oid": ref["target"]["oid"],
    }


# ------------------------------------------------------------
# 현재 GitHub 폴더의 파일 목록
#
# REST Tree API 사용
# 파일 내용은 다운로드하지 않음
# ------------------------------------------------------------

def get_remote_files(token):

    url = (
        f"{REST_URL}/repos/"
        f"{OWNER}/{REPO}/git/trees/"
        f"{BRANCH}?recursive=1"
    )

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2026-03-10",
        "User-Agent": "Python-GitHub-MP3-Uploader",
    }

    for attempt in range(1, MAX_RETRIES + 1):

        try:

            response = requests.get(
                url,
                headers=headers,
                timeout=120,
            )

            if response.status_code in (
                429,
                500,
                502,
                503,
                504,
            ):

                if attempt == MAX_RETRIES:
                    response.raise_for_status()

                wait = min(60, 2 ** attempt)

                warning(
                    f"Tree API {response.status_code}. "
                    f"{wait}초 후 재시도..."
                )

                time.sleep(wait)
                continue

            response.raise_for_status()

            data = response.json()

            if data.get("truncated"):
                raise RuntimeError(
                    "GitHub Tree 응답이 truncated 상태입니다."
                )

            result = set()

            for item in data.get("tree", []):

                if item.get("type") != "blob":
                    continue

                path = item.get("path", "")

                if path.startswith(TARGET_DIR + "/"):
                    result.add(path)

            return result

        except requests.RequestException as e:

            if attempt == MAX_RETRIES:
                raise

            wait = min(60, 2 ** attempt)

            warning(
                f"네트워크 오류: {e}"
            )

            time.sleep(wait)

    raise RuntimeError(
        "Remote 파일 목록 조회 실패"
    )


# ------------------------------------------------------------
# 로컬 MP3 검색
# ------------------------------------------------------------

def get_local_mp3_files(source_folder):

    root = Path(source_folder).resolve()

    if not root.exists():
        raise RuntimeError(
            f"폴더가 존재하지 않습니다: {root}"
        )

    if not root.is_dir():
        raise RuntimeError(
            f"폴더가 아닙니다: {root}"
        )

    files = []

    for path in root.rglob("*"):

        if not path.is_file():
            continue

        if path.suffix.lower() != ".mp3":
            continue

        files.append(path)

    files.sort(
        key=lambda p: str(p).lower()
    )

    return root, files


# ------------------------------------------------------------
# GitHub 경로 생성
# ------------------------------------------------------------

def github_path(root, file_path):

    relative = file_path.relative_to(root)

    relative_str = str(relative).replace(
        os.sep,
        "/"
    )

    return f"{TARGET_DIR}/{relative_str}"


# ------------------------------------------------------------
# Base64 변환
# ------------------------------------------------------------

def encode_mp3(file_path):

    with open(file_path, "rb") as f:
        data = f.read()

    return base64.b64encode(data).decode("ascii")


# ------------------------------------------------------------
# GraphQL Commit
# ------------------------------------------------------------

COMMIT_MUTATION = """
mutation(
    $repositoryNameWithOwner: String!,
    $branchName: String!,
    $expectedHeadOid: GitObjectID!,
    $message: String!,
    $additions: [FileAddition!]
) {

    createCommitOnBranch(
        input: {
            branch: {
                repositoryNameWithOwner: $repositoryNameWithOwner
                branchName: $branchName
            }

            expectedHeadOid: $expectedHeadOid

            message: {
                headline: $message
            }

            fileChanges: {
                additions: $additions
            }
        }
    ) {

        commit {
            oid
            url
        }

        ref {
            name
            target {
                oid
            }
        }
    }
}
"""


# ------------------------------------------------------------
# 한 Batch Commit
# ------------------------------------------------------------

def upload_batch(
    token,
    files,
    root,
    head_oid,
    batch_number,
    total_batches,
):

    additions = []

    total_size = 0

    for file_path in files:

        github_file_path = github_path(
            root,
            file_path,
        )

        size = file_path.stat().st_size

        total_size += size

        info(
            f"  준비: "
            f"{file_path.name} "
            f"({size / 1024:.1f} KB)"
        )

        contents = encode_mp3(
            file_path
        )

        additions.append({
            "path": github_file_path,
            "contents": contents,
        })

    message = (
        f"Add HSK TTS MP3 batch "
        f"{batch_number}/{total_batches}"
    )

    variables = {
        "repositoryNameWithOwner":
            f"{OWNER}/{REPO}",

        "branchName":
            BRANCH,

        "expectedHeadOid":
            head_oid,

        "message":
            message,

        "additions":
            additions,
    }

    print()
    info(
        f"GitHub에 Batch "
        f"{batch_number}/{total_batches} 업로드..."
    )

    data = graphql_request(
        token,
        COMMIT_MUTATION,
        variables,
    )

    result = data[
        "createCommitOnBranch"
    ]

    commit = result["commit"]

    return {
        "oid": commit["oid"],
        "url": commit["url"],
        "size": total_size,
    }


# ------------------------------------------------------------
# 메인
# ------------------------------------------------------------

def main():

    print()
    print("=" * 70)
    print(" GitHub HSK-TTS MP3 Bulk Uploader")
    print("=" * 70)
    print()

    print(
        "Repository:"
        f" {OWNER}/{REPO}"
    )

    print(
        "GitHub path:"
        f" {TARGET_DIR}/"
    )

    print(
        "Branch:"
        f" {BRANCH}"
    )

    print(
        "Batch size:"
        f" {BATCH_SIZE} files / commit"
    )

    print()

    # --------------------------------------------------------
    # Token
    # --------------------------------------------------------

    token = getpass.getpass(
        "GitHub Fine-grained PAT 입력: "
    ).strip()

    if not token:
        raise RuntimeError(
            "GitHub Token이 비어 있습니다."
        )

    # --------------------------------------------------------
    # Local folder
    # --------------------------------------------------------

    source = input(
        "MP3가 들어있는 로컬 폴더 경로: "
    ).strip()

    if (
        len(source) >= 2
        and source.startswith('"')
        and source.endswith('"')
    ):
        source = source[1:-1]

    root, local_files = get_local_mp3_files(
        source
    )

    print()

    success(
        f"로컬 MP3 발견: "
        f"{len(local_files):,}개"
    )

    # --------------------------------------------------------
    # Remote state
    # --------------------------------------------------------

    info(
        "현재 GitHub 상태 확인 중..."
    )

    state = get_repository_state(
        token
    )

    success(
        f"Repository: "
        f"{state['nameWithOwner']}"
    )

    info(
        f"현재 main HEAD: "
        f"{state['head_oid']}"
    )

    # --------------------------------------------------------
    # Remote files
    # --------------------------------------------------------

    info(
        "GitHub의 기존 hsk-tts 파일 확인 중..."
    )

    remote_files = get_remote_files(
        token
    )

    success(
        f"GitHub에 현재 존재하는 파일: "
        f"{len(remote_files):,}개"
    )

    # --------------------------------------------------------
    # 이미 올라간 파일 제외
    # --------------------------------------------------------

    pending_files = []

    for file_path in local_files:

        path = github_path(
            root,
            file_path,
        )

        if path in remote_files:
            continue

        pending_files.append(
            file_path
        )

    already_uploaded = (
        len(local_files)
        - len(pending_files)
    )

    print()
    print("-" * 70)

    print(
        f"로컬 MP3 전체       : "
        f"{len(local_files):,}개"
    )

    print(
        f"이미 GitHub에 존재  : "
        f"{already_uploaded:,}개"
    )

    print(
        f"이번에 업로드       : "
        f"{len(pending_files):,}개"
    )

    print("-" * 70)

    if not pending_files:

        success(
            "업로드할 새로운 MP3가 없습니다."
        )

        return

    # --------------------------------------------------------
    # 예상 Batch
    # --------------------------------------------------------

    total_batches = (
        len(pending_files)
        + BATCH_SIZE
        - 1
    ) // BATCH_SIZE

    print()
    print(
        f"예상 Commit 수: "
        f"{total_batches:,}개"
    )

    print()
    print(
        "주의: 각 Batch는 하나의 GitHub commit으로 "
        "생성됩니다."
    )

    print(
        "중간에 프로그램을 종료해도 이미 완료된 "
        "Batch는 유지됩니다."
    )

    print()

    confirm = input(
        "정말 업로드를 시작할까요? "
        "(YES 입력): "
    ).strip()

    if confirm != "YES":
        print(
            "업로드를 취소했습니다."
        )
        return

    # --------------------------------------------------------
    # Upload
    # --------------------------------------------------------

    start_time = time.time()

    head_oid = state["head_oid"]

    uploaded_count = 0
    uploaded_bytes = 0

    for batch_index in range(
        total_batches
    ):

        start = (
            batch_index * BATCH_SIZE
        )

        end = min(
            start + BATCH_SIZE,
            len(pending_files)
        )

        batch = pending_files[
            start:end
        ]

        batch_number = (
            batch_index + 1
        )

        print()
        print()
        print("=" * 70)

        print(
            f" BATCH "
            f"{batch_number}/{total_batches}"
        )

        print(
            f" 파일 "
            f"{start + 1:,} ~ {end:,}"
        )

        print("=" * 70)

        result = upload_batch(
            token=token,
            files=batch,
            root=root,
            head_oid=head_oid,
            batch_number=batch_number,
            total_batches=total_batches,
        )

        # 다음 commit의 parent
        head_oid = result["oid"]

        uploaded_count += len(batch)

        uploaded_bytes += result["size"]

        elapsed = (
            time.time()
            - start_time
        )

        percent = (
            uploaded_count
            / len(pending_files)
            * 100
        )

        speed = (
            uploaded_count
            / max(elapsed, 1)
        )

        remaining = (
            len(pending_files)
            - uploaded_count
        )

        eta_seconds = (
            remaining
            / max(speed, 0.001)
        )

        print()
        success(
            f"Batch {batch_number} 완료"
        )

        print(
            f"진행률 : "
            f"{uploaded_count:,} / "
            f"{len(pending_files):,} "
            f"({percent:.1f}%)"
        )

        print(
            f"업로드 용량 : "
            f"{uploaded_bytes / 1024 / 1024:.2f} MB"
        )

        print(
            f"속도 : "
            f"{speed:.2f} files/sec"
        )

        print(
            f"예상 남은 시간 : "
            f"{eta_seconds / 60:.1f}분"
        )

        print(
            f"Commit : "
            f"{result['oid']}"
        )

        print(
            f"URL : "
            f"{result['url']}"
        )

        # ----------------------------------------------------
        # API 안정화
        # ----------------------------------------------------

        time.sleep(
            REQUEST_DELAY
        )

    # --------------------------------------------------------
    # 완료
    # --------------------------------------------------------

    elapsed = (
        time.time()
        - start_time
    )

    print()
    print()
    print("=" * 70)
    print(" 업로드 완료")
    print("=" * 70)

    print()
    print(
        f"업로드 파일 : "
        f"{uploaded_count:,}개"
    )

    print(
        f"업로드 용량 : "
        f"{uploaded_bytes / 1024 / 1024:.2f} MB"
    )

    print(
        f"소요 시간 : "
        f"{elapsed / 60:.2f}분"
    )

    print()
    print(
        f"https://github.com/"
        f"{OWNER}/{REPO}/tree/"
        f"{BRANCH}/{TARGET_DIR}"
    )

    print()
    success(
        "모든 업로드가 완료되었습니다."
    )


# ------------------------------------------------------------
# 실행
# ------------------------------------------------------------

if __name__ == "__main__":

    try:
        main()

    except KeyboardInterrupt:

        print()
        warning(
            "사용자가 업로드를 중단했습니다."
        )

        print(
            "다시 실행하면 이미 GitHub에 올라간 "
            "파일은 자동으로 건너뜁니다."
        )

        sys.exit(1)

    except Exception as e:

        print()
        error(
            f"업로드 실패: {e}"
        )

        print()
        print(
            "다시 실행해도 기존에 성공한 파일은 "
            "자동으로 건너뛰도록 되어 있습니다."
        )

        sys.exit(1)
