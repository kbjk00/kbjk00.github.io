---
title: "SQL Injection은 뭐야? [Web Hacking]"
date: 2026-02-19 10:21:11 +0900
categories: [Hacking]
tags: ["web hacking"]
---
## 시작하며

SQL Injection은 웹 애플리케이션의 입력 필드에 SQL 코드를 삽입하여 데이터베이스를 조작하는 공격 기법입니다. 이 글에서는 SQL Injection이 어떻게 동작하는지, 어떤 공격 기법이 있는지, 그리고 어떻게 방어하는지를 처음부터 끝까지 다룹니다.

> ⚠️ 주의: 이 글에서 소개하는 기법은 본인이 소유하거나 명시적으로 허가받은 시스템에서만 사용해야 합니다.
> 허가 없이 타인의 시스템에 사용하는 것은 불법입니다.

## 웹 로그인의 동작 원리

SQL Injection을 이해하려면 먼저 웹 로그인이 내부적으로 어떻게 동작하는지 알아야 합니다.

로그인 폼에 아이디와 비밀번호를 입력하고 로그인 버튼을 누르면, 웹 애플리케이션은 다음과 같은 과정을 거칩니다.

```text
사용자가 입력한 아이디와 비밀번호를 백엔드(서버)로 전송
백엔드에서 사용자 입력값을 SQL 쿼리(데이터베이스에 보내는 명령문)에 삽입
데이터베이스가 해당 쿼리를 실행하여 일치하는 계정이 있는지 확인
결과가 참(TRUE)이면 로그인 성공, 거짓(FALSE)이면 로그인 실패를 반환
```

이 과정에서 서버가 실행하는 SQL 쿼리는 보통 다음과 같은 형태입니다.

```sql
SELECT * FROM accounts WHERE username = '입력한_아이디' AND password = '입력한_비밀번호'
```

이 쿼리는 `accounts`라는 테이블에서 아이디와 비밀번호가 모두 일치하는 행(row)을 찾습니다.  
일치하는 행이 있으면 로그인에 성공하고, 없으면 실패합니다.

문제는 사용자가 입력한 값이 쿼리 안의 **따옴표 사이(문자열 영역)**에 그대로 들어간다는 것입니다. 만약 사용자 입력을 아무런 검증 없이 쿼리에 집어넣으면, 사용자가 따옴표를 포함한 SQL 코드를 입력했을 때 쿼리의 구조 자체가 바뀌어 버립니다.

## SQL Injection 취약점 탐지: 따옴표 테스트

SQL Injection이 가능한지 확인하는 가장 기본적인 방법은 입력 필드에 **작은따옴표(`'`)**를 넣어보는 것입니다. 정상적으로 잘못된 아이디를 입력하면 "아이디 또는 비밀번호가 올바르지 않습니다" 같은 일반적인 에러 메시지가 나옵니다. 그런데 따옴표를 입력했을 때 갑자기 다른 형태의 에러 메시지(예: `syntax error`)가 나타난다면, 이 입력 필드는 SQL Injection에 취약할 가능성이 높습니다.

왜 그럴까요? 사용자가 입력한 따옴표가 쿼리 안의 문자열 경계를 깨뜨리기 때문입니다.

```sql
-- 정상 입력: admin
SELECT * FROM accounts WHERE username = 'admin' AND password = '1234'

-- 따옴표 입력: admin'
SELECT * FROM accounts WHERE username = 'admin'' AND password = '1234'
```

두 번째 쿼리에서 따옴표가 하나 더 생기면서 문자열이 올바르게 닫히지 않습니다. SQL 문법에서 문자열(string)은 반드시 두 개의 따옴표 사이에 있어야 하는데, 따옴표가 홀수 개가 되면 SQL 문법 오류가 발생합니다. 이 에러가 사용자에게 노출된다는 것은, 입력값이 SQL 쿼리에 직접 삽입되고 있다는 증거입니다.

> 개발 시 에러 메시지를 너무 자세하게 작성하면 해커에게 유용한 정보를 제공하게 됩니다.  
> 운영 환경에서는 SQL 에러를 사용자에게 직접 노출하지 않아야 합니다.

### 따옴표에는 큰따옴표(`"`)도 있다.

