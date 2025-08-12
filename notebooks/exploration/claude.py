import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Tuple, Optional
import warnings

class GARCHGRUCell(nn.Module):
    """
    Custom GRU cell with integrated GARCH(1,1) volatility dynamics.
    
    This cell combines:
    - Standard GRU operations for sequential modeling
    - GARCH(1,1) volatility estimation 
    - Volatility-aware hidden state updates
    """
    
    def __init__(self, input_size: int, hidden_size: int, 
                 learn_garch_params: bool = True,
                 initial_omega: float = 0.01,
                 initial_alpha: float = 0.1, 
                 initial_beta: float = 0.8,
                 gamma_init: float = 0.1):
        """
        Args:
            input_size: Size of input features
            hidden_size: Size of hidden state
            learn_garch_params: Whether GARCH parameters are learnable
            initial_omega, initial_alpha, initial_beta: Initial GARCH parameters
            gamma_init: Initial value for volatility influence parameter
        """
        super(GARCHGRUCell, self).__init__()
        
        self.input_size = input_size
        self.hidden_size = hidden_size
        
        # Standard GRU parameters
        self.weight_ih = nn.Parameter(torch.randn(3 * hidden_size, input_size))
        self.weight_hh = nn.Parameter(torch.randn(3 * hidden_size, hidden_size))
        self.bias_ih = nn.Parameter(torch.randn(3 * hidden_size))
        self.bias_hh = nn.Parameter(torch.randn(3 * hidden_size))
        
        # GARCH parameters
        if learn_garch_params:
            # Use log-space to ensure positivity, then exp() in forward pass
            self.log_omega = nn.Parameter(torch.log(torch.tensor(initial_omega)))
            self.log_alpha = nn.Parameter(torch.log(torch.tensor(initial_alpha)))
            self.log_beta = nn.Parameter(torch.log(torch.tensor(initial_beta)))
        else:
            self.register_buffer('log_omega', torch.log(torch.tensor(initial_omega)))
            self.register_buffer('log_alpha', torch.log(torch.tensor(initial_alpha)))
            self.register_buffer('log_beta', torch.log(torch.tensor(initial_beta)))
        
        # Volatility integration parameters
        self.volatility_proj = nn.Linear(1, hidden_size)  # Project scalar volatility to hidden dim
        self.gamma = nn.Parameter(torch.tensor(gamma_init))  # Volatility influence weight
        
        self.reset_parameters()
    
    def reset_parameters(self):
        """Initialize parameters using Xavier uniform initialization"""
        std = 1.0 / (self.hidden_size)
        for weight in self.parameters():
            if weight.dim() > 1:
                torch.nn.init.xavier_uniform_(weight)
            else:
                weight.data.uniform_(-std, std)
    
    def get_garch_params(self) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """Get current GARCH parameters, ensuring constraints"""
        omega = torch.exp(self.log_omega)
        alpha = torch.exp(self.log_alpha)
        beta = torch.exp(self.log_beta)
        
        # Ensure stationarity: alpha + beta < 1
        alpha_beta_sum = alpha + beta
        if alpha_beta_sum >= 1.0:
            # Normalize to ensure stationarity
            alpha = alpha / (alpha_beta_sum + 1e-6) * 0.99
            beta = beta / (alpha_beta_sum + 1e-6) * 0.99
            
        return omega, alpha, beta
    
    def update_garch_variance(self, returns: torch.Tensor, 
                            prev_variance: torch.Tensor,
                            prev_error: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Update GARCH(1,1) variance estimate
        
        Args:
            returns: Current returns (batch_size,)
            prev_variance: Previous variance estimate (batch_size,)
            prev_error: Previous error term (batch_size,)
            
        Returns:
            current_variance, current_error
        """
        omega, alpha, beta = self.get_garch_params()
        
        # GARCH(1,1): σ²_t = ω + α*ε²_{t-1} + β*σ²_{t-1}
        current_variance = omega + alpha * (prev_error ** 2) + beta * prev_variance
        
        # Current error (assuming mean = 0 for simplicity)
        current_error = returns
        
        return current_variance, current_error
    
    def forward(self, input: torch.Tensor, hidden: torch.Tensor,
                prev_variance: torch.Tensor, prev_error: torch.Tensor,
                returns: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Forward pass through GARCH-GRU cell
        
        Args:
            input: Input tensor (batch_size, input_size)
            hidden: Previous hidden state (batch_size, hidden_size)
            prev_variance: Previous GARCH variance (batch_size,)
            prev_error: Previous GARCH error (batch_size,)
            returns: Current returns for GARCH update (batch_size,)
            
        Returns:
            new_hidden, current_variance, current_error
        """
        # Standard GRU operations
        gi = F.linear(input, self.weight_ih, self.bias_ih)
        gh = F.linear(hidden, self.weight_hh, self.bias_hh)
        i_r, i_i, i_n = gi.chunk(3, 1)
        h_r, h_i, h_n = gh.chunk(3, 1)
        
        resetgate = torch.sigmoid(i_r + h_r)
        inputgate = torch.sigmoid(i_i + h_i)
        newgate = torch.tanh(i_n + resetgate * h_n)
        
        # Standard GRU hidden state update
        h_hat = (1 - inputgate) * hidden + inputgate * newgate
        
        # Update GARCH variance
        current_variance, current_error = self.update_garch_variance(
            returns, prev_variance, prev_error
        )
        
        # Convert variance to volatility and project to hidden dimension
        volatility = torch.sqrt(current_variance.clamp(min=1e-8))  # Avoid sqrt(0)
        volatility_features = self.volatility_proj(volatility.unsqueeze(-1))  # (batch, hidden_size)
        
        # Integrate volatility information into hidden state
        new_hidden = torch.tanh(h_hat + self.gamma * volatility_features)
        
        return new_hidden, current_variance, current_error


class GARCHGRU(nn.Module):
    """
    Multi-layer GARCH-GRU network for volatility-aware embeddings
    """
    
    def __init__(self, input_size: int, hidden_size: int, num_layers: int = 1,
                 dropout: float = 0.0, learn_garch_params: bool = True,
                 initial_omega: float = 0.01, initial_alpha: float = 0.1, 
                 initial_beta: float = 0.8, gamma_init: float = 0.1):
        """
        Args:
            input_size: Size of input features
            hidden_size: Size of hidden state
            num_layers: Number of GARCH-GRU layers
            dropout: Dropout probability
            learn_garch_params: Whether GARCH parameters are learnable
            initial_omega, initial_alpha, initial_beta: Initial GARCH parameters
            gamma_init: Initial volatility influence parameter
        """
        super(GARCHGRU, self).__init__()
        
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        # Create GARCH-GRU cells for each layer
        self.cells = nn.ModuleList([
            GARCHGRUCell(
                input_size if i == 0 else hidden_size,
                hidden_size,
                learn_garch_params,
                initial_omega,
                initial_alpha, 
                initial_beta,
                gamma_init
            ) for i in range(num_layers)
        ])
        
        self.dropout = nn.Dropout(dropout) if dropout > 0 else None
        
    def forward(self, sequences: torch.Tensor, returns_sequences: torch.Tensor,
                initial_hidden: Optional[torch.Tensor] = None) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Forward pass through multi-layer GARCH-GRU
        
        Args:
            sequences: Input sequences (batch_size, seq_len, input_size)
            returns_sequences: Return sequences for GARCH (batch_size, seq_len)
            initial_hidden: Initial hidden states (num_layers, batch_size, hidden_size)
            
        Returns:
            outputs: All hidden states (batch_size, seq_len, hidden_size)
            final_hidden: Final hidden states (num_layers, batch_size, hidden_size)
        """
        batch_size, seq_len, _ = sequences.size()
        
        # Initialize hidden states and GARCH states
        if initial_hidden is None:
            hidden_states = [torch.zeros(batch_size, self.hidden_size, 
                                       device=sequences.device, dtype=sequences.dtype) 
                           for _ in range(self.num_layers)]
        else:
            hidden_states = [initial_hidden[i] for i in range(self.num_layers)]
        
        # Initialize GARCH states (variance and error)
        garch_variances = [torch.full((batch_size,), 0.01, 
                                    device=sequences.device, dtype=sequences.dtype) 
                         for _ in range(self.num_layers)]
        garch_errors = [torch.zeros(batch_size, 
                                  device=sequences.device, dtype=sequences.dtype) 
                       for _ in range(self.num_layers)]
        
        outputs = []
        
        # Process each timestep
        for t in range(seq_len):
            current_input = sequences[:, t, :]
            current_returns = returns_sequences[:, t]
            
            # Process through each layer
            for layer in range(self.num_layers):
                hidden_states[layer], garch_variances[layer], garch_errors[layer] = \
                    self.cells[layer](
                        current_input,
                        hidden_states[layer],
                        garch_variances[layer],
                        garch_errors[layer], 
                        current_returns
                    )
                
                current_input = hidden_states[layer]
                
                # Apply dropout between layers (not after last layer)
                if self.dropout is not None and layer < self.num_layers - 1:
                    current_input = self.dropout(current_input)
            
            outputs.append(hidden_states[-1])
        
        # Stack outputs: (batch_size, seq_len, hidden_size)
        outputs = torch.stack(outputs, dim=1)
        
        # Stack final hidden states: (num_layers, batch_size, hidden_size)
        final_hidden = torch.stack(hidden_states, dim=0)
        
        return outputs, final_hidden


class VolatilityPredictor(nn.Module):
    """
    Complete GARCH-GRU model with volatility prediction head
    """
    
    def __init__(self, input_size: int, hidden_size: int, num_layers: int = 1,
                 dropout: float = 0.1, learn_garch_params: bool = True,
                 output_volatility: bool = True):
        """
        Args:
            input_size: Size of input features
            hidden_size: Size of hidden state  
            num_layers: Number of GARCH-GRU layers
            dropout: Dropout probability
            learn_garch_params: Whether GARCH parameters are learnable
            output_volatility: Whether to include volatility prediction head
        """
        super(VolatilityPredictor, self).__init__()
        
        self.garch_gru = GARCHGRU(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout,
            learn_garch_params=learn_garch_params
        )
        
        self.output_volatility = output_volatility
        
        if output_volatility:
            # Volatility prediction head (ensures non-negative output)
            self.volatility_head = nn.Sequential(
                nn.Linear(hidden_size, hidden_size // 2),
                nn.ReLU(),
                nn.Dropout(dropout),
                nn.Linear(hidden_size // 2, 1),
                nn.Softplus()  # Ensures positive volatility predictions
            )
    
    def forward(self, sequences: torch.Tensor, returns_sequences: torch.Tensor,
                return_embeddings: bool = False) -> torch.Tensor:
        """
        Forward pass
        
        Args:
            sequences: Input feature sequences (batch_size, seq_len, input_size)
            returns_sequences: Return sequences (batch_size, seq_len)
            return_embeddings: If True, return volatility-aware embeddings
            
        Returns:
            If output_volatility=True: predicted volatilities (batch_size, seq_len, 1)
            If return_embeddings=True: volatility-aware embeddings (batch_size, seq_len, hidden_size)
        """
        # Get GARCH-GRU outputs (volatility-aware embeddings)
        embeddings, _ = self.garch_gru(sequences, returns_sequences)
        
        if return_embeddings:
            return embeddings
        
        if self.output_volatility:
            # Predict volatility from embeddings
            volatility_pred = self.volatility_head(embeddings)
            return volatility_pred
        else:
            return embeddings


# Training utilities
class GARCHGRUTrainer:
    """Utility class for training GARCH-GRU models"""
    
    def __init__(self, model: VolatilityPredictor, lr: float = 0.001):
        self.model = model
        self.optimizer = torch.optim.Adam(model.parameters(), lr=lr)
        self.criterion = nn.MSELoss()
        
    def train_step(self, sequences: torch.Tensor, returns_sequences: torch.Tensor,
                   target_volatility: torch.Tensor) -> float:
        """Single training step"""
        self.model.train()
        self.optimizer.zero_grad()
        
        # Forward pass
        pred_volatility = self.model(sequences, returns_sequences)
        
        # Compute loss
        loss = self.criterion(pred_volatility.squeeze(-1), target_volatility)
        
        # Backward pass
        loss.backward()
        
        # Gradient clipping for stability
        torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
        
        self.optimizer.step()
        
        return loss.item()
    
    def validate(self, sequences: torch.Tensor, returns_sequences: torch.Tensor,
                target_volatility: torch.Tensor) -> float:
        """Validation step"""
        self.model.eval()
        with torch.no_grad():
            pred_volatility = self.model(sequences, returns_sequences)
            loss = self.criterion(pred_volatility.squeeze(-1), target_volatility)
        return loss.item()


# Example usage and data preparation
def prepare_financial_data(returns: np.ndarray, features: Optional[np.ndarray] = None,
                          sequence_length: int = 20) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """
    Prepare financial data for GARCH-GRU training
    
    Args:
        returns: Array of returns (n_samples,)
        features: Additional features (n_samples, n_features) or None
        sequence_length: Length of input sequences
        
    Returns:
        sequences, returns_sequences, target_volatility
    """
    n_samples = len(returns)
    
    # If no features provided, use lagged returns as features
    if features is None:
        features = np.column_stack([
            np.roll(returns, i) for i in range(1, 6)  # 5 lagged returns
        ])
        features = features[5:]  # Remove first 5 rows due to rolling
        returns = returns[5:]
        n_samples = len(returns)
    
    # Create sequences
    sequences_list = []
    returns_sequences_list = []
    target_vol_list = []
    
    for i in range(sequence_length, n_samples):
        # Input sequence
        seq_features = features[i-sequence_length:i]
        seq_returns = returns[i-sequence_length:i]
        
        sequences_list.append(seq_features)
        returns_sequences_list.append(seq_returns)
        
        # Target: realized volatility (could be GARCH-estimated or realized vol)
        # Here we use a simple rolling standard deviation as proxy
        target_vol = np.std(returns[i-sequence_length:i])
        target_vol_list.append(target_vol)
    
    sequences = torch.FloatTensor(np.array(sequences_list))
    returns_sequences = torch.FloatTensor(np.array(returns_sequences_list))
    target_volatility = torch.FloatTensor(np.array(target_vol_list))
    
    return sequences, returns_sequences, target_volatility


# Demo function
def demo_garch_gru():
    """Demonstration of GARCH-GRU model"""
    # Generate synthetic financial data
    np.random.seed(42)
    n_samples = 1000
    
    # Simulate GARCH-like returns
    returns = []
    sigma_t = 0.02  # Initial volatility
    for t in range(n_samples):
        epsilon = np.random.normal(0, 1)
        r_t = sigma_t * epsilon
        returns.append(r_t)
        
        # Update volatility (simple GARCH simulation)
        sigma_t = np.sqrt(0.01 + 0.1 * r_t**2 + 0.8 * sigma_t**2)
    
    returns = np.array(returns)
    
    # Prepare data
    sequences, returns_sequences, target_volatility = prepare_financial_data(
        returns, sequence_length=20
    )
    
    print(f"Data shapes:")
    print(f"Sequences: {sequences.shape}")
    print(f"Returns sequences: {returns_sequences.shape}")
    print(f"Target volatility: {target_volatility.shape}")
    
    # Create model
    model = VolatilityPredictor(
        input_size=sequences.shape[-1],  # Number of features
        hidden_size=32,
        num_layers=2,
        dropout=0.1,
        learn_garch_params=True
    )
    
    print(f"\nModel created with {sum(p.numel() for p in model.parameters())} parameters")
    
    # Quick forward pass test
    model.eval()
    with torch.no_grad():
        # Test volatility prediction
        pred_vol = model(sequences[:10], returns_sequences[:10])
        print(f"Prediction shape: {pred_vol.shape}")
        
        # Test embedding extraction
        embeddings = model(sequences[:10], returns_sequences[:10], return_embeddings=True)
        print(f"Embeddings shape: {embeddings.shape}")
    
    print("\nGARCH-GRU model demo completed successfully!")

if __name__ == "__main__":
    demo_garch_gru()