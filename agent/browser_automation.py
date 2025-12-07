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


# Remove or comment out the BrowserAutomation class methods that conflict
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


# Standalone async functions for browser automation

async def execute_step(page, step: Dict, step_number: int) -> Dict:
    """Execute a single reproduction step"""
    
    action = step.get("action", "").lower()
    target = step.get("target", "")
    value = step.get("value", "")
    selectors = step.get("selectors", [])
    description = step.get("description", "")
    
    print(f"\n  Step {step_number}: {action.upper()} - {description}")
    
    # Mask sensitive information in logs
    display_target = target
    display_value = value
    if value and ("password" in target.lower() or "password" in description.lower()):
        display_value = "*" * len(value)
    
    print(f"    Target: {display_target}")
    if display_value and action == "fill":
        print(f"    Value: {display_value}")
    
    try:
        if action == "navigate":
            # Navigate to URL
            url = value
            
            if not url or url == "application URL":
                raise Exception(f"Invalid URL: '{url}'. Expected actual URL value.")
            
            print(f"    Navigating to: {url}")
            # Reduced timeout and use domcontentloaded for speed
            await page.goto(url, wait_until="domcontentloaded", timeout=20000)
            # Reduced wait time
            await page.wait_for_timeout(500)
            
            result = {
                "status": "success",
                "message": f"Successfully navigated to {url}"
            }
            
        elif action == "fill":
            # Fill form field
            if not value:
                raise Exception(f"No value provided for fill action on '{target}'")
            
            print(f"    Trying {len(selectors)} selector(s)...")
            result = await execute_fill_action(page, selectors, value, target, step_number)
            
        elif action == "click":
            # Click element
            print(f"    Trying {len(selectors)} selector(s)...")
            result = await execute_click_action(page, selectors, target, step_number)
            
            # After click, wait for any navigation or AJAX
            print(f"    Waiting for page to stabilize after click...")
            await page.wait_for_timeout(500)
            
            try:
                # Wait for network idle or load state
                await page.wait_for_load_state("networkidle", timeout=5000)
                print(f"    ✓ Page stabilized")
            except:
                # If networkidle times out, just wait a bit more
                await page.wait_for_timeout(1500)
                print(f"    ⊙ Timeout waiting for network idle, continuing...")
            
        elif action == "wait":
            # Wait for condition
            wait_time = int(value) if value and str(value).isdigit() else 2000
            print(f"    Waiting for {wait_time}ms")
            await page.wait_for_timeout(wait_time)
            
            # Also wait for network idle if reasonable wait time
            if wait_time >= 1000:
                try:
                    await page.wait_for_load_state("networkidle", timeout=3000)
                except:
                    pass
            
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
    
    # Don't log password values
    is_password = "password" in target.lower()
    display_value = "*" * len(value) if is_password else value
    
    last_error = None
    
    for i, selector in enumerate(selectors, 1):
        try:
            print(f"      [{i}/{len(selectors)}] Trying: {selector}")
            
            # Reduced timeout for faster failure
            await page.wait_for_selector(selector, timeout=3000, state='visible')
            
            # Clear and fill - reduced waits
            await page.fill(selector, '')
            await page.wait_for_timeout(100)
            await page.fill(selector, value)
            await page.wait_for_timeout(100)
            
            # Skip verification for passwords (faster)
            if not is_password:
                entered_value = await page.input_value(selector)
                if entered_value != value:
                    last_error = f"Value mismatch"
                    continue
            
            print(f"      ✓ Success with: {selector}")
            return {
                "status": "success",
                "message": f"Filled '{target}' successfully",
                "selector_used": selector
            }
                
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
            
            # Reduced timeout
            await page.wait_for_selector(selector, timeout=3000, state='visible')
            
            # Click element
            await page.click(selector)
            await page.wait_for_timeout(300)  # Reduced wait
            
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
    """Execute verify action with multiple selector attempts and smart waiting"""
    
    print(f"    Verifying: {target}")
    print(f"    Waiting for page to stabilize...")
    
    # Wait for network to be idle (ensures AJAX/data loading is complete)
    try:
        await page.wait_for_load_state("networkidle", timeout=5000)
    except:
        await page.wait_for_timeout(2000)  # Fallback wait
    
    if not selectors:
        selectors = generate_fallback_selectors(target)
    
    last_error = None
    
    # Try CSS/XPath selectors first
    for i, selector in enumerate(selectors, 1):
        try:
            print(f"      [{i}/{len(selectors)}] Verifying: {selector}")
            
            # Wait for element with reduced timeout
            element = await page.wait_for_selector(selector, timeout=2000)
            
            if element:
                is_visible = await element.is_visible()
                if is_visible:
                    # Get text content
                    text_content = await element.text_content()
                    if text_content:
                        text_content = text_content.strip()
                        print(f"      ✓ Element visible with text: '{text_content}'")
                        
                        # Extract numeric value if present
                        import re
                        numbers = re.findall(r'\d+', text_content)
                        numeric_value = int(numbers[0]) if numbers else None
                        
                        return {
                            "status": "success",
                            "message": f"Element '{target}' found. Content: {text_content}" + 
                                     (f" (Value: {numeric_value})" if numeric_value is not None else ""),
                            "selector_used": selector,
                            "text_content": text_content,
                            "numeric_value": numeric_value
                        }
                    
                    print(f"      ✓ Element visible (no text)")
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
    
    # Strategy 2: XPath text search
    print(f"      Trying XPath text-based search...")
    xpath_patterns = [
        f"//*[contains(text(), '{target}')]",
        f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{target.lower()}')]",
        "//span[contains(@class, 'count')]",
        "//div[contains(@class, 'metric')]",
        "//span[contains(@class, 'stat')]"
    ]
    
    for xpath in xpath_patterns:
        try:
            element = await page.wait_for_selector(f"xpath={xpath}", timeout=1000)
            if element and await element.is_visible():
                text = await element.text_content()
                if text:
                    print(f"      ✓ Found via XPath: '{text.strip()}'")
                    return {
                        "status": "success",
                        "message": f"Found element with text: {text.strip()}",
                        "selector_used": xpath,
                        "text_content": text.strip()
                    }
        except:
            continue
    
    # Strategy 3: Text content search in common elements
    print(f"      Trying comprehensive text search...")
    search_keywords = target.lower().split()
    text_elements = await page.query_selector_all("span, div, h1, h2, h3, p, td, li")
    
    for elem in text_elements[:50]:  # Check first 50 elements
        try:
            if not await elem.is_visible():
                continue
                
            text = await elem.text_content()
            if not text:
                continue
            
            text_lower = text.strip().lower()
            
            # Check if any keyword matches
            if any(keyword in text_lower for keyword in search_keywords):
                print(f"      ✓ Found matching element: '{text.strip()}'")
                
                # Try to extract numeric value
                import re
                numbers = re.findall(r'\d+', text)
                numeric_value = int(numbers[0]) if numbers else None
                
                return {
                    "status": "success",
                    "message": f"Found element containing '{target}': {text.strip()}" +
                             (f" (Value: {numeric_value})" if numeric_value is not None else ""),
                    "text_content": text.strip(),
                    "numeric_value": numeric_value
                }
        except:
            continue
    
    # Strategy 4: Take screenshot and get page content for debugging
    try:
        screenshot_path = f"screenshots/verify_failed_step_{step_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        await page.screenshot(path=screenshot_path, full_page=True)
        print(f"      📸 Debug screenshot: {screenshot_path}")
        
        # Get visible text on page for debugging
        body_text = await page.evaluate("() => document.body.innerText")
        print(f"      Page content preview: {body_text[:200]}...")
        
        # Check if target keywords appear in page text
        if target.lower() in body_text.lower():
            print(f"      ⚠ Target text '{target}' found in page but element not located")
            # Extract surrounding context
            idx = body_text.lower().find(target.lower())
            context = body_text[max(0, idx-50):min(len(body_text), idx+100)]
            
            return {
                "status": "partial",
                "message": f"Text '{target}' found in page content but element not properly located. Context: {context}",
                "text_content": context,
                "screenshot": screenshot_path
            }
    except Exception as e:
        print(f"      ⚠ Debug capture failed: {str(e)}")
    
    # All attempts failed
    raise Exception(f"Verification of '{target}' failed after trying {len(selectors)} selectors and text search. Last error: {last_error}")


