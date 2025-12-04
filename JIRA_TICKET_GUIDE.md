# 📝 Creating JIRA Tickets for Automated Bug Reproduction

## 🎯 Overview

This guide shows you how to create JIRA tickets that the Bug Reproduction Agent can automatically process and execute.

## ✅ Required Information in JIRA Ticket

### 1. **Application URL** (MANDATORY)

The agent **must** find the application URL. Include it in one of these places:

#### Option A: In Description (Recommended)
```
Description:
The login functionality is broken.

Application: https://myapp.example.com
Environment: Staging
```

#### Option B: As a Link
```
Description:
Bug found in the application: https://myapp.example.com
```

#### Option C: In Environment Field
```
Environment field:
Staging - https://staging.myapp.com
```

#### Option D: In Custom Field
If your JIRA has custom fields like:
- "Application URL"
- "App Link"
- "Testing URL"

Fill these with the full URL.

---

### 2. **Reproduction Steps** (MANDATORY)

Write clear, numbered steps that can be automated:

#### ✅ GOOD Example:
```
Steps to Reproduce:
1. Navigate to https://myapp.example.com
2. Click on the "Login" button in the top-right corner
3. Enter username: test@example.com
4. Enter password: Test123!
5. Click the "Submit" button
6. Observe that an error message "500 Internal Server Error" appears
```

#### ❌ BAD Example (Too Vague):
```
Steps to Reproduce:
1. Go to the app
2. Try to login
3. It doesn't work
```

**Why it's bad:**
- No specific URL
- No specific button names
- No specific credentials
- No observable outcome

---

### 3. **Expected Behavior** (REQUIRED)

Describe what should happen:

```
Expected Result:
User should be logged in and redirected to the dashboard page with a welcome message "Welcome, Test User"
```

---

### 4. **Actual Behavior** (REQUIRED)

Describe what actually happens (the bug):

```
Actual Result:
Instead of logging in, an error message "500 Internal Server Error" appears on the screen, and the user remains on the login page.
```

---

## 📋 Complete JIRA Ticket Template

### Example 1: Login Bug

```
Summary: Login button returns 500 error for valid credentials

Issue Type: Bug

Priority: High

Description:
When a user attempts to log in with valid credentials, the application 
returns a 500 Internal Server Error instead of authenticating the user.

Application URL: https://staging.myapp.example.com
Environment: Staging
Browser: Chrome 120+

Steps to Reproduce:
1. Navigate to https://staging.myapp.example.com
2. Click on the "Login" button (CSS selector: #login-btn)
3. Enter username in the email field: test@example.com
4. Enter password in the password field: Test123!
5. Click the "Submit" button (CSS selector: #submit-btn)
6. Wait for 3 seconds
7. Observe the error message displayed

Expected Result:
- User should be authenticated successfully
- User should be redirected to /dashboard
- Welcome message should appear: "Welcome, Test User"
- User profile icon should be visible in top-right corner

Actual Result:
- Error message appears: "500 Internal Server Error"
- User remains on the login page
- No authentication occurs
- Browser console shows: "POST /api/auth/login 500"

Environment: 
Staging - https://staging.myapp.example.com

Labels: automation-ready, login, critical

Attachments: 
- screenshot_error.png
- browser_console.txt
```

---

### Example 2: Shopping Cart Bug

```
Summary: Add to cart button doesn't update cart count

Issue Type: Bug

Priority: Medium

Description:
When clicking "Add to Cart" on a product page, the cart icon count 
doesn't update, though the item is added to the cart.

Application: https://shop.example.com
Test Credentials: 
- Username: testuser@shop.com
- Password: Shop123!

Steps to Reproduce:
1. Navigate to https://shop.example.com
2. Click "Login" button
3. Enter username: testuser@shop.com
4. Enter password: Shop123!
5. Click "Sign In"
6. Navigate to https://shop.example.com/products/laptop-123
7. Click "Add to Cart" button
8. Verify the cart icon in the header shows updated count

Expected Result:
- Cart icon should show count "1"
- Success message should appear: "Item added to cart"
- Cart icon should have a visual indicator (red dot)

Actual Result:
- Cart icon still shows "0"
- Success message does appear
- Item is in cart (verified by clicking cart icon)
- Count only updates after page refresh

Environment: Production - https://shop.example.com
Browser: Chrome 120, Firefox 119
```

---

### Example 3: Form Validation Bug

```
Summary: Email validation accepts invalid email format

Issue Type: Bug

Priority: Low

Description:
The email field in the registration form accepts invalid email formats
like "test@" or "invalid.email" without validation errors.

Application: https://app.example.com/register

Steps to Reproduce:
1. Navigate to https://app.example.com/register
2. Click in the "Email" input field (name="email")
3. Enter invalid email: "notanemail@"
4. Click in another field (to trigger validation)
5. Click "Register" button
6. Observe that form submits without error

Expected Result:
- Email field should show error: "Please enter a valid email address"
- Form should not submit
- Email field should have red border
- Submit button should be disabled

Actual Result:
- No validation error appears
- Form attempts to submit
- Server returns 400 error
- User sees generic error message

Environment: https://app.example.com/register
```

---

