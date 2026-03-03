---
title: "[모바일 애플리케이션 분석] 3주차 - Mobile Baby Analysis2"
date: 2025-10-05 22:58:48 +0900
categories: [Projects, "모바일 분석"]
tags: []
---
이번에 풀어볼 문제는 저번 Mobile Baby Analysis1 에 이어서

Mobile Baby Analysis2 이다.

---

## JADX 로 분석

먼저 힌트를 살펴보자.

> What can a screen consist of?

스크린은 무엇으로 구성될 수 있는지 질문하고 있다.

스크린을 구성하는 컴포넌트는 Activity 이다.

그러니 Activity 를 살펴보겠다.

<br>

```
<activity

            android:name="mobilehacking.kr.mobilebabyanalysis2.MainActivity"

            android:exported="true">

            <intent-filter>

                <action android:name="android.intent.action.MAIN"/>

                <category android:name="android.intent.category.LAUNCHER"/>

            </intent-filter>

            <meta-data

                android:name="android.app.lib_name"

                android:value=""/>

        </activity>
```

AndroidManifest.xml 에서 Activity 태그를 찾았다.

내부 코드를 살펴서 mobilehacking.kr.mobilebabyanalysis2.MainActivity 에서 시작한다는 것을 알았으니,

이 곳으로 이동하였다.

<br>

```
public static final boolean onCreate$lambda$0(MainActivity this$0, MenuItem item) {
        Intrinsics.checkNotNullParameter(this$0, "this$0");
        Intrinsics.checkNotNullParameter(item, "item");
        switch (item.getItemId()) {
            case R.id.nav_feed /* 2131231024 */:
                this$0.replaceFragment(new FeedFragment());
                break;
            case R.id.nav_messages /* 2131231025 */:
                this$0.replaceFragment(new MessageFragment());
                break;
            case R.id.nav_notifications /* 2131231026 */:
                this$0.replaceFragment(new NotificationFragment());
                break;
            case R.id.nav_profile /* 2131231027 */:
                this$0.replaceFragment(new ProfileFragment());
                break;
        }
        return true;
    }
```

MainActivity 의 일부분이다.

이 코드를 보면 아이템의 ID 에 따라서

Feed, Message, Notification, ProfileFragment 로 나누었다.

<br>

각각 4개의 Fragment 를 확인해보면 단서를 찾을 수 있을 것이다.

```
const-string v0, "flag{fr4gm3n7_"
```

FeedFragment 에서 하나,

```
private final String secretPart4 = "fr4gm3nt5}";
```

MessageFragment 에서 하나,

```
private final String secretPart3 = "1n_4ndr01d_";
```

NotificationFragment 에서 하나,

```
private final String secretPart2 = "h1dd3n_";
```

ProfileFragment 에서 하나로,

총 4개의 단서를 발견하였다.

따라서 최종 플래그는 flag{fr4gm3n7\_h1dd3n\_1n\_4ndr01d\_fr4gm3nt5} 이다.

<br>

---

## 후기

컴포넌트 중 Activity 를 사용한 문제로, 2주차에 배운 컴포넌트를 복습할 수 있어서 좋았다.

이번 애플리케이션을 화면을 4개의 Fragment 로 나누었고, 그 안에 플래그 조각들을 숨겨서

애플리케이션을 실행해도 플래그와 관련한 것을 아무것도 볼 수 없어서 조금 당황했다.

<br>