def generate_fallback_selectors(target: str) -> List[str]:
    """Generate fallback selectors based on target description"""
    
    selectors = []
    target_lower = target.lower()
    
    # Email/Username field patterns
    if 'email' in target_lower or 'username' in target_lower or 'user' in target_lower:
        selectors.extend([
            "#email", "#username", "#user", "#login-email", "#user-email",
            "input[name='email']", "input[name='username']", "input[name='user']",
            "input[type='email']", "input[type='text']",
            "input[placeholder*='email' i]", "input[placeholder*='username' i]", "input[placeholder*='user' i]",
            ".email-input", ".login-email", ".user-email", ".username-input",
            "input[aria-label*='email' i]", "input[aria-label*='username' i]",
            "input[data-testid='email']", "input[data-testid='username']"
        ])
    
    # Password field patterns
    elif 'password' in target_lower or 'pass' in target_lower:
        selectors.extend([
            "#password", "#passwd", "#pass", "#user-password", "#login-password",
            "input[name='password']", "input[name='passwd']", "input[name='pass']",
            "input[type='password']",
            "input[placeholder*='password' i]", "input[placeholder*='pass' i]",
            ".password-input", ".login-password",
            "input[aria-label*='password' i]",
            "input[data-testid='password']"
        ])
    
    # Button/Submit patterns
    elif 'button' in target_lower or 'submit' in target_lower or 'btn' in target_lower:
        # Extract button text if available (e.g., "login button" -> "login")
        button_text = target_lower.replace('button', '').replace('btn', '').strip()
        
        selectors.extend([
            f"#{button_text}-btn", f"#{button_text}-button", f"#{button_text}",
            "button[type='submit']", "input[type='submit']",
            "button", ".btn", ".button",
            f"button[name='{button_text}']",
            f".{button_text}-button", f".btn-{button_text}"
        ])
        
        # Add text-based selectors if button text is meaningful
        if button_text and len(button_text) > 2:
            selectors.extend([
                f"button:has-text('{button_text.title()}')",
                f"button:has-text('{button_text.upper()}')",
                f"button:has-text('{button_text}')",
                f"a:has-text('{button_text.title()}')"
            ])
    
    # Link patterns
    elif 'link' in target_lower:
        link_text = target_lower.replace('link', '').strip()
        selectors.extend([
            f"a:has-text('{link_text}')", f"a[href*='{link_text}']",
            "a", ".link"
        ])
    
    # Generic element patterns (for verify actions)
    else:
        # Try ID and name first
        selectors.extend([
            f"#{target}", f"#{target.replace(' ', '-')}", f"#{target.replace(' ', '_')}",
            f"[name='{target}']", f"[name='{target.replace(' ', '-')}']"
        ])
        
        # Try class patterns
        selectors.extend([
            f".{target}", f".{target.replace(' ', '-')}", f".{target.replace(' ', '_')}",
            f"[class*='{target}']", f"[class*='{target.replace(' ', '-')}']"
        ])
        
        # Try data attributes
        selectors.extend([
            f"[data-testid='{target}']", f"[data-testid*='{target}']",
            f"[data-id='{target}']", f"[data-name='{target}']"
        ])
        
        # Generic visible elements
        selectors.extend([
            "h1", "h2", "h3", ".metric", ".stat", ".count", ".value",
            "div", "span", "p"
        ])
    
    return selectors


