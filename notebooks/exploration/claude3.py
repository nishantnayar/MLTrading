import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

class AssetEmbeddingGRU(nn.Module):
    """
    GRU-based encoder for generating dynamic asset embeddings
    """
    def __init__(self, input_dim, hidden_dim=64, embedding_dim=32, 
                 num_layers=2, dropout=0.2):
        super(AssetEmbeddingGRU, self).__init__()
        
        self.hidden_dim = hidden_dim
        self.embedding_dim = embedding_dim
        self.num_layers = num_layers
        
        # Input normalization
        self.input_norm = nn.LayerNorm(input_dim)
        
        # GRU layers
        self.gru = nn.GRU(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            dropout=dropout if num_layers > 1 else 0,
            batch_first=True,
            bidirectional=False
        )
        
        # Embedding projection layers
        self.embedding_layers = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, embedding_dim),
            nn.Tanh()  # Normalize embeddings to [-1, 1]
        )
        
        # Reconstruction head (for self-supervised training)
        self.reconstruction_head = nn.Sequential(
            nn.Linear(embedding_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, input_dim)
        )
        
    def forward(self, x):
        """
        Forward pass
        Args:
            x: (batch_size, sequence_length, input_dim)
        Returns:
            embeddings: (batch_size, embedding_dim)
            reconstruction: (batch_size, sequence_length, input_dim)
        """
        batch_size, seq_len, _ = x.shape
        
        # Normalize input
        x_norm = self.input_norm(x)
        
        # GRU forward pass
        gru_out, hidden = self.gru(x_norm)
        
        # Use final hidden state for embedding
        final_hidden = hidden[-1]  # (batch_size, hidden_dim)
        
        # Generate embedding
        embeddings = self.embedding_layers(final_hidden)
        
        # Reconstruction (for training)
        reconstruction = self.reconstruction_head(embeddings)
        reconstruction = reconstruction.unsqueeze(1).repeat(1, seq_len, 1)
        
        return embeddings, reconstruction

class AssetSequenceDataset(Dataset):
    """
    Dataset for training the GRU embedding model
    """
    def __init__(self, sequences, symbols, dates):
        self.sequences = torch.FloatTensor(sequences)
        self.symbols = symbols
        self.dates = dates
        
    def __len__(self):
        return len(self.sequences)
    
    def __getitem__(self, idx):
        return {
            'sequence': self.sequences[idx],
            'symbol': self.symbols[idx],
            'date': self.dates[idx]
        }

