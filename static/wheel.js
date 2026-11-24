const colors = ["#eaf3e6", "#f8e6c7", "#f2d9ce", "#d9e9f4", "#daeade"];

function radialBounds(direction, low, high) {
  if (Math.abs(direction) < 1e-9) {
    return low <= 0 && high >= 0 ? [-Infinity, Infinity] : [Infinity, -Infinity];
  }
  const start = low / direction;
  const end = high / direction;
  return direction > 0 ? [start, end] : [end, start];
}

function fitZoomedLabels(viewport, face, { zoom, size, winner }) {
  const diameter = viewport.getBoundingClientRect().width;
  if (!diameter) return;

  // The zoom is anchored at the top of the wheel. Express its visible window in wheel coordinates.
  const halfWidth = diameter / (2 * zoom);
  const top = -diameter / 2;
  const bottom = top + diameter / zoom;
  const rim = 0.46 * diameter;
  const sectorSlope = Math.tan(0.86 * Math.PI / size);
  const inset = 2 / zoom;
  const fitted = Array.from(face.querySelectorAll(".wheel-label"), label => {
    const style = getComputedStyle(label);
    const textWidth = Math.ceil(parseFloat(style.width));
    const textHeight = Math.ceil(parseFloat(style.height));
    const fontSize = parseFloat(style.fontSize);
    const offset = Number(label.dataset.wheelIndex) - winner;
    const angle = offset * 2 * Math.PI / size;
    const dx = Math.sin(angle);
    const dy = -Math.cos(angle);

    // The whole label must fit between the sector edges and inside the zoomed viewport.
    const endAtScale = scale => {
      const halfHeight = textHeight * scale / 2;
      const padX = inset + Math.abs(dy) * halfHeight;
      const padY = inset + Math.abs(dx) * halfHeight;
      const [left, right] = radialBounds(dx, -halfWidth + padX, halfWidth - padX);
      const [upper, lower] = radialBounds(dy, top + padY, bottom - padY);
      const start = Math.max(left, upper, halfHeight / sectorSlope);
      const end = Math.min(right, lower, rim);
      return end - start >= textWidth * scale ? end : null;
    };

    if (endAtScale(0) === null) return { label, end: rim, scale: 0, hasRoom: false };
    let lower = 0;
    let upper = Math.min(16, diameter * .048) / (fontSize * zoom);
    for (let attempt = 0; attempt < 10; attempt++) {
      const scale = (lower + upper) / 2;
      if (endAtScale(scale) === null) upper = scale;
      else lower = scale;
    }
    const nearWinner = Math.min(Math.abs(offset), size - Math.abs(offset)) <= 1;
    const hasRoom = lower > 0 && (nearWinner || fontSize * lower * zoom >= 8);
    return { label, end: endAtScale(lower), scale: lower, hasRoom };
  });
  for (const { label, end, scale, hasRoom } of fitted) {
    label.style.setProperty("--wheel-zoom-label-end", `${end ?? rim}px`);
    label.style.setProperty("--wheel-zoom-label-scale", String(scale));
    label.toggleAttribute("data-wheel-label-outside", !hasRoom);
  }
}

