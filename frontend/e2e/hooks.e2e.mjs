// Regression: /dashboard, /imaging, /investigations must not crash when the patient
// case arrives after first render (hook-order change). Needs `vite dev` on :5173.
// Run: npm i --no-save playwright && node e2e/hooks.e2e.mjs   (CHROMIUM_PATH optional)
// e2e/case.json is a serialized PatientCase from src/lib/mock-data.ts (cases.primary).
import { chromium } from "playwright";
import fs from "fs";
const kase = JSON.parse(fs.readFileSync(new URL("./case.json", import.meta.url)));
const b = await chromium.launch({executablePath:process.env.CHROMIUM_PATH||undefined});
let fail=0;
for (const [route, expect] of [["/dashboard",/Operational Risk|Preparation|alert/i],["/imaging",/Pneumonia|X-ray|Heatmap/i],["/investigations",/ECG|Troponin/i]]) {
  const ctx = await b.newContext({viewport:{width:1440,height:900}});
  await ctx.addInitScript(()=>localStorage.setItem("current_intake_id","INT-T1"));
  const p = await ctx.newPage(); const errs=[];
  p.on("pageerror",e=>errs.push(e.message.slice(0,140)));
  p.on("console",m=>{if(m.type()==="error"&&/hook|Rendered more|Rendered fewer/i.test(m.text()))errs.push(m.text().slice(0,140))});
  await p.route("**/api/intake/INT-T1", async r=>{ await new Promise(s=>setTimeout(s,1500)); r.fulfill({status:200,contentType:"application/json",headers:{"access-control-allow-origin":"*"},body:JSON.stringify(kase)}) });
  await p.goto("http://localhost:5173"+route);
  await p.waitForTimeout(500);
  const before=(await p.locator("main").innerText()).includes("No patient selected");
  await p.waitForTimeout(3000);
  const txt=await p.locator("main").innerText();
  const ok = before && !errs.length && expect.test(txt) && !txt.includes("No patient selected");
  if(!ok)fail++;
  console.log(ok?"PASS":"FAIL",route,"emptyFirst="+before,"errors="+JSON.stringify(errs));
  await ctx.close();
}
await b.close(); process.exit(fail?1:0);
