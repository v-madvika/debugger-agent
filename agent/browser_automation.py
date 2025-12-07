"""
Browser Automation Module for Bug Reproduction
Uses Playwright for cross-browser automation
"""
import asyncio
import os
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from agent_state import ReproductionStep


class BrowserAutomation:
    """
    Real browser automation for executing bug reproduction steps
    """
    
    def __init__(self, headless: bool = False, browser_type: str = "chromium"):
        self.headless = headless
        self.browser_type = browser_type
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.screenshots_dir = "screenshots"
        self.playwright = None
        
        # Create screenshots directory
        os.makedirs(self.screenshots_dir, exist_ok=True)
    
    async def start(self):
        """Initialize browser"""
        self.playwright = await async_playwright().start()
        
        # Launch browser based on type
        if self.browser_type == "chromium":
            self.browser = await self.playwright.chromium.launch(headless=self.headless)
        elif self.browser_type == "firefox":
            self.browser = await self.playwright.firefox.launch(headless=self.headless)
        elif self.browser_type == "webkit":
            self.browser = await self.playwright.webkit.launch(headless=self.headless)
        else:
            raise ValueError(f"Unknown browser type: {self.browser_type}")
        
        # Create context with reasonable defaults
        self.context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        
        # Create page
        self.page = await self.context.new_page()
        
        print(f"✓ Browser started: {self.browser_type}")
    
    async def stop(self):
        """Close browser"""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        
        print("✓ Browser stopped")
    
    def parse_selector(self, target: str) -> Tuple[str, str]:
        """
        Parse selector string into type and value
        
        Formats:
        - "css:#element-id" -> ("css", "#element-id")
        - "xpath://button" -> ("xpath", "//button")
        - "text:Click Here" -> ("text", "Click Here")
        - "id:submit" -> ("id", "submit")
        - "name:username" -> ("name", "username")
        - "#element-id" -> ("css", "#element-id") [default]
        """
        if not target:
            return ("css", "body")
        
        # Check for explicit type
        if ":" in target:
            parts = target.split(":", 1)
            selector_type = parts[0].lower()
            selector_value = parts[1]
            
            if selector_type in ["css", "xpath", "text", "id", "name"]:
                # Convert id and name to CSS selectors
                if selector_type == "id":
                    return ("css", f"#{selector_value}")
                elif selector_type == "name":
                    return ("css", f"[name='{selector_value}']")
                else:
                    return (selector_type, selector_value)
        
        # Default to CSS
        return ("css", target)
    
# Standalone async functions for browser automation

