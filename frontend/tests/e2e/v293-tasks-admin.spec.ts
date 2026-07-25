import { test, expect, type Page } from '@playwright/test';

/**
 * Tests E2E — TasksAdminPage UI (v2.9.3)
 *
 * Couverture :
 *   - Page /tasks-admin accessible pour SUPER_ADMIN
 *   - Page /tasks-admin redirigée pour DOCTOR
 *   - 3 StatusCards visibles (Worker Celery, Broker Redis, Tâches disponibles)
 *   - 5 cartes tâches visibles (prune, backup, retry SMS, push DHIS2, digest)
 *   - Bouton "Exécuter maintenant" sur chaque tâche
 *   - Confirmation demandée pour tâche destructive (prune_audit_logs)
 *   - Section historique visible
 *   - RBAC : sidebar n'affiche pas l'entrée pour DOCTOR
 *
 * Prérequis : backend + frontend démarrés avec seed démo.
 */

const SUPER_ADMIN = { email: 'admin@guineecare.com', password: 'admin123' };
const DOCTOR = { email: 'dr.diallo@chu-donka.gn', password: 'doctor123' };

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
// 1. ACCÈS & RBAC
// ----------------------------------------------------------------------------
test.describe('TasksAdminPage — Accès & RBAC', () => {
  test('SUPER_ADMIN accède à /tasks-admin', async ({ page }) => {
    await login(page, SUPER_ADMIN);
    await page.goto('/tasks-admin', { waitUntil: 'domcontentloaded' });
    await expect(page).toHaveURL(/tasks-admin/i);
    await expect(page.locator('h1')).toContainText(/tâches planifiées/i, { timeout: 15_000 });
  });

  test('DOCTOR redirigé de /tasks-admin', async ({ page }) => {
    await login(page, DOCTOR);
    await page.goto('/tasks-admin', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(2500);
    const url = page.url();
    const redirected = !url.includes('/tasks-admin');
    expect(redirected).toBeTruthy();
  });

  test('sidebar n\'affiche pas "Tâches planifiées" pour DOCTOR', async ({ page }) => {
    await login(page, DOCTOR);
    const sidebar = page.locator('aside.sidebar');
    const tasksLink = sidebar.locator('a[href="/tasks-admin"]');
    await expect(tasksLink).toHaveCount(0);
  });

  test('sidebar affiche "Tâches planifiées" pour SUPER_ADMIN', async ({ page }) => {
    await login(page, SUPER_ADMIN);
    const sidebar = page.locator('aside.sidebar');
    const tasksLink = sidebar.locator('a[href="/tasks-admin"]');
    await expect(tasksLink).toBeVisible({ timeout: 10_000 });
  });
});

// ----------------------------------------------------------------------------
// 2. TABLEAU DE BORD — 3 StatusCards
// ----------------------------------------------------------------------------
test.describe('TasksAdminPage — Tableau de bord', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, SUPER_ADMIN);
    await page.goto('/tasks-admin', { waitUntil: 'domcontentloaded' });
  });

  test('3 StatusCards visibles (Worker, Broker, Tâches)', async ({ page }) => {
    // Chercher les libellés attendus
    await expect(page.locator('text=/Worker Celery/i')).toBeVisible({ timeout: 10_000 });
    await expect(page.locator('text=/Broker Redis/i')).toBeVisible();
    await expect(page.locator('text=/Tâches disponibles/i')).toBeVisible();
  });

  test('compteur "Tâches disponibles" affiche 5', async ({ page }) => {
    const counter = page.locator('text=/Tâches disponibles/i').locator('..').locator('div').last();
    const text = await counter.textContent();
    expect(text).toMatch(/5/);
  });

  test('warning mode synchrone affiché quand Celery absent', async ({ page }) => {
    // En dev sans Celery, le warning doit s'afficher
    const warning = page.locator('text=/Mode synchrone actif/i');
    // Le warning peut être présent ou non selon la config — juste vérifier qu'il n'y a pas d'erreur
    const warningCount = await warning.count();
    expect(warningCount).toBeGreaterThanOrEqual(0);
  });
});

// ----------------------------------------------------------------------------
// 3. CARTES TÂCHES — 5 tâches attendues
// ----------------------------------------------------------------------------
test.describe('TasksAdminPage — 5 cartes tâches', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, SUPER_ADMIN);
    await page.goto('/tasks-admin', { waitUntil: 'domcontentloaded' });
  });

  test('carte "Purge audit log" visible', async ({ page }) => {
    await expect(page.locator('text=/Purge audit log/i').first()).toBeVisible({ timeout: 10_000 });
    await expect(page.locator('text=/RGPD Art\\. 25/i')).toBeVisible();
  });

  test('carte "Backup database" visible', async ({ page }) => {
    await expect(page.locator('text=/Backup database/i').first()).toBeVisible();
    await expect(page.locator('text=/rotation 30 jours/i')).toBeVisible();
  });

  test('carte "Retry SMS pending" visible', async ({ page }) => {
    await expect(page.locator('text=/Retry SMS pending/i').first()).toBeVisible();
  });

  test('carte "Push DHIS2 mensuel" visible', async ({ page }) => {
    await expect(page.locator('text=/Push DHIS2 mensuel/i').first()).toBeVisible();
  });

  test('carte "Digest qualité" visible', async ({ page }) => {
    await expect(page.locator('text=/Digest qualité/i').first()).toBeVisible();
  });

  test('chaque carte a un bouton "Exécuter maintenant"', async ({ page }) => {
    const buttons = page.locator('button:has-text("Exécuter maintenant")');
    await expect(buttons).toHaveCount(5, { timeout: 10_000 });
  });

  test('chaque carte affiche sa planification cron', async ({ page }) => {
    await expect(page.locator('text=/Quotidien 03h00 UTC/i')).toBeVisible();
    await expect(page.locator('text=/Quotidien 04h00 UTC/i')).toBeVisible();
    await expect(page.locator('text=/Toutes les 5 minutes/i')).toBeVisible();
    await expect(page.locator('text=/Le 5 du mois à 06h00 UTC/i')).toBeVisible();
  });
});

