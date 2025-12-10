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
            
            # Detect if this is a state-changing action (needs longer wait)
            is_state_changing = any(word in target.lower() for word in 
                ['complete', 'submit', 'delete', 'update', 'save', 'create', 'add', 'remove'])
            
            # Detect if this is a tab/navigation click
            is_tab_click = 'tab' in target.lower() or 'nav' in target.lower()
            
            if is_state_changing:
                print(f"    ⚡ State-changing action detected - waiting for server response")
                await page.wait_for_timeout(2000)  # Give server time to process
            elif is_tab_click:
                print(f"    ⚡ Tab navigation detected - waiting for content")
                await page.wait_for_timeout(1000)  # Give tab content time to load
            else:
                await page.wait_for_timeout(500)  # Standard wait
            
            try:
                # Wait for network idle or load state
                await page.wait_for_load_state("networkidle", timeout=5000)
                print(f"    ✓ Page stabilized")
            except:
                # If networkidle times out, wait a bit more
                additional_wait = 2000 if is_state_changing else 1000
                await page.wait_for_timeout(additional_wait)
                print(f"    ⊙ Timeout waiting for network idle, waited {additional_wait}ms")
        
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
            
            # Add extra wait before verification to ensure data is loaded
            print(f"    ⚡ Pre-verification wait - ensuring data is loaded")
            await page.wait_for_timeout(1500)
            
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
    """Execute click action with multiple selector attempts, prioritizing context-specific selectors"""
    
    if not selectors:
        selectors = generate_fallback_selectors(target)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_selectors = []
    for selector in selectors:
        if selector not in seen:
            seen.add(selector)
            unique_selectors.append(selector)
    
    selectors = unique_selectors
    
    print(f"    Attempting to click: {target}")
    print(f"    Strategy: Try context-specific selectors first, generic last")
    
    # Special handling for tab/navigation clicks - add extra wait
    is_tab_click = 'tab' in target.lower() or 'nav' in target.lower()
    if is_tab_click:
        print(f"    ⚡ Tab/navigation click detected - adding extra wait time")
        await page.wait_for_timeout(1000)  # Extra wait for tabs to be ready
    
    last_error = None
    
    for i, selector in enumerate(selectors, 1):
        try:
            print(f"      [{i}/{len(selectors)}] Trying: {selector}")
            
            # For tabs, use longer timeout
            timeout = 5000 if is_tab_click else 3000
            
            await page.wait_for_selector(selector, timeout=timeout, state='visible')
            
            # Get all matching elements
            elements = await page.query_selector_all(selector)
            
            if not elements:
                last_error = f"Selector matched but no elements found"
                continue
            
            print(f"      Found {len(elements)} matching element(s)")
            
            # If multiple elements match, we need to be more careful
            if len(elements) > 1:
                is_generic = selector in ["button", ".btn", ".button", "button[type='button']", "button[type='submit']", "a"]
                
                if is_generic:
                    print(f"      ⚠ Warning: Generic selector matched {len(elements)} elements - may click wrong one!")
                else:
                    print(f"      ℹ Context-specific selector, using first match")
            
            # Click the first matching element
            element = elements[0]
            
            # Verify element is visible before clicking
            is_visible = await element.is_visible()
            if not is_visible:
                last_error = f"Element found but not visible"
                continue
            
            # Get element text for confirmation
            try:
                element_text = await element.text_content()
                print(f"      Clicking element with text: '{element_text.strip() if element_text else '(no text)'}'")
            except:
                pass
            
            # Click element
            await element.click()
            
            # For tabs, wait longer for content to load
            if is_tab_click:
                print(f"      Waiting for tab content to load...")
                await page.wait_for_timeout(1500)  # Extra wait for tab content
            else:
                await page.wait_for_timeout(300)
            
            print(f"      ✓ Success with: {selector}")
            return {
                "status": "success",
                "message": f"Clicked '{target}' successfully",
                "selector_used": selector
            }
            
        except Exception as e:
            last_error = str(e)[:100]
            print(f"      ✗ Selector failed: {last_error}")
            continue
    
    # All selectors failed - provide helpful debugging info
    error_msg = f"Failed to click '{target}' after {len(selectors)} attempts."
    print(f"    ✗ {error_msg}")
    print(f"    Last error: {last_error}")
    
    # Take debug screenshot and try to find similar elements
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = f"screenshots/click_failed_step_{step_number}_{timestamp}.png"  # FIX: Complete the line
        await page.screenshot(path=screenshot_path, full_page=True)
        print(f"    📸 Debug screenshot: {screenshot_path}")
        
        # Try to find buttons on the page for debugging
        all_buttons = await page.query_selector_all("button, a[role='button'], input[type='button'], input[type='submit']")
        print(f"    Found {len(all_buttons)} clickable elements on page")
        
        # Show first few button texts
        for idx, btn in enumerate(all_buttons[:10]):
            try:
                btn_text = await btn.text_content()
                btn_visible = await btn.is_visible()
                if btn_text and btn_visible:
                    print(f"      - Button {idx+1}: '{btn_text.strip()}'")
            except:
                continue
                
    except Exception as e:
        print(f"      ⚠ Debug failed: {str(e)}")
    
    raise Exception(f"{error_msg} Last error: {last_error}")