def run_browser_automation(steps: List[Dict], headless: bool = False) -> List[ReproductionStep]:
    """
    Run browser automation with Playwright synchronously
    
    Args:
        steps: List of step dictionaries
        headless: Run in headless mode (False = show browser window)
        
    Returns:
        List of ReproductionStep objects with execution results
    """
    
    async def run_async():
        from playwright.async_api import async_playwright
        
        # Create screenshots directory
        os.makedirs("screenshots", exist_ok=True)
        
        print(f"\n{'='*60}")
        print(f"BROWSER AUTOMATION SETTINGS:")
        print(f"  Headless mode: {headless}")
        print(f"  Browser will {'NOT be visible' if headless else 'be VISIBLE'}")
        print(f"  Speed optimizations: ENABLED")
        print(f"{'='*60}\n")
        
        results = []
        
        async with async_playwright() as p:
            # Launch browser with optimizations
            print(f"Launching Chromium browser (headless={headless})...")
            browser = await p.chromium.launch(
                headless=headless,
                # Optimizations for speed
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                ] + (['--start-maximized'] if not headless else [])
            )
            
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080} if headless else None,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                # Speed optimizations
                ignore_https_errors=True,
            )
            
            # Set default timeout
            context.set_default_timeout(10000)  # 10 seconds default
            
            page = await context.new_page()
            
            print(f"✓ Browser launched successfully")
            
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
