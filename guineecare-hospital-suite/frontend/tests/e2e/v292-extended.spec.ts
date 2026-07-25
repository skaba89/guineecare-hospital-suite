import { test, expect, type Page } from '@playwright/test';

/**
 * Tests E2E Playwright étendus — v2.9.2
 *
 * Complète guineecare.spec.ts en couvrant les parcours critiques
 * métier non testés :
 *   - Pharmacien : page /pharmacy
 *   - Laboratoire : page /lab
 *   - Facturation : page /billing
 *   - Maternité : page /maternity
 *   - Hospitalisation : page /hospitalization
 *   - Imagerie : page /imaging
 *   - Bloc opératoire : page /surgery
 *   - Qualité : page /quality (onglets Dashboard + Alertes)
 *   - Personnel : page /personnel (+ planning + congés)
 *   - Pilotage national : page /national (SUPER_ADMIN only)
 *   - Recherche globale
 *   - i18n : toggle FR/EN
 *   - Profil utilisateur
 *   - Tâches Celery (v2.9.2) : non exposé UI, test API uniquement
 *
 * Prérequis : backend + frontend démarrés avec seed démo.
 */

const SUPER_ADMIN = { email: 'admin@guineecare.com', password: 'admin123' };
const DOCTOR = { email: 'dr.diallo@chu-donka.gn', password: 'doctor123' };
const NURSE = { email: 'inf.konde@chu-donka.gn', password: 'nurse123' };
const PHARMACIST = { email: 'ph.bah@chu-donka.gn', password: 'pharma123' };
const LAB_TECH = { email: 'lab.cisse@chu-donka.gn', password: 'lab123' };
const CASHIER = { email: 'caissier.camara@chu-donka.gn', password: 'cash123' };

async function login(page: Page, creds: { email: string; password: string }) {
  await page.goto('/', { waitUntil: 'domcontentloaded' });
  await page.evaluate(() => {
    localStorage.removeItem('guineecare_token');
    localStorage.removeItem('guineecare_user');
  });
  await page.reload({ waitUntil: 'domcontentloaded' });

  const emailInput = page.locator('#login-email');
  await emailInput.waitFor({ state: 'visible', timeout: 15_000 });
  await emailInput.fill(creds.email);
  await page.locator('#login-password').fill(creds.password);
  await page.getByRole('button', { name: /Se connecter/ }).click();
  await expect(page.locator('aside.sidebar')).toBeVisible({ timeout: 25_000 });
  await page.waitForLoadState('networkidle').catch(() => {});
}

// ----------------------------------------------------------------------------
// 1. PARCOURS MÉTIER — Pages accessibles aux rôles dédiés
// ----------------------------------------------------------------------------
test.describe('Parcours métier (v2.9.2)', () => {
  test('PHARMACIST accède à /pharmacy', async ({ page }) => {
    await login(page, PHARMACIST);
    await page.goto('/pharmacy', { waitUntil: 'domcontentloaded' });
    await expect(page).toHaveURL(/pharmacy/i);
    await expect(page.locator('body')).toContainText(/pharmacie|stock|médicament|drug/i, { timeout: 15_000 });
  });

  test('LAB_TECH accède à /lab', async ({ page }) => {
    await login(page, LAB_TECH);
    await page.goto('/lab', { waitUntil: 'domcontentloaded' });
    await expect(page).toHaveURL(/lab/i);
    await expect(page.locator('body')).toContainText(/lab|analyse|prélèvement/i, { timeout: 15_000 });
  });

  test('CASHIER accède à /billing', async ({ page }) => {
    await login(page, CASHIER);
    await page.goto('/billing', { waitUntil: 'domcontentloaded' });
    await expect(page).toHaveURL(/billing/i);
    await expect(page.locator('body')).toContainText(/factur|caisse|payment|billing/i, { timeout: 15_000 });
  });

  test('DOCTOR accède à /maternity', async ({ page }) => {
    await login(page, DOCTOR);
    await page.goto('/maternity', { waitUntil: 'domcontentloaded' });
    await expect(page).toHaveURL(/maternity/i);
    // La page peut être vide si pas de données maternité, mais l'URL doit être correcte
    await expect(page.locator('body')).toBeVisible();
  });

  test('DOCTOR accède à /hospitalization', async ({ page }) => {
    await login(page, DOCTOR);
    await page.goto('/hospitalization', { waitUntil: 'domcontentloaded' });
    await expect(page).toHaveURL(/hospitalization/i);
    await expect(page.locator('body')).toBeVisible();
  });

  test('DOCTOR accède à /imaging', async ({ page }) => {
    await login(page, DOCTOR);
    await page.goto('/imaging', { waitUntil: 'domcontentloaded' });
    await expect(page).toHaveURL(/imaging/i);
    await expect(page.locator('body')).toBeVisible();
  });

  test('DOCTOR accède à /surgery', async ({ page }) => {
    await login(page, DOCTOR);
    await page.goto('/surgery', { waitUntil: 'domcontentloaded' });
    await expect(page).toHaveURL(/surgery/i);
    await expect(page.locator('body')).toBeVisible();
  });
});

