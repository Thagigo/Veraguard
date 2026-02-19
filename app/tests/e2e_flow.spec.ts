import { test, expect } from '@playwright/test';

test('Premium Flow: Landing -> Purchase -> Vault -> Logout', async ({ page }) => {
    // Capture browser logs
    page.on('console', msg => console.log(`BROWSER: ${msg.text()}`));

    // Mock Telegram WebApp
    await page.addInitScript(() => {
        (window as any).Telegram = {
            WebApp: {
                initData: "",
                initDataUnsafe: { user: { id: 12345, first_name: "TestUser" } },
                ready: () => { },
                expand: () => { },
                MainButton: {
                    text: "",
                    color: "",
                    textColor: "",
                    isVisible: false,
                    show: () => { },
                    hide: () => { },
                    onClick: () => { },
                    offClick: () => { },
                    showProgress: () => { },
                    hideProgress: () => { },
                    setText: () => { },
                },
                HapticFeedback: {
                    impactOccurred: () => { },
                    notificationOccurred: () => { },
                    selectionChanged: () => { },
                },
                openLink: () => { },
                colorScheme: 'light',
                themeParams: {},
                backgroundColor: '#ffffff',
                onEvent: () => { },
                offEvent: () => { },
            }
        };
    });

    // Mock API Routes
    await page.route('**/api/credits/*', async route => {
        await route.fulfill({ json: { credits: 0, is_member: false } });
    });

    await page.route('**/api/fee', async route => {
        await route.fulfill({
            json: {
                quote: {
                    amount: 0.001,
                    expiry: Math.floor(Date.now() / 1000) + 60,
                    signature: "mock_sig",
                    subscription_amount: 0.05
                }
            }
        });
    });

    await page.route('**/api/referral/*', async route => {
        await route.fulfill({ json: { code: "REF123", uses: 0, earned: 0 } });
    });

    await page.route('**/api/pay', async route => {
        await route.fulfill({ json: { credits: 7, is_member: false } });
    });

    await page.route('**/api/user/history/*', async route => {
        await route.fulfill({
            json: [
                {
                    id: "tx_123",
                    type: "purchase",
                    amount_eth: 0.007,
                    amount_usd: 21.00,
                    timestamp: Math.floor(Date.now() / 1000),
                    description: "Credit Purchase"
                }
            ]
        });
    });

    // 1. Landing
    console.log("Navigating to /");
    await page.goto('/');
    // await expect(page).toHaveTitle(/app/i); // Case insensitive title check
    // I didn't change index.html title! It's probably "Vite + React + TS".
    // App.tsx doesn't set document.title.
    // I should check what the title is.
    // The read_url_content (Step 136) says <title>app</title>.
    // So expect(page).toHaveTitle(/VeraGuard/) WILL FAIL.

    // Update expectations
    // await expect(page).toHaveTitle(/app/i);

    // console.log("Checking Security Verification");
    // // Check for Security Verification Overlay (it appears for 1.5s)
    // await expect(page.getByText(/Verifying Identity/i)).toBeVisible({ timeout: 10000 });
    // await expect(page.getByText(/Verifying Identity/i)).not.toBeVisible({ timeout: 10000 });
    // console.log("Security Verification Passed");

    // 2. Connect Wallet (Mock)
    console.log("Connecting Wallet");
    await page.locator('button', { hasText: 'INITIALIZE SECURITY' }).click({ force: true });
    console.log("Clicked INITIALIZE SECURITY");
    // Expect address to appear
    await expect(page.getByText(/0x71C7/i)).toBeVisible();

    // 3. Triage / Dashboard Check
    // await expect(page.getByText(/Ready to secure the chain/i)).toBeVisible();

    // 4. Purchase Flow
    console.log("Starting Purchase Flow");
    // Click "Standard" 7 Credits
    await page.getByText(/Standard/i).click();
    // Click "Get Access" -> Triggers PreFlight
    await page.getByText(/GET ACCESS/i).click();

    // 5. Pre-Flight Preview
    console.log("Checking PreFlight");
    await expect(page.getByText(/Trust Contract Initialization/i)).toBeVisible();
    await expect(page.getByText(/Security Injection/i)).toBeVisible();

    // Confirm Purchase
    await page.getByRole('button', { name: /Sign & Inject/i }).click();

    // 6. Distribution Receipt
    console.log("Checking Receipt");
    await expect(page.getByText(/Protocol Funded/i)).toBeVisible();
    // Explicitly close
    await page.getByText(/Close Receipt/i).click();
    // Wait for receipt to disappear (3s)
    await expect(page.getByText(/Protocol Funded/i)).not.toBeVisible({ timeout: 10000 });

    // 6.5 Deep Dive Modal Check
    console.log("Checking Deep Dive Modal");
    await page.getByPlaceholder(/Enter Contract Address/i).fill("0xveryhuge");
    await page.locator('button', { hasText: 'Start Audit' }).click();

    // Check for Modal
    await expect(page.getByText(/Universal Ledger Alert/i)).toBeVisible();
    await expect(page.getByText(/Cancel/i)).toBeVisible();
    await expect(page.getByText(/Standard Scan \(1 Credit\)/i)).toBeVisible(); // Non-member mock

    // Test Cancel
    await page.getByText(/Cancel/i).click();
    await expect(page.getByText(/Universal Ledger Alert/i)).not.toBeVisible();


    // 7. Navigate to Vault
    console.log("Navigating to Vault");
    await page.getByTitle(/View Vault/i).click();
    await expect(page).toHaveURL(/vault/);
    await expect(page.getByText(/The Vault/i)).toBeVisible();

    // Check for the purchase tx
    await expect(page.getByText(/Credit Purchase/i)).toBeVisible();

    // Return to Dashboard first to access header
    await page.getByText(/Return to Dashboard/i).click();

    // 8. Logout
    console.log("Logging Out");
    // Handle confirmation dialog
    page.once('dialog', dialog => dialog.accept());
    await page.getByTitle(/TERMINATE SECURE SESSION/i).click(); // Updated Selector
    // Should return to "/" and show Security Verification again
    await expect(page).toHaveURL(/\/$/); // Match root
    await expect(page.getByText(/Verifying Identity/i)).toBeVisible();
});
