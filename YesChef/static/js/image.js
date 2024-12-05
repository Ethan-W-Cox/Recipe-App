document.addEventListener("DOMContentLoaded", () => {
    const uploadImageButton = document.getElementById("uploadImageButton");
    const uploadedThumbnail = document.getElementById("uploadedThumbnail");

    uploadImageButton.addEventListener("click", () => {
        // Create a file input dynamically
        const fileInput = document.createElement("input");
        fileInput.type = "file";
        fileInput.accept = "image/*";

        fileInput.addEventListener("change", (event) => {
            const file = event.target.files[0];
            if (file) {
                // Generate a URL for the uploaded image
                const imageUrl = URL.createObjectURL(file);

                // Display the thumbnail
                uploadedThumbnail.src = imageUrl;
                uploadedThumbnail.style.display = "block";
            }
        });

        // Trigger the file input click event to open the file chooser
        fileInput.click();
    });
});
