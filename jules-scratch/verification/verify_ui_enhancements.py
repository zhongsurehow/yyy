from playwright.sync_api import sync_playwright, expect

def run_verification(playwright):
    """
    This script verifies the new UI enhancements for the Tianji Bian web application.
    - It checks that the new Game Fund and Celestial Card panels are visible.
    - It takes a screenshot of the initial, fully-rendered UI.
    """
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()

    try:
        # 1. Navigate to the application
        page.goto("http://127.0.0.1:5000")

        # 2. Wait for the initial game state to load and verify new elements.
        # Check for the Game Fund display
        expect(page.locator("#game-fund-info")).to_contain_text("奖金池:", timeout=10000)
        expect(page.locator("#game-fund-info")).not_to_contain_text("?", timeout=10000)

        # Check for the Celestial Cards panel
        expect(page.locator("#celestial-stem-card .card-name")).not_to_have_text("-", timeout=10000)
        expect(page.locator("#celestial-branch-card .card-name")).not_to_have_text("-", timeout=10000)

        # Check that player hands are rendered
        expect(page.locator("#player1-hand")).not_to_be_empty()
        expect(page.locator("#player2-hand")).not_to_be_empty()

        # 3. Take a screenshot for visual confirmation.
        screenshot_path = "jules-scratch/verification/ui_enhancements.png"
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