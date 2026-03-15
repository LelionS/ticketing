document.addEventListener("DOMContentLoaded", function() {
    const chatBubbles = document.querySelectorAll(".chat-bubble");

    // Hide all but the last 5 messages initially
    chatBubbles.forEach((bubble, index) => {
        if (index < chatBubbles.length - 5) {
            bubble.style.display = "none";
        }
    });

    // Add a toggle button
    if(chatBubbles.length > 5){
        const toggleButton = document.createElement("button");
        toggleButton.innerText = "Show Older Messages";
        toggleButton.type = "button";
        toggleButton.style.marginBottom = "8px";
        toggleButton.addEventListener("click", () => {
            chatBubbles.forEach(bubble => bubble.style.display = "");
            toggleButton.style.display = "none";
        });
        chatBubbles[0].parentNode.insertBefore(toggleButton, chatBubbles[0]);
    }
});