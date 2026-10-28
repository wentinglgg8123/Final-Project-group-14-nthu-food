import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {recommend, openingStatus, localTime} from '../src/recommend.js';
const data=JSON.parse(readFileSync(new URL('../src/restaurants.json',import.meta.url)));
const weights={price:35,distance:30,type:35};
const people=[{budget:2.5,walk:15,type:'不限'}];
const options={origin:'清大校門',time:'2026-10-28T12:00',strict:true,area:'全部',occasion:'不限'};
test('all 14 supplied restaurants are available and score ordering is deterministic',()=>{
 const results=recommend(data,people,weights,options);assert.equal(results.length,14);
 assert.ok(results.every((r,i)=>r.score>=0&&r.score<=100&&(!i||results[i-1].score>=r.score)));
});
test('each diner budget and walk limit is respected, including a new restrictive diner',()=>{
 const results=recommend(data,[...people,{budget:1,walk:5,type:'不限'}],weights,options);
 assert.equal(results.length,1);assert.equal(results[0].name,'立晉豆花');
});
test('cuisine weight changes ranking and gives preference explanations',()=>{
 const results=recommend(data,[{...people[0],type:'火鍋'}],{price:0,distance:0,type:100},options);
 assert.match(results[0].name,/六扇門/);assert.equal(results[0].score,100);assert.match(results[0].reasons[0],/1 人/);
});
test('holiday hours and weekly closures follow Taiwan calendar',()=>{
 const bun=data.find(r=>r.id===1), breakfast=data.find(r=>r.id===4), dessert=data.find(r=>r.id===13);
 assert.equal(openingStatus(bun,'2026-10-31T08:00').state,'closed');
 assert.equal(openingStatus(bun,'2026-10-30T08:00').state,'open');
 assert.equal(openingStatus(breakfast,'2026-11-01T10:00').state,'closed');
 assert.equal(openingStatus(dessert,'2026-11-02T13:00').state,'closed');
});
test('midnight, lunch breaks, unknown times and closing boundaries',()=>{
 assert.equal(openingStatus(data[12],'2026-10-28T00:00').state,'closed');
 assert.equal(openingStatus(data[12],'2026-10-28T23:59').state,'open');
 assert.equal(openingStatus(data[6],'2026-10-28T14:00').state,'closed');
 assert.equal(openingStatus(data[2],options.time).state,'unknown');
 assert.equal(openingStatus(data[4],'2026-10-28T03:00').state,'open');
 assert.equal(openingStatus(data[0],'').state,'unknown');
});
test('open-only excludes unknown hours, supports search, area, occasion, and empty results',()=>{
 const results=recommend(data,people,weights,{...options,openOnly:true});
 assert.ok(results.every(r=>r.status.state==='open'));assert.ok(!results.some(r=>r.id===3));
 assert.ok(recommend(data,people,weights,{...options,area:'清夜',occasion:'約會'}).every(r=>r.location==='清夜'&&r.occasions.includes('約會')));
 assert.equal(recommend(data,people,weights,{...options,search:'不存在的餐廳'}).length,0);
 assert.equal(recommend(data,people,weights,{...options,search:'咖哩'}).length,1);
});
test('zero weights fall back to equal weights and relaxed conditions keep alternatives',()=>{
 assert.ok(recommend(data,people,{price:0,distance:0,type:0},options).every(r=>Number.isFinite(r.score)));
 assert.equal(recommend(data,[{budget:1,walk:5,type:'不限'}],weights,{...options,strict:false}).length,14);
 assert.equal(localTime(new Date('2026-10-28T16:30:00Z')),'2026-10-29T00:30');
});
