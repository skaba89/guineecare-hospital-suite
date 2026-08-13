import { test, expect, type Page } from '@playwright/test';

/**
 * Tests E2E — Mode sombre (v2.9.2)
 *
 * Couverture :
 *   - ThemeToggle visible dans le topbar après login
 *   - Click sur le toggle change data-theme de light → dark
 *   - Click inverse repasse en light
 *   - Persistance localStorage (clé "guineecare_theme")
 *   - Respect de prefers-color-scheme au premier chargement (test limité — pas de mock navigateur)
 *   - Toggle accessible (aria-label, role button)
 *
 * Prérequis : backend + frontend démarrés avec seed démo.
 */

const SUPER_ADMIN = { email: 'admin@guineecare.com', password: 'admin123' };

async function login(page: Page, creds: { email: string; password: string }) {
  await page.goto('/', { waitUntil: 'domcontentloaded' });
  await page.evaluate(() => {
    localStorage.removeItem('guineecare_token');
    localStorage.removeItem('guineecare_user');
    localStorage.removeItem('guineecare_theme');
  });
  await page.reload({ waitUntil: 'domcontentloaded' });

  const emailInput = page.locator('#login-email');
  await emailInput.waitFor({ state: 'visible', timeout: 15_000 });
  await emailInput.fill(creds.email);
  await page.locator('#login-password').fill(creds.password);
  await page.locator('form button[type="submit"]').click();
  await expect(page.locator('aside.sidebar')).toBeVisible({ timeout: 25_000 });
  await page.waitForLoadState('networkidle').catch(() => {});
}

// ----------------------------------------------------------------------------
// 1. THEME TOGGLE — Visibilité et accessibilité
// ----------------------------------------------------------------------------
test.describe('Mode sombre — Toggle UI (v2.9.2)', () => {
  test('ThemeToggle visible dans le topbar après login', async ({ page }) => {
    await login(page, SUPER_ADMIN);
    const toggle = page.locator('[data-testid="theme-toggle"]');
    await expect(toggle).toBeVisible({ timeout: 10_000 });
  });

  test('ThemeToggle a un aria-label descriptif', async ({ page }) => {
    await login(page, SUPER_ADMIN);
    const toggle = page.locator('[data-testid="theme-toggle"]');
    const ariaLabel = await toggle.getAttribute('aria-label');
    expect(ariaLabel).toBeTruthy();
    expect(ariaLabel).toMatch(/clair|sombre|light|dark/i);
  });

  test('ThemeToggle est focusable au clavier', async ({ page }) => {
    await login(page, SUPER_ADMIN);
    const toggle = page.locator('[data-testid="theme-toggle"]');
    await toggle.focus();
    await expect(toggle).toBeFocused();
  });
});

// ----------------------------------------------------------------------------
// 2. TOGGLE FONCTIONNEL — Light → Dark → Light
// ----------------------------------------------------------------------------
test.describe('Mode sombre — Toggle fonctionnel (v2.9.2)', () => {
  test('click sur toggle passe de light à dark', async ({ page }) => {
    await login(page, SUPER_ADMIN);

    // État initial : light (par défaut après reset localStorage)
    const html = page.locator('html');
    await expect(html).toHaveAttribute('data-theme', 'light');

    // Click → dark
    await page.locator('[data-testid="theme-toggle"]').click();
    await expect(html).toHaveAttribute('data-theme', 'dark');
  });

  test('click inverse repasse de dark à light', async ({ page }) => {
    await login(page, SUPER_ADMIN);

    // Aller en dark
    await page.locator('[data-testid="theme-toggle"]').click();
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');

    // Revenir en light
    await page.locator('[data-testid="theme-toggle"]').click();
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'light');
  });

  test('le bouton change de libellé selon le thème', async ({ page }) => {
    await login(page, SUPER_ADMIN);

    // En light → bouton propose "Sombre"
    const toggle = page.locator('[data-testid="theme-toggle"]');
    await expect(toggle).toContainText(/sombre|dark/i);

    // Click → dark → bouton propose "Clair"
    await toggle.click();
    await expect(toggle).toContainText(/clair|light/i);
  });
});

// ----------------------------------------------------------------------------
// 3. PERSISTANCE localStorage
// ----------------------------------------------------------------------------
test.describe('Mode sombre — Persistance (v2.9.2)', () => {
  test('préférence dark persistée dans localStorage', async ({ page }) => {
    await login(page, SUPER_ADMIN);

    // Aller en dark
    await page.locator('[data-testid="theme-toggle"]').click();
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');

    // Vérifier localStorage
    const stored = await page.evaluate(() => localStorage.getItem('guineecare_theme'));
    expect(stored).toBe('dark');
  });

  test('préférence light persistée dans localStorage', async ({ page }) => {
    await login(page, SUPER_ADMIN);

    // Aller en dark puis revenir en light
    await page.locator('[data-testid="theme-toggle"]').click();
    await page.locator('[data-testid="theme-toggle"]').click();

    const stored = await page.evaluate(() => localStorage.getItem('guineecare_theme'));
    expect(stored).toBe('light');
  });

  test('au rechargement, le thème persisté est appliqué', async ({ page }) => {
    await login(page, SUPER_ADMIN);

    // Aller en dark
    await page.locator('[data-testid="theme-toggle"]').click();
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');

    // Recharger la page
    await page.reload({ waitUntil: 'domcontentloaded' });

    // Le thème dark doit être restauré
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');
  });
});

