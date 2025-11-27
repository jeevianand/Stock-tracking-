// create floating hearts
function createHeart() {
    const heart = document.createElement("div");
    heart.className = "heart";
    heart.innerText = "❤";

    let leftPos = Math.random() * 100; 
    heart.style.left = leftPos + "vw";

    let size = Math.random() * 20 + 15;
    heart.style.fontSize = size + "px";

    document.getElementById("hearts-container").appendChild(heart);

    setTimeout(() => {
        heart.remove();
    }, 4000);
}

setInterval(createHeart, 300);

// after animation, go to home page
setTimeout(() => {
    window.location.href = "/add_trade_page";
}, 6200);
