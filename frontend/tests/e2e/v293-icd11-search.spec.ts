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
 *   - Recherche par code et état sans résultat
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

async function createTestPatient(page: Page): Promise<string> {
  const token = await page.evaluate(() => localStorage.getItem('guineecare_token'));
  expect(token).toBeTruthy();

  const resp = await page.request.post('/api/v1/patients', {
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    data: {
      first_name: 'ICD11',
      last_name: 'TestPatient',
      gender: 'M',
      date_of_birth: '1990-01-01',
      phone: '+224 600 000 000',
    },
  });

  expect(resp.status()).toBe(200);
  const body = await resp.json();
  const patientId = body.data?.id || body.id || body.data?.[0]?.id;
  expect(patientId).toBeTruthy();
  return patientId;
}

/**
 * Attend explicitement le rendu du dossier patient avant d'interagir avec les
 * onglets. `domcontentloaded` n'implique pas que la requête patient React soit
 * terminée : l'ancien test faisait count() pendant l'écran "Chargement…" et
 * sautait silencieusement le clic Diagnostics.
 */
async function openDiagnostics(page: Page, patientId: string) {
  await page.goto(`/patients/${patientId}`, { waitUntil: 'domcontentloaded' });
  await expect(page).toHaveURL(new RegExp(`/patients/${patientId}`));

  const diagnosticsTab = page.getByRole('button', { name: /^Diagnostics$/i });
  await expect(diagnosticsTab).toBeVisible({ timeout: 15_000 });
  await diagnosticsTab.click();

  const newDiagnosticButton = page.getByRole('button', { name: /Nouveau diagnostic/i });
  await expect(newDiagnosticButton).toBeVisible({ timeout: 10_000 });
  return newDiagnosticButton;
}

async function openDiagnosticForm(page: Page, patientId: string) {
  const newDiagnosticButton = await openDiagnostics(page, patientId);
  await newDiagnosticButton.click();

  const icdField = page.locator('input[placeholder*="paludisme" i]').first();
  await expect(icdField).toBeVisible({ timeout: 10_000 });
  return icdField;
}

// ----------------------------------------------------------------------------
// 1. ACCÈS AU FORMULAIRE DIAGNOSTIC
// ----------------------------------------------------------------------------
test.describe('ICD11Search — Accès formulaire', () => {
  test('SUPER_ADMIN peut accéder à un patient et voir l\'onglet Diagnostics', async ({ page }) => {
    await login(page, SUPER_ADMIN);
    const patientId = await createTestPatient(page);

    const newDiagnosticButton = await openDiagnostics(page, patientId);
    await expect(newDiagnosticButton).toBeVisible();
  });
});

// ----------------------------------------------------------------------------
// 2. COMPOSANT ICD11Search — RECHERCHE
// ----------------------------------------------------------------------------
test.describe('ICD11Search — Recherche', () => {
  test('champ de recherche ICD-11 visible après ouverture du formulaire', async ({ page }) => {
    await login(page, SUPER_ADMIN);
    const patientId = await createTestPatient(page);

    const icdField = await openDiagnosticForm(page, patientId);
    await expect(icdField).toBeVisible();
  });

  test('recherche "paludisme" affiche des résultats', async ({ page }) => {
    await login(page, SUPER_ADMIN);
    const patientId = await createTestPatient(page);
    const icdField = await openDiagnosticForm(page, patientId);

    await icdField.fill('palu');

    // L'assertion attend le debounce et le rendu des résultats sans sommeil fixe.
    await expect(page.getByRole('option').first()).toBeVisible({ timeout: 5_000 });
    await expect(page.getByText(/Paludisme/i).first()).toBeVisible();
  });

  test('sélection d\'un résultat affiche le badge ICD-11 code', async ({ page }) => {
    await login(page, SUPER_ADMIN);
    const patientId = await createTestPatient(page);
    const icdField = await openDiagnosticForm(page, patientId);

    await icdField.fill('paludisme');
    const firstResult = page.getByRole('option').first();
    await expect(firstResult).toBeVisible({ timeout: 5_000 });
    await firstResult.click();

    await expect(page.getByText(/ICD-11:.*1F/i).first()).toBeVisible({ timeout: 5_000 });
  });
});

// ----------------------------------------------------------------------------
// 3. RECHERCHE PAR CODE
// ----------------------------------------------------------------------------
test.describe('ICD11Search — Recherche par code', () => {
  test('recherche "1F" affiche tous les codes paludisme', async ({ page }) => {
    await login(page, SUPER_ADMIN);
    const patientId = await createTestPatient(page);
    const icdField = await openDiagnosticForm(page, patientId);

    await icdField.fill('1F');

    const options = page.getByRole('option');
    await expect(options.first()).toBeVisible({ timeout: 5_000 });
    await expect.poll(() => options.count(), { timeout: 5_000 }).toBeGreaterThanOrEqual(2);
  });

  test('recherche "BA00" trouve l\'hypertension', async ({ page }) => {
    await login(page, SUPER_ADMIN);
    const patientId = await createTestPatient(page);
    const icdField = await openDiagnosticForm(page, patientId);

    await icdField.fill('BA00');
    await expect(page.getByText(/Hypertension essentielle/i).first()).toBeVisible({ timeout: 5_000 });
  });
});

// ----------------------------------------------------------------------------
// 4. RECHERCHE SANS RÉSULTAT
// ----------------------------------------------------------------------------
test.describe('ICD11Search — Aucun résultat', () => {
  test('recherche "zzz_inexistant" affiche "Aucun code ICD-11 trouvé"', async ({ page }) => {
    await login(page, SUPER_ADMIN);
    const patientId = await createTestPatient(page);
    const icdField = await openDiagnosticForm(page, patientId);

    await icdField.fill('zzz_inexistant_zzz');
    await expect(page.getByText(/Aucun code ICD-11 trouvé/i)).toBeVisible({ timeout: 5_000 });
  });
});
