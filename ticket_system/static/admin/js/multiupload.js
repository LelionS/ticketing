document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll('input[type="file"][multiple]').forEach(input => {
        const dropZone = document.createElement("div");
        dropZone.style.border = "2px dashed #999";
        dropZone.style.padding = "20px";
        dropZone.style.marginBottom = "10px";
        dropZone.innerText = "Drag & drop files here or click to upload";

        input.parentNode.insertBefore(dropZone, input);

        dropZone.addEventListener("click", () => input.click());

        dropZone.addEventListener("dragover", e => {
            e.preventDefault();
            dropZone.style.background = "#eee";
        });

        dropZone.addEventListener("dragleave", () => {
            dropZone.style.background = "";
        });

        dropZone.addEventListener("drop", e => {
            e.preventDefault();
            input.files = e.dataTransfer.files;
        });
    });
});