async def execute_step(page, step: Dict, step_number: int) -> Dict:
    """Execute a single reproduction step"""
    
    action = step.get("action", "").lower()
    target = step.get("target", "")
    value = step.get("value", "")
    selectors = step.get("selectors", [])
    description = step.get("description", "")
    
    print(f"\n  Step {step_number}: {action.upper()} - {description}")
    print(f"    Target: {target}")
    
    try:
        if action == "navigate":
            # Navigate to URL
            url = value  # The URL is in the value field
            
            if not url or url == "application URL":
                raise Exception(f"Invalid URL: '{url}'. Expected actual URL value.")
            
            print(f"    Navigating to: {url}")
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(2000)
            
            result = {
                "status": "success",
                "message": f"Successfully navigated to {url}",
                "screenshot": f"screenshots/step_{step_number}_navigate.png"
            }
            
        elif action == "fill":
            # Fill form field
            if not value:
                raise Exception(f"No value provided for fill action on '{target}'")
            
            # Mask password in logs
            display_value = value
            if "password" in target.lower():
                display_value = "*" * len(value)
            print(f"    Value to fill: {display_value}")
            print(f"    Trying {len(selectors)} selector(s)...")
            
            result = await execute_fill_action(page, selectors, value, target, step_number)
            
        elif action == "click":
            # Click element
            print(f"    Trying {len(selectors)} selector(s)...")
            result = await execute_click_action(page, selectors, target, step_number)
            
        elif action == "wait":
            # Wait for condition
            wait_time = int(value) if value else 2000
            print(f"    Waiting for {wait_time}ms")
            await page.wait_for_timeout(wait_time)
            
            result = {
                "status": "success",
                "message": f"Waited for {wait_time}ms"
            }
            
        elif action == "verify":
            # Verify element or condition
            print(f"    Verifying: {target}")
            result = await execute_verify_action(page, selectors, target, step_number)
            
        elif action == "screenshot":
            # Take screenshot
            screenshot_path = f"screenshots/step_{step_number}_screenshot.png"
            await page.screenshot(path=screenshot_path, full_page=True)
            print(f"    Screenshot saved: {screenshot_path}")
            
            result = {
                "status": "success",
                "message": "Screenshot captured",
                "screenshot": screenshot_path
            }
            
        else:
            raise Exception(f"Unknown action: {action}")
        
        # Take screenshot on success if requested
        if step.get("screenshot", False) and action != "screenshot":
            screenshot_path = f"screenshots/step_{step_number}_success.png"
            await page.screenshot(path=screenshot_path)
            result["screenshot"] = screenshot_path
        
        print(f"    ✓ SUCCESS: {result.get('message', '')}")
        return result
        
    except Exception as e:
        error_msg = str(e)
        print(f"    ✗ FAILED: {error_msg}")
        
        # Take error screenshot
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = f"screenshots/error_step_{step_number}_{timestamp}.png"
        try:
            await page.screenshot(path=screenshot_path)
            print(f"    📸 Error screenshot: {screenshot_path}")
        except:
            pass
        
        return {
            "status": "failed",
            "message": error_msg,
            "screenshot": screenshot_path,
            "error": error_msg
        }


async def execute_fill_action(page, selectors: List[str], value: str, target: str, step_number: int) -> Dict:
    """Execute fill action with multiple selector attempts"""
    
    if not selectors:
        selectors = generate_fallback_selectors(target)
    
    last_error = None
    
    for i, selector in enumerate(selectors, 1):
        try:
            print(f"      [{i}/{len(selectors)}] Trying: {selector}")
            
            # Wait for element
            await page.wait_for_selector(selector, timeout=5000, state='visible')
            
            # Clear and fill
            await page.fill(selector, '')
            await page.wait_for_timeout(200)
            await page.fill(selector, value)
            await page.wait_for_timeout(300)
            
            # Verify
            entered_value = await page.input_value(selector)
            if entered_value == value:
                print(f"      ✓ Success with: {selector}")
                return {
                    "status": "success",
                    "message": f"Filled '{target}' successfully",
                    "selector_used": selector
                }
            else:
                last_error = f"Value mismatch: expected '{value}', got '{entered_value}'"
                
        except Exception as e:
            last_error = str(e)[:100]
            continue
    
    # All selectors failed
    raise Exception(f"Failed to fill '{target}' after {len(selectors)} attempts. Last error: {last_error}")


async def execute_click_action(page, selectors: List[str], target: str, step_number: int) -> Dict:
    """Execute click action with multiple selector attempts"""
    
    if not selectors:
        selectors = generate_fallback_selectors(target)
    
    last_error = None
    
    for i, selector in enumerate(selectors, 1):
        try:
            print(f"      [{i}/{len(selectors)}] Trying: {selector}")
            
            # Wait for element
            await page.wait_for_selector(selector, timeout=5000, state='visible')
            
            # Click element
            await page.click(selector)
            await page.wait_for_timeout(500)
            
            print(f"      ✓ Success with: {selector}")
            return {
                "status": "success",
                "message": f"Clicked '{target}' successfully",
                "selector_used": selector
            }
            
        except Exception as e:
            last_error = str(e)[:100]
            continue
    
    # All selectors failed
    raise Exception(f"Failed to click '{target}' after {len(selectors)} attempts. Last error: {last_error}")


