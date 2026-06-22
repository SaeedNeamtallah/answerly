import { chromium } from '@playwright/test';
import fs from 'fs';

async function run() {
  const auth = JSON.parse(fs.readFileSync('./auth.json', 'utf8'));
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();
  
  // Set local storage by going to the domain first
  await page.goto('http://localhost:3001');
  await page.evaluate((authObj) => {
    localStorage.setItem('ragmind-next-auth', JSON.stringify(authObj));
  }, auth);
  
  // Go to the target page
  await page.goto('http://localhost:3001/whatsapp-bots/2');
  
  // Wait for React to load and any network requests to finish
  await page.waitForTimeout(6000);
  
  // Take screenshot
  await page.screenshot({ path: 'screenshot.png', fullPage: true });
  await browser.close();
  console.log('Screenshot saved to screenshot.png');
}

run().catch(console.error);
