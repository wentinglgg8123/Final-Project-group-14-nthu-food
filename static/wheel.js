const colors = ["#eaf3e6", "#f8e6c7", "#f2d9ce", "#d9e9f4", "#daeade"];

function fitZoomedLabels(viewport, face, zoom) {
  const frame = viewport.getBoundingClientRect();
  const faceWidth = face.getBoundingClientRect().width;
  if (!frame.width || !faceWidth) return;

  // Project each label to the final zoom, even when the zoom transition is still running.
  const scale = zoom * frame.width / faceWidth;
  const center = frame.left + frame.width / 2;
  const x = value => center + (value - center) * scale;
  const y = value => frame.top + (value - frame.top) * scale;
  const inset = 2;
  const cropped = Array.from(face.querySelectorAll(".wheel-label"), label => {
    const box = label.getBoundingClientRect();
    const outside = x(box.left) < frame.left + inset || x(box.right) > frame.right - inset ||
      y(box.top) < frame.top + inset || y(box.bottom) > frame.bottom - inset;
    return [label, outside];
  });
  for (const [label, outside] of cropped) label.toggleAttribute("data-wheel-label-outside", outside);
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
  const fitZoom = () => fitZoomedLabels(viewport, face, zoom);
  let disconnect;
  if (!sparse && spin !== null) {
    const observer = new ResizeObserver(() => {
      if (wheel.hasAttribute("data-wheel-stopped")) fitZoom();
    });
    observer.observe(viewport);
    disconnect = () => observer.disconnect();
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
  wheel.style.setProperty("--wheel-zoom", String(zoom));
  const stops = [];
  const labels = document.createDocumentFragment();
  // Allocate text near the wider rim, leaving space at each sector boundary.
  let labelWidth = size <= 4 ? "30%" : sparse ? "22%" : size <= 12 ? "36%" : size <= 35 ? "25%" : "18%";
  rotor.style.setProperty("--wheel-label-size", `min(.7rem, ${155 / Math.min(size, 120)}cqw)`);
  if (size > 2 && size <= 120) {
    const sectorSlope = Math.tan(0.92 * Math.PI / size);
    const edge = 50 * sectorSlope;
    rotor.style.setProperty(
      "--wheel-label-clip",
      `polygon(50% 50%, ${50 - edge}% 0%, ${50 + edge}% 0%)`,
    );
    if (!sparse) {
      labelWidth = `min(${labelWidth}, calc(45cqw - var(--wheel-label-size) / ${2 * sectorSlope}))`;
    }
  } else {
    rotor.style.removeProperty("--wheel-label-clip");
  }
  rotor.style.setProperty("--wheel-label-width", labelWidth);
  for (let index = 0; index < size; index++) {
    let color = colors[index % colors.length];
    if (index === size - 1 && index > 0 && color === colors[0]) color = colors[1];
    stops.push(`${color} ${index * step}deg ${(index + 1) * step}deg`);
    if (size <= 120 || (spin !== null && index === winner)) {
      const spoke = document.createElement("span");
      spoke.className = "wheel-spoke";
      if (index === winner) spoke.classList.add("wheel-winner");
      spoke.style.setProperty("--spoke-angle", `${index * step}deg`);
      const label = document.createElement("span");
      label.className = "wheel-label";
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
    if (!sparse) fitZoom();
    wheel.dataset.wheelStopped = "";
    wheel.removeAttribute("data-wheel-spinning");
    status.textContent = `抽到 ${names[winner]}`;
  };
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
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