## 🎨 UI Element Selection Tips

To help the automation find elements, include:

### CSS Selectors (Preferred)
```
Steps:
1. Click the login button (CSS: #login-btn)
2. Enter text in username field (CSS: input[name="username"])
3. Click submit (CSS: button[type="submit"])
```

### Element Text (Alternative)
```
Steps:
1. Click the button with text "Sign In"
2. Click the link with text "Forgot Password?"
```

### XPath (For Complex Elements)
```
Steps:
1. Click the button (XPath: //button[@class='btn-primary'][text()='Submit'])
```

### Name Attributes
```
Steps:
1. Enter text in field with name="email"
2. Enter text in field with name="password"
```

---

## 🔐 Including Credentials

If the bug requires login:

### Option 1: In Description
```
Description:
Login bug in staging environment.

Test Credentials:
- Username: test@example.com
- Password: Test123!
```

### Option 2: In Steps
```
Steps to Reproduce:
1. Navigate to https://app.example.com
2. Login with username: test@example.com and password: Test123!
3. Click dashboard
```

### Option 3: Use Test Account
```
Description:
Use test account credentials:
Email: automation@test.com
Password: AutoTest2024!

Application: https://staging.app.com
```

---

## 📸 Optional but Helpful

### Attachments
- Screenshots showing the bug
- Browser console logs
- Network request logs
- Video recordings

### Labels
Add labels to help categorize:
- `automation-ready` - Ready for automated testing
- `ui-bug` - UI related
- `critical` - High priority
- `staging` - Environment

### Additional Fields
- Browser: Chrome 120
- OS: Windows 11
- Screen Resolution: 1920x1080
- Device: Desktop

---

## ✅ Checklist Before Saving JIRA Ticket

- [ ] **Application URL included** (https://...)
- [ ] **Reproduction steps are numbered and specific**
- [ ] **UI elements identified** (button names, CSS selectors, IDs)
- [ ] **Test data provided** (usernames, passwords, input values)
- [ ] **Expected behavior clearly stated**
- [ ] **Actual behavior (bug) clearly described**
- [ ] **Environment specified** (dev/staging/prod)
- [ ] **Credentials included** (if login required)
- [ ] **Observable outcome mentioned** (error message, behavior)

---

## 🚀 Quick Template (Copy-Paste)

```
Summary: [Brief description of the bug]

Description:
[Detailed explanation of what's wrong]

Application URL: https://[your-app-url]
Environment: [dev/staging/prod]

Test Credentials (if needed):
- Username: [test-username]
- Password: [test-password]

Steps to Reproduce:
1. Navigate to https://[app-url]
2. Click on [specific element]
3. Enter [specific data] in [specific field]
4. Click [specific button]
5. Observe [specific result]

Expected Result:
[What should happen - be specific]

Actual Result:
[What actually happens - the bug]

Additional Info:
- Browser: Chrome/Firefox/Safari
- OS: Windows/Mac/Linux
- Frequency: Always/Sometimes/Rare
```

---

## 💡 Pro Tips

### 1. Be Specific with URLs
✅ Good: `https://staging.myapp.com/products/item/123`
❌ Bad: `the product page`

### 2. Include Data Values
✅ Good: `Enter "John Smith" in the name field`
❌ Bad: `Enter a name`

### 3. Mention Visual Elements
✅ Good: `Verify error message "Invalid credentials" appears in red below the form`
❌ Bad: `Error shows up`

### 4. Include Wait Times
✅ Good: `Wait 3 seconds for the page to load, then verify...`
❌ Bad: `Check if it loaded`

### 5. Use Standard Terminology
- "Click" not "Press" or "Hit"
- "Navigate to" not "Go to"
- "Enter" not "Type" or "Input"
- "Verify" not "Check" or "See if"

---

## 🎯 Example: Creating Your First Automation-Ready Ticket

### Step-by-Step:

1. **Create New Issue** in JIRA
2. **Select Issue Type**: Bug
3. **Add Summary**: "Login button returns 500 error"
4. **Fill Description**:
   ```
   Application: https://myapp.example.com
   
   Steps to Reproduce:
   1. Navigate to https://myapp.example.com
   2. Click "Login" button
   3. Enter username: test@example.com
   4. Enter password: Test123
   5. Click "Submit"
   
   Expected: User logs in
   Actual: 500 error appears
   ```
5. **Set Priority**: High
6. **Add Labels**: `automation-ready`
7. **Save**

Now run:
```bash
python bug_reproduction_agent.py YOUR-TICKET-KEY
```

---

## 🔍 Testing Your Ticket

Before running automation, verify:

1. **Can you follow the steps manually?**
   - If you can't, the agent can't either

2. **Is the URL accessible?**
   - Open it in a browser

3. **Are element selectors correct?**
   - Use browser DevTools to verify

4. **Are credentials valid?**
   - Test login manually first

---

## 📞 Need Help?

If the automation fails:
1. Check that URL is in JIRA description
2. Verify reproduction steps are specific
3. Run with `--simulate` flag first
4. Check `screenshots/` folder for evidence
5. Review terminal output for errors

---

**Remember**: The more specific and detailed your JIRA ticket, the better the automation will work! 🎯
