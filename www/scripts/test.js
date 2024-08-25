const canvas = document.getElementById("JSCanvas");
const ctx = canvas.getContext("2d");

function draw() {
    ctx.strokeStyle = "#" + Math.floor(Math.random() * 16777216).toString(16).padStart(6, '0')
    ctx.beginPath();
    ctx.moveTo(Math.random() * 511, Math.random() * 511);
    ctx.lineTo(Math.random() * 511, Math.random() * 511);
    ctx.stroke();
}

for (let i = 0; i < 50; i++) {
    draw()
}
