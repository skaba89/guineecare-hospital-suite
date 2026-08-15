import { test, expect, type Dialog, type Page } from '@playwright/test';

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

type DialogSnapshot = {
  type: string;
  message: string;
  defaultValue: string;
};

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

function taskCard(page: Page, label: string) {
  return page.locator('.card').filter({ hasText: label }).first();
}

function statusCard(page: Page, label: string) {
  return page.locator('.card').filter({ hasText: label }).first();
}

async function expandSystemSectionIfPresent(page: Page) {
  const header = page
    .locator('button.sidebar-section-header')
    .filter({ hasText: /SYSTÈME|SYSTEM/i })
    .first();

  if ((await header.count()) === 0) return;
  if ((await header.getAttribute('aria-expanded')) !== 'true') {
    await header.click();
    await expect(header).toHaveAttribute('aria-expanded', 'true');
  }
}

function snapshotDialog(dialog: Dialog): DialogSnapshot {
  return {
    type: dialog.type(),
    message: dialog.message(),
    defaultValue: dialog.defaultValue(),
  };
}

async function clickWithDialogs(
  page: Page,
  click: () => Promise<void>,
  actions: Array<'accept' | 'dismiss'>,
): Promise<DialogSnapshot[]> {
  const snapshots: DialogSnapshot[] = [];
  let index = 0;
  let resolveDialogs!: (value: DialogSnapshot[]) => void;
  let rejectDialogs!: (reason?: unknown) => void;

  const dialogsHandled = new Promise<DialogSnapshot[]>((resolve, reject) => {
    resolveDialogs = resolve;
    rejectDialogs = reject;
  });

  const handler = async (dialog: Dialog) => {
    try {
      snapshots.push(snapshotDialog(dialog));
      const action = actions[index];
      index += 1;

      if (action === 'dismiss') {
        await dialog.dismiss();
      } else {
        await dialog.accept();
      }

      if (index === actions.length) {
        page.off('dialog', handler);
        resolveDialogs(snapshots);
      }
    } catch (error) {
      page.off('dialog', handler);
      rejectDialogs(error);
    }
  };

  page.on('dialog', handler);
  try {
    await click();
    return await dialogsHandled;
  } finally {
    page.off('dialog', handler);
  }
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
    await expect(page).not.toHaveURL(/\/tasks-admin(?:[/?#]|$)/, { timeout: 10_000 });
  });

  test('sidebar n\'affiche pas "Tâches planifiées" pour DOCTOR', async ({ page }) => {
    await login(page, DOCTOR);
    await expandSystemSectionIfPresent(page);
    await expect(page.locator('aside.sidebar a[href="/tasks-admin"]')).toHaveCount(0);
  });

  test('sidebar contient "Tâches planifiées" pour SUPER_ADMIN', async ({ page }) => {
    await login(page, SUPER_ADMIN);
    await expandSystemSectionIfPresent(page);
    const tasksLink = page.locator('aside.sidebar a[href="/tasks-admin"]');
    await expect(tasksLink).toHaveCount(1);
    await expect(tasksLink).toBeVisible();
  });
});

// ----------------------------------------------------------------------------
// 2. TABLEAU DE BORD — 3 StatusCards
// ----------------------------------------------------------------------------
test.describe('TasksAdminPage — Tableau de bord', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, SUPER_ADMIN);
    await page.goto('/tasks-admin', { waitUntil: 'domcontentloaded' });
    await expect(page.locator('h1')).toContainText(/tâches planifiées/i, { timeout: 15_000 });
  });

  test('3 StatusCards visibles (Worker, Broker, Tâches)', async ({ page }) => {
    await expect(statusCard(page, 'Worker Celery')).toBeVisible();
    await expect(statusCard(page, 'Broker Redis')).toBeVisible();
    await expect(statusCard(page, 'Tâches disponibles')).toBeVisible();
  });

  test('compteur "Tâches disponibles" affiche 5', async ({ page }) => {
    await expect(statusCard(page, 'Tâches disponibles')).toContainText('5');
  });

  test('mode synchrone est signalé quand Celery est absent', async ({ page }) => {
    const worker = statusCard(page, 'Worker Celery');
    await expect(worker).toBeVisible();
    const workerText = (await worker.textContent()) || '';

    if (/Synchrone/i.test(workerText)) {
      await expect(page.getByText(/Mode synchrone actif/i).first()).toBeVisible();
    }
  });
});

// ----------------------------------------------------------------------------
// 3. CARTES TÂCHES — 5 tâches attendues
// ----------------------------------------------------------------------------
test.describe('TasksAdminPage — 5 cartes tâches', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, SUPER_ADMIN);
    await page.goto('/tasks-admin', { waitUntil: 'domcontentloaded' });
    await expect(page.locator('h1')).toContainText(/tâches planifiées/i, { timeout: 15_000 });
  });

  test('carte "Purge audit log" visible', async ({ page }) => {
    const card = taskCard(page, 'Purge audit log');
    await expect(card).toBeVisible();
    await expect(card).toContainText(/RGPD Art\. 25/i);
  });

  test('carte "Backup database" visible', async ({ page }) => {
    const card = taskCard(page, 'Backup database');
    await expect(card).toBeVisible();
    await expect(card).toContainText(/rotation 30 jours/i);
  });

  test('carte "Retry SMS pending" visible', async ({ page }) => {
    await expect(taskCard(page, 'Retry SMS pending')).toBeVisible();
  });

  test('carte "Push DHIS2 mensuel" visible', async ({ page }) => {
    await expect(taskCard(page, 'Push DHIS2 mensuel')).toBeVisible();
  });

  test('carte "Digest qualité" visible', async ({ page }) => {
    await expect(taskCard(page, 'Digest qualité')).toBeVisible();
  });

  test('chaque carte a un bouton "Exécuter maintenant"', async ({ page }) => {
    const buttons = page.getByRole('button', { name: /Exécuter maintenant/i });
    await expect(buttons).toHaveCount(5, { timeout: 10_000 });
  });

  test('chaque carte affiche sa planification cron', async ({ page }) => {
    await expect(taskCard(page, 'Purge audit log')).toContainText(/Quotidien 03h00 UTC/i);
    await expect(taskCard(page, 'Backup database')).toContainText(/Quotidien 04h00 UTC/i);
    await expect(taskCard(page, 'Retry SMS pending')).toContainText(/Toutes les 5 minutes/i);
    await expect(taskCard(page, 'Push DHIS2 mensuel')).toContainText(/Le 5 du mois à 06h00 UTC/i);
    await expect(taskCard(page, 'Digest qualité')).toContainText(/Quotidien 06h30 UTC/i);
  });
});

