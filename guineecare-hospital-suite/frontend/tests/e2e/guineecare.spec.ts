import { test, expect, type Page } from '@playwright/test';

/**
 * Tests E2E Playwright — GuinéeCare Hospital Suite
 *
 * Prérequis :
 *   - Backend FastAPI sur http://127.0.0.1:8000 (avec seed démo)
 *   - Frontend Vite sur http://127.0.0.1:5173 (Vite proxy /api → backend)
 *
 * Couverture :
 *   - Authentification (login succès/échec, logout, multi-rôles)
 *   - Navigation pages admin (/users, /rbac, /facilities, /departments)
 *   - RBAC (DOCTOR/NURSE redirigés des pages admin)
 *   - Parcours patients
 *   - Dashboard
 */

const SUPER_ADMIN = { email: 'admin@guineecare.com', password: 'admin123' };
const DOCTOR = { email: 'dr.diallo@chu-donka.gn', password: 'doctor123' };
const NURSE = { email: 'inf.konde@chu-donka.gn', password: 'nurse123' };

/**
 * Connexion fiable :
 *   1. Vide localStorage pour repartir d'un état propre
 *   2. Charge la page de login
 *   3. Remplit les champs via leurs IDs stables
 *   4. Soumet le formulaire et attend l'apparition de la sidebar
 */
async function login(page: Page, creds: { email: string; password: string }) {
  // Clear any residual auth state from previous test
  await page.goto('/', { waitUntil: 'domcontentloaded' });
  await page.evaluate(() => {
    localStorage.removeItem('guineecare_token');
    localStorage.removeItem('guineecare_user');
  });
  await page.reload({ waitUntil: 'domcontentloaded' });

  // Wait for the login form to be ready
  const emailInput = page.locator('#login-email');
  await emailInput.waitFor({ state: 'visible', timeout: 15_000 });
  await emailInput.fill(creds.email);
  await page.locator('#login-password').fill(creds.password);

  // Submit + wait for sidebar (proves login succeeded)
  await page.getByRole('button', { name: /Se connecter/ }).click();
  await expect(page.locator('aside.sidebar')).toBeVisible({ timeout: 25_000 });

  // Wait for network idle so that subsequent navigation doesn't race with auth bootstrap
  await page.waitForLoadState('networkidle').catch(() => {});
}

// ----------------------------------------------------------------------------
// 1. AUTHENTIFICATION
// ----------------------------------------------------------------------------
test.describe('Authentification', () => {
  test('login SUPER_ADMIN réussit', async ({ page }) => {
    await login(page, SUPER_ADMIN);
    await expect(page.locator('aside.sidebar')).toBeVisible();
  });

  test('login avec mauvais mot de passe → message d\'erreur', async ({ page }) => {
    await page.goto('/');
    await page.evaluate(() => {
      localStorage.removeItem('guineecare_token');
      localStorage.removeItem('guineecare_user');
    });
    await page.reload({ waitUntil: 'domcontentloaded' });

    await page.locator('#login-email').fill('admin@guineecare.com');
    await page.locator('#login-password').fill('wrong-password');
    await page.getByRole('button', { name: /Se connecter/ }).click();
    await expect(page.locator('body')).toContainText(/impossible|incorrect|invalid/i, { timeout: 10_000 });
  });

  test('login DOCTOR réussit', async ({ page }) => {
    await login(page, DOCTOR);
    await expect(page.locator('aside.sidebar')).toBeVisible();
  });

  test('logout retourne à la page de login', async ({ page }) => {
    await login(page, SUPER_ADMIN);
    const logoutBtn = page.locator('.sidebar-logout-btn');
    await expect(logoutBtn).toBeVisible({ timeout: 10_000 });
    await logoutBtn.click();
    await expect(page.locator('#login-email')).toBeVisible({ timeout: 15_000 });
  });
});

// ----------------------------------------------------------------------------
// 2. PARCOURS PATIENTS
// ----------------------------------------------------------------------------
test.describe('Gestion patients', () => {
  test('page /patients accessible pour SUPER_ADMIN', async ({ page }) => {
    await login(page, SUPER_ADMIN);
    await page.goto('/patients', { waitUntil: 'domcontentloaded' });
    await expect(page).toHaveURL(/patients/i);
    await expect(page.locator('body')).toContainText(/patients/i, { timeout: 15_000 });
  });
});