async def execute_verify_action(page, selectors: List[str], target: str, step_number: int) -> Dict:
    """Execute verify action with multiple selector attempts"""
    
    last_error = None
    
    for i, selector in enumerate(selectors, 1):
        try:
            print(f"      [{i}/{len(selectors)}] Verifying: {selector}")
            
            # Wait for element
            element = await page.wait_for_selector(selector, timeout=5000)
            
            if element:
                is_visible = await element.is_visible()
                if is_visible:
                    print(f"      ✓ Element visible")
                    return {
                        "status": "success",
                        "message": f"Element '{target}' is visible",
                        "selector_used": selector
                    }
                else:
                    last_error = f"Element exists but not visible"
            else:
                last_error = f"Element not found"
        
        except Exception as e:
            last_error = str(e)[:100]
            continue
    
    # All selectors failed
    raise Exception(f"Verification of '{target}' failed. Last error: {last_error}")


def generate_fallback_selectors(target: str) -> List[str]:
    """Generate fallback selectors based on target description"""
    
    selectors = []
    target_lower = target.lower()
    
    # Email field patterns
    if 'email' in target_lower or 'username' in target_lower:
        selectors.extend([
            "#email", "#username", "#user", "#login-email",
            "input[name='email']", "input[name='username']",
            "input[type='email']",
            "input[placeholder*='email' i]",
            ".email-input", ".login-email",
            "input[data-testid='email']"
        ])
    
    # Password field patterns
    elif 'password' in target_lower:
        selectors.extend([
            "#password", "#passwd", "#user-password",
            "input[name='password']",
            "input[type='password']",
            "input[placeholder*='password' i]",
            ".password-input",
            "input[data-testid='password']"
        ])
    
    # Button patterns
    elif 'button' in target_lower or 'submit' in target_lower or 'login' in target_lower:
        selectors.extend([
            "button[type='submit']",
            "button:has-text('Log in')",
            "button:has-text('Sign in')",
            "input[type='submit']",
            "#login-button", "#submit",
            ".login-button", ".btn-login"
        ])
    
    # Generic fallback
    else:
        selectors.extend([
            f"#{target}",
            f"[name='{target}']",
            target
        ])
    
    return selectors


def run_browser_automation(steps: List[Dict], headless: bool = False) -> List[ReproductionStep]:
    """
    Run browser automation with Playwright synchronously
    
    Args:
        steps: List of step dictionaries
        headless: Run in headless mode
        
    Returns:
        List of ReproductionStep objects with execution results
    """
    
    async def run_async():
        from playwright.async_api import async_playwright
        
        # Create screenshots directory
        os.makedirs("screenshots", exist_ok=True)
        
        results = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=headless)
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = await context.new_page()
            
            try:
                for step_dict in steps:
                    step_number = step_dict.get("step_number", len(results) + 1)
                    
                    try:
                        # Execute step using standalone function
                        result = await execute_step(page, step_dict, step_number)
                        
                        # Create ReproductionStep object
                        executed_step = ReproductionStep(
                            step_number=step_number,
                            description=step_dict.get("description", ""),
                            action=step_dict.get("action", ""),
                            target=step_dict.get("target", ""),
                            expected_result=step_dict.get("expected_result", ""),
                            status=result.get("status", "failed"),
                            actual_result=result.get("message", ""),
                            error=result.get("error")
                        )
                        
                        results.append(executed_step)
                        
                    except Exception as e:
                        print(f"    ✗ Exception during step execution: {str(e)}")
                        import traceback
                        traceback.print_exc()
                        
                        # Create failed step
                        failed_step = ReproductionStep(
                            step_number=step_number,
                            description=step_dict.get("description", ""),
                            action=step_dict.get("action", ""),
                            target=step_dict.get("target", ""),
                            expected_result=step_dict.get("expected_result", ""),
                            status="failed",
                            actual_result="Step execution failed",
                            error=str(e)
                        )
                        results.append(failed_step)
                
                return results
            finally:
                await browser.close()
    
    # Run the async function
    return asyncio.run(run_async())
