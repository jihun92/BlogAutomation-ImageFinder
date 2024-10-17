# ImageFinder

**ImageFinder**는 Pixabay API를 사용하여 이미지를 검색하고 다운로드할 수 있는 GUI 기반의 애플리케이션입니다. 이 프로그램은 사용자의 홈 디렉토리에 `.ImageFinder` 폴더를 생성하여 설정 파일을 저장하고, 해당 설정 파일을 참조해 이미지를 검색 및 다운로드합니다.

## 목차
- [기능](#기능)
- [설치](#설치)
- [사용법](#사용법)
- [빌드](#빌드)
- [구성 파일 설정](#구성-파일-설정)
- [문제 해결](#문제-해결)

## 기능

- Pixabay API를 사용하여 원하는 키워드로 이미지를 검색
- 검색된 이미지들을 GUI에 표시
- 선택한 이미지를 다운로드
- 클립보드로 이미지를 복사하여 다른 애플리케이션에 바로 붙여넣기 가능
- 한 페이지당 최대 20개의 이미지 표시 (설정 가능)

## 설치

### 요구 사항

- Python 3.8 이상
- 다음 Python 패키지:
  - `requests`
  - `yaml`
  - `Pillow`
  - `tkinter`
  - `pyperclip`
  - `pyinstaller` (빌드용)

### 의존성 설치

다음 명령어로 필요한 패키지를 설치할 수 있습니다:

```bash
pip install requests pyyaml Pillow pyperclip
```

## 사용법

1. **Pixabay API 키 설정**:
   - Pixabay API 키를 먼저 발급받아야 합니다. Pixabay API 키는 [Pixabay](https://pixabay.com/api/docs/)에서 무료로 생성할 수 있습니다.
   - API 키를 얻은 후, 프로그램은 이를 읽기 위해 홈 디렉토리의 `.ImageFinder/pixabay.yaml` 파일을 참조합니다.

2. **설정 파일 구성**:
   - 프로그램 실행 전에, 다음과 같이 설정 파일을 준비하세요:
   - 사용자 홈 디렉토리에 `.ImageFinder` 폴더를 생성하고, 그 안에 `pixabay.yaml` 파일을 아래와 같이 작성합니다:
   
     ```yaml
     YOUR_PIXABAY_API_KEY
     ```

3. **프로그램 실행**:
   - 터미널에서 다음 명령어로 프로그램을 실행합니다:
   
     ```bash
     python src/main.py
     ```

   - 프로그램이 실행되면 검색창이 나타나며, 원하는 키워드를 입력하고 "검색" 버튼을 누르면 관련 이미지들이 표시됩니다.

4. **이미지 다운로드 및 복사**:
   - 검색된 이미지에서 마음에 드는 이미지를 선택하여 다운로드하거나 클립보드로 복사할 수 있습니다.

## 빌드

프로그램을 하나의 실행 파일로 빌드하려면 `pyinstaller`를 사용해야 합니다. 다음 명령어로 빌드할 수 있습니다:

```bash
pyinstaller --onefile --windowed --icon="img/icon-windowed.icns" src/main.py
```

이 명령어는 하나의 실행 파일을 생성하며, 프로그램을 다른 시스템에 배포할 수 있습니다.

### 빌드 후 구성 파일 경로

- 빌드된 실행 파일은 여전히 사용자 홈 디렉토리의 `.ImageFinder/pixabay.yaml` 파일을 참조합니다. 빌드 후에도 이 경로에 설정 파일이 있어야 프로그램이 제대로 동작합니다.

## 구성 파일 설정

프로그램은 홈 디렉토리의 `.ImageFinder` 폴더에 있는 `pixabay.yaml` 파일을 통해 API 키를 불러옵니다.

구성 파일 예시는 다음과 같습니다:

```yaml
YOUR_PIXABAY_API_KEY
```

## 문제 해결

1. **설정 파일을 찾을 수 없다는 오류**:
   - 설정 파일 경로가 올바르게 설정되었는지 확인하세요. 홈 디렉토리에 `.ImageFinder/pixabay.yaml` 파일이 있어야 합니다.

2. **API 키가 잘못되었다는 오류**:
   - 올바른 API 키를 사용하고 있는지 확인하세요. Pixabay에서 발급받은 API 키를 `pixabay.yaml` 파일에 정확히 입력해야 합니다.

3. **이미지가 검색되지 않음**:
   - 인터넷 연결 상태를 확인하고, Pixabay API 서버가 정상 작동 중인지 확인하세요.