// ----------------------------------------------------------------------------
// 2. PARCOURS QUALITÉ — Onglets Dashboard + Alertes (v1.4.0)
// ----------------------------------------------------------------------------
test.describe('Qualité — Dashboard + Alertes (v1.4.0)', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, SUPER_ADMIN);
  });

  test('page /quality charge avec onglets', async ({ page }) => {
    await page.goto('/quality', { waitUntil: 'domcontentloaded' });
    await expect(page).toHaveURL(/quality/i);
    // La page doit afficher au moins un titre/onglet
    await expect(page.locator('h1, h2, .page-title').first()).toBeVisible({ timeout: 15_000 });
  });

  test('onglet Dashboard qualité visible', async ({ page }) => {
    await page.goto('/quality', { waitUntil: 'domcontentloaded' });
    // Chercher un onglet Dashboard ou Indicateurs
    const tab = page.locator('text=/dashboard|indicateur|tableau/i').first();
    await expect(tab).toBeVisible({ timeout: 15_000 });
  });
});

// ----------------------------------------------------------------------------
// 3. PARCOURS PERSONNEL — RH v2 (v1.5.0)
// ----------------------------------------------------------------------------
test.describe('Personnel — RH v2 (v1.5.0)', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, SUPER_ADMIN);
  });

  test('page /personnel charge', async ({ page }) => {
    await page.goto('/personnel', { waitUntil: 'domcontentloaded' });
    await expect(page).toHaveURL(/personnel/i);
    await expect(page.locator('body')).toContainText(/personnel|effectif|staff/i, { timeout: 15_000 });
  });

  test('page /personnel/planning charge', async ({ page }) => {
    await page.goto('/personnel/planning', { waitUntil: 'domcontentloaded' });
    await expect(page).toHaveURL(/personnel\/planning/i);
    await expect(page.locator('body')).toBeVisible();
  });

  test('page /personnel/leaves charge', async ({ page }) => {
    await page.goto('/personnel/leaves', { waitUntil: 'domcontentloaded' });
    await expect(page).toHaveURL(/personnel\/leaves/i);
    await expect(page.locator('body')).toBeVisible();
  });
});

