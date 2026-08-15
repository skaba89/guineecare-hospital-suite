import { test, expect, type Dialog, type Page } from '@playwright/test';

const SUPER_ADMIN = { email: 'admin@guineecare.com', password: 'admin123' };

async function login(page: Page) {
  await page.goto('/', { waitUntil: 'domcontentloaded' });
  await page.evaluate(() => {
    localStorage.removeItem('guineecare_token');
    localStorage.removeItem('guineecare_user');
  });
  await page.reload({ waitUntil: 'domcontentloaded' });

  await page.locator('#login-email').waitFor({ state: 'visible', timeout: 15_000 });
  await page.locator('#login-email').fill(SUPER_ADMIN.email);
  await page.locator('#login-password').fill(SUPER_ADMIN.password);
  await page.locator('form button[type="submit"]').click();
  await expect(page.locator('aside.sidebar')).toBeVisible({ timeout: 25_000 });
}

test.describe('TasksAdmin — sécurité purge audit', () => {
  test('annuler le prompt de rétention n’émet aucun POST destructif', async ({ page }) => {
    await login(page);
    await page.goto('/tasks-admin', { waitUntil: 'domcontentloaded' });
    await expect(page.locator('h1')).toContainText(/tâches planifiées/i, { timeout: 15_000 });

    let destructivePosts = 0;
    page.on('request', (request) => {
      if (
        request.method() === 'POST' &&
        /\/api\/v1\/tasks\/trigger\/prune_audit_logs(?:\?|$)/.test(request.url())
      ) {
        destructivePosts += 1;
      }
    });

    const dialogTypes: string[] = [];
    let resolvePromptDismissed!: () => void;
    let rejectPromptDismissed!: (reason?: unknown) => void;
    const promptDismissed = new Promise<void>((resolve, reject) => {
      resolvePromptDismissed = resolve;
      rejectPromptDismissed = reject;
    });

    const handleDialog = async (dialog: Dialog) => {
      try {
        dialogTypes.push(dialog.type());
        if (dialog.type() === 'confirm') {
          await dialog.accept();
          return;
        }
        if (dialog.type() === 'prompt') {
          await dialog.dismiss();
          page.off('dialog', handleDialog);
          resolvePromptDismissed();
          return;
        }
        await dialog.dismiss();
      } catch (error) {
        page.off('dialog', handleDialog);
        rejectPromptDismissed(error);
      }
    };

    page.on('dialog', handleDialog);
    try {
      const pruneCard = page.locator('.card').filter({ hasText: 'Purge audit log' }).first();
      const triggerButton = pruneCard.getByRole('button', { name: /Exécuter maintenant/i });
      await expect(triggerButton).toBeVisible();

      await triggerButton.click();
      await promptDismissed;
      await expect(triggerButton).toBeEnabled();

      expect(dialogTypes).toEqual(['confirm', 'prompt']);
      expect(destructivePosts).toBe(0);
    } finally {
      page.off('dialog', handleDialog);
    }
  });
});
