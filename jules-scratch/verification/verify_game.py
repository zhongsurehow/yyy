from playwright.sync_api import sync_playwright, expect

def run_verification(playwright):
    """
    This script verifies the main functionalities of the Tianji Bian web application.
    It now includes console message logging to debug the frontend.
    """
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()

    # --- Event Listener for Console Messages ---
    def log_console_message(msg):
        print(f"Browser Console: {msg.text}")

    page.on("console", log_console_message)

    try:
        # 1. Navigate to the application
        page.goto("http://127.0.0.1:5000")

        # 2. Wait for the initial game state to load.
        # This is the part that has been failing. We'll use the log to see why.
        expect(page.locator("#phase-info")).to_have_text("阶段: SETUP", timeout=15000)
        expect(page.locator("#player1-health")).to_have_text("100", timeout=10000)
        expect(page.locator("#player1-hand")).not_to_be_empty()

        # 3. Click "Start Game"
        start_button = page.get_by_role("button", name="开始游戏")
        expect(start_button).to_be_enabled()
        start_button.click()

        # 4. Verify that the game has advanced.
        expect(page.locator("#phase-info")).to_have_text("阶段: TIME")

        # 5. Take a screenshot for visual confirmation.
        screenshot_path = "jules-scratch/verification/verification.png"
        page.screenshot(path=screenshot_path)
        print(f"Screenshot saved to {screenshot_path}")

    except Exception as e:
        print(f"An error occurred during Playwright execution: {e}")
        page.screenshot(path="jules-scratch/verification/error.png")

    finally:
        browser.close()

if __name__ == "__main__":
    with sync_playwright() as playwright:
        run_verification(playwright)