export default function ({ parentElement, data }) {
  const wheel = parentElement.querySelector(".restaurant-wheel");
  const viewport = wheel.querySelector(".wheel-viewport");
  const face = viewport.querySelector(".wheel-face");
  const rotor = wheel.querySelector(".wheel-rotor");
  const status = parentElement.querySelector(".wheel-status");
  const { names, winner, start, spin } = data;
  const size = names.length;
  const sparse = size <= 8;
  const zoom = sparse ? 1.12 : size <= 12 ? 2.25 : size <= 35 ? 3.1 : 3.6;
  const motion = window.matchMedia("(prefers-reduced-motion: no-preference)").matches;
  const widthFraction = size <= 4 ? .30 : sparse ? .22 : size <= 12 ? .36 : size <= 35 ? .25 : .18;
  const fitZoom = () => fitZoomedLabels(viewport, face, { zoom, size, winner });
  let disconnect;
  if (motion && !sparse && spin !== null) {
    const refit = () => {
      if (wheel.hasAttribute("data-wheel-stopped")) fitZoom();
    };
    const observer = new ResizeObserver(refit);
    observer.observe(viewport);
    document.fonts.addEventListener("loadingdone", refit);
    disconnect = () => {
      observer.disconnect();
      document.fonts.removeEventListener("loadingdone", refit);
    };
  }
  const signature = JSON.stringify(data);
  if (wheel.dataset.draw === signature) return disconnect;
  wheel.dataset.draw = signature;
  wheel.removeAttribute("data-wheel-stopped");
  wheel.removeAttribute("data-wheel-spinning");
  wheel.classList.toggle("wheel-sparse", sparse);
  status.textContent = "";
  for (const animation of rotor.getAnimations()) animation.cancel();

  const step = 360 / size;
  const stopAngle = -winner * step;
  const zoomNeighborLimit = size > 120 ? Math.ceil(Math.atan(1 / (zoom - 2)) * 180 / Math.PI / step) : 0;
  wheel.style.setProperty("--wheel-zoom", String(zoom));
  const stops = [];
  const labels = document.createDocumentFragment();
  // Allocate text near the wider rim, leaving space at each sector boundary.
  let labelWidth = `${100 * widthFraction}%`;
  rotor.style.setProperty("--wheel-label-size", `min(.7rem, ${122 / Math.min(size, 120)}cqw)`);
  if (size > 2) {
    const sectorSlope = Math.tan(0.92 * Math.PI / size);
    const edge = 50 * sectorSlope;
    rotor.style.setProperty(
      "--wheel-label-clip",
      `polygon(50% 50%, ${50 - edge}% 0%, ${50 + edge}% 0%)`,
    );
    if (!sparse) {
      const labelHeight = "var(--wheel-label-size) * var(--wheel-label-leading, 1) + var(--wheel-label-ink-inset, 0px)";
      labelWidth = `min(${labelWidth}, calc(45cqw - (${labelHeight}) / ${2 * sectorSlope}))`;
    }
  } else {
    rotor.style.removeProperty("--wheel-label-clip");
  }
  rotor.style.setProperty("--wheel-label-width", labelWidth);
  for (let index = 0; index < size; index++) {
    let color = colors[index % colors.length];
    if (index === size - 1 && index > 0 && color === colors[0]) color = colors[1];
    stops.push(`${color} ${index * step}deg ${(index + 1) * step}deg`);
    const offset = Math.abs(index - winner);
    const inZoom = motion && Math.min(offset, size - offset) <= zoomNeighborLimit;
    if (size <= 120 || (spin !== null && (index === winner || inZoom))) {
      const spoke = document.createElement("span");
      spoke.className = "wheel-spoke";
      if (index === winner) spoke.classList.add("wheel-winner");
      if (size > 120 && index !== winner) spoke.dataset.wheelZoomOnly = "";
      spoke.style.setProperty("--spoke-angle", `${index * step}deg`);
      const label = document.createElement("span");
      label.className = "wheel-label";
      label.dataset.wheelIndex = String(index);
      if (sparse) label.style.setProperty("--wheel-label-turn", `${winner * step - index * step}deg`);
      label.textContent = names[index];
      label.title = names[index];
      spoke.append(label);
      labels.append(spoke);
    }
  }
  const hub = document.createElement("span");
  hub.className = "wheel-hub";
  rotor.replaceChildren(labels, hub);
  const gradient = () => `conic-gradient(from ${-step / 2}deg,${stops.join(",")})`;
  rotor.style.background = gradient();
  rotor.style.transform = `rotate(${stopAngle}deg)`;

  wheel.dataset.wheelReady = "";
  if (spin === null) return;
  const showWinner = () => {
    stops[winner] = `#f3cf83 ${winner * step}deg ${(winner + 1) * step}deg`;
    rotor.style.background = gradient();
    wheel.dataset.wheelStopped = "";
    if (motion && !sparse) fitZoom();
    wheel.removeAttribute("data-wheel-spinning");
    status.textContent = `抽到 ${names[winner]}`;
  };
  if (!motion) {
    showWinner();
    return disconnect;
  }
  wheel.dataset.wheelSpinning = "";
  status.textContent = "輪盤轉動中";
  const startAngle = -start * step;
  const endAngle = startAngle + 1800 + ((stopAngle - startAngle + 360) % 360);
  const animation = rotor.animate(
    [{ transform: `rotate(${startAngle}deg)` }, { transform: `rotate(${endAngle}deg)` }],
    { duration: 3400, easing: "cubic-bezier(.12, .55, .22, 1)" },
  );
  animation.onfinish = showWinner;
  return disconnect;
}