class DynamicPairSelector:
    """
    Main class for GRU-based dynamic pair selection
    """
    def __init__(self, input_dim, hidden_dim=64, embedding_dim=32, 
                 num_layers=2, dropout=0.2, device='cpu'):
        self.device = device
        self.model = AssetEmbeddingGRU(
            input_dim=input_dim,
            hidden_dim=hidden_dim,
            embedding_dim=embedding_dim,
            num_layers=num_layers,
            dropout=dropout
        ).to(device)
        
        self.scaler = StandardScaler()
        self.is_trained = False
        
    def prepare_data(self, splits):
        """
        Prepare data for training
        """
        # Combine all sequences for scaling
        all_sequences = np.concatenate([
            splits['train']['sequences'],
            splits['val']['sequences'],
            splits['test']['sequences']
        ])
        
        # Fit scaler on training data only
        train_sequences_flat = splits['train']['sequences'].reshape(-1, 
                                splits['train']['sequences'].shape[-1])
        self.scaler.fit(train_sequences_flat)
        
        # Scale all splits
        scaled_splits = {}
        for split_name, split_data in splits.items():
            sequences = split_data['sequences']
            original_shape = sequences.shape
            sequences_flat = sequences.reshape(-1, sequences.shape[-1])
            sequences_scaled = self.scaler.transform(sequences_flat)
            sequences_scaled = sequences_scaled.reshape(original_shape)
            
            scaled_splits[split_name] = {
                'sequences': sequences_scaled,
                'symbols': split_data['symbols'],
                'dates': split_data['dates']
            }
            
        return scaled_splits
    
    def train_model(self, splits, epochs=100, batch_size=64, lr=0.001,
                   early_stopping_patience=10, reconstruction_weight=1.0):
        """
        Train the GRU embedding model
        """
        print("Preparing data...")
        scaled_splits = self.prepare_data(splits)
        
        # Create datasets
        train_dataset = AssetSequenceDataset(
            scaled_splits['train']['sequences'],
            scaled_splits['train']['symbols'], 
            scaled_splits['train']['dates']
        )
        val_dataset = AssetSequenceDataset(
            scaled_splits['val']['sequences'],
            scaled_splits['val']['symbols'],
            scaled_splits['val']['dates']
        )
        
        # Create dataloaders
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
        
        # Setup training
        optimizer = optim.Adam(self.model.parameters(), lr=lr)
        scheduler = optim.lr_scheduler.ReduceLROnPlateau(
            optimizer, mode='min', patience=5, factor=0.5, verbose=True
        )
        
        # Training loop
        train_losses = []
        val_losses = []
        best_val_loss = float('inf')
        patience_counter = 0
        
        print(f"Training for {epochs} epochs...")
        
        for epoch in range(epochs):
            # Training phase
            self.model.train()
            train_loss = 0.0
            
            for batch in train_loader:
                sequences = batch['sequence'].to(self.device)
                
                optimizer.zero_grad()
                
                # Forward pass
                embeddings, reconstruction = self.model(sequences)
                
                # Reconstruction loss
                recon_loss = nn.MSELoss()(reconstruction, sequences)
                
                # Embedding regularization (encourage diversity)
                embedding_std = torch.std(embeddings, dim=0).mean()
                regularization = -0.01 * embedding_std  # Encourage diversity
                
                total_loss = reconstruction_weight * recon_loss + regularization
                
                total_loss.backward()
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
                optimizer.step()
                
                train_loss += total_loss.item()
            
            # Validation phase
            self.model.eval()
            val_loss = 0.0
            
            with torch.no_grad():
                for batch in val_loader:
                    sequences = batch['sequence'].to(self.device)
                    embeddings, reconstruction = self.model(sequences)
                    
                    recon_loss = nn.MSELoss()(reconstruction, sequences)
                    embedding_std = torch.std(embeddings, dim=0).mean()
                    regularization = -0.01 * embedding_std
                    
                    total_loss = reconstruction_weight * recon_loss + regularization
                    val_loss += total_loss.item()
            
            train_loss /= len(train_loader)
            val_loss /= len(val_loader)
            
            train_losses.append(train_loss)
            val_losses.append(val_loss)
            
            # Learning rate scheduling
            scheduler.step(val_loss)
            
            # Early stopping
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                patience_counter = 0
                # Save best model
                torch.save(self.model.state_dict(), 'best_embedding_model.pth')
            else:
                patience_counter += 1
            
            if epoch % 10 == 0 or epoch == epochs - 1:
                print(f"Epoch {epoch+1}/{epochs}")
                print(f"  Train Loss: {train_loss:.6f}")
                print(f"  Val Loss: {val_loss:.6f}")
                print(f"  Best Val Loss: {best_val_loss:.6f}")
            
            if patience_counter >= early_stopping_patience:
                print(f"Early stopping at epoch {epoch+1}")
                break
        
        # Load best model
        self.model.load_state_dict(torch.load('best_embedding_model.pth'))
        self.is_trained = True
        
        # Plot training history
        self._plot_training_history(train_losses, val_losses)
        
        return train_losses, val_losses
    
    def _plot_training_history(self, train_losses, val_losses):
        """Plot training and validation losses"""
        plt.figure(figsize=(12, 4))
        
        plt.subplot(1, 2, 1)
        plt.plot(train_losses, label='Train Loss', alpha=0.7)
        plt.plot(val_losses, label='Validation Loss', alpha=0.7)
        plt.xlabel('Epoch')
        plt.ylabel('Loss')
        plt.title('Training History')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        plt.subplot(1, 2, 2)
        plt.plot(train_losses[-50:], label='Train Loss (Last 50)', alpha=0.7)
        plt.plot(val_losses[-50:], label='Val Loss (Last 50)', alpha=0.7)
        plt.xlabel('Epoch')
        plt.ylabel('Loss')
        plt.title('Training History (Zoomed)')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()
    
    def generate_embeddings(self, sequences, symbols, dates, batch_size=64):
        """
        Generate embeddings for given sequences
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before generating embeddings")
        
        # Scale sequences
        original_shape = sequences.shape
        sequences_flat = sequences.reshape(-1, sequences.shape[-1])
        sequences_scaled = self.scaler.transform(sequences_flat)
        sequences_scaled = sequences_scaled.reshape(original_shape)
        
        # Create dataset and dataloader
        dataset = AssetSequenceDataset(sequences_scaled, symbols, dates)
        dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=False)
        
        embeddings_list = []
        symbols_list = []
        dates_list = []
        
        self.model.eval()
        with torch.no_grad():
            for batch in dataloader:
                sequences_batch = batch['sequence'].to(self.device)
                embeddings, _ = self.model(sequences_batch)
                
                embeddings_list.append(embeddings.cpu().numpy())
                symbols_list.extend(batch['symbol'])
                dates_list.extend(batch['date'])
        
        embeddings_array = np.vstack(embeddings_list)
        
        return embeddings_array, symbols_list, dates_list
    
    def find_dynamic_pairs(self, embeddings, symbols, dates, 
                          top_k_pairs=20, similarity_threshold=0.7,
                          exclude_same_sector=True):
        """
        Find pairs based on embedding similarity
        """
        # Calculate cosine similarity matrix
        similarity_matrix = cosine_similarity(embeddings)
        
        # Create DataFrame for easier manipulation
        embedding_df = pd.DataFrame({
            'symbol': symbols,
            'date': dates,
            **{f'emb_{i}': embeddings[:, i] for i in range(embeddings.shape[1])}
        })
        
        # Group by date to find pairs for each time period
        pairs_by_date = defaultdict(list)
        
        unique_dates = sorted(set(dates))
        
        for date in unique_dates:
            date_mask = embedding_df['date'] == date
            date_embeddings = embeddings[date_mask]
            date_symbols = np.array(symbols)[date_mask]
            
            if len(date_embeddings) < 2:
                continue
            
            # Calculate similarity for this date
            date_similarity = cosine_similarity(date_embeddings)
            
            # Find top pairs
            pairs = []
            n_assets = len(date_symbols)
            
            for i in range(n_assets):
                for j in range(i + 1, n_assets):
                    similarity = date_similarity[i, j]
                    
                    if similarity >= similarity_threshold:
                        pairs.append({
                            'asset1': date_symbols[i],
                            'asset2': date_symbols[j],
                            'similarity': similarity,
                            'date': date
                        })
            
            # Sort by similarity and take top k
            pairs.sort(key=lambda x: x['similarity'], reverse=True)
            pairs_by_date[date] = pairs[:top_k_pairs]
        
        return pairs_by_date
    
    def analyze_embedding_evolution(self, embeddings, symbols, dates):
        """
        Analyze how embeddings evolve over time
        """
        # Create DataFrame
        df = pd.DataFrame({
            'symbol': symbols,
            'date': pd.to_datetime(dates),
            **{f'emb_{i}': embeddings[:, i] for i in range(embeddings.shape[1])}
        })
        
        # Calculate embedding stability over time
        stability_metrics = {}
        
        for symbol in df['symbol'].unique():
            symbol_df = df[df['symbol'] == symbol].sort_values('date')
            if len(symbol_df) < 2:
                continue
            
            # Calculate embedding changes over time
            embedding_cols = [col for col in df.columns if col.startswith('emb_')]
            embeddings_ts = symbol_df[embedding_cols].values
            
            # Calculate consecutive differences
            diffs = np.diff(embeddings_ts, axis=0)
            embedding_velocity = np.linalg.norm(diffs, axis=1)
            
            stability_metrics[symbol] = {
                'mean_velocity': np.mean(embedding_velocity),
                'std_velocity': np.std(embedding_velocity),
                'max_velocity': np.max(embedding_velocity),
                'volatility': np.std(embedding_velocity) / (np.mean(embedding_velocity) + 1e-8)
            }
        
        return stability_metrics
    
    def visualize_embeddings(self, embeddings, symbols, dates, method='tsne'):
        """
        Visualize embeddings in 2D space
        """
        from sklearn.manifold import TSNE
        from sklearn.decomposition import PCA
        
        # Reduce dimensionality for visualization
        if method == 'tsne':
            reducer = TSNE(n_components=2, random_state=42, perplexity=min(30, len(embeddings)//2))
        else:  # PCA
            reducer = PCA(n_components=2, random_state=42)
        
        embeddings_2d = reducer.fit_transform(embeddings)
        
        # Create visualization
        plt.figure(figsize=(15, 5))
        
        # Plot 1: All embeddings colored by symbol
        plt.subplot(1, 3, 1)
        unique_symbols = list(set(symbols))
        colors = plt.cm.tab20(np.linspace(0, 1, len(unique_symbols)))
        
        for i, symbol in enumerate(unique_symbols):
            symbol_mask = np.array(symbols) == symbol
            if symbol_mask.sum() > 0:
                plt.scatter(embeddings_2d[symbol_mask, 0], embeddings_2d[symbol_mask, 1],
                           c=[colors[i]], label=symbol, alpha=0.7, s=20)
        
        plt.xlabel(f'{method.upper()} Component 1')
        plt.ylabel(f'{method.upper()} Component 2')
        plt.title('Asset Embeddings by Symbol')
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        
        # Plot 2: Embeddings colored by time
        plt.subplot(1, 3, 2)
        dates_numeric = pd.to_datetime(dates).map(pd.Timestamp.timestamp)
        scatter = plt.scatter(embeddings_2d[:, 0], embeddings_2d[:, 1],
                            c=dates_numeric, cmap='viridis', alpha=0.7, s=20)
        plt.colorbar(scatter, label='Time')
        plt.xlabel(f'{method.upper()} Component 1')
        plt.ylabel(f'{method.upper()} Component 2')
        plt.title('Asset Embeddings Over Time')
        
        # Plot 3: Embedding density
        plt.subplot(1, 3, 3)
        plt.hexbin(embeddings_2d[:, 0], embeddings_2d[:, 1], gridsize=20, cmap='Blues')
        plt.colorbar(label='Density')
        plt.xlabel(f'{method.upper()} Component 1')
        plt.ylabel(f'{method.upper()} Component 2')
        plt.title('Embedding Density')
        
        plt.tight_layout()
        plt.show()

# Example usage and testing
def example_usage():
    """
    Example of how to use the DynamicPairSelector
    """
    # Assuming you have your splits from create_chronological_splits_updated
    # splits = create_chronological_splits_updated(sequences, dates, symbols)
    
    # Initialize the pair selector
    input_dim = 5  # price, volume, returns, etc.
    selector = DynamicPairSelector(
        input_dim=input_dim,
        hidden_dim=64,
        embedding_dim=32,
        num_layers=2,
        dropout=0.2,
        device='cuda' if torch.cuda.is_available() else 'cpu'
    )
    
    print("Dynamic Pair Selector initialized!")
    print("Next steps:")
    print("1. Train the model: selector.train_model(splits)")
    print("2. Generate embeddings: embeddings, symbols, dates = selector.generate_embeddings(...)")
    print("3. Find pairs: pairs = selector.find_dynamic_pairs(embeddings, symbols, dates)")
    print("4. Analyze evolution: stability = selector.analyze_embedding_evolution(...)")
    print("5. Visualize: selector.visualize_embeddings(...)")

if __name__ == "__main__":
    example_usage()