작은따옴표를 넣었는데 아무런 에러가 없다고 해서 취약점이 없는 것은 아닙니다.  
쿼리가 **큰따옴표**로 문자열을 감싸고 있을 수도 있기 때문입니다.

```sql
-- 큰따옴표를 사용하는 쿼리 예시
SELECT * FROM accounts WHERE username = "admin" AND password = "1234"
```

이런 쿼리에서는 작은따옴표를 입력해도 문자열 경계가 깨지지 않아 에러가 발생하지 않습니다.  
이 경우 큰따옴표(`"`)를 입력했을 때 `syntax error`가 나타나면 취약점이 존재하는 것입니다.

## SQL Injection 공격 기법 1 — OR 페이로드

취약점을 발견했다면, 이제 SQL 코드를 삽입하여 인증을 우회할 수 있습니다.  
가장 대표적인 페이로드(공격에 사용하는 입력값)가 `' OR 1=1`입니다.

아이디 필드에 다음과 같이 입력합니다.

```sql
' OR 1=1 --
```

그러면 서버에서 실행되는 쿼리는 다음과 같이 변합니다.

```sql
SELECT * FROM accounts WHERE username = '' OR 1=1 -- ' AND password = '아무거나'
```

이 쿼리에서 `--` 이후의 내용은 전부 주석 처리되어 무시됩니다. 따라서 데이터베이스가 실제로 실행하는 쿼리는 다음과 같습니다.

```sql
-- 실제 실행되는 쿼리 (주석 이후 제거)
SELECT * FROM accounts WHERE username = '' OR 1=1
```

### 왜 이 쿼리가 항상 성공할까?

```text
`username = ''` → 빈 문자열과 일치하는 아이디가 있는가? → 보통 FALSE
`OR 1=1` → 1은 1과 같은가? → 항상 TRUE
```

`OR` 연산은 둘 중 하나만 TRUE이면 전체가 TRUE입니다. `1=1`은 항상 TRUE이므로, 이 WHERE 절은 테이블의 **모든 행**에 대해 TRUE로 평가됩니다.

결과적으로 `accounts` 테이블의 모든 계정 정보가 반환되고, 서버는 보통 그 중 맨 위에 있는 행 하나를 사용하여 로그인을 처리합니다. 데이터베이스에서 맨 위에 있는 계정은 테스트 계정이거나 관리자(admin) 계정인 경우가 많기 때문에, 이 공격으로 관리자 권한을 탈취할 수 있습니다.

쿼리가 큰따옴표를 사용하는 경우에는 작은따옴표 대신 큰따옴표를 사용하면 됩니다.

<br>

```sql
" OR 1=1 --
```

```sql
-- 큰따옴표 기반 쿼리에서 실행되는 결과
SELECT * FROM accounts WHERE username = "" OR 1=1 -- " AND password = "아무거나"
```

## SQL Injection 공격 기법 2 — 주석 처리

주석을 이용한 공격은 OR 페이로드보다 더 단순합니다. SQL에서 `--`(대시 두 개 + 공백)은 주석(comment) 문법으로, 이후의 모든 코드를 무시합니다. MySQL에서는 `#`도 주석 문자로 사용할 수 있습니다.

아이디 필드에 다음과 같이 입력합니다.

```sql
admin'--
```

> 주의: MySQL에서 `--`는 뒤에 **공백이 1개 이상** 있어야 주석으로 인식됩니다.  
> 공백 없이 `--`만 쓰면 주석으로 처리되지 않으니 반드시 `--`(대시 두 개 + 공백)으로 작성하세요.  
> 공백 입력이 번거롭다면 `#`을 사용해도 됩니다.   
> 단, `#` 주석은 **MySQL 전용**으로,  
> MSSQL이나 Oracle 같은 다른 DBMS에서는 동작하지 않습니다.

서버에서 실행되는 쿼리는 다음과 같습니다.

```sql
SELECT * FROM accounts WHERE username = 'admin'-- ' AND password = '아무거나'
```

`--` 이후의 비밀번호 검증 부분이 전부 주석 처리됩니다. 데이터베이스가 실제로 실행하는 쿼리는 다음과 같습니다.

```sql
-- 실제 실행되는 쿼리 (주석 이후 제거)
SELECT * FROM accounts WHERE username = 'admin'
```

