const canvas = document.getElementById("JSCanvas");
const ctx = canvas.getContext("2d");

ctx.strokeStyle = "blue"
ctx.beginPath();
ctx.moveTo(0, 0);
ctx.lineTo(511, 511);
ctx.stroke();

