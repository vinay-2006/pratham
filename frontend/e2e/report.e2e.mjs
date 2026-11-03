// Regression: doctor report page must use top-level status/case_id/arrival_type from
// GET /api/report/:id (live status -> Close Case button vs closed state). Network is mocked.
// Needs `vite dev` on :5173. Run: npm i --no-save playwright && node e2e/report.e2e.mjs
import { chromium } from "playwright";
const base = (status) => ({
  intake_id:"INT-R1", generated_at:"2026-10-27T10:00:00", report_version:"5.0.0",
  status, case_id:"PRA-2026-ABC123", arrival_type:"ambulance", severity:"high", created_at:"2026-10-27T09:30:00",
  patient_summary:{patient_id:"P1",case_id:"PRA-2026-ABC123",name:"Test Patient",age:54,gender:"male",contact:null,chief_complaint:"Chest pain",emergency_description:"",severity:"high",allergies:[],medications:[],medical_history:[],arrival_time:"09:30"},
  vitals:{heart_rate:110,spo2:91,bp_systolic:100,bp_diastolic:60,blood_pressure:"100/60",temperature:37.1,respiratory_rate:22},
  symptoms:["chest pain"], nlp_findings:{flags:{},entities:[],summary:""},
  risk_engine:{cardiac:70,respiratory:30,trauma:0,neurological:0,severity:"high"},
  lab_intelligence:{available:false}, imaging_intelligence:{available:false},
  aggregation:{available:false,probabilities:{},evidence_breakdown:{},source_summary:{}},
  evidence:[], pipeline_status:{nlp:"completed",risk:"completed",lab:"pending",imaging:"pending",aggregation:"pending"},
  investigations:[], clinical_interpretation:{}, clinical_conclusions:{},
});
const b = await chromium.launch({executablePath:process.env.CHROMIUM_PATH||undefined});
let fail=0;
for (const status of ["clinical_report_ready","case_closed"]) {
  const ctx = await b.newContext({viewport:{width:1440,height:1000}});
  const p = await ctx.newPage(); const errs=[];
  p.on("pageerror",e=>errs.push(e.message.slice(0,160)));
  await p.route("**/api/report/INT-R1", r=>r.fulfill({status:200,contentType:"application/json",headers:{"access-control-allow-origin":"*"},body:JSON.stringify(base(status))}));
  await p.route("**/api/report/INT-R1/mark-reviewed", r=>r.fulfill({status:200,contentType:"application/json",headers:{"access-control-allow-origin":"*"},body:"{}"}));
  await p.route("**/api/**/workflow*", r=>r.fulfill({status:200,contentType:"application/json",headers:{"access-control-allow-origin":"*"},body:"[]"}));
  await p.goto("http://localhost:5173/doctor/report/INT-R1"); await p.waitForTimeout(2500);
  const t=await p.locator("body").innerText();
  const hasCase=t.includes("PRA-2026-ABC123"), hasAmb=/ambulance/i.test(t), hasClose=t.includes("Close Case"), closed=/Case Closed/.test(t);
  const ok = !errs.length && hasCase && hasAmb && (status==="case_closed" ? !hasClose : hasClose);
  if(!ok)fail++;
  console.log(ok?"PASS":"FAIL",status,{hasCase,hasAmb,hasClose,closed,errs});
  if(status==="case_closed") await p.screenshot({path:process.env.TMPDIR+"report_closed.png"});
  await ctx.close();
}
await b.close(); process.exit(fail?1:0);
