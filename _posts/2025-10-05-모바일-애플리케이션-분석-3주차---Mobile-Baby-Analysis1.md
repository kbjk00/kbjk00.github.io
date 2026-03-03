---
title: "[모바일 애플리케이션 분석] 3주차 - Mobile Baby Analysis1"
date: 2025-10-05 21:54:48 +0900
categories: [Projects, "모바일 분석"]
tags: [리버싱, 팀프로젝트, "write up", "모바일 분석"]
---

이번 문제는 Mobile Baby Analysis1 이다.

writeup 태그가 없기 때문에

같은 조원들끼리만 공유하도록 비밀글로 작성한다.

---

## JADX 로 분석

JADX 로 MobileBabyAnalysis1.apk 를 분석하였다.

분석의 목적은 정보를 알기 위함이다.

따라서 애플리케이션의 정보가 담긴 AndroidManifest.xml 을 살펴보았다.

```
<meta-data
        android:name="flag"
        android:value="flag{4ndr01d_m4nif35t}"/>
```

AndroidManifest.xml 에서 meta-data 라는 태그 안에 적힌 코드이다.

어떤 뜻인지 알아보자.

android:name 은 아이템 이름을 설정하는 것이다.

여기 있는 아이템 이름은 flag 라는 말이다.

그리고 밑에 있는 android:value 는 아이템에 할당된 값을 설정하는 것이다.

즉, flag 라는 아이템 안에는 flag{4ndr01d\_m4nif35t} 라는 값이 담겨있다.

이 값이 이 문제의 플래그이다.

---

## 후기

이 문제 밑에 적혀있는 문장이 있다.

> The Basics of Mobile App Analytics!

모바일 애플리케이션의 기초 중 하나가 AndroidManifest.xml 을 보는 것이라고 생각한다.

왜냐하면 AndroidManifest.xml 내부에 컴포넌트, 버전 등 애플리케이션의 정보가 저장되기 때문이다.
