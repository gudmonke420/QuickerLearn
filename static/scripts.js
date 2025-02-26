async function sendMessage() {
    let input = document.getElementById("user-input");
    let chatHistory = document.getElementById("chat-history");

    let userMessage = input.value;
    if (!userMessage) return;

    chatHistory.innerHTML += `<div class='message user'>${userMessage}</div>`;
    input.value = "";

    try {
        let response = await fetch("/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: userMessage })
        });

        let data = await response.json();
        chatHistory.innerHTML += `<div class='message bot'>${data.reply}</div>`;

        // Scroll to the latest message
        chatHistory.scrollTop = chatHistory.scrollHeight;

    } catch (error) {
        chatHistory.innerHTML += `<div class='message bot'>Error: Could not connect</div>`;
    }
}
