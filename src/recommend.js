export const walks = { '清大校門': {'小吃部': 8, '清夜': 5}, '小吃部': {'小吃部': 2, '清夜': 12}, '清夜': {'小吃部': 12, '清夜': 3} };
export function localTime(date = new Date()) {
  const f = new Intl.DateTimeFormat('sv-SE', {timeZone:'Asia/Taipei', year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hour12:false});
  return f.format(date).replace(' ', 'T');
}
// The supplied value is a wall-clock time in Taiwan, independent of browser timezone.
export function openingStatus(r, time) {
  if (!time || !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/.test(time)) return {state:'unknown', label:'營業時間待確認'};
  const [date, clock] = time.split('T');
  const day = new Date(`${date}T12:00:00+08:00`).getUTCDay();
  if ((r.specialHours.includes('每週日') && day === 0) || (r.specialHours.includes('每週一') && day === 1)) return {state:'closed',label:'當日公休'};
  let hours = r.hours;
  if ((day === 0 || day === 6) && r.specialHours.includes('假日')) hours = r.specialHours.replace('假日','');
  if (!hours) return {state:'unknown',label:'營業時間待確認'};
  if (hours.includes('24小時')) return {state:'open',label:'營業中'};
  const minute = s => {const [h,m] = s.split(':').map(Number); return h * 60 + m;};
  const current = minute(clock);
  const spans = [...hours.matchAll(/(\d{1,2}:\d{2})~(\d{1,2}:\d{2})/g)];
  if (!spans.length) return {state:'unknown',label:'營業時間待確認'};
  const open = spans.some(([,start,end]) => {const a=minute(start), b=minute(end); return b > a ? current >= a && current < b : current >= a || current < b;});
  return {state:open?'open':'closed',label:open?'營業中':'非營業時間'};
}
export function recommend(restaurants, people, weights, options) {
  if (!people.length) return [];
  const total = weights.price + weights.distance + weights.type;
  return restaurants.flatMap(r => {
    const walk = walks[options.origin]?.[r.location];
    const status = openingStatus(r, options.time);
    if (options.openOnly && status.state !== 'open') return [];
    if (options.area !== '全部' && r.location !== options.area) return [];
    if (options.occasion !== '不限' && !r.occasions.includes(options.occasion)) return [];
    if (options.search && !`${r.name} ${r.types.join(' ')} ${r.location}`.toLowerCase().includes(options.search.toLowerCase().trim())) return [];
    const eligible = people.filter(p => r.price <= Number(p.budget) && walk <= Number(p.walk));
    if (options.strict && eligible.length !== people.length) return [];
    const parts = people.map(p => ({
      price:r.price <= Number(p.budget) ? 1 : Math.max(0,1-(r.price-Number(p.budget))/1.5),
      distance:walk <= Number(p.walk) ? 1 - 0.25 * walk / Number(p.walk) : Math.max(0, 0.6-(walk-Number(p.walk))/15),
      type:p.type === '不限' || r.types.includes(p.type) ? 1 : 0.15
    }));
    const avg = key => parts.reduce((sum,p) => sum + p[key], 0) / parts.length;
    const score = total ? Math.round(100*(avg('price')*weights.price+avg('distance')*weights.distance+avg('type')*weights.type)/total) : Math.round(100*(avg('price')+avg('distance')+avg('type'))/3);
    const liked = people.filter(p => p.type !== '不限' && r.types.includes(p.type)).length;
    const inBudget = people.filter(p=>r.price <= Number(p.budget)).length;
    const reasons = [liked ? `符合 ${liked} 人的料理偏好` : people.every(p=>p.type==='不限') ? '各種口味都願意試試' : '換個口味的新選擇', inBudget===people.length ? '符合所有人的預算' : `${inBudget}/${people.length} 人預算內`, `步行約 ${walk} 分鐘`];
    return [{...r, walk, status, score, reasons, eligible:eligible.length}];
  }).sort((a,b)=>b.score-a.score || a.walk-b.walk || a.price-b.price || a.id-b.id);
}
