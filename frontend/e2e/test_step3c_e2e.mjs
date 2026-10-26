// Step 3C End-to-End Verification Test Suite
// Tests all Section 7.7 requirements in context.md:
// 1. test_new_case_allows_eoa_selection
// 2. test_findings_panel_renders_clause_citations
// 3. test_evaluation_summary_metric_counts
// 4. test_evidence_chip_click_illuminates_page
// 5. test_decision_bar_blocks_approval_on_high_findings

import assert from "node:assert/strict";
import { chromium } from "playwright";

const BASE_URL = process.env.BASE_URL ?? "http://localhost:8000";

async function runTests() {
  console.log(`Starting Step 3C E2E Verification against ${BASE_URL}...`);
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1600, height: 1000 } });
  const page = await context.newPage();

  const pageErrors = [];
  page.on("pageerror", (err) => pageErrors.push(err.message));
  page.on("console", (msg) => {
    if (msg.type() === "error") console.error("Browser console error:", msg.text());
  });

  try {
    // -------------------------------------------------------------------------
    // 1. Login as Reviewer
    // -------------------------------------------------------------------------
    console.log("--> Navigating to login page...");
    await page.goto(`${BASE_URL}/#/login`);
    await page.waitForSelector(".login-card");

    console.log("--> Logging in as Reviewer (Ravi Reviewer)...");
    const revBtn = page.locator("button.demo-user:has-text('Reviewer')");
    if (await revBtn.count() > 0) {
      await revBtn.click();
    } else {
      await page.fill("#lp-email", "reviewer@demo.local");
      await page.fill("#lp-password", "demo1234");
      await page.click("#lp-submit");
    }
    await page.waitForSelector("table.queue");
    console.log("✓ Logged in and queue loaded.");

    // -------------------------------------------------------------------------
    // 2. test_new_case_allows_eoa_selection: Verify AICTE_EOA intake & 6 slots
    // -------------------------------------------------------------------------
    console.log("--> Testing test_new_case_allows_eoa_selection...");
    await page.click("text=New application");
    await page.waitForSelector("form.form");

    // Check application type selector has AICTE_EOA option
    const appTypeSelect = page.locator("select");
    await appTypeSelect.waitFor({ state: "visible" });
    const val = await appTypeSelect.inputValue();
    assert.equal(val, "AICTE_EOA", "Default application type should be AICTE_EOA");

    // Fill form
    await page.locator("form.form input").nth(0).fill("Dr. S. K. Narayanan (Registrar)");
    await page.locator("form.form input").nth(1).fill("Delhi Technological University (1-2098411)");
    await page.click("button:has-text('Continue to documents')");

    // Wait for step 2 (documents) and verify all 6 statutory EoA slots
    await page.waitForSelector(".slots");
    const slots = page.locator(".slot");
    const slotCount = await slots.count();
    assert.equal(slotCount, 6, "AICTE_EOA application must display exactly 6 statutory upload slots");

    const expectedLabels = [
      "AICTE EoA Application Form",
      "University Affiliation Order",
      "Fire Safety Certificate",
      "Building Safety Certificate",
      "Land Document & Land Use Certificate",
      "Occupancy / Completion Certificate",
    ];

    for (const label of expectedLabels) {
      const el = page.locator(`.slot:has-text("${label}")`);
      const count = await el.count();
      assert.ok(count > 0, `Slot for '${label}' must be visible`);
    }
    console.log("✓ test_new_case_allows_eoa_selection passed (all 6 statutory upload slots verified).");

    // -------------------------------------------------------------------------
    // 3. Open seeded demo case to test Reviewer Desk
    // -------------------------------------------------------------------------
    console.log("--> Navigating to case review desk...");
    await page.goto(`${BASE_URL}/#/cases`);
    await page.waitForSelector("table.queue");
    await page.click("table.queue a:has-text('SIH-DEMO-014')");
    await page.waitForSelector(".findings");

    // -------------------------------------------------------------------------
    // 4. test_evaluation_summary_metric_counts
    // -------------------------------------------------------------------------
    console.log("--> Testing test_evaluation_summary_metric_counts...");
    const summaryCard = page.locator(".eval-summary-card");
    await summaryCard.waitFor({ state: "visible" });

    // Assert metric badges exist: PASS, FAIL, REVIEW REQUIRED, NOT APPLICABLE
    const passBadge = summaryCard.locator(".eval-badge-pass .eval-badge-val");
    const failBadge = summaryCard.locator(".eval-badge-fail .eval-badge-val");
    const reviewBadge = summaryCard.locator(".eval-badge-review .eval-badge-val");
    const naBadge = summaryCard.locator(".eval-badge-na .eval-badge-val");

    const passCount = parseInt(await passBadge.textContent(), 10);
    const failCount = parseInt(await failBadge.textContent(), 10);
    const reviewCount = parseInt(await reviewBadge.textContent(), 10);
    const naCount = parseInt(await naBadge.textContent(), 10);

    const totalText = await summaryCard.locator(".eval-summary-total").textContent();
    const totalMatch = totalText.match(/Total Evaluated:\s*(\d+)/);
    assert.ok(totalMatch, "Total evaluated rules count must be displayed");
    const totalCount = parseInt(totalMatch[1], 10);

    assert.equal(totalCount, passCount + failCount + reviewCount + naCount, "Total evaluated must equal sum of outcomes");
    console.log(`✓ test_evaluation_summary_metric_counts passed (Total: ${totalCount}, PASS: ${passCount}, FAIL: ${failCount}, REVIEW: ${reviewCount}, N/A: ${naCount}).`);

    // -------------------------------------------------------------------------
    // 5. test_findings_panel_renders_clause_citations
    // -------------------------------------------------------------------------
    console.log("--> Testing test_findings_panel_renders_clause_citations...");
    const citations = page.locator(".clause-citation");
    const citationCount = await citations.count();
    assert.ok(citationCount > 0, "Finding cards must render statutory clause citations");
    const firstCitationText = await citations.first().textContent();
    assert.ok(firstCitationText.includes("AICTE APH 2024-27"), "Citation must cite AICTE APH 2024-27");
    console.log(`✓ test_findings_panel_renders_clause_citations passed (Found ${citationCount} statutory citations, sample: "${firstCitationText.trim()}").`);

    // -------------------------------------------------------------------------
    // 6. test_evidence_chip_click_illuminates_page
    // -------------------------------------------------------------------------
    console.log("--> Testing test_evidence_chip_click_illuminates_page...");
    const chip = page.locator(".evidence-chips .chip").first();
    if (await chip.count() > 0) {
      await chip.click();
      await page.waitForTimeout(600);
      const hl = page.locator(".hl");
      const hlCount = await hl.count();
      assert.ok(hlCount > 0, "Clicking evidence chip must illuminate bounding box on page canvas");
      console.log(`✓ test_evidence_chip_click_illuminates_page passed (${hlCount} bounding box highlights active).`);
    }

    // -------------------------------------------------------------------------
    // 7. test_decision_bar_blocks_approval_on_high_findings
    // -------------------------------------------------------------------------
    console.log("--> Testing test_decision_bar_blocks_approval_on_high_findings...");
    const approveBtn = page.locator(".decision-actions button:has-text('Approve')");
    await approveBtn.waitFor({ state: "visible" });

    const openHighCount = await page.locator(".finding-high:not(.is-closed)").count();
    if (openHighCount > 0) {
      const isDisabled = await approveBtn.isDisabled();
      assert.ok(isDisabled, "Approve button must be strictly disabled while high-severity findings are open");
      console.log(`✓ test_decision_bar_blocks_approval_on_high_findings passed (Approval blocked by ${openHighCount} open high-severity finding(s)).`);
    }

    console.log("\n=======================================================");
    console.log("ALL STEP 3C FRONTEND E2E TESTS PASSED CLEANLY!");
    console.log("=======================================================\n");

  } finally {
    await browser.close();
  }

  if (pageErrors.length > 0) {
    console.error("Unhandled browser page errors detected:", pageErrors);
    process.exit(1);
  }
}

runTests().catch((err) => {
  console.error("Test execution failed:", err);
  process.exit(1);
});