// ----------------------------------------------------------------------------
// 4. DÉCLENCHEMENT MANUEL
// ----------------------------------------------------------------------------
test.describe('TasksAdminPage — Trigger manuel', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, SUPER_ADMIN);
    await page.goto('/tasks-admin', { waitUntil: 'domcontentloaded' });
    await expect(page.locator('h1')).toContainText(/tâches planifiées/i, { timeout: 15_000 });
  });

  test('backup_database peut être déclenché (sans danger)', async ({ page }) => {
    const backupCard = taskCard(page, 'Backup database');
    const triggerBtn = backupCard.getByRole('button', { name: /Exécuter maintenant/i });

    const [confirmation] = await clickWithDialogs(page, () => triggerBtn.click(), ['accept']);
    expect(confirmation.type).toBe('confirm');
    await expect(backupCard).toContainText(/Exécuté/i, { timeout: 30_000 });
  });

  test('prune_audit_logs demande confirmation destructive', async ({ page }) => {
    const pruneCard = taskCard(page, 'Purge audit log');
    const triggerBtn = pruneCard.getByRole('button', { name: /Exécuter maintenant/i });

    const [confirmation] = await clickWithDialogs(page, () => triggerBtn.click(), ['dismiss']);
    expect(confirmation.type).toBe('confirm');
    expect(confirmation.message).toMatch(/destructrice|Purge|prune/i);
  });

  test('prompt retention_days propose 365 sur prune_audit_logs', async ({ page }) => {
    const pruneCard = taskCard(page, 'Purge audit log');
    const triggerBtn = pruneCard.getByRole('button', { name: /Exécuter maintenant/i });

    const dialogs = await clickWithDialogs(page, () => triggerBtn.click(), ['accept', 'dismiss']);
    expect(dialogs).toHaveLength(2);
    expect(dialogs[0].type).toBe('confirm');
    expect(dialogs[1].type).toBe('prompt');
    expect(dialogs[1].defaultValue).toBe('365');
  });
});

// ----------------------------------------------------------------------------
// 5. HISTORIQUE
// ----------------------------------------------------------------------------
test.describe('TasksAdminPage — Historique', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, SUPER_ADMIN);
    await page.goto('/tasks-admin', { waitUntil: 'domcontentloaded' });
    await expect(page.locator('h1')).toContainText(/tâches planifiées/i, { timeout: 15_000 });
  });

  test('section historique visible', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /Historique récent/i })).toBeVisible();
  });

  test('historique affiche un tableau ou son état vide', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /Historique récent/i })).toBeVisible();

    const table = page.locator('table').first();
    const emptyMessage = page.getByText(/Aucune exécution de tâche enregistrée/i);
    await expect.poll(async () => (await table.count()) + (await emptyMessage.count()), {
      timeout: 10_000,
    }).toBeGreaterThan(0);

    if (await table.count()) {
      await expect(table.locator('thead')).toContainText(/Date/);
      await expect(table.locator('thead')).toContainText(/Tâche/);
      await expect(table.locator('thead')).toContainText(/Statut/);
      await expect(table.locator('thead')).toContainText(/Détails/);
    }
  });

  test('historique rempli après exécution d\'une tâche', async ({ page }) => {
    const backupCard = taskCard(page, 'Backup database');
    const triggerBtn = backupCard.getByRole('button', { name: /Exécuter maintenant/i });

    const [confirmation] = await clickWithDialogs(page, () => triggerBtn.click(), ['accept']);
    expect(confirmation.type).toBe('confirm');
    await expect(backupCard).toContainText(/Exécuté/i, { timeout: 30_000 });
    await expect(page.locator('table tbody tr').first()).toBeVisible({ timeout: 15_000 });
  });
});

// ----------------------------------------------------------------------------
// 6. BOUTON RAFRAÎCHIR
// ----------------------------------------------------------------------------
test.describe('TasksAdminPage — Rafraîchissement', () => {
  test('bouton "Rafraîchir" visible et fonctionnel', async ({ page }) => {
    await login(page, SUPER_ADMIN);
    await page.goto('/tasks-admin', { waitUntil: 'domcontentloaded' });
    await expect(page.locator('h1')).toContainText(/tâches planifiées/i, { timeout: 15_000 });

    const refreshBtn = page.getByRole('button', { name: /Rafraîchir/i });
    await expect(refreshBtn).toBeVisible();

    const tasksResponse = page.waitForResponse(
      (response) =>
        /\/api\/v1\/tasks(?:\?|$)/.test(response.url()) &&
        response.request().method() === 'GET' &&
        response.status() === 200,
      { timeout: 15_000 },
    );
    await refreshBtn.click();
    await tasksResponse;

    await expect(page.locator('h1')).toContainText(/tâches planifiées/i);
    await expect(statusCard(page, 'Tâches disponibles')).toContainText('5');
  });
});