아이디만 맞으면 비밀번호 없이 로그인이 됩니다. 비밀번호 검증 로직을 통째로 날려버리는 것입니다.

큰따옴표 기반 쿼리라면 페이로드도 큰따옴표로 바꿉니다.

```sql
admin"--
```

```sql
-- 큰따옴표 기반 쿼리에서 실행되는 결과
SELECT * FROM accounts WHERE username = "admin"-- " AND password = "아무거나"
```

## 공격 기법 3 — UNION SELECT로 데이터 추출

앞의 두 기법이 인증 우회에 초점을 맞췄다면, UNION SELECT는 **데이터베이스의 다른 테이블에서 정보를 빼내는** 기법입니다.

`UNION`은 SQL 문법으로, 두 개의 `SELECT` 문의 결과를 하나로 합쳐줍니다. 단, 두 `SELECT` 문의 컬럼(column) 개수와 데이터 타입이 일치해야 합니다.

예를 들어, 웹사이트에서 URL 파라미터로 작가 번호를 받아 소개 글을 보여주는 페이지가 있다고 가정하겠습니다.

<br>

```text
https://example.com/author?id=1
```

서버에서는 다음과 같은 쿼리가 실행됩니다.

```sql
SELECT name, bio FROM authors WHERE id = 1
```

이 `id` 파라미터에 UNION SELECT를 삽입하면, 원래 쿼리 결과에 다른 테이블의 데이터를 끼워 넣을 수 있습니다.

```text
https://example.com/author?id=1 UNION SELECT username, password FROM accounts --
```

서버에서 실행되는 쿼리는 다음과 같습니다.

```sql
SELECT name, bio FROM authors WHERE id = 1
UNION
SELECT username, password FROM accounts --
```

이 쿼리는 작가 소개 글과 함께 `accounts` 테이블의 사용자 이름과 비밀번호를 한꺼번에 출력합니다. 작가 소개가 표시되어야 할 영역에 계정 정보가 그대로 노출되는 것입니다.

UNION SELECT를 사용하려면 원래 쿼리의 컬럼 개수를 알아야 합니다. 컬럼 개수를 모르면 `UNION SELECT NULL, NULL, NULL...`처럼 NULL을 하나씩 늘려가며 에러가 나지 않는 개수를 찾습니다.

다른 방법으로는 `ORDER BY`를 이용하는 방법이 있습니다. `ORDER BY`는 특정 컬럼을 기준으로 결과를 정렬하는 SQL 문법인데, 컬럼 번호를 숫자로 지정할 수 있습니다.

<br>

```text
https://example.com/author?id=1 ORDER BY 1--
https://example.com/author?id=1 ORDER BY 2--
https://example.com/author?id=1 ORDER BY 3--
```

숫자를 1부터 하나씩 늘려가다가 에러가 발생하는 순간, 그 직전 숫자가 컬럼 개수입니다. 예를 들어 ORDER BY 3에서 에러가 나면 컬럼이 2개라는 뜻입니다.

## SQL Injection 방어 방법

SQL Injection은 오래된 공격이지만 매우 위험한 공격 중 하나입니다. SQL Injection의 근본 원인은 **사용자 입력을 검증 없이 SQL 쿼리에 직접 삽입**하는 것입니다.

### 1. Prepared Statements (Parameterized Queries)

가장 효과적인 방어 방법입니다. 사용자 입력을 쿼리의 일부로 해석하지 않고, 별도의 파라미터로 전달합니다.

```python
# 취약한 코드 (절대 사용 금지)
query = f"SELECT * FROM accounts WHERE username = '{user_input}'"

# 안전한 코드 (Prepared Statement)
query = "SELECT * FROM accounts WHERE username = %s"
cursor.execute(query, (user_input,))
```

취약한 코드는 사용자 입력을 문자열 포맷팅으로 쿼리에 직접 삽입합니다. 이 경우 따옴표나 SQL 코드가 그대로 쿼리에 들어갑니다. 이런 경우 데이터베이스에서 사용자 입력을 명령어의 일부로 오해할 수 있습니다.

