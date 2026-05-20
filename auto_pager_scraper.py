import os
import time
import pandas as pd
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

load_dotenv()


def _build_driver(headless: bool) -> webdriver.Chrome:
    options = Options()
    if headless:
        options.add_argument("--headless")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    return webdriver.Chrome(options=options)


def _click_all_load_more(
    driver: webdriver.Chrome,
    wait: WebDriverWait,
    button_selector: str,
    max_clicks: int,
) -> None:
    for click_count in range(1, max_clicks + 1):
        try:
            button = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, button_selector))
            )
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", button)
            print(f"🔄 {click_count}回目の『もっと見る』を展開しました...")
            time.sleep(3)
        except Exception:
            print("✅ これ以上『もっと見る』ボタンはありません。全件展開完了！")
            break


def main() -> None:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    url = os.getenv("TARGET_URL")
    output_file = os.path.join(base_dir, os.getenv("OUTPUT_CSV", "all_items.csv"))
    button_selector = os.getenv("BUTTON_SELECTOR")
    item_selector = os.getenv("ITEM_SELECTOR")
    max_clicks = int(os.getenv("MAX_CLICKS", 50))
    headless = os.getenv("HEADLESS", "False").lower() == "true"
    save_debug = os.getenv("SAVE_DEBUG_HTML", "False").lower() == "true"

    driver = _build_driver(headless)
    wait = WebDriverWait(driver, 10)

    try:
        print(f"🚀 アクセス中: {url}")
        driver.get(url)

        _click_all_load_more(driver, wait, button_selector, max_clicks)

        if save_debug:
            debug_path = os.path.join(base_dir, "debug_full_page.html")
            with open(debug_path, "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            print(f"📝 調査用のHTMLを保存しました: {debug_path}")

        print("📊 データ抽出を開始します...")
        items = driver.find_elements(By.CSS_SELECTOR, item_selector)
        products = []
        for item in items:
            text_lines = item.text.split("\n")
            if any(text_lines):
                products.append({"Raw_Data": " | ".join(text_lines)})

        df = pd.DataFrame(products)
        df.to_csv(output_file, index=False, encoding="utf-8-sig")
        print(f"🎉 完了！合計 {len(df)} 件のデータを {output_file} に保存しました。")

    except Exception as e:
        print(f"❌ 予期せぬエラーが発生しました: {e}")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