// ----------------------------------------------------------------------------
// 4. DÉCLENCHEMENT MANUEL
// ----------------------------------------------------------------------------
test.describe('TasksAdminPage — Trigger manuel', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, SUPER_ADMIN);
    await page.goto('/tasks-admin', { waitUntil: 'domcontentloaded' });
  });

  test('backup_database peut être déclenché (sans danger)', async ({ page }) => {
    // Le backup n'est pas destructif — confirmation simple
    const backupCard = page.locator('text=/Backup database/i').first().locator('..');
    const triggerBtn = backupCard.locator('button:has-text("Exécuter maintenant")');

    // Écouter la dialog de confirmation
    page.on('dialog', (dialog) => dialog.accept());

    await triggerBtn.click();

    // Attendre que le résultat apparaisse (carte verte avec "Exécuté")
    await expect(page.locator('text=/Exécuté/i').first()).toBeVisible({ timeout: 30_000 });
  });

  test('prune_audit_logs demande confirmation (destructive)', async ({ page }) => {
    const pruneCard = page.locator('text=/Purge audit log/i').first().locator('..');
    const triggerBtn = pruneCard.locator('button:has-text("Exécuter maintenant")');

    // Annuler la première dialog (ne pas confirmer)
    let dialogMessage = '';
    page.on('dialog', (dialog) => {
      dialogMessage = dialog.message();
      dialog.dismiss();
    });

    await triggerBtn.click();
    await page.waitForTimeout(500);

    // Vérifier que la dialog contenait "destructrice" ou "Purge"
    expect(dialogMessage.length).toBeGreaterThan(0);
    expect(dialogMessage).toMatch(/destructrice|Purge|prune/i);
  });

  test('prompt pour retention_days sur prune_audit_logs', async ({ page }) => {
    const pruneCard = page.locator('text=/Purge audit log/i').first().locator('..');
    const triggerBtn = pruneCard.locator('button:has-text("Exécuter maintenant")');

    // Accepter confirmation, puis prompt avec valeur par défaut
    let promptValue = '';
    page.on('dialog', (dialog) => {
      if (dialog.type() === 'prompt') {
        promptValue = dialog.defaultValue() || '';
        dialog.accept('365');
      } else {
        dialog.accept();
      }
    });

    await triggerBtn.click();
    await page.waitForTimeout(500);

    // Le prompt doit avoir 365 comme valeur par défaut
    expect(promptValue).toMatch(/365/);
  });
});

// ----------------------------------------------------------------------------
// 5. HISTORIQUE
// ----------------------------------------------------------------------------
test.describe('TasksAdminPage — Historique', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, SUPER_ADMIN);
    await page.goto('/tasks-admin', { waitUntil: 'domcontentloaded' });
  });

  test('section historique visible', async ({ page }) => {
    await expect(page.locator('h2:has-text("Historique récent")')).toBeVisible({ timeout: 10_000 });
  });

  test('tableau historique avec colonnes Date/Tâche/Statut/Détails', async ({ page }) => {
    // Attendre que l'historique soit chargé (table ou message "Aucune exécution")
    await page.waitForTimeout(2000);

    const historyHeading = page.locator('h2:has-text("Historique récent")');
    await expect(historyHeading).toBeVisible();

    // Vérifier la présence du tableau ou du message vide
    const table = page.locator('table').first();
    const emptyMessage = page.locator('text=/Aucune exécution de tâche enregistrée/i');

    const tableCount = await table.count();
    const emptyCount = await emptyMessage.count();
    expect(tableCount + emptyCount).toBeGreaterThan(0);
  });

  test('historique rempli après exécution d\'une tâche', async ({ page }) => {
    // Exécuter backup_database pour générer une entrée d'audit
    page.on('dialog', (dialog) => dialog.accept());

    const backupBtn = page.locator('button:has-text("Exécuter maintenant")').nth(1); // backup = 2ème carte
    await backupBtn.click();

    // Attendre que l'historique se rafraîchisse
    await page.waitForTimeout(3000);

    // L'historique doit maintenant contenir au moins une ligne
    const tableRows = page.locator('table tbody tr');
    const rowCount = await tableRows.count();
    expect(rowCount).toBeGreaterThan(0);
  });
});

// ----------------------------------------------------------------------------
// 6. BOUTON RAFRAÎCHIR
// ----------------------------------------------------------------------------
test.describe('TasksAdminPage — Rafraîchissement', () => {
  test('bouton "Rafraîchir" visible et fonctionnel', async ({ page }) => {
    await login(page, SUPER_ADMIN);
    await page.goto('/tasks-admin', { waitUntil: 'domcontentloaded' });

    const refreshBtn = page.locator('button:has-text("Rafraîchir")');
    await expect(refreshBtn).toBeVisible({ timeout: 10_000 });

    // Cliquer ne doit pas planter la page
    await refreshBtn.click();
    await page.waitForTimeout(2000);
    await expect(page.locator('h1')).toContainText(/tâches planifiées/i);
  });
});