안전한 코드는 `%s`를 플레이스홀더(자리 표시자)로 사용하고, 실제 값은 `execute` 함수의 두 번째 인자로 별도 전달합니다. 데이터베이스 드라이버가 입력값을 SQL 코드가 아닌 순수한 데이터로 처리하므로, 어떤 입력을 넣어도 쿼리 구조가 변하지 않습니다.

### 2. 입력 검증 (Input Validation)

사용자 입력에 허용할 문자를 미리 정의하고, 그 외의 문자를 거부하는 방식입니다.

```python
import re

# 허용 목록(Allow List) 방식: 영문, 숫자만 허용
if not re.match(r'^[a-zA-Z0-9]+$', user_input):
    raise ValueError("허용되지 않는 문자가 포함되어 있습니다")
```

이 코드는 사용자 입력이 영문과 숫자로만 구성되어 있는지 확인합니다. 따옴표, 대시, 세미콜론 같은 SQL에서 특별한 의미를 가지는 문자를 원천 차단합니다.

### 3. 이스케이프 처리 (Escape User Input)

사용자 입력에 포함된 특수 문자를 SQL에서 문법으로 해석하지 않도록 이스케이프(무력화) 처리하는 방법입니다. 예를 들어 작은따옴표 `'`를 `\'`로 변환하면, SQL은 이를 문자열의 끝이 아닌 문자 그대로의 따옴표로 인식합니다.

단, 이스케이프 처리만으로는 모든 SQL Injection을 방어하기 어렵습니다. Prepared Statements와 함께 사용하는 것을 권장합니다.

### 4. Stored Procedures

SQL 쿼리를 애플리케이션 코드가 아닌 데이터베이스 내부에 미리 정의해 두고, 애플리케이션은 파라미터만 전달하는 방식입니다. 쿼리 구조가 데이터베이스 안에 고정되어 있으므로 외부에서 조작하기 어렵습니다. 구현 방법은 DB 종류(MySQL, PostgreSQL, Oracle 등)마다 다르므로, 사용 중인 DB의 공식 문서를 참고해주세요.

## SQL Injection 유형 분류

지금까지 다룬 기법들은 SQL Injection의 여러 유형 중 일부입니다. 더 깊이 학습하고 싶다면, 아래 유형별 차이를 알아두면 도움이 됩니다.

| 유형 | 설명 | 특징 |
| --- | --- | --- |
| **Error-based** | 에러 메시지를 통해 정보를 추출하는 방식 | 가장 기초적이고 흔한 유형 |
| **Union-based** | 추가 쿼리로 정보를 추출하는 방식 | 다른 테이블의 데이터를 직접 추출 가능 |
| **Blind SQL Injection** | 서버의 반응을 통해 정보를 추론하는 방식 | 에러 메시지를 숨겨도 공격 가능 |

이 글에서 다룬 따옴표 테스트와 OR/주석 공격은 Error-based에 해당하고, UNION SELECT는 Union-based에 해당합니다.

Blind SQL Injection은 두 가지 방식으로 나뉩니다.

- **Boolean-based Blind**: 참/거짓에 따라 웹 페이지의 응답이 달라지는 것을 이용합니다. 예를 들어 조건이 참이면 정상 페이지가, 거짓이면 빈 페이지가 표시되는 차이를 관찰하여 한 글자씩 데이터를 추론합니다.
- **Time-based Blind**: `SLEEP(5)` 같은 시간 지연 함수를 삽입하여, 조건이 참일 때 응답이 5초 늦어지는지 확인하는 방식입니다. 응답 페이지에 아무런 차이가 없어도 공격이 가능합니다.

<br>

## 마치며

SQL Injection은 1998년에 처음 보고된 이후 20년 넘게 웹 보안의 핵심 위협으로 남아 있습니다. 원리 자체는 단순합니다. 사용자 입력이 SQL 쿼리에 그대로 삽입될 때, 공격자는 따옴표로 문자열 경계를 깨고 원하는 SQL 코드를 주입합니다. OR 페이로드로 인증을 우회하고, 주석으로 검증 로직을 제거하며, UNION SELECT로 데이터를 빼냅니다.

방어의 핵심은 **사용자 입력을 절대 신뢰하지 않는 것**입니다. Prepared Statements를 기본으로 사용하고, 입력 검증과 이스케이프 처리를 병행하면 SQL Injection을 효과적으로 차단할 수 있습니다.
