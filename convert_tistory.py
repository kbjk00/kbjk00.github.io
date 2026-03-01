import re
import shutil
from pathlib import Path

from bs4 import BeautifulSoup
import markdownify as md_lib

BACKUP_DIR = Path("TistoryBackup")
POSTS_DIR = Path("_posts")
IMAGES_DIR = Path("assets/img")


def strip_emoji(text):
    emoji_pattern = re.compile(
        "["
        "\U0001F300-\U0001F9FF"
        "\U0001FA00-\U0001FA6F"
        "\U0001FA70-\U0001FAFF"
        "\u2600-\u26FF"
        "\u2700-\u27BF"
        "\uFE00-\uFE0F"
        "\u200D"
        "]+",
        flags=re.UNICODE,
    )
    return emoji_pattern.sub("", text).strip()


def get_slug_from_filename(html_file):
    name = html_file.stem  # e.g. "1-[모바일-애플리케이션-분석]-1주차---환경-구축"
    name = re.sub(r"^\d+-", "", name)   # remove leading "1-"
    name = name.replace("[", "").replace("]", "")
    return name


def parse_categories(cat_text):
    cats = []
    for part in cat_text.split("/"):
        clean = strip_emoji(part).strip()
        # 이모지가 ?로 대체된 경우 앞쪽 비문자 제거 (첫 한글/영문자부터 시작)
        match = re.search(r"[A-Za-z\uAC00-\uD7A3]", clean)
        if match:
            clean = clean[match.start():]
        if clean:
            cats.append(clean)
    return cats


def parse_tags(tags_text):
    tags = []
    for tag in tags_text.split("#"):
        clean = tag.strip().replace("-", " ").strip()
        if clean:
            tags.append(clean)
    return tags


def preprocess_content(content_div, date_str, slug):
    # 1. opengraph 카드 → 일반 링크로 변환
    for fig in content_div.find_all("figure", attrs={"data-ke-type": "opengraph"}):
        url = fig.get("data-og-source-url", "")
        title = fig.get("data-og-title", url).replace("\xa0", " ").strip()
        if url:
            new_tag = BeautifulSoup(f'<p><a href="{url}">{title}</a></p>', "html.parser")
            fig.replace_with(new_tag)
        else:
            fig.decompose()

    # 2. 이미지 src 경로 교체
    for img in content_div.find_all("img"):
        src = img.get("src", "")
        if src.startswith("./img/"):
            filename = src[len("./img/"):]
            img["src"] = f"/assets/img/{date_str}-{slug}/{filename}"
            img["alt"] = ""

    # 3. 코드블록 언어 클래스 추가 (markdownify 인식용)
    for pre in content_div.find_all("pre", attrs={"data-ke-type": "codeblock"}):
        lang = pre.get("data-ke-language", "")
        code_tag = pre.find("code")
        if code_tag and lang:
            code_tag["class"] = [f"language-{lang}"]

    # 4. 불필요한 wrapper 제거
    for span in content_div.find_all("span", attrs={"data-lightbox": True}):
        span.unwrap()
    for figcap in content_div.find_all("figcaption"):
        if not figcap.get_text(strip=True):
            figcap.decompose()
    for fig in content_div.find_all("figure", class_="imageblock"):
        fig.unwrap()


def to_markdown(content_div):
    result = md_lib.markdownify(
        str(content_div),
        heading_style="ATX",
        bullets="-",
        strip=["div"],
    )
    # &nbsp; 제거
    result = result.replace("\xa0", " ").replace("&nbsp;", " ")
    # 연속 빈줄 정리
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result.strip()


def format_yaml_list(items):
    if not items:
        return "[]"
    parts = []
    for item in items:
        # 공백/특수문자 포함 시 따옴표
        if re.search(r'[\s,\[\]{}#&*!|>\'":%@`]', item):
            parts.append(f'"{item}"')
        else:
            parts.append(item)
    return "[" + ", ".join(parts) + "]"


def convert_post(folder_num):
    folder = BACKUP_DIR / str(folder_num)
    html_files = list(folder.glob("*.html"))
    if not html_files:
        print(f"  [SKIP] 폴더 {folder_num}: HTML 없음")
        return None

    html_file = html_files[0]

    with open(html_file, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    title_el = soup.find("h2", class_="title-article")
    date_el = soup.find("p", class_="date")
    cat_el = soup.find("p", class_="category")
    tags_el = soup.find("div", class_="tags")

    if not title_el or not date_el:
        print(f"  [ERROR] 폴더 {folder_num}: 메타데이터 누락")
        return None

    title = title_el.get_text(strip=True)
    date = date_el.get_text(strip=True)    # "2025-09-21 23:27:20"
    date_str = date[:10]                   # "2025-09-21"

    categories = parse_categories(cat_el.get_text()) if cat_el else []
    tags = parse_tags(tags_el.get_text()) if tags_el else []

    slug = get_slug_from_filename(html_file)

    # 이미지 복사
    src_img_dir = folder / "img"
    if src_img_dir.exists():
        dest_img_dir = IMAGES_DIR / f"{date_str}-{slug}"
        dest_img_dir.mkdir(parents=True, exist_ok=True)
        for img_file in src_img_dir.iterdir():
            if img_file.is_file():
                shutil.copy2(img_file, dest_img_dir / img_file.name)

    # 본문 변환
    content_div = soup.find("div", class_="contents_style")
    if not content_div:
        print(f"  [ERROR] 폴더 {folder_num}: 본문 없음")
        return None

    preprocess_content(content_div, date_str, slug)
    markdown_content = to_markdown(content_div)

    # title 따옴표 이스케이프
    safe_title = title.replace('"', '\\"')

    front_matter = (
        f'---\n'
        f'title: "{safe_title}"\n'
        f'date: {date} +0900\n'
        f'categories: {format_yaml_list(categories)}\n'
        f'tags: {format_yaml_list(tags)}\n'
        f'---\n\n'
        f'{markdown_content}\n'
    )

    post_filename = f"{date_str}-{slug}.md"
    post_path = POSTS_DIR / post_filename
    with open(post_path, "w", encoding="utf-8") as f:
        f.write(front_matter)

    print(f"  [OK] {post_filename}")
    return post_filename


if __name__ == "__main__":
    print("티스토리 → Jekyll 변환 시작...\n")
    POSTS_DIR.mkdir(exist_ok=True)
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    success = 0
    total = 0
    for i in range(1, 26):
        folder = BACKUP_DIR / str(i)
        if not folder.exists():
            print(f"  [SKIP] 폴더 {i}: 없음")
            continue
        total += 1
        result = convert_post(i)
        if result:
            success += 1

    print(f"\n완료! {success}/{total}개 포스트 변환됨.")
