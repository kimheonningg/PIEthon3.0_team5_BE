from PIL import Image
import torch
from transformers import AutoImageProcessor, AutoModelForImageClassification
import os


# Load model and processor
processor = AutoImageProcessor.from_pretrained("codewithdark/vit-chest-xray")
model = AutoModelForImageClassification.from_pretrained("codewithdark/vit-chest-xray")

print(model)

# Define label columns (class names)
label_columns = ['Cardiomegaly', 'Edema', 'Consolidation', 'Pneumonia', 'No Finding']


image_list = os.listdir('./example_images/')
for image_path in image_list:
    # Open the image
    image = Image.open(os.path.join('./example_images/', image_path))

    # Ensure the image is in RGB mode (required by most image classification models)
    if image.mode != 'RGB':
        image = image.convert('RGB')
        print("Image converted to RGB.")

    # Step 2: Preprocess the image using the processor
    inputs = processor(images=image, return_tensors="pt")

    # Step 3: Make a prediction (using the model)
    with torch.no_grad():  # Disable gradient computation during inference
        outputs = model(**inputs)

    # Step 4: Extract logits and get the predicted class index
    logits = outputs.logits  # Raw logits from the model
    predicted_class_idx = torch.argmax(logits, dim=-1).item()  # Get the class index

    # Step 5: Map the predicted index to a class label
    # You can also use `model.config.id2label`, but we'll use `label_columns` for this task
    predicted_class_label = label_columns[predicted_class_idx]

    # Output the results
    print(f"original Class Label : {image_path[:-4]}")
    print(f"Predicted Class Index: {predicted_class_idx}")
    print(f"Predicted Class Label: {predicted_class_label}")

'''
Output :
Predicted Class Index: 4
Predicted Class Label: No Finding
'''