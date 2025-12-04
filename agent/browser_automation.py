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
    
    async def execute_step(self, step: ReproductionStep) -> ReproductionStep:
        """
        Execute a single reproduction step
        
        Returns:
            Updated step with execution results
        """
        if not self.page:
            step.status = "failed"
            step.error = "Browser not initialized"
            return step
        
        try:
            action = step.action.lower()
            target = step.target
            
            # Extract data if stored in actual_result
            data = None
            if step.actual_result and step.actual_result.startswith("DATA:"):
                data = step.actual_result[5:]
                step.actual_result = None
            
            print(f"  Executing: {action} on {target}")
            
            if action == "navigate":
                await self.page.goto(target, wait_until="domcontentloaded", timeout=30000)
                step.actual_result = f"Navigated to {target}"
                step.status = "success"
                
            elif action == "click":
                selector_type, selector_value = self.parse_selector(target)
                
                if selector_type == "text":
                    await self.page.click(f"text={selector_value}", timeout=10000)
                elif selector_type == "xpath":
                    await self.page.click(f"xpath={selector_value}", timeout=10000)
                else:
                    await self.page.click(selector_value, timeout=10000)
                
                step.actual_result = f"Clicked on {target}"
                step.status = "success"
                
            elif action == "input":
                selector_type, selector_value = self.parse_selector(target)
                
                if selector_type == "xpath":
                    await self.page.fill(f"xpath={selector_value}", data or "", timeout=10000)
                else:
                    await self.page.fill(selector_value, data or "", timeout=10000)
                
                step.actual_result = f"Entered text in {target}"
                step.status = "success"
                
            elif action == "select":
                selector_type, selector_value = self.parse_selector(target)
                
                if selector_type == "xpath":
                    await self.page.select_option(f"xpath={selector_value}", data, timeout=10000)
                else:
                    await self.page.select_option(selector_value, data, timeout=10000)
                
                step.actual_result = f"Selected option '{data}' in {target}"
                step.status = "success"
                
            elif action == "wait":
                selector_type, selector_value = self.parse_selector(target)
                
                if selector_type == "text":
                    await self.page.wait_for_selector(f"text={selector_value}", timeout=10000)
                elif selector_type == "xpath":
                    await self.page.wait_for_selector(f"xpath={selector_value}", timeout=10000)
                else:
                    await self.page.wait_for_selector(selector_value, timeout=10000)
                
                step.actual_result = f"Element {target} appeared"
                step.status = "success"
                
            elif action == "verify":
                selector_type, selector_value = self.parse_selector(target)
                
                try:
                    if selector_type == "text":
                        element = await self.page.wait_for_selector(f"text={selector_value}", timeout=5000)
                    elif selector_type == "xpath":
                        element = await self.page.wait_for_selector(f"xpath={selector_value}", timeout=5000)
                    else:
                        element = await self.page.wait_for_selector(selector_value, timeout=5000)
                    
                    if element:
                        is_visible = await element.is_visible()
                        if is_visible:
                            step.actual_result = f"✓ Element {target} is visible"
                            step.status = "success"
                        else:
                            step.actual_result = f"✗ Element {target} exists but not visible"
                            step.status = "failed"
                    else:
                        step.actual_result = f"✗ Element {target} not found"
                        step.status = "failed"
                except Exception as e:
                    step.actual_result = f"✗ Verification failed: {target} not found"
                    step.status = "failed"
                    step.error = str(e)
                
            elif action == "screenshot":
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_path = os.path.join(self.screenshots_dir, f"step_{step.step_number}_{timestamp}.png")
                await self.page.screenshot(path=screenshot_path, full_page=True)
                step.actual_result = f"Screenshot saved: {screenshot_path}"
                step.status = "success"
                
            elif action == "execute_js":
                result = await self.page.evaluate(data or target)
                step.actual_result = f"JavaScript executed, result: {result}"
                step.status = "success"
                
            else:
                step.actual_result = f"Unknown action: {action}"
                step.status = "skipped"
            
            # Take screenshot after each step for debugging
            if step.status == "success" and action != "screenshot":
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_path = os.path.join(self.screenshots_dir, f"step_{step.step_number}_{timestamp}.png")
                await self.page.screenshot(path=screenshot_path)
            
        except Exception as e:
            step.status = "failed"
            step.error = f"Execution error: {str(e)}"
            step.actual_result = f"Failed to execute {action} on {target}"
            
            # Take screenshot on error
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_path = os.path.join(self.screenshots_dir, f"error_step_{step.step_number}_{timestamp}.png")
                await self.page.screenshot(path=screenshot_path)
                step.error += f" (Screenshot: {screenshot_path})"
            except:
                pass
        
        return step
    
    async def get_page_info(self) -> Dict[str, Any]:
        """Get current page information"""
        if not self.page:
            return {}
        
        return {
            "url": self.page.url,
            "title": await self.page.title(),
            "content": await self.page.content()
        }


def run_browser_automation(steps: List[ReproductionStep], headless: bool = False) -> List[ReproductionStep]:
    """
    Synchronous wrapper for browser automation
    
    Args:
        steps: List of reproduction steps to execute
        headless: Run browser in headless mode
    
    Returns:
        List of executed steps with results
    """
    async def _run():
        automation = BrowserAutomation(headless=headless)
        try:
            await automation.start()
            
            executed_steps = []
            for step in steps:
                executed_step = await automation.execute_step(step)
                executed_steps.append(executed_step)
                
                # Stop on critical failure
                if executed_step.status == "failed" and executed_step.action == "navigate":
                    print(f"✗ Critical failure at step {executed_step.step_number}, stopping execution")
                    break
            
            return executed_steps
        finally:
            await automation.stop()
    
    return asyncio.run(_run())