// ----------------------------------------------------------------------------
// 3. PAGES ADMIN
// ----------------------------------------------------------------------------
test.describe('Pages admin (SUPER_ADMIN only)', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, SUPER_ADMIN);
  });

  test('page /users accessible', async ({ page }) => {
    await page.goto('/users', { waitUntil: 'domcontentloaded' });
    await expect(page).toHaveURL(/users/i);
    await expect(page.locator('body')).toContainText(/utilisateurs|users|user/i, { timeout: 15_000 });
  });

  test('page /rbac accessible', async ({ page }) => {
    await page.goto('/rbac', { waitUntil: 'domcontentloaded' });
    await expect(page).toHaveURL(/rbac/i);
    await expect(page.locator('body')).toContainText(/rôle|permission|role/i, { timeout: 15_000 });
  });

  test('page /facilities accessible', async ({ page }) => {
    await page.goto('/facilities', { waitUntil: 'domcontentloaded' });
    await expect(page).toHaveURL(/facilities/i);
    await expect(page.locator('body')).toContainText(/établissement|facility|hôpital/i, { timeout: 15_000 });
  });

  test('page /departments accessible', async ({ page }) => {
    await page.goto('/departments', { waitUntil: 'domcontentloaded' });
    await expect(page).toHaveURL(/departments/i);
    // The DepartmentsPage renders a ResourcePage with title "Départements"
    await expect(page.locator('h1, h2, .page-title, .resource-title').first()).toBeVisible({ timeout: 10_000 });
    await expect(page.locator('body')).toContainText(/département|department/i, { timeout: 15_000 });
  });
});

// ----------------------------------------------------------------------------
// 4. RBAC — DOCTOR/NURSE redirigés des pages admin
// ----------------------------------------------------------------------------
test.describe('RBAC restrictions', () => {
  test('DOCTOR redirigé de /users vers /', async ({ page }) => {
    await login(page, DOCTOR);
    await page.goto('/users', { waitUntil: 'domcontentloaded' });
    // Give the ProtectedRoute time to evaluate and redirect
    await page.waitForTimeout(2500);
    const url = page.url();
    const bodyText = (await page.locator('body').textContent() || '').toLowerCase();
    const redirected = !url.includes('/users');
    const hasForbidden = /403|interdit|forbidden|non autorisé|accès/.test(bodyText);
    expect(redirected || hasForbidden).toBeTruthy();
  });

  test('NURSE redirigé de /rbac vers /', async ({ page }) => {
    await login(page, NURSE);
    await page.goto('/rbac', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(2500);
    const url = page.url();
    const bodyText = (await page.locator('body').textContent() || '').toLowerCase();
    const redirected = !url.includes('/rbac');
    const hasForbidden = /403|interdit|forbidden|non autorisé|accès/.test(bodyText);
    expect(redirected || hasForbidden).toBeTruthy();
  });
});

// ----------------------------------------------------------------------------
// 5. DASHBOARD
// ----------------------------------------------------------------------------
test.describe('Dashboard SUPER_ADMIN', () => {
  test('affiche du contenu après login', async ({ page }) => {
    await login(page, SUPER_ADMIN);
    await expect(page.locator('body')).toContainText(/\d+/, { timeout: 15_000 });
  });
});

// ----------------------------------------------------------------------------
// 6. AUDIT LOG (v0.6.0)
// ----------------------------------------------------------------------------
test.describe('Journal d\'audit (v0.6.0)', () => {
  test('page /audit accessible pour SUPER_ADMIN', async ({ page }) => {
    await login(page, SUPER_ADMIN);
    await page.goto('/audit', { waitUntil: 'domcontentloaded' });
    await expect(page).toHaveURL(/audit/i);
    await expect(page.locator('h1')).toContainText(/audit/i, { timeout: 15_000 });
  });

  test('DOCTOR redirigé de /audit', async ({ page }) => {
    await login(page, DOCTOR);
    await page.goto('/audit', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(2500);
    const url = page.url();
    const redirected = !url.includes('/audit');
    expect(redirected).toBeTruthy();
  });
});

// ----------------------------------------------------------------------------
// 7. NOTIFICATIONS (v0.7.0)
// ----------------------------------------------------------------------------
test.describe('Notifications (v0.7.0)', () => {
  test('page /notifications accessible pour SUPER_ADMIN', async ({ page }) => {
    await login(page, SUPER_ADMIN);
    await page.goto('/notifications', { waitUntil: 'domcontentloaded' });
    await expect(page).toHaveURL(/notifications/i);
    await expect(page.locator('h1')).toContainText(/notifications/i, { timeout: 15_000 });
  });

  test('page /notifications accessible pour DOCTOR (boîte de réception personnelle)', async ({ page }) => {
    await login(page, DOCTOR);
    await page.goto('/notifications', { waitUntil: 'domcontentloaded' });
    await expect(page).toHaveURL(/notifications/i);
    await expect(page.locator('h1')).toContainText(/notifications/i, { timeout: 15_000 });
  });
});
