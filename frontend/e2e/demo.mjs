// End-to-end demo walkthrough. Start the app with seeded data first, then: npm run e2e
// Screenshots land in e2e/screenshots/. BASE_URL defaults to http://localhost:8000.
import { mkdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
const here = path.dirname(fileURLToPath(import.meta.url));
const BASE = process.env.BASE_URL ?? "http://localhost:8000";
const FIX = path.resolve(here, "../../backend/fixtures");
mkdirSync(path.join(here, "screenshots"), { recursive: true });
process.chdir(path.join(here, "screenshots"));
import { chromium } from "playwright";
const b = await chromium.launch();
const p = await b.newPage({ viewport: { width: 1600, height: 1000 } });
const errors = [];
p.on("pageerror", (e) => errors.push("pageerror: " + e.message));
p.on("console", (m) => { if (m.type() === "error") errors.push("console: " + m.text()); });
await p.goto(BASE + "/");
await p.waitForSelector(".login-card");
await p.screenshot({ path: "01-login.png" });
await p.click("button.demo-user:has-text(\"Reviewer\")");
await p.waitForSelector("table.queue");
await p.screenshot({ path: "02-queue.png" });
await p.click("text=SIH-DEMO-014");
await p.waitForSelector(".finding");
await p.waitForSelector(".page img");
await p.screenshot({ path: "03-case.png" });
// click CMP-001 finding -> highlight signature region
await p.click(".finding:has-text('CMP-001') .finding-main");
await p.waitForTimeout(900);
await p.screenshot({ path: "04-finding-highlight.png" });
// click CON-001 -> letter
await p.click(".finding:has-text('CON-001') .chip >> nth=1");
await p.waitForTimeout(1000);
await p.screenshot({ path: "05-con001.png" });
// correct total field
await p.click(".field:has-text('Total amount claimed') .field-edit");
await p.fill(".correct input >> nth=0", "Rs. 1,33,500.00");
await p.fill(".correct input >> nth=1", "Applicant confirmed the total by phone");
await p.click("text=Save correction");
await p.waitForSelector(".toast");
await p.waitForTimeout(600);
const ari = await p.locator(".finding:has-text('ARI-001')").count();
console.log("ARI-001 after correction:", ari);
// waive high findings
for (const rule of ["CMP-001", "CON-002"]) {
  await p.click(`.finding:has-text('${rule}') >> text=Waive`);
  await p.fill("dialog[open] textarea", "Verified with institution registrar by phone");
  await p.click("dialog[open] .modal-foot .btn-primary");
  await p.waitForTimeout(500);
}
await p.screenshot({ path: "06-after-waive.png" });
await p.click(".decision-actions >> text=Request clarification");
await p.selectOption("dialog[open] select", "SIGNATURE_REQUIRED");
await p.fill("dialog[open] textarea", "Please upload a signed application form.");
await p.screenshot({ path: "07-decision-modal.png" });
await p.click("dialog[open] .modal-foot >> text=Request clarification");
await p.waitForSelector(".status-clarification_requested");
await p.click("text=Case report");
await p.waitForSelector(".report");
await p.screenshot({ path: "08-report.png", fullPage: true });
// scanned case
await p.goto(BASE + "/#/cases");
await p.waitForSelector("table.queue");
await p.click("text=SIH-DEMO-015");
await p.waitForSelector(".page img");
await p.click(".doc-tab >> nth=2");
const enrollField = p.locator(".field:has-text('Enrolment number') .field-row");
if (await enrollField.count() > 0) {
  await enrollField.click();
} else {
  const anyField = p.locator(".field .field-row").first();
  if (await anyField.count() > 0) await anyField.click();
}
await p.waitForTimeout(800);
await p.screenshot({ path: "09-ocr.png" });
// mobile
await p.setViewportSize({ width: 390, height: 844 });
await p.goto(BASE + "/#/cases");
await p.waitForSelector("table.queue");
await p.screenshot({ path: "10-mobile.png" });
// applicant view + new application wizard
await p.setViewportSize({ width: 1400, height: 950 });
await p.click("text=Sign out");
await p.click("button.demo-user:has-text(\"Applicant\")");
await p.waitForSelector("table.queue");
await p.click("text=SIH-DEMO-014");
await p.waitForSelector(".banner-warn");
await p.screenshot({ path: "11-applicant.png" });
await p.click("text=New application");
await p.fill("input >> nth=0", "Meera Iyer");
await p.fill("input >> nth=1", "Northstar Technical Institute");
await p.click("text=Continue to documents");
await p.waitForSelector(".slots");
await p.setInputFiles("input[type=file] >> nth=0", FIX + "/cases/SIH-DEMO-013/application_form.pdf");
await p.waitForSelector(".slot-done");
await p.setInputFiles("input[type=file] >> nth=1", FIX + "/invalid/encrypted.pdf");
await p.waitForSelector(".slot-error");
await p.screenshot({ path: "12-wizard.png" });
console.log("ERRORS:", JSON.stringify(errors));
await b.close();
if (errors.some((e) => e.startsWith("pageerror"))) { console.error("Page errors found"); process.exit(1); }
console.log("E2E demo walkthrough passed.");
