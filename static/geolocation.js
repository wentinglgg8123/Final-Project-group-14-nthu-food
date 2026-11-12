export default function(component) {
  const {parentElement, data, setTriggerValue} = component;
  const locate = parentElement.querySelector('[data-locate]');
  const clear = parentElement.querySelector('[data-clear]');
  const status = parentElement.querySelector('[data-status]');
  let disposed = false;
  let generation = 0;
  const send = (event) => {
    if (!disposed) setTriggerValue('event', {...event, nonce: `${Date.now()}-${Math.random()}`});
  };
  clear.hidden = !data?.active;
  locate.textContent = data?.active ? '⌖ 更新我的位置' : '⌖ 取得我的位置';
  locate.onclick = () => {
    if (!window.isSecureContext) { send({kind:'error',code:'insecure'}); return; }
    if (!navigator.geolocation) { send({kind:'error',code:'unsupported'}); return; }
    const request = ++generation;
    locate.disabled = true;
    clear.hidden = false;
    status.textContent = '正在定位，請回應瀏覽器的位置權限要求…';
    navigator.geolocation.getCurrentPosition((position) => {
      if (disposed || request !== generation) return;
      locate.disabled = false;
      status.textContent = '已取得位置';
      send({kind:'position',latitude:position.coords.latitude,longitude:position.coords.longitude,accuracy:position.coords.accuracy});
    }, (error) => {
      if (disposed || request !== generation) return;
      locate.disabled = false;
      status.textContent = '未能取得位置';
      send({kind:'error',code:({1:'denied',2:'unavailable',3:'timeout'})[error.code] || 'unavailable'});
    }, {enableHighAccuracy:true, timeout:12000, maximumAge:0});
  };
  clear.onclick = () => {
    ++generation;
    locate.disabled = false;
    send({kind:'clear'});
  };
  return () => { disposed = true; ++generation; locate.onclick = null; clear.onclick = null; };
}