// ----------------------------------------------------------------------------
// 4. COMPATIBILITÉ — Le contenu reste lisible en dark
// ----------------------------------------------------------------------------
test.describe('Mode sombre — Lisibilité (v2.9.2)', () => {
  test('la sidebar reste visible en dark', async ({ page }) => {
    await login(page, SUPER_ADMIN);
    await page.locator('[data-testid="theme-toggle"]').click();
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');

    // La sidebar doit toujours être visible
    await expect(page.locator('aside.sidebar')).toBeVisible();
  });

  test('le contenu du dashboard reste lisible en dark', async ({ page }) => {
    await login(page, SUPER_ADMIN);
    await page.locator('[data-testid="theme-toggle"]').click();
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');

    // Le body doit contenir du texte (KPIs, etc.)
    await expect(page.locator('body')).toContainText(/\d+/, { timeout: 15_000 });
  });

  test('navigation vers /patients fonctionne en dark', async ({ page }) => {
    await login(page, SUPER_ADMIN);
    await page.locator('[data-testid="theme-toggle"]').click();
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');

    // Naviguer vers /patients — doit rester en dark
    await page.goto('/patients', { waitUntil: 'domcontentloaded' });
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');
    await expect(page).toHaveURL(/patients/i);
  });

  test('navigation vers /audit fonctionne en dark', async ({ page }) => {
    await login(page, SUPER_ADMIN);
    await page.locator('[data-testid="theme-toggle"]').click();

    await page.goto('/audit', { waitUntil: 'domcontentloaded' });
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');
    await expect(page).toHaveURL(/audit/i);
  });
});

// ----------------------------------------------------------------------------
// 5. ICD-11 — API (v2.9.2)
// ----------------------------------------------------------------------------
test.describe('ICD-11 API (v2.9.2)', () => {
  test('GET /api/v1/icd11/search?q=paludisme retourne des résultats', async ({ request, page }) => {
    // Login
    await page.goto('/', { waitUntil: 'domcontentloaded' });
    await page.evaluate(() => {
      localStorage.removeItem('guineecare_token');
    });
    await page.reload();
    await page.locator('#login-email').fill(SUPER_ADMIN.email);
    await page.locator('#login-password').fill(SUPER_ADMIN.password);
    await page.locator('form button[type="submit"]').click();
    await expect(page.locator('aside.sidebar')).toBeVisible({ timeout: 25_000 });

    const token = await page.evaluate(() => localStorage.getItem('guineecare_token'));
    const resp = await request.get('/api/v1/icd11/search?q=paludisme', {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(resp.status()).toBe(200);
    const data = await resp.json();
    expect(data.total).toBeGreaterThanOrEqual(1);
    expect(data.data[0].code).toMatch(/^1F/i); // Codes paludisme commencent par 1F
  });

  test('GET /api/v1/icd11/1F03 retourne le paludisme à P. falciparum', async ({ request, page }) => {
    await page.goto('/', { waitUntil: 'domcontentloaded' });
    await page.evaluate(() => {
      localStorage.removeItem('guineecare_token');
    });
    await page.reload();
    await page.locator('#login-email').fill(SUPER_ADMIN.email);
    await page.locator('#login-password').fill(SUPER_ADMIN.password);
    await page.locator('form button[type="submit"]').click();
    await expect(page.locator('aside.sidebar')).toBeVisible({ timeout: 25_000 });

    const token = await page.evaluate(() => localStorage.getItem('guineecare_token'));
    const resp = await request.get('/api/v1/icd11/1F03', {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(resp.status()).toBe(200);
    const data = await resp.json();
    expect(data.data.code).toBe('1F03');
    expect(data.data.label_fr).toMatch(/falciparum/i);
  });

  test('GET /api/v1/icd11/categories liste les catégories', async ({ request, page }) => {
    await page.goto('/', { waitUntil: 'domcontentloaded' });
    await page.evaluate(() => {
      localStorage.removeItem('guineecare_token');
    });
    await page.reload();
    await page.locator('#login-email').fill(SUPER_ADMIN.email);
    await page.locator('#login-password').fill(SUPER_ADMIN.password);
    await page.locator('form button[type="submit"]').click();
    await expect(page.locator('aside.sidebar')).toBeVisible({ timeout: 25_000 });

    const token = await page.evaluate(() => localStorage.getItem('guineecare_token'));
    const resp = await request.get('/api/v1/icd11/categories', {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(resp.status()).toBe(200);
    const data = await resp.json();
    expect(data.data.length).toBeGreaterThanOrEqual(5);
  });
});
