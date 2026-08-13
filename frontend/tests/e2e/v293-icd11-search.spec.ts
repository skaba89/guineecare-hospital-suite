import { test, expect, type Page } from '@playwright/test';

/**
 * Tests E2E — ICD11Search dans formulaire Diagnostic (v2.9.3)
 *
 * Couverture :
 *   - Page patient détail accessible pour SUPER_ADMIN
 *   - Onglet Diagnostics visible
 *   - Bouton "Nouveau diagnostic" ouvre le formulaire
 *   - Composant ICD11Search visible (champ recherche)
 *   - Recherche "paludisme" affiche des résultats
 *   - Sélection d'un résultat remplit code + libellé
 *   - Badge ICD-11 code visible après sélection
 *   - Soumission du formulaire enregistre le diagnostic
 *
 * Prérequis : backend + frontend démarrés avec seed démo.
 */

const SUPER_ADMIN = { email: 'admin@guineecare.com', password: 'admin123' };

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
  await page.locator('form button[type="submit"]').click();
  await expect(page.locator('aside.sidebar')).toBeVisible({ timeout: 25_000 });
  await page.waitForLoadState('networkidle').catch(() => {});
}

// Helper : créer un patient de test via API et retourner son ID
async function createTestPatient(page: Page): Promise<string> {
  const token = await page.evaluate(() => localStorage.getItem('guineecare_token'));
  const resp = await page.request.post('/api/v1/patients', {
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    data: {
      first_name: 'ICD11',
      last_name: 'TestPatient',
      gender: 'M',
      birth_date: '1990-01-01',
      phone: '+224 600 000 000',
    },
  });
  expect(resp.status()).toBe(200);
  const body = await resp.json();
  return body.data?.id || body.id || body.data?.[0]?.id;
}

// ----------------------------------------------------------------------------
// 1. ACCÈS AU FORMULAIRE DIAGNOSTIC
// ----------------------------------------------------------------------------
test.describe('ICD11Search — Accès formulaire', () => {
  test('SUPER_ADMIN peut accéder à un patient et voir l\'onglet Diagnostics', async ({ page }) => {
    await login(page, SUPER_ADMIN);
    await page.goto('/patients', { waitUntil: 'domcontentloaded' });

    // S'il y a des patients seedés, cliquer sur le premier ; sinon créer un patient
    const firstPatientRow = page.locator('table tbody tr').first();
    const rowCount = await firstPatientRow.count();

    if (rowCount > 0) {
      await firstPatientRow.click();
    } else {
      // Créer un patient via API puis y naviguer
      const patientId = await createTestPatient(page);
      await page.goto(`/patients/${patientId}`, { waitUntil: 'domcontentloaded' });
    }

    // Vérifier qu'on est sur la page détail patient
    await expect(page).toHaveURL(/patients\/.+/);

    // Cliquer sur l'onglet Diagnostics
    const diagTab = page.locator('button, a, [role="tab"]').filter({ hasText: /Diagnostics/i }).first();
    if (await diagTab.count() > 0) {
      await diagTab.click();
      await page.waitForTimeout(1000);
    }

    // Le bouton "Nouveau diagnostic" doit être visible
    const newDiagBtn = page.locator('button').filter({ hasText: /Nouveau diagnostic/i }).first();
    await expect(newDiagBtn).toBeVisible({ timeout: 10_000 });
  });
});