async def execute_verify_action(page, selectors: List[str], target: str, step_number: int) -> Dict:
    """Execute verify action with multiple selector attempts and smart waiting, supports context-specific verification"""
    
    print(f"    Verifying: {target}")
    print(f"    Waiting for page to stabilize...")
    
    # Wait for network to be idle (ensures AJAX/data loading is complete)
    try:
        await page.wait_for_load_state("networkidle", timeout=5000)
    except:
        await page.wait_for_timeout(2000)  # Fallback wait
    
    if not selectors:
        selectors = generate_fallback_selectors(target)
    
    # Extract context from target if present
    import re
    context_match = re.search(r"['\"]([^'\"]*)['\"]", target)
    context_text = context_match.group(1) if context_match else None
    
    # Extract location/tab information if present
    location_match = re.search(r"in (?:the )?(\w+) (tab|section|area)", target.lower())
    expected_location = location_match.group(1) if location_match else None
    
    if context_text:
        print(f"      🎯 Context-specific verification: Looking for '{context_text}' in target '{target}'")
    if expected_location:
        print(f"      📍 Expected location: '{expected_location}' tab/section")
    
    last_error = None
    found_elements = []
    
    # If we have BOTH context and location, we need strict validation
    if context_text and expected_location:
        print(f"      ⚠ STRICT MODE: Must find '{context_text}' specifically in '{expected_location}' location")
        
        # Strategy: Search ONLY in the specified tab/section
        # First, verify we're on the correct tab
        try:
            # Check if the tab is active
            active_tab_selectors = [
                f"a.nav-link.active:has-text('{expected_location.title()}')",
                f"//a[contains(@class, 'nav-link') and contains(@class, 'active')][contains(., '{expected_location.title()}')]",
                f"[role='tab'][aria-selected='true']:has-text('{expected_location.title()}')"
            ]
            
            tab_verified = False
            for tab_sel in active_tab_selectors:
                try:
                    tab_elem = await page.query_selector(tab_sel)
                    if tab_elem and await tab_elem.is_visible():
                        print(f"      ✓ Confirmed on '{expected_location}' tab")
                        tab_verified = True
                        break
                except:
                    continue
            
            if not tab_verified:
                print(f"      ⚠ Warning: Could not confirm '{expected_location}' tab is active")
        except Exception as e:
            print(f"      ⚠ Tab verification failed: {str(e)}")
        
        # Now search for the context text ONLY in visible tab content
        context_found = False
        context_patterns = [
            # Search in active tab pane
            f"//div[contains(@class, 'tab-pane') and contains(@class, 'active')]//h5[contains(., '{context_text}')]",
            f"//div[contains(@class, 'tab-pane') and contains(@class, 'active')]//*[contains(., '{context_text}')]",
            f"//div[@role='tabpanel' and not(contains(@style, 'display: none'))]//h5[contains(., '{context_text}')]",
            f"//div[@role='tabpanel' and not(contains(@style, 'display: none'))]//*[contains(., '{context_text}')]",
            # Generic visible containers
            f"//h5[contains(., '{context_text}') and not(ancestor::*[contains(@style, 'display: none')])]",
            f"//*[contains(., '{context_text}') and not(ancestor::*[contains(@style, 'display: none')])]",
        ]
        
        for pattern in context_patterns[:4]:  # Try first 4 (most specific)
            try:
                elements = await page.query_selector_all(f"xpath={pattern}")
                for elem in elements:
                    if not await elem.is_visible():
                        continue
                    
                    elem_text = await elem.text_content()
                    if elem_text and context_text in elem_text:
                        # Double-check it's not from the wrong tab by checking ancestors
                        is_in_wrong_tab = await page.evaluate(
                            """(el) => {
                                const tabPane = el.closest('.tab-pane');
                                if (tabPane && tabPane.classList.contains('active')) return false;
                                if (tabPane && !tabPane.classList.contains('active')) return true;
                                return false;
                            }""",
                            elem
                        )
                        
                        if is_in_wrong_tab:
                            print(f"      ⊘ Found '{context_text}' but in INACTIVE tab - MISMATCH")
                            continue
                        
                        print(f"      ✓ Found '{context_text}' in active '{expected_location}' content")
                        context_found = True
                        
                        return {
                            "status": "success",
                            "message": f"Verified: Found '{context_text}' in '{expected_location}' tab: {elem_text.strip()[:100]}",
                            "selector_used": pattern,
                            "text_content": elem_text.strip(),
                            "context": context_text,
                            "location": expected_location,
                            "location_verified": True
                        }
            except Exception as e:
                print(f"      Pattern failed: {str(e)[:50]}")
                continue
        
        # If we reach here, context was NOT found in the expected location
        if not context_found:
            # Check if it exists in other tabs (wrong location)
            print(f"      ⊗ Checking if '{context_text}' exists in OTHER locations...")
            
            all_matches = await page.query_selector_all(f"//h5[contains(., '{context_text}')] | //*[contains(text(), '{context_text}')]")
            other_location_count = 0
            
            for match in all_matches[:5]:
                if await match.is_visible():
                    other_location_count += 1
                    match_text = await match.text_content()
                    print(f"        - Found in different location: {match_text.strip()[:50]}")
            
            # Return failure with location mismatch
            return {
                "status": "failed",
                "message": f"LOCATION MISMATCH: '{context_text}' NOT found in '{expected_location}' tab " +
                         (f"(found in {other_location_count} other location(s))" if other_location_count > 0 else "(not found anywhere)"),
                "selector_used": "location_validation",
                "text_content": f"Expected in '{expected_location}' but not present",
                "context": context_text,
                "location": expected_location,
                "location_verified": False,
                "location_mismatch": True
            }
    
    # Original strategies for non-location-specific verification
    # Strategy 1: Try provided selectors first
    for i, selector in enumerate(selectors, 1):
        try:
            print(f"      [{i}/{len(selectors)}] Verifying: {selector}")
            
            element = await page.wait_for_selector(selector, timeout=2000)
            
            if element:
                is_visible = await element.is_visible()
                if is_visible:
                    text_content = await element.text_content()
                    if text_content:
                        text_content = text_content.strip()
                        
                        # If we have context, validate it's in the text
                        if context_text and context_text not in text_content:
                            print(f"      ⊘ Found element but doesn't contain '{context_text}'")
                            continue
                        
                        print(f"      ✓ Element visible with text: '{text_content}'")
                        
                        # Extract numeric value if present
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
    
    # Strategy 2: Context-specific verification with location validation
    if context_text:
        print(f"      Trying context-specific verification for '{context_text}'...")
        
        # Find all elements containing the context text
        context_patterns = [
            # Header-based search
            f"//h5[contains(., '{context_text}')]/ancestor::div[1]",
            f"//h4[contains(., '{context_text}')]/ancestor::div[1]",
            f"//h3[contains(., '{context_text}')]/ancestor::div[1]",
            # Card/container search
            f"//div[contains(@class, 'card')][.//*[contains(., '{context_text}')]]",
            f"//div[contains(@class, 'task')][.//*[contains(., '{context_text}')]]",
            f"//li[contains(., '{context_text}')]",
            f"//tr[contains(., '{context_text}')]",
        ]
        
        for pattern in context_patterns:
            try:
                containers = await page.query_selector_all(f"xpath={pattern}")
                for container in containers:
                    if not await container.is_visible():
                        continue
                    
                    # Get all text within this container
                    container_text = await container.text_content()
                    if not container_text or context_text not in container_text:
                        continue
                    
                    # If location is specified, validate it
                    if expected_location:
                        container_text_lower = container_text.lower()
                        # Check if the expected location is mentioned in or near this container
                        if expected_location not in container_text_lower:
                            # Check parent elements for tab/section indicators
                            parent_text = await page.evaluate(
                                "(el) => el.closest('[role=\"tabpanel\"], .tab-pane, .section')?.textContent || ''",
                                container
                            )
                            if expected_location not in parent_text.lower():
                                print(f"      ⊘ Found '{context_text}' but not in '{expected_location}' location")
                                continue
                    
                    # Found the right container, extract relevant data
                    print(f"      ✓ Found container with context '{context_text}'")
                    
                    # Try to find numeric values or specific elements within
                    inner_elements = await container.query_selector_all("span, h1, h2, div, p")
                    for elem in inner_elements:
                        if await elem.is_visible():
                            elem_text = await elem.text_content()
                            if elem_text:
                                elem_text = elem_text.strip()
                                # Extract numbers
                                numbers = re.findall(r'\d+', elem_text)
                                numeric_value = int(numbers[0]) if numbers else None
                                
                                # Check if this element has meaningful content
                                if numeric_value is not None or len(elem_text) > 0:
                                    location_info = f" in '{expected_location}'" if expected_location else ""
                                    
                                    return {
                                        "status": "success",
                                        "message": f"Found '{target}' in context of '{context_text}'{location_info}: {elem_text}" +
                                                 (f" (Value: {numeric_value})" if numeric_value is not None else ""),
                                        "selector_used": pattern,
                                        "text_content": elem_text,
                                        "numeric_value": numeric_value,
                                        "context": context_text,
                                        "location": expected_location
                                    }
            except:
                continue
    
    # Strategy 3: If we found elements but they didn't match context/location, report that
    if found_elements:
        print(f"      ⚠ Found {len(found_elements)} element(s) but none matched context/location requirements")
        # Return the first found element with a note about location
        elem = found_elements[0]
        location_note = f" (Expected in '{expected_location}' but found elsewhere)" if expected_location else ""
        
        return {
            "status": "success",
            "message": f"Found element but location mismatch{location_note}. Content: {elem['text']}" +
                     (f" (Value: {elem['numeric_value']})" if elem['numeric_value'] is not None else ""),
            "selector_used": elem['selector'],
            "text_content": elem['text'],
            "numeric_value": elem['numeric_value'],
            "location_mismatch": True if expected_location else False
        }
    
    # Strategy 4: General text search (fallback)
    print(f"      Trying comprehensive text search...")
    search_keywords = target.lower().replace("'", "").replace('"', '').split()
    text_elements = await page.query_selector_all("span, div, h1, h2, h3, h4, h5, p, td, li")
    
    for elem in text_elements[:50]:
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
                
                # Extract numeric value
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
    
    # Strategy 5: Take screenshot and get page content for debugging
    try:
        screenshot_path = f"screenshots/verify_failed_step_{step_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        await page.screenshot(path=screenshot_path, full_page=True)
        print(f"      📸 Debug screenshot: {screenshot_path}")
        
        # Get visible text on page for debugging
        body_text = await page.evaluate("() => document.body.innerText")
        print(f"      Page content preview: {body_text[:200]}...")
        
        # Check if target keywords appear in page text
        target_clean = target.lower().replace("'", "").replace('"', '')
        if any(word in body_text.lower() for word in target_clean.split()):
            print(f"      ⚠ Target text '{target}' found in page but element not located")
            idx = body_text.lower().find(target_clean.split()[0])
            if idx >= 0:
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
    raise Exception(f"Verification of '{target}' failed after trying {len(selectors)} selectors. Last error: {last_error}")


