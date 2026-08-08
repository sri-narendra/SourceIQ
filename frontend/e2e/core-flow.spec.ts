import { expect, test } from "@playwright/test";

const email = `e2e_${Date.now()}@testmail.dev`;
const password = "Testpass1!";

test("core flow: register, login, create workspace, chat", async ({ page }) => {
  await page.goto("/");

  await expect(page).toHaveURL(/\/login/);

  await page.getByTestId("submit").waitFor();

  await page.getByTestId("email").fill(email);
  await page.getByTestId("password").fill(password);
  await page.getByTestId("submit").click();

  await page.goto("/");
  await expect(page).toHaveURL(/\/login/);

  await page.getByText("Need an account? Register").click();
  await expect(page).toHaveURL(/\/login/);

  await page.getByTestId("name").fill("E2E Tester");
  await page.getByTestId("email").fill(email);
  await page.getByTestId("password").fill(password);
  await page.getByTestId("submit").click();

  await expect(page).toHaveURL(/\/dashboard/);

  await page.getByTestId("workspace-name").fill("My Workspace");
  await page.getByTestId("create-workspace").click();

  await expect(page.getByTestId("current-workspace")).toHaveText("My Workspace");

  await page.getByTestId("chat-input").fill("What is AI?");
  await page.getByTestId("send").click();

  await expect(page.getByTestId("chat-input")).toBeEnabled();
});
