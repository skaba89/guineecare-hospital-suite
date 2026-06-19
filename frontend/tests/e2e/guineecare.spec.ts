import { test, expect, type Page } from '@playwright/test';

/**
 * Tests E2E Playwright — GuinéeCare Hospital Suite
 *
 * Prérequis :
 *   - Backend FastAPI sur http://127.0.0.1:8000 (avec seed démo)
 *   - Frontend Vite sur http://127.0.0.1:5173 (Vite proxy /api → backend)
 *
 * Couverture :
 *   - Authentification (login succès/échec, logout)
 *   - Navigation pages admin (/users, /rbac, /facilities, /departments)
 *   - RBAC (DOCTOR/NURSE redirigés des pages admin)
 *   - Parcours patients
 *   - Dashboard
 *
 * Note : certains tests peuvent être flaky (re-render React asynchrone).
 * En cas d'échec intermittent, relancer : `npm run test:e2e`
 */

const SUPER_ADMIN = { email: 'admin@guineecare.com', password: 'admin123' };
const DOCTOR = { email: 'dr.diallo@chu-donka.gn', password: 'doctor123' };
const NURSE = { email: 'inf.konde@chu-donka.gn', password: 'nurse123' };

async function login(page: Page, creds: { email: string; password: string }) {
  await page.goto('/', { waitUntil: 'domcontentloaded' });

  // Si résidu d'un test précédent, se déconnecter
  const logoutBtn = page.locator('.sidebar-logout-btn, [title="Déconnexion"]');
  if (await logoutBtn.first().isVisible({ timeout: 1500 }).catch(() => false)) {
    await logoutBtn.first().click({ force: true });
    await page.getByLabel('Email').first().waitFor({ state: 'visible', timeout: 10_000 });
  }

  const emailInput = page.getByLabel('Email').first();
  await emailInput.waitFor({ state: 'visible', timeout: 15_000 });
  await emailInput.fill(creds.email);
  await page.getByLabel('Mot de passe').first().fill(creds.password);
  await page.getByRole('button', { name: /Se connecter/ }).click();
  await expect(page.locator('aside.sidebar')).toBeVisible({ timeout: 20_000 });
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
    await page.getByLabel('Email').first().fill('admin@guineecare.com');
    await page.getByLabel('Mot de passe').first().fill('wrong-password');
    await page.getByRole('button', { name: /Se connecter/ }).click();
    await expect(page.locator('body')).toContainText(/impossible|incorrect|invalid/i);
  });

  test('login DOCTOR réussit', async ({ page }) => {
    await login(page, DOCTOR);
    await expect(page.locator('aside.sidebar')).toBeVisible();
  });

  test('logout retourne à la page de login', async ({ page }) => {
    await login(page, SUPER_ADMIN);
    const logoutBtn = page.locator('.sidebar-logout-btn, [title="Déconnexion"]');
    await expect(logoutBtn.first()).toBeVisible();
    await logoutBtn.first().click({ force: true });
    await expect(page.getByRole('button', { name: /Se connecter/ })).toBeVisible({ timeout: 15_000 });
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
    await page.waitForTimeout(2000);
    const url = page.url();
    const bodyText = (await page.locator('body').textContent() || '').toLowerCase();
    const redirected = !url.includes('/users');
    const hasForbidden = /403|interdit|forbidden|non autorisé|accès/.test(bodyText);
    expect(redirected || hasForbidden).toBeTruthy();
  });

  test('NURSE redirigé de /rbac vers /', async ({ page }) => {
    await login(page, NURSE);
    await page.goto('/rbac', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(2000);
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