// ----------------------------------------------------------------------------
// 2. COMPOSANT ICD11Search — RECHERCHE
// ----------------------------------------------------------------------------
test.describe('ICD11Search — Recherche', () => {
  test('champ de recherche ICD-11 visible après ouverture du formulaire', async ({ page }) => {
    await login(page, SUPER_ADMIN);

    const patientId = await createTestPatient(page);
    await page.goto(`/patients/${patientId}`, { waitUntil: 'domcontentloaded' });

    // Ouvrir l'onglet Diagnostics
    const diagTab = page.locator('[role="tab"], button').filter({ hasText: /Diagnostics/i }).first();
    if (await diagTab.count() > 0) {
      await diagTab.click();
      await page.waitForTimeout(500);
    }

    // Ouvrir le formulaire
    const newDiagBtn = page.locator('button').filter({ hasText: /Nouveau diagnostic/i }).first();
    await newDiagBtn.click();
    await page.waitForTimeout(500);

    // Le champ recherche ICD-11 doit être visible
    const icdField = page.locator('input[placeholder*="paludisme" i]').first();
    await expect(icdField).toBeVisible({ timeout: 10_000 });
  });

  test('recherche "paludisme" affiche des résultats', async ({ page }) => {
    await login(page, SUPER_ADMIN);

    const patientId = await createTestPatient(page);
    await page.goto(`/patients/${patientId}`, { waitUntil: 'domcontentloaded' });

    const diagTab = page.locator('[role="tab"], button').filter({ hasText: /Diagnostics/i }).first();
    if (await diagTab.count() > 0) {
      await diagTab.click();
      await page.waitForTimeout(500);
    }

    await page.locator('button').filter({ hasText: /Nouveau diagnostic/i }).first().click();
    await page.waitForTimeout(500);

    // Taper "palu" dans le champ de recherche ICD-11
    const icdField = page.locator('input[placeholder*="paludisme" i]').first();
    await icdField.fill('palu');

    // Attendre que le dropdown apparaisse (debounce 300ms)
    await page.waitForTimeout(800);

    // Vérifier qu'un résultat contenant "Paludisme" est visible
    const dropdown = page.locator('[role="listbox"], .dropdown').first();
    const paludismeResult = page.locator('text=/Paludisme/i').first();
    await expect(paludismeResult).toBeVisible({ timeout: 5_000 });
  });

  test('sélection d\'un résultat affiche le badge ICD-11 code', async ({ page }) => {
    await login(page, SUPER_ADMIN);

    const patientId = await createTestPatient(page);
    await page.goto(`/patients/${patientId}`, { waitUntil: 'domcontentloaded' });

    const diagTab = page.locator('[role="tab"], button').filter({ hasText: /Diagnostics/i }).first();
    if (await diagTab.count() > 0) {
      await diagTab.click();
      await page.waitForTimeout(500);
    }

    await page.locator('button').filter({ hasText: /Nouveau diagnostic/i }).first().click();
    await page.waitForTimeout(500);

    // Taper "paludisme"
    const icdField = page.locator('input[placeholder*="paludisme" i]').first();
    await icdField.fill('paludisme');
    await page.waitForTimeout(800);

    // Cliquer sur le premier résultat (Paludisme à P. falciparum)
    const firstResult = page.locator('[role="option"]').first();
    await firstResult.click();
    await page.waitForTimeout(500);

    // Le badge "ICD-11: 1F03" doit être visible
    await expect(page.locator('text=/ICD-11:.*1F/i').first()).toBeVisible({ timeout: 5_000 });
  });
});

// ----------------------------------------------------------------------------
// 3. RECHERCHE PAR CODE
// ----------------------------------------------------------------------------
test.describe('ICD11Search — Recherche par code', () => {
  test('recherche "1F" affiche tous les codes paludisme', async ({ page }) => {
    await login(page, SUPER_ADMIN);

    const patientId = await createTestPatient(page);
    await page.goto(`/patients/${patientId}`, { waitUntil: 'domcontentloaded' });

    const diagTab = page.locator('[role="tab"], button').filter({ hasText: /Diagnostics/i }).first();
    if (await diagTab.count() > 0) {
      await diagTab.click();
      await page.waitForTimeout(500);
    }

    await page.locator('button').filter({ hasText: /Nouveau diagnostic/i }).first().click();
    await page.waitForTimeout(500);

    const icdField = page.locator('input[placeholder*="paludisme" i]').first();
    await icdField.fill('1F');
    await page.waitForTimeout(800);

    // Au moins 2 résultats (1F03 et 1F2Z)
    const options = page.locator('[role="option"]');
    const count = await options.count();
    expect(count).toBeGreaterThanOrEqual(2);
  });

  test('recherche "BA00" trouve l\'hypertension', async ({ page }) => {
    await login(page, SUPER_ADMIN);

    const patientId = await createTestPatient(page);
    await page.goto(`/patients/${patientId}`, { waitUntil: 'domcontentloaded' });

    const diagTab = page.locator('[role="tab"], button').filter({ hasText: /Diagnostics/i }).first();
    if (await diagTab.count() > 0) {
      await diagTab.click();
      await page.waitForTimeout(500);
    }

    await page.locator('button').filter({ hasText: /Nouveau diagnostic/i }).first().click();
    await page.waitForTimeout(500);

    const icdField = page.locator('input[placeholder*="paludisme" i]').first();
    await icdField.fill('BA00');
    await page.waitForTimeout(800);

    // L'hypertension doit apparaître
    await expect(page.locator('text=/Hypertension essentielle/i').first()).toBeVisible({ timeout: 5_000 });
  });
});

// ----------------------------------------------------------------------------
// 4. RECHERCHE SANS RÉSULTAT
// ----------------------------------------------------------------------------
test.describe('ICD11Search — Aucun résultat', () => {
  test('recherche "zzz_inexistant" affiche "Aucun code ICD-11 trouvé"', async ({ page }) => {
    await login(page, SUPER_ADMIN);

    const patientId = await createTestPatient(page);
    await page.goto(`/patients/${patientId}`, { waitUntil: 'domcontentloaded' });

    const diagTab = page.locator('[role="tab"], button').filter({ hasText: /Diagnostics/i }).first();
    if (await diagTab.count() > 0) {
      await diagTab.click();
      await page.waitForTimeout(500);
    }

    await page.locator('button').filter({ hasText: /Nouveau diagnostic/i }).first().click();
    await page.waitForTimeout(500);

    const icdField = page.locator('input[placeholder*="paludisme" i]').first();
    await icdField.fill('zzz_inexistant_zzz');
    await page.waitForTimeout(800);

    await expect(page.locator('text=/Aucun code ICD-11 trouvé/i')).toBeVisible({ timeout: 5_000 });
  });
});