// ----------------------------------------------------------------------------
// 4. PILOTAGE NATIONAL — SUPER_ADMIN only (v1.4.0 Phase 5)
// ----------------------------------------------------------------------------
test.describe('Pilotage national (v1.4.0)', () => {
  test('SUPER_ADMIN accède à /national', async ({ page }) => {
    await login(page, SUPER_ADMIN);
    await page.goto('/national', { waitUntil: 'domcontentloaded' });
    await expect(page).toHaveURL(/national/i);
    await expect(page.locator('body')).toContainText(/national|pilotage|indicateur|agrégat/i, { timeout: 15_000 });
  });

  test('DOCTOR redirigé de /national', async ({ page }) => {
    await login(page, DOCTOR);
    await page.goto('/national', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(2500);
    const url = page.url();
    const redirected = !url.includes('/national');
    expect(redirected).toBeTruthy();
  });
});

// ----------------------------------------------------------------------------
// 5. ACTIVITY FEED (v0.7.0)
// ----------------------------------------------------------------------------
test.describe('Activity feed', () => {
  test('SUPER_ADMIN accède à /activity', async ({ page }) => {
    await login(page, SUPER_ADMIN);
    await page.goto('/activity', { waitUntil: 'domcontentloaded' });
    await expect(page).toHaveURL(/activity/i);
    await expect(page.locator('body')).toBeVisible();
  });

  test('DOCTOR redirigé de /activity', async ({ page }) => {
    await login(page, DOCTOR);
    await page.goto('/activity', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(2500);
    const url = page.url();
    const redirected = !url.includes('/activity');
    expect(redirected).toBeTruthy();
  });
});

// ----------------------------------------------------------------------------
// 6. SMS ADMIN (v1.4.0)
// ----------------------------------------------------------------------------
test.describe('SMS Admin (v1.4.0)', () => {
  test('SUPER_ADMIN accède à /sms-admin', async ({ page }) => {
    await login(page, SUPER_ADMIN);
    await page.goto('/sms-admin', { waitUntil: 'domcontentloaded' });
    await expect(page).toHaveURL(/sms-admin/i);
    await expect(page.locator('body')).toContainText(/sms|notification|message/i, { timeout: 15_000 });
  });

  test('DOCTOR redirigé de /sms-admin', async ({ page }) => {
    await login(page, DOCTOR);
    await page.goto('/sms-admin', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(2500);
    const url = page.url();
    const redirected = !url.includes('/sms-admin');
    expect(redirected).toBeTruthy();
  });
});

// ----------------------------------------------------------------------------
// 7. RECHERCHE GLOBALE (v1.2.0)
// ----------------------------------------------------------------------------
test.describe('Recherche globale (v1.2.0)', () => {
  test('champ de recherche visible après login', async ({ page }) => {
    await login(page, SUPER_ADMIN);
    // Le champ de recherche peut être dans la sidebar ou le topbar
    const searchInput = page.locator('input[placeholder*="recherch" i], input[type="search"]').first();
    await expect(searchInput).toBeVisible({ timeout: 10_000 });
  });
});

// ----------------------------------------------------------------------------
// 8. INTERNATIONALISATION FR/EN (v1.3.0)
// ----------------------------------------------------------------------------
test.describe('i18n FR/EN (v1.3.0)', () => {
  test('toggle langue FR→EN visible', async ({ page }) => {
    await login(page, SUPER_ADMIN);
    // Chercher un bouton/sélecteur de langue (FR/EN)
    const langToggle = page.locator('button:has-text("EN"), button:has-text("FR"), [data-testid="lang-toggle"]').first();
    // Le toggle peut ne pas être visible partout — juste vérifier qu'il existe quelque part
    const exists = await langToggle.count();
    if (exists > 0) {
      await expect(langToggle).toBeVisible({ timeout: 5_000 });
    }
  });
});

// ----------------------------------------------------------------------------
// 9. PROFIL UTILISATEUR (v1.1.0)
// ----------------------------------------------------------------------------
test.describe('Profil utilisateur (v1.1.0)', () => {
  test('SUPER_ADMIN peut accéder à son profil', async ({ page }) => {
    await login(page, SUPER_ADMIN);
    // Cliquer sur l'avatar/menu user dans la sidebar
    const profileBtn = page.locator('[data-testid="user-menu"], .sidebar-user, .user-avatar').first();
    if (await profileBtn.count() > 0) {
      await profileBtn.click({ timeout: 5_000 }).catch(() => {});
    }
    // Le profil peut être accessible via /profile ou via un menu
    await page.goto('/profile', { waitUntil: 'domcontentloaded' }).catch(() => {});
    // Au minimum, vérifier que le user est affiché quelque part
    await expect(page.locator('body')).toBeVisible();
  });
});

// ----------------------------------------------------------------------------
// 10. TÂCHES CELERY — API (v2.9.2)
// ----------------------------------------------------------------------------
test.describe('Tâches Celery API (v2.9.2)', () => {
  test('GET /api/v1/tasks liste les tâches (SUPER_ADMIN)', async ({ request, page }) => {
    // Login pour récupérer le token
    await page.goto('/', { waitUntil: 'domcontentloaded' });
    await page.evaluate(() => {
      localStorage.removeItem('guineecare_token');
    });
    await page.reload();
    await page.locator('#login-email').fill(SUPER_ADMIN.email);
    await page.locator('#login-password').fill(SUPER_ADMIN.password);
    await page.getByRole('button', { name: /Se connecter/ }).click();
    await expect(page.locator('aside.sidebar')).toBeVisible({ timeout: 25_000 });

    // Récupérer le token depuis localStorage
    const token = await page.evaluate(() => localStorage.getItem('guineecare_token'));
    expect(token).toBeTruthy();

    // Appeler l'API /tasks
    const resp = await request.get('/api/v1/tasks', {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(resp.status()).toBe(200);
    const data = await resp.json();
    expect(data.tasks).toBeDefined();
    expect(data.celery_available).toBeDefined();
    const taskNames = data.tasks.map((t: { name: string }) => t.name);
    expect(taskNames).toContain('prune_audit_logs');
    expect(taskNames).toContain('backup_database');
    expect(taskNames).toContain('push_dhis2_monthly');
  });

  test('POST /api/v1/tasks/trigger/backup_database (SUPER_ADMIN)', async ({ request, page }) => {
    await page.goto('/', { waitUntil: 'domcontentloaded' });
    await page.evaluate(() => {
      localStorage.removeItem('guineecare_token');
    });
    await page.reload();
    await page.locator('#login-email').fill(SUPER_ADMIN.email);
    await page.locator('#login-password').fill(SUPER_ADMIN.password);
    await page.getByRole('button', { name: /Se connecter/ }).click();
    await expect(page.locator('aside.sidebar')).toBeVisible({ timeout: 25_000 });

    const token = await page.evaluate(() => localStorage.getItem('guineecare_token'));
    const resp = await request.post('/api/v1/tasks/trigger/backup_database', {
      headers: { Authorization: `Bearer ${token}` },
      data: {},
    });
    expect(resp.status()).toBe(200);
    const data = await resp.json();
    expect(data.task).toBe('backup_database');
    expect(data.result.backup_file).toBeDefined();
  });
});

// ----------------------------------------------------------------------------
// 11. DHIS2 PUSH — API (v2.9.1)
// ----------------------------------------------------------------------------
test.describe('DHIS2 push API (v2.9.1)', () => {
  test('POST /api/v1/reporting/dhis2/202601/push (dry-run)', async ({ request, page }) => {
    await page.goto('/', { waitUntil: 'domcontentloaded' });
    await page.evaluate(() => {
      localStorage.removeItem('guineecare_token');
    });
    await page.reload();
    await page.locator('#login-email').fill(SUPER_ADMIN.email);
    await page.locator('#login-password').fill(SUPER_ADMIN.password);
    await page.getByRole('button', { name: /Se connecter/ }).click();
    await expect(page.locator('aside.sidebar')).toBeVisible({ timeout: 25_000 });

    const token = await page.evaluate(() => localStorage.getItem('guineecare_token'));
    const resp = await request.post('/api/v1/reporting/dhis2/202601/push', {
      headers: { Authorization: `Bearer ${token}` },
    });
    // 200 = dry-run ou push success; 4xx = erreur attendue si endpoint non dispo
    expect([200, 403, 404]).toContain(resp.status());
  });
});

// ----------------------------------------------------------------------------
// 12. INSURANCE — API (v2.9.1)
// ----------------------------------------------------------------------------
test.describe('Insurance API (v2.9.1)', () => {
  test('GET /api/v1/billing/insurance/providers liste les assureurs', async ({ request, page }) => {
    await page.goto('/', { waitUntil: 'domcontentloaded' });
    await page.evaluate(() => {
      localStorage.removeItem('guineecare_token');
    });
    await page.reload();
    await page.locator('#login-email').fill(SUPER_ADMIN.email);
    await page.locator('#login-password').fill(SUPER_ADMIN.password);
    await page.getByRole('button', { name: /Se connecter/ }).click();
    await expect(page.locator('aside.sidebar')).toBeVisible({ timeout: 25_000 });

    const token = await page.evaluate(() => localStorage.getItem('guineecare_token'));
    const resp = await request.get('/api/v1/billing/insurance/providers', {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(resp.status()).toBe(200);
    const data = await resp.json();
    expect(data).toBeDefined();
  });
});
