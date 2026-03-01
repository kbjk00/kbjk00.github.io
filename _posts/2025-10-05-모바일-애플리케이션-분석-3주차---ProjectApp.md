---
title: "[모바일 애플리케이션 분석] 3주차 - ProjectApp"
date: 2025-10-05 16:03:23 +0900
categories: ["? Projects", "? 모바일 분석"]
tags: [리버싱, 팀프로젝트, 워게임, "write up", "모바일 분석"]
---

apk 파일을 분석하기 위해서 JADX 를 사용하였다.

만약 설치되어 있지 않다면, 1주차 환경설정 블로그를 보고 오기를 추천한다.

<https://sec-ret.tistory.com/1>

[[모바일 애플리케이션 분석] 1주차 - 환경 설정](https://sec-ret.tistory.com/1)

---

## 애플리케이션 설치 후 실행

apk 파일을 이용해, 애플리케이션을 설치한 후 실행하였다.

터미널에서 설치하고자 하는 apk 파일이 있는 경로로 이동한다.

그 후 adb install app\_name.apk 형식으로 입력을 하면 설치가 된다.

```
PS D:\My_Projects\Mobile_Analysis\WarGame\ProjectApp.apk> adb install ProjectApp.apk
Performing Streamed Install
Success
```

![](/assets/img/2025-10-05-모바일-애플리케이션-분석-3주차---ProjectApp/img.png)

ProjectApp 실행 모습

이 애플리케이션은 입력을 할 수 있는 창과

SERIAL CHECK 라는 버튼이 있다.

올바른 시리얼을 입력하면 플래그를 출력하는 애플리케이션으로 추측한다.

---
