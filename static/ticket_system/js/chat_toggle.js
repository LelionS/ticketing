document.addEventListener("DOMContentLoaded", function() {
    const chatContainer = document.querySelector(".chat-container");
    const chatInput = document.querySelector(".chat-input textarea");
    const sendButton = document.querySelector(".chat-input button");

    // Scroll to last message initially
    if(chatContainer){
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    // Handle send button click
    if(sendButton && chatInput){
        sendButton.addEventListener("click", () => {
            if(chatInput.value.trim() !== ""){
                // Submit the Django admin form
                chatInput.form.submit();
            }
        });
    }

    // Pressing Enter submits message
    if(chatInput){
        chatInput.addEventListener("keypress", (e) => {
            if(e.key === "Enter" && !e.shiftKey){
                e.preventDefault();
                sendButton.click();
            }
        });
    }
});