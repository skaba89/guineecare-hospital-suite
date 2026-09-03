// Screenshot démo BodyMap — utilise Playwright
import { chromium } from 'playwright';
import { fileURLToPath } from 'url';
import path from 'path';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({
    viewport: { width: 1280, height: 900 },
    deviceScaleFactor: 2,
  });
  await page.goto('file://' + path.join(__dirname, 'bodymap_demo.html'));
  await page.waitForLoadState('networkidle');
  // Attendre que les polices soient chargées
  await page.waitForTimeout(500);
  await page.screenshot({
    path: path.join(__dirname, '..', 'download', 'bodymap_demo.png'),
    fullPage: true,
  });
  console.log('Screenshot saved: /home/z/my-project/download/bodymap_demo.png');
  await browser.close();
})();
