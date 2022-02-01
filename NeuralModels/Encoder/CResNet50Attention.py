import torch.nn as nn
import torch
import torchvision.models as models

class CResNet50Attention(nn.Module):
    def __init__(self, encoder_dim: int, number_of_splits: int = 3, device: str = "cpu"):
        """Constructor of the Encoder NN

        Args:
            encoder_dim (int): Unused. Internally resnet with 2 layers removed represent each pixel in a vector of 2048 components.
            
            number_of_splits (int):
                How many pieces do you want to split the images, for border.
                    Examples:
                        number_of_splits = 3 -> The images will be splitted into 9 pieces (3x3). 
                
            device (str, optional): Default "cpu".
                The device on which the operations will be performed. 
        """
        super(CResNet50Attention, self).__init__()
        
        self.device = torch.device(device)
        resnet = models.resnet50(pretrained=True)
        for param in resnet.parameters(): # Freezing weights 
            param.requires_grad_(False)
        
        modules = list(resnet.children())[:-2]   # Expose the last convolutional layer. 512 Filters of size 3x3. Output of the ConvLayer -> (H_in/32,W_in/32,512) 
        
        self.encoder_dim = 2048 
        
        self.number_of_splits = number_of_splits
        
        # Q. Why (H_in/32, W_in/32)
        # A. Due to the resnet50 implementation, each convolutional layer will reduce the dimensionality of Heigth and Width by 2 times.
        
        self.resnet = nn.Sequential(*modules)
        
        # Applies a 2D adaptive average pooling over an input signal composed of several input planes.
        self.avg = torch.nn.AdaptiveAvgPool2d((number_of_splits, number_of_splits)) # IN : (batch_dim, 2048, Heigth/32, Width/32) -> OUT : (batch_dim, 2048, H_splits, W_splits)
        
    def forward(self, images: torch.Tensor) -> torch.Tensor:
        """Forward operation of the nn

        Args:
            images (torch.tensor):  `(batch_dim, Channels, Width, Height)`
                The tensor of the images.

        Returns:
            [torch.tensor]: `(batch_dim, H_splits, W_splits, encoder_dim)`
                Features Projection Tensor 
        """
        
        features = self.resnet(images) # Out: (batch_dim, Heigth/32, Width/32, 512) 
        features = self.avg(features)  # Out: (batch_dim, 2048, H_splits, W_splits)
        features = features.permute(0, 2, 3, 1)  # (batch_dim, H_splits, W_splits, 2048)
        return features