def generate_fallback_selectors(target: str) -> List[str]:
    """Generate fallback selectors based on target description, prioritizing context-specific selectors"""
    
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
    
    # Tab/Navigation patterns (NEW - handle tab clicks)
    elif 'tab' in target_lower or 'nav' in target_lower:
        # Extract the tab name from quotes or after "tab"
        import re
        tab_match = re.search(r"['\"]([^'\"]*)['\"]", target)
        tab_name = tab_match.group(1) if tab_match else None
        
        # If no quotes, try to extract word before/after "tab"
        if not tab_name:
            # Pattern: "click on the Completed tab" -> "Completed"
            words = [w for w in target.split() if w.lower() not in ['click', 'on', 'the', 'tab', 'button']]
            tab_name = words[0] if words else "tab"
        
        print(f"      🎯 Tab/Navigation detected: '{tab_name}'")
        
        selectors.extend([
            # PRIORITY 1: Direct nav-link with contains text (works with icons)
            f"a.nav-link:has-text('{tab_name}')",
            f"//a[contains(@class, 'nav-link')][contains(., '{tab_name}')]",
            f"//a[contains(@class, 'nav-link')][contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{tab_name.lower()}')]",
            
            # PRIORITY 2: Nav-item containing the link
            f".nav-item a:has-text('{tab_name}')",
            f"//li[contains(@class, 'nav-item')]//a[contains(., '{tab_name}')]",
            
            # PRIORITY 3: Links with href filter parameter
            f"a[href*='{tab_name.lower()}']",
            f"a[href*='filter={tab_name.lower()}']",
            f"//a[contains(@href, '{tab_name.lower()}')]",
            f"//a[contains(@href, 'filter={tab_name.lower()}')]",
            
            # PRIORITY 4: Tab role selectors (if using ARIA)
            f"a[role='tab']:has-text('{tab_name}')",
            f"button[role='tab']:has-text('{tab_name}')",
            f"//a[@role='tab'][contains(., '{tab_name}')]",
            
            # PRIORITY 5: Nav link with partial class match
            f"[class*='nav-link']:has-text('{tab_name}')",
            f"[class*='nav']:has-text('{tab_name}')",
            
            # PRIORITY 6: Tab class patterns
            f".tab:has-text('{tab_name}')",
            f".tab-button:has-text('{tab_name}')",
            
            # PRIORITY 7: Generic text-based (case-insensitive)
            f"a:has-text('{tab_name}')",
            f"button:has-text('{tab_name}')",
            f"//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{tab_name.lower()}')]",
            
            # PRIORITY 8: Generic clickable elements with nav classes
            ".nav-link", ".nav-item a",
            "[role='tab']",
            ".tab", ".tab-button",
            "a", "button"
        ])
    
    # Button/Submit patterns with context-aware matching
    elif 'button' in target_lower or 'submit' in target_lower or 'btn' in target_lower or 'click' in target_lower:
        # Extract meaningful keywords from target
        import re
        
        # Remove common words but preserve structure
        cleaned = target_lower
        for word in ['button', 'btn', 'click', 'on', 'the', 'of', 'a', 'an', 'for', 'in', 'task']:
            cleaned = cleaned.replace(word, ' ')
        
        # Extract quoted text (this is the context - e.g., 'The Idea Jar')
        quoted = re.findall(r"['\"]([^'\"]*)['\"]", target)
        
        # Get keywords (button action words)
        keywords = [k.strip() for k in cleaned.split() if len(k.strip()) > 2]
        
        # Build selectors with CONTEXT FIRST approach
        if quoted and keywords:
            # We have both context (e.g., "The Idea Jar") and button text (e.g., "complete")
            button_text = keywords[0] if keywords else "button"
            context_text = quoted[0] if quoted else ""
            context_lower = context_text.lower()
            
            print(f"      🎯 Context detected: '{context_text}', Button: '{button_text}'")
            
            # PRIORITY 1: Find headers with context text, then navigate to button
            selectors.extend([
                # Try all header levels (h1-h6)
                f"//h1[contains(., '{context_text}')]/ancestor::div[1]//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{button_text}')]",
                f"//h2[contains(., '{context_text}')]/ancestor::div[1]//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{button_text}')]",
                f"//h3[contains(., '{context_text}')]/ancestor::div[1]//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{button_text}')]",
                f"//h4[contains(., '{context_text}')]/ancestor::div[1]//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{button_text}')]",
                f"//h5[contains(., '{context_text}')]/ancestor::div[1]//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{button_text}')]",
                f"//h6[contains(., '{context_text}')]/ancestor::div[1]//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{button_text}')]",
            ])
            
            # PRIORITY 2: Find header, go up to card/row container, find any button
            selectors.extend([
                f"//h5[contains(., '{context_text}')]/ancestor::div[contains(@class, 'card')]//button",
                f"//h5[contains(., '{context_text}')]/ancestor::div[contains(@class, 'row')]//button",
                f"//h4[contains(., '{context_text}')]/ancestor::div[contains(@class, 'card')]//button",
                f"//h3[contains(., '{context_text}')]/ancestor::div[contains(@class, 'card')]//button",
                # Any header with context → first parent container → button
                f"//h5[contains(., '{context_text}')]/ancestor::*[self::div or self::li or self::tr][1]//button",
            ])
            
            # PRIORITY 3: Case-insensitive header search
            selectors.extend([
                f"//h5[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{context_lower}')]/ancestor::div[1]//button",
                f"//h4[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{context_lower}')]/ancestor::div[1]//button",
            ])
            
            # PRIORITY 4: Traditional container-based search
            selectors.extend([
                f"//div[contains(., '{context_text}')]//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{button_text}')]",
                f"//li[contains(., '{context_text}')]//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{button_text}')]",
                f"//tr[contains(., '{context_text}')]//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{button_text}')]",
            ])
            
            # PRIORITY 5: CSS with Playwright text selectors
            selectors.extend([
                f".card:has-text('{context_text}') button:has-text('{button_text.title()}')",
                f".task-item:has-text('{context_text}') button:has-text('{button_text}')",
                f".item:has-text('{context_text}') button:has-text('{button_text}')",
            ])
            
            # PRIORITY 6: Context-specific data attributes
            selectors.extend([
                f"[data-task-name='{context_text}'] button",
                f"[data-item-name='{context_text}'] button",
                f"[data-name='{context_text}'] button",
            ])
            
            # PRIORITY 7: Find any div/li with context, then any button
            selectors.extend([
                f"//div[contains(., '{context_text}')]//button",
                f"//li[contains(., '{context_text}')]//button",
            ])
            
            # PRIORITY 8: Button text match (less specific - will match ANY button with this text!)
            selectors.extend([
                f"button:has-text('{button_text.title()}')",
                f"button:has-text('{button_text}')",
                f"//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{button_text}')]",
            ])
            
            # PRIORITY 9: Generic CSS class patterns
            selectors.extend([
                f"button.{button_text}", f".btn-{button_text}",
                f"button[data-action='{button_text}']",
                f"button[aria-label*='{button_text}' i]",
            ])
            
            # PRIORITY 10: Last resort - generic button selectors
            selectors.extend([
                "button[type='button']", "button[type='submit']",
                "button", ".btn"
            ])
            
        elif keywords:
            button_text = keywords[0]
            selectors.extend([
                f"#{button_text}-btn", f"#{button_text}-button", f"#{button_text}",
                f"button:has-text('{button_text.title()}')",
                f"button:has-text('{button_text}')",
                f"//button[contains(text(), '{button_text}')]",
                f"button.{button_text}", f".btn-{button_text}",
                "button[type='submit']", "button", ".btn"
            ])
        else:
            selectors.extend([
                "button[type='submit']", "input[type='submit']",
                "button", ".btn", ".button",
                "a[role='button']"
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
    
    # Remove duplicates while preserving order
    seen = set()
    unique_selectors = []
    for selector in selectors:
        if selector not in seen:
            seen.add(selector)
            unique_selectors.append(selector)
    
    return unique_selectors


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
        print(f"  Browser will {'NOT be visible' if headless else 'be VISIBLE (FULLSCREEN)'}")
        print(f"  Speed optimizations: ENABLED")
        print(f"{'='*60}\n")
        
        results = []
        
        async with async_playwright() as p:
            # Launch browser with optimizations
            print(f"Launching Chromium browser (headless={headless})...")
            
            # Build browser args
            browser_args = [
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
            ]
            
            if not headless:
                # Add full screen args for visible mode
                browser_args.extend([
                    '--start-maximized',
                    '--start-fullscreen',
                    '--kiosk',  # Forces full screen mode
                ])
            
            browser = await p.chromium.launch(
                headless=headless,
                args=browser_args
            )
            
            # Create context with full screen viewport
            if headless:
                # For headless, use standard resolution
                viewport_config = {"width": 1920, "height": 1080}
            else:
                # For visible mode, use None to inherit from window (full screen)
                viewport_config = None
            
            context = await browser.new_context(
                viewport=viewport_config,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                # Speed optimizations
                ignore_https_errors=True,
                # Additional settings for better display
                screen={"width": 1920, "height": 1080} if not headless else None,
                no_viewport=not headless  # Disable viewport restrictions for full screen
            )
            
            # Set default timeout
            context.set_default_timeout(10000)  # 10 seconds default
            
            page = await context.new_page()
            
            # For non-headless mode, maximize the viewport
            if not headless:
                try:
                    # Set viewport to screen size
                    await page.set_viewport_size({"width": 1920, "height": 1080})
                except:
                    pass  # Ignore if it fails
            
            print(f"✓ Browser launched successfully in {'FULLSCREEN' if not headless else 'headless'} mode")
